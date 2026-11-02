"""HA transport, authenticated responses and durable configuration."""
from __future__ import annotations
import asyncio
from copy import deepcopy
from datetime import timedelta
from time import time
import logging
from uuid import uuid4

from homeassistant.core import Context
from homeassistant.exceptions import HomeAssistantError, Unauthorized
from homeassistant.helpers.storage import Store
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CHANNELS, LABELS, EVENT, TYPES
from .model import AlarmModel, stamp
from .charts import cleanup_history_images

_LOGGER = logging.getLogger(__name__)


class AlarmEngine:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.store = Store(hass, 1, f"{DOMAIN}.registry_and_events", private=True,
                           atomic_writes=True, serialize_in_event_loop=False)
        self.model = AlarmModel(site_id=entry.data["site_id"])
        self.lock = asyncio.Lock()
        self.transport = asyncio.Lock()
        self.persistence = asyncio.Lock()
        self.tasks = set()
        self.confirmations = {}  # short-lived, actor/incident-bound; not persisted
        self.unsub = []
        self._last_purge = 0
        self.setup_running = set()
        self.setup_receipts = {}
        self.playback_receipts = {}
        self.recovering = False
        self.stopping = False
        self.open_popups = {}
        self.popup_lock = asyncio.Lock()
        self.running_cycles = set()
        self.transport_dirty = False
        self.transport_save_task = None
        self.completed_confirmations = {}
        self.recovery_task = None

    async def start(self):
        self.recovering = True
        await cleanup_history_images(self.hass)
        saved = await self.store.async_load()
        if saved:
            self.model = AlarmModel(saved)
        self.unsub.append(async_track_time_interval(self.hass, self.tick, timedelta(seconds=1)))
        self.unsub.append(self.hass.bus.async_listen("mobile_app_notification_action", self.mobile_response))
        self.unsub.append(self.hass.bus.async_listen("state_changed", self.state_changed))
        self.unsub.append(self.hass.bus.async_listen("mobile_app_notification_received", self.setup_received))
        await self.refresh_names()
        # Recover an interrupted playback lease before repeating any persisted open alarm.
        self.spawn(self.recover())

    def spawn(self, coro):
        task = self.hass.async_create_background_task(coro, "alarm_system worker")
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    async def recover(self):
        self.recovering = True
        try:
            async with self.transport:
                await self.stop_devices()
            for source in list(self.model.data["sources"].values()):
                state = self.sensor(source["entity_id"])
                await self.receive_signal(source["entity_id"], state)
            for i in self.model.active():
                if i.get('test_device'):
                    for sid, source in i['sources'].items():
                        if source['active']:
                            self.model.end_source(i['id'], sid, None)
                    self.model.log('test_aborted', incident=i, text='Gerätetest nach HA-Neustart beendet')
                elif i["status"] == "open":
                    i["next_due"] = 0
            await self.save()
        finally:
            self.recovering = False

    async def stop(self):
        self.stopping = True
        for unsub in self.unsub:
            unsub()
        for task in list(self.tasks):
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        async with self.transport:
            await self.stop_devices()
        await self.save()

    async def save(self, publish=True):
        started = time()
        async with self.persistence:
            await self.store.async_save(self.model.snapshot())
        if publish:
            self.publish()
        elapsed = round((time()-started)*1000)
        if elapsed > 500:
            _LOGGER.warning("Alarmspeicherung benötigte %s ms", elapsed)

    def defer_transport_save(self):
        # Transport history is batched. Configuration, incident transitions and
        # recovery leases still use an awaited durable save.
        self.transport_dirty = True
        if self.stopping:
            return  # stop() performs the final durable write.
        if not self.transport_save_task or self.transport_save_task.done():
            self.transport_save_task = self.spawn(self.flush_transport())

    async def flush_transport(self):
        while self.transport_dirty:
            await asyncio.sleep(0.25)
            self.transport_dirty = False
            await self.save(publish=False)

    def publish(self):
        active = self.model.active()
        self.hass.states.async_set("sensor.alarm_system_active", len(active), {
            "friendly_name": "Aktive Alarme", "icon": "mdi:alarm-light",
            # Detailed incidents are exposed only through the account-filtered API.
        })
        self.hass.bus.async_fire(EVENT)

    async def refresh_names(self):
        for u in await self.hass.auth.async_get_users():
            if u.id in self.model.data["users"]:
                self.model.data["users"][u.id]["name"] = u.name or u.id
        await self.save()

    async def actor(self, user_id, incident=None, admin=False):
        user = await self.hass.auth.async_get_user(user_id) if user_id else None
        if not user or not user.is_active:
            raise Unauthorized("Antwort erfordert angemeldeten HA-Benutzer")
        if admin and not user.is_admin:
            raise Unauthorized("Nur Administratoren dürfen die Konfiguration ändern")
        if incident and incident.get("test_device") and not user.is_admin and self.model.data["devices"].get(incident["test_device"], {}).get("user_id") != user.id:
            raise Unauthorized("Dieser Gerätetest gehört zu einem anderen Benutzer")
        if incident and not (user.is_admin or self.model.authorized(user.id, incident)):
            raise Unauthorized("Benutzer ist kein Empfänger dieser Alarmart")
        return user

    async def dispatch(self, data, user_id=None):
        # Logic from automations/Node-RED can have no user context. Authenticated manual calls
        # must be admins, or registered recipients for the corresponding type.
        if user_id:
            await self.actor(user_id, {"type": data["type"]})
        if data["type"] in ("INFO", "WARNING"):
            await self.simple_message(data)
            return
        async with self.lock:
            incident, result = self.model.raise_alarm(data)
            self.model.log("alarm_raised" if result == "new" else result, kind=data["type"], incident=incident,
                source={"id": data.get("source_id", ""), **data, "name": data.get("source_name", "")}, user_id=user_id)
            await self.save()
        if result == "new":
            self.spawn(self.cycle(incident["id"]))
        elif result == "source_added":
            self.spawn(self.status(incident, f'Zusätzliche Meldung: {data.get("source_name", data["source_id"])}', popup=True))

    async def respond(self, incident_id, action, user_id, source_id=None, token=None, background=False):
        async with self.lock:
            i = self.model.data["incidents"].get(incident_id)
            if not i:
                raise HomeAssistantError("Alarm nicht gefunden")
            user = await self.actor(user_id, i)
            if action == 'seen':
                if self.model.view(incident_id, user.id, user.name):
                    self.model.log('viewed', incident=i, user_id=user.id, user_name=user.name)
                    self.publish()
                    self.defer_transport_save()
                return None
            if action == "coming" and i.get("responses", {}).get(user.id, {}).get("answer") == "coming":
                return None
            if action == "end_source" and source_id in i["sources"] and not i["sources"][source_id]["active"]:
                return None
            if action == "request_false":
                for existing, confirmation in self.confirmations.items():
                    if confirmation[:2] == (user.id, incident_id) and confirmation[2] > time():
                        return existing
            if action == "false_alarm" and i["status"] == "false_alarm" and self.completed_confirmations.get(token, ())[:2] == (user.id, incident_id) and self.completed_confirmations[token][2] > time():
                return None
            self.model.log("response_requested", incident=i, user_id=user.id, user_name=user.name,
                source=i["sources"].get(source_id, {}), details={"requested_action": action})
            if action == "request_false":
                token = uuid4().hex
                self.confirmations[token] = (user.id, incident_id, time()+60)
                self.model.audit(i, "false_alarm_requested", user.id)
                self.model.log("false_alarm_requested", incident=i, user_id=user.id, user_name=user.name)
                # The token is intentionally in-memory. Opening a confirmation
                # must not wait for disk I/O or hold the response lock during it.
                self.defer_transport_save()
                return token
            if action == "cancel_false":
                confirmation = self.confirmations.pop(token, None)
                if not confirmation or confirmation[:2] != (user.id, incident_id):
                    await self.save()
                    raise HomeAssistantError("Bestätigung gehört nicht zu diesem Benutzer und Ereignis")
                self.model.audit(i, "false_alarm_cancelled", user.id)
                self.model.log("false_alarm_cancelled", incident=i, user_id=user.id, user_name=user.name)
                self.defer_transport_save()
                return None
            if action == "false_alarm":
                confirmation = self.confirmations.pop(token, None)
                if not confirmation or confirmation[:2] != (user.id, incident_id) or confirmation[2] < time():
                    await self.save()
                    raise HomeAssistantError("Fehlalarm muss erneut bestätigt werden")
                self.completed_confirmations = {k: v for k, v in self.completed_confirmations.items() if v[2] > time()}
                self.completed_confirmations[token] = (user.id, incident_id, time()+300)
                self.model.false_alarm(incident_id, user.id)
                i["ended_by_name"] = user.name or user.id
                text = f"Fehlalarm bestätigt von {user.name}"
            elif action == "coming":
                self.model.come(incident_id, user.id, user.name)
                text = f"{user.name}: Ich komme"
            elif action == "end_source":
                if source_id not in i["sources"]:
                    raise HomeAssistantError("Quelle nicht gefunden")
                self.model.end_source(incident_id, source_id, user.id)
                text = f'{user.name} hat {i["sources"][source_id]["name"]} beendet'
            else:
                raise HomeAssistantError("Unbekannte Rückmeldung")
            self.model.log(action, incident=i, user_id=user.id, user_name=user.name,
                source=i["sources"].get(source_id, {}), text=text)
            if i["status"] != "open":
                # Free devices can start the next open incident on the next tick.
                for current in self.model.active():
                    if current["status"] == "open":
                        current["next_due"] = 0
            await self.save()
        target_ids = [i['id']]
        if background:
            self.spawn(self.finish_response(i, action, text, target_ids))
            return None
        await self.finish_response(i, action, text, target_ids)
        return None

    async def finish_response(self, i, action, text, target_ids):
        targets = [self.model.data['incidents'][iid] for iid in target_ids if iid in self.model.data['incidents']]
        # Status delivery runs alongside restoration, never reopening the alarm popup.
        # Keep the existing notification and replace its text using the same tag.
        async def announce():
            for current in targets:
                await self.status(current, text, popup=False)
        announcement = self.spawn(announce())
        try:
            async with self.transport:
                for target_id in target_ids:
                    await self.stop_devices(target_id)
            if action == "false_alarm" or i["status"] == "ended":
                await self.close_popups(i, exclude_user=i.get("ended_by") if action == "false_alarm" and not i.get("test_device") else None)
            await announcement
            if action == "false_alarm":
                await self.false_alarm_notice(i, text)
        finally:
            if not announcement.done():
                announcement.cancel()
                await asyncio.gather(announcement, return_exceptions=True)
        return None

    async def abort_test(self, device_id, user_id):
        user = await self.actor(user_id, admin=True)
        async with self.lock:
            tests = [i for i in self.model.active() if i.get('test_device') == device_id]
            for i in tests:
                for sid, source in i['sources'].items():
                    if source['active']:
                        self.model.end_source(i['id'], sid, user.id)
                self.model.log('test_aborted', incident=i, user_id=user.id, user_name=user.name)
            if tests:
                await self.save()
        for i in tests:
            async with self.transport:
                await self.stop_devices(i['id'])
            await self.close_popups(i)
            await self.status(i, f'{user.name}: Gerätetest abgebrochen', popup=False)

    async def tick(self, _now):
        if self.recovering or self.stopping:
            return
        if time()-self._last_purge > 3600:
            self._last_purge = time()
            async with self.lock:
                self.model.purge()
                await self.save()
            await cleanup_history_images(self.hass)
        for i in self.model.active():
            if i["status"] == "open" and i["id"] not in self.running_cycles and time() >= i["next_due"]:
                i["next_due"] = time()+30
                self.spawn(self.cycle(i["id"]))
        self.schedule_category_setup()
        if (self.model.data["leases"]
                and (self.recovery_task is None or self.recovery_task.done())):
            self.recovery_task = self.spawn(self.retry_restorations())

    def required_categories(self, d):
        if d.get("platform") == "browser" or not d.get("notify_action"):
            return []
        user = self.model.data["users"].get(d.get("user_id"), {})
        categories = [CHANNELS[t] for t in TYPES if t in user.get("types", [])]
        if any(t in user.get("types", []) for t in ("FIRE", "INTRUSION")):
            categories.append("Alarmstatus")
        return categories

    def missing_categories(self, d):
        prepared = d.get("category_setup", {})
        return [c for c in self.required_categories(d) if c not in prepared]

    def schedule_category_setup(self):
        # Each physical handset owns its preparation history, independent of its owner.
        if self.recovering or self.stopping:
            return
        for d in list(self.model.data["devices"].values()):
            recovery_pending = self.model.data["leases"].get(d["id"], {}).get("incident_id") == "setup"
            if ((self.missing_categories(d) or recovery_pending) and d["id"] not in self.setup_running
                    and time() >= d.get("setup_retry_at", 0)):
                self.setup_running.add(d["id"])
                self.spawn(self.prepare_categories(d["id"], scheduled=True))

    async def setup_received(self, event):
        tag = event.data.get("tag")
        playback = self.playback_receipts.get(tag)
        if playback and event.data.get("alarm_playback_id") == playback[0] and not playback[1].done():
            playback[1].set_result(True)
        receipt = self.setup_receipts.get(tag)
        if receipt:
            receipt.set_result(True) if not receipt.done() else None

    async def wait_for_quiet_volume(self, d):
        deadline = time() + 12
        await self.command(d, "command_update_sensors")
        while time() < deadline:
            if self.model.active() or d["id"] not in self.model.data["devices"]:
                return False
            if self.sensor(d.get("volume_sensor")) == "0":
                return True
            await asyncio.sleep(0.25)
        return False

    async def wait_setup_receipt(self, future, d):
        deadline = time() + 12
        while time() < deadline:
            if self.model.active() or self.sensor(d.get("volume_sensor")) != "0":
                raise HomeAssistantError("Einrichtung unterbrochen; später automatisch fortsetzen")
            done, _ = await asyncio.wait({future}, timeout=0.25)
            if done:
                return
        raise asyncio.TimeoutError

    def ensure_device_idle(self, device_id):
        if device_id in self.setup_running or device_id in self.model.data["leases"] or any(i.get("test_device") == device_id for i in self.model.active()):
            raise HomeAssistantError("Gerät wird gerade eingerichtet oder alarmiert. Zuerst den Test beenden bzw. die Alarmierung stoppen und die Wiederherstellung abwarten.")

    def ensure_test_ready(self, d):
        if (d["id"] in self.setup_running or self.missing_categories(d)
                or d["id"] in self.model.data["leases"]):
            raise HomeAssistantError("Kategorien werden noch eingerichtet. Handy geöffnet lassen und warten, bis die Einrichtung abgeschlossen ist.")

    async def prepare_category_batch(self, d):
        requests = []
        group = None
        completed = False
        try:
            for channel in self.missing_categories(d):
                tag = "alarm_system_setup_" + uuid4().hex
                future = asyncio.get_running_loop().create_future()
                self.setup_receipts[tag] = future
                requests.append((channel, tag, future))
            if self.model.active() or self.sensor(d.get("volume_sensor")) != "0":
                raise HomeAssistantError("Einrichtung unterbrochen; später automatisch fortsetzen")
            async def send_one(channel, tag):
                if self.model.active() or self.sensor(d.get("volume_sensor")) != "0":
                    return False
                return await self.send(d, {"title": "Alarmsystem: Einrichtung",
                "message": f"Einrichtung der Kategorie {channel}. Kein Alarm.",
                "data": {"channel": channel, "importance": "low" if channel == "Alarmstatus" else "high",
                    "vibrationPattern": "0", "tag": tag, "confirmation": True,
                    "priority": "high", "ttl": 0, "timeout": 8}})
            results = await asyncio.gather(*(send_one(channel, tag) for channel, tag, _ in requests))
            if not all(results):
                raise HomeAssistantError("Einrichtungsmeldung konnte nicht gesendet werden")
            group = asyncio.gather(*(future for _, _, future in requests))
            await self.wait_setup_receipt(group, d)
            # One shared grace period after receipt, rather than one per category.
            await asyncio.sleep(1)
            completed = True
        finally:
            if group is not None:
                if not group.done():
                    group.cancel()
                try:
                    await group
                except asyncio.CancelledError:
                    pass
            for channel, tag, future in requests:
                if completed and future.done() and not future.cancelled() and future.result() is True and self.model.data["devices"].get(d["id"]) is d:
                    d.setdefault("category_setup", {})[channel] = {"state": "received", "at": stamp()}
                self.setup_receipts.pop(tag, None)
                if not future.done():
                    future.cancel()
            if requests:
                await self.save()
                await asyncio.gather(*(self.command(d, "clear_notification", tag=tag) for _, tag, _ in requests))

    async def prepare_categories(self, device_id, scheduled=False):
        if not scheduled:
            if device_id in self.setup_running:
                return
            self.setup_running.add(device_id)
        d = self.model.data["devices"].get(device_id)
        if not d:
            self.setup_running.discard(device_id)
            return
        try:
            async with self.transport:
                pending = self.model.data["leases"].get(device_id)
                if pending and pending.get("incident_id") == "setup":
                    await self.restore_device(d)
                    if device_id in self.model.data["leases"]:
                        d["setup_error"] = "Vorherige Lautstärke-Wiederherstellung nicht bestätigt. Automatischer neuer Versuch."
                        return
                if self.model.active():
                    d["setup_error"] = "Nach Ende des aktiven Alarms automatisch fortsetzen."
                    return
                if not self.missing_categories(d):
                    d.pop("setup_error", None)
                    return
                if d["platform"] == "android":
                    volume = self.sensor(d.get("volume_sensor"))
                    ringer = self.sensor(d.get("ringer_sensor"))
                    if not str(volume).isdigit() or ringer not in ("normal", "vibrate", "silent"):
                        d["setup_error"] = "Handy öffnen und die beiden Companion-Sensoren bereitstellen."
                        return
                    if device_id in self.model.data["leases"]:
                        d["setup_error"] = "Vorherige Lautstärke-Wiederherstellung steht noch aus."
                        return
                    self.model.data["leases"][device_id] = {"ringer": ringer, "volume": int(volume),
                        "incident_id": "setup", "playback_id": uuid4().hex}
                    await self.save()
                    try:
                        if not await self.command(d, "command_volume_level", command=0, media_stream="notification_stream"):
                            raise HomeAssistantError("Lautstärke konnte nicht angefordert werden")
                        if not await self.wait_for_quiet_volume(d):
                            raise HomeAssistantError("Stummschaltung nicht bestätigt; keine Kategorienmeldung gesendet")
                        await self.prepare_category_batch(d)
                    finally:
                        await self.restore_device(d)
                    if device_id in self.model.data["leases"]:
                        raise HomeAssistantError("Vorherige Lautstärke-Wiederherstellung nicht bestätigt. Automatischer neuer Versuch.")
                elif d["platform"] == "ios":
                    for channel in self.missing_categories(d):
                        if self.model.active():
                            raise HomeAssistantError("Einrichtung nach Alarmende fortsetzen")
                        if not await self.send(d, {"title": "Alarmsystem: Einrichtung",
                            "message": f"Stumme Testmeldung für {channel}. Kein Alarm.",
                            "data": {"push": {"sound": "none"}}}):
                            raise HomeAssistantError("Einrichtungsmeldung konnte nicht gesendet werden")
                        d.setdefault("category_setup", {})[channel] = {"state": "requested", "at": stamp()}
                d.pop("setup_error", None)
        except asyncio.TimeoutError:
            d["setup_error"] = "Keine Empfangsbestätigung; Handy öffnen. Automatischer neuer Versuch."
        except Exception as err:
            d["setup_error"] = str(err)
        finally:
            d["setup_retry_at"] = time() + 60
            self.setup_running.discard(device_id)
            await self.save()

    def recipients(self, incident):
        if incident.get("test_device"):
            device = self.model.data["devices"].get(incident["test_device"])
            return [device] if device else []
        return self.model.recipients(incident["type"])

    def primary(self):
        return sorted(self.model.active(), key=lambda i: (bool(i.get("test_device")), i["type"] != "INTRUSION", i["started_at"]))

    def primary_for_device(self, device, *, open_only=False):
        """Choose priority among incidents assigned to this particular device."""
        candidates = [i for i in self.primary()
                      if (not open_only or i["status"] == "open")
                      and any(d["id"] == device["id"] for d in self.recipients(i))]
        return next((i for i in candidates if i["status"] == "open"),
                    candidates[0] if candidates else None)

    async def cycle(self, incident_id):
        if incident_id in self.running_cycles or self.stopping:
            return
        self.running_cycles.add(incident_id)
        baselines = {}
        try:
            while not self.stopping:
                i = self.model.data["incidents"].get(incident_id)
                if not i or i["status"] != "open":
                    return
                i["next_due"] = time()+30
                recipients = deepcopy(self.recipients(i))
                playback_devices = []
                async with self.transport:
                    if i["status"] != "open":
                        return
                    for d in recipients:
                        if not self.device_active(d, i):
                            continue
                        primary = self.primary_for_device(d, open_only=True)
                        if not primary or primary["id"] != incident_id:
                            if d.get("push") or d.get("sound"):
                                await self.notify(d, i, loud=False)
                            continue
                        if d["id"] in baselines:
                            d["_audio_baseline"] = baselines[d["id"]]
                        if d.get("popup"):
                            self.spawn(self.show_popup(d, i, launch=True))
                        playback_devices.append(d)
                    completions = await asyncio.gather(*(self.play_device(d, i) for d in playback_devices))
                    await self.save()
                recipients = playback_devices
                baselines.update({d["id"]: d["_audio_baseline"] for d in recipients if "_audio_baseline" in d})
                playback = [task for task in completions if task is not None]
                if playback:
                    await asyncio.gather(*playback)
                elif any(d.get("sound") and d["platform"] == "ios" for d in recipients):
                    await asyncio.sleep(max(float(d.get("fire_seconds",5) if i["type"] == "FIRE" else d.get("intrusion_seconds",5)) for d in recipients if d.get("sound") and d["platform"] == "ios"))
                else:
                    return  # Push-only or unavailable audio retains the 30-second retry.
                # No fixed pause after the configured TTS/audio duration.
        finally:
            self.running_cycles.discard(incident_id)

    async def play_device(self, d, i):
        if i["status"] != "open" or not self.device_active(d, i):
            return
        if d.get("sound") and d["platform"] == "android":
            # Never change an unknown mode: exact restoration requires known enabled sensors.
            previous = self.model.data["leases"].get(d["id"]) or d.get("_audio_baseline")
            ringer = previous["ringer"] if previous else self.sensor(d.get("ringer_sensor"))
            volume = previous["volume"] if previous else self.sensor(d.get("volume_sensor"))
            if ringer not in ("normal", "vibrate", "silent") or not str(volume).isdigit():
                self.delivery(i, d, "audio_skipped", "Klingelmodus/Lautstärke unbekannt; Push bleibt aktiv")
                await self.notify(d, i, loud=False)
                return
            lease = self.model.data["leases"].get(d["id"])
            owner = self.model.data["incidents"].get(lease.get("incident_id")) if lease else None
            keep_audio = bool(owner and owner["status"] == "open" and self.device_active(d, owner)
                              and not lease.get("restore_pending"))
            if not keep_audio:
                await self.restore_device(d)
                if d["id"] in self.model.data["leases"]:
                    self.delivery(i, d, "audio_skipped", "Wiederherstellung ausstehend; Push bleibt aktiv")
                    if d.get("push") or d.get("sound"):
                        await self.notify(d, i, loud=False)
                    return
            d["_audio_baseline"] = {"ringer": ringer, "volume": int(volume)}
            self.model.data["leases"][d["id"]] = {"ringer": ringer, "volume": int(volume), "incident_id": i["id"], "playback_id": uuid4().hex}
            await self.save()  # write recovery information BEFORE changing the phone
            if not keep_audio:
                await self.command(d, "command_ringer_mode", command="normal")
                await self.command(d, "command_volume_level", command=100, media_stream="notification_stream")
                await asyncio.sleep(0.5)
        if i["status"] != "open" or not self.device_active(d, i):
            await self.restore_device(d)
            return
        receipt = None
        if d.get("push") or d.get("sound"):
            receipt = await self.notify(d, i, loud=bool(d.get("sound")))
        if d["platform"] == "android" and d.get("sound"):
            return self.spawn(self.finish_android_cycle(d, i, self.model.data["leases"][d["id"]]["playback_id"], receipt))

    async def finish_android_cycle(self, d, i, playback_id, receipt=None):
        completed = False
        try:
            if receipt is not None:
                try:
                    await asyncio.wait_for(asyncio.shield(receipt), timeout=10)
                    self.delivery(i, d, "notification_received", "Handy bestätigt Empfang; kein Wiedergabenachweis")
                    self.model.log("notification_received", incident=i, device=d, details={"playback_id": playback_id})
                except asyncio.TimeoutError:
                    self.delivery(i, d, "receipt_timeout", "Keine Empfangsbestätigung nach 10 s; Tonfrist beginnt jetzt")
                    self.model.log("receipt_timeout", incident=i, device=d, details={"playback_id": playback_id})
            if i["status"] != "open" or self.model.data["leases"].get(d["id"], {}).get("playback_id") != playback_id:
                return
            await asyncio.sleep(float(d.get("fire_seconds", 5) if i["type"] == "FIRE" else d.get("intrusion_seconds", 5)))
            async with self.transport:
                if i["status"] != "open" or not self.device_active(d, i) or self.model.data["leases"].get(d["id"], {}).get("playback_id") != playback_id:
                    return
                if d.get("speech"):
                    areas = list(dict.fromkeys(s["area"] for s in i["sources"].values() if s["active"] and s["area"]))
                    text = f'Achtung. {LABELS[i["type"]]}. Standort {i["site_id"]}. {". ".join(areas)}.'
                    await self.command(d, "TTS", media_stream="alarm_stream_max", tts_text=text)
            if d.get("speech"):
                await asyncio.sleep(float(d.get("speech_seconds", 8)))
            completed = True
        finally:
            tag = self.notification_tag(d, i)
            pending = self.playback_receipts.get(tag)
            if pending and pending[0] == playback_id:
                self.playback_receipts.pop(tag, None)
                if not pending[1].done():
                    pending[1].cancel()
            async with self.transport:
                # A completed tone/TTS round is not the end of the alarm.
                # Keep the original baseline and loud mode across repeats.
                keep_audio = completed and not self.stopping and i["status"] == "open" and self.device_active(d, i)
                if not keep_audio and self.model.data["leases"].get(d["id"], {}).get("playback_id") == playback_id:
                    await self.restore_device(d)
                    await self.save()

    def device_active(self, d, incident=None):
        if incident and incident.get("test_device") == d["id"]:
            return d["id"] in self.model.data["devices"]
        latest = self.model.data["devices"].get(d["id"], {})
        user = self.model.data["users"].get(d["user_id"], {})
        return bool(latest.get("enabled") and latest.get("tested") and user
                    and user.get("enabled", True)
                    and (not incident or incident["type"] in user.get("types", [])))

    def sensor(self, entity_id):
        state = self.hass.states.get(entity_id) if entity_id else None
        return state.state if state else None

    async def command(self, d, message, **data):
        lease = self.model.data["leases"].get(d["id"], {})
        incident = self.model.data["incidents"].get(lease.get("incident_id"))
        return await self.send(d, {"message": message, "data": {"priority": "high", "ttl": 0, **data}}, incident)

    async def send(self, d, payload, incident=None, *, source=None, kind=None):
        action = d.get("notify_action", "")
        if not action:
            return False
        domain, _, service = action.partition(".")
        started = time()
        try:
            await self.hass.services.async_call(domain, service, payload, blocking=True)
            if incident:
                self.delivery(incident, d, "requested", action)
            command = payload.get("message", "").startswith("command_") or payload.get("message") in ("TTS", "clear_notification")
            extra = payload.get("data", {})
            self.model.log("command_requested" if command else "notification_requested", incident=incident, device=d,
                source=source, kind=kind or next((k for k, v in CHANNELS.items() if v == extra.get("channel")), None),
                text=extra.get("tts_text", payload.get("message", "")),
                details={"title": payload.get("title", ""), "channel": extra.get("channel", ""),
                         "command": payload.get("message", "") if command else "", "value": extra.get("command", ""),
                         "media_stream": extra.get("media_stream", ""), "tag": extra.get("tag", ""), "service_ms": round((time()-started)*1000)})
            self.defer_transport_save()
            return True
        except Exception as err:
            _LOGGER.warning("Alarmtransport %s fehlgeschlagen: %s", action, err)
            if incident:
                self.delivery(incident, d, "error", str(err))
            self.model.log("transport_error", incident=incident, device=d, source=source, kind=kind, text=str(err))
            self.defer_transport_save()
            return False

    def delivery(self, i, d, state, detail):
        i["delivery"].append({"at": stamp(), "device_id": d["id"], "state": state, "detail": detail})

    def notification_tag(self, d, i):
        return f'{i["site_id"]}_{i["id"]}_{d["id"]}'

    async def notify(self, d, i, loud):
        receipt = None
        data = {"tag": self.notification_tag(d, i), "priority": "high", "ttl": 0,
                "actions": [{"action": f'AS_COMING:{i["id"]}', "title": "Ich komme"},
                            {"action": "URI", "title": "Fehlalarm / Details", "uri": f"/alarm-system?alarm={i['id']}"}]}
        if d["platform"] == "android":
            data.update(channel=CHANNELS[i["type"]] if loud else "Alarmstatus",
                        importance="high", visibility="public", sticky=True,
                        alert_once=not loud, clickAction=f"/alarm-system?alarm={i['id']}")
            lease = self.model.data["leases"].get(d["id"])
            if loud and lease:
                receipt = asyncio.get_running_loop().create_future()
                self.playback_receipts[data["tag"]] = (lease["playback_id"], receipt)
                data.update(confirmation=True, alarm_playback_id=lease["playback_id"])
        elif loud:
            data["push"] = {"sound": {"name": d.get("fire_sound", "default") if i["type"] == "FIRE" else d.get("intrusion_sound", "default"),
                                      "critical": 1, "volume": 1.0}}
            data["url"] = f"/alarm-system?alarm={i['id']}"
        else:
            data["push"] = {"sound": "none"}
            data["url"] = f"/alarm-system?alarm={i['id']}"
        sent = await self.send(d, {"title": f'{LABELS[i["type"]]} · {i["site_id"]}',
                           "message": self.summary(i), "data": data}, i)
        if not sent and receipt is not None:
            self.playback_receipts.pop(data["tag"], None)
            receipt.cancel()
            return None
        return receipt

    def summary(self, i):
        return "\n".join(f'{s["name"]} · {s["area"]} · {s["detection"]}'
                          for s in i["sources"].values() if s["active"]) or "Alle Quellen beendet"

    async def wait_for_restored_state(self, d, lease, requested_at):
        # Commands being accepted by HA do not prove that the phone handled them.
        # Keep the original baseline durable until companion sensors report it.
        await self.command(d, "command_update_sensors")
        deadline = time() + 4
        while time() < deadline:
            expected = ((d.get("volume_sensor"), str(lease["volume"])),
                        (d.get("ringer_sensor"), lease["ringer"]))
            confirmed = True
            for entity_id, value in expected:
                state = self.hass.states.get(entity_id) if entity_id else None
                reported = (getattr(state, "last_reported", None)
                            or getattr(state, "last_updated", None))
                if (not state or state.state != value or not reported
                        or reported.timestamp() < requested_at):
                    confirmed = False
                    break
            if confirmed:
                return True
            await asyncio.sleep(0.25)
        return False

    async def restore_device(self, d):
        lease = self.model.data["leases"].get(d["id"])
        if not lease:
            return
        lease["restore_pending"] = True
        requested_at = time()
        ok = await self.command(d, "command_stop_tts")
        ok = await self.command(d, "command_volume_level", command=lease["volume"], media_stream="notification_stream") and ok
        ok = await self.command(d, "command_ringer_mode", command=lease["ringer"]) and ok
        if ok:
            ok = await self.wait_for_restored_state(d, lease, requested_at)
        if self.model.data["leases"].get(d["id"]) is not lease:
            return
        if ok:
            self.model.data["leases"].pop(d["id"], None)
        else:
            lease["retry_at"] = time() + 30

    async def retry_restorations(self):
        """Retry pending alarm restorations without interrupting active playback."""
        async with self.transport:
            devices = []
            for device_id, lease in list(self.model.data["leases"].items()):
                if lease.get("incident_id") == "setup" or time() < lease.get("retry_at", 0):
                    continue
                owner = self.model.data["incidents"].get(lease.get("incident_id"))
                device = self.model.data["devices"].get(device_id)
                if device and (lease.get("restore_pending") or not owner
                               or owner["status"] != "open" or not self.device_active(device, owner)):
                    devices.append(device)
            if devices:
                await asyncio.gather(*(self.restore_device(d) for d in devices))
                await self.save()

    async def stop_devices(self, incident_id=None):
        for d in list(self.model.data["devices"].values()):
            lease = self.model.data["leases"].get(d["id"])
            if incident_id and (not lease or lease["incident_id"] != incident_id):
                continue
            if not lease and d["platform"] == "android" and d.get("notify_action"):
                await self.command(d, "command_stop_tts")
            await self.restore_device(d)
        await self.save()

    async def status(self, i, text, popup):
        responses = " · ".join(
            f'{r.get("name") or self.model.data["users"].get(uid, {}).get("name") or "Name nicht verfügbar"}: Ich komme'
            for uid, r in i["responses"].items() if r.get("answer") == "coming")
        for d in deepcopy(self.recipients(i)):
            if d.get("push"):
                await self.send(d, {"title": f'{i["site_id"]} · ' + ("Gerätetest beendet" if i.get("test_device") and i["status"] in ("false_alarm", "ended") else "FEHLALARM bestätigt" if i["status"] == "false_alarm" else f'{LABELS[i["type"]]} · Status'),
                                   "message": f'{text}\n{self.summary(i)}\n' + (responses or "Noch keine Zusage") + f'\n{dt_util.as_local(dt_util.utcnow()).strftime("%d.%m.%Y %H:%M:%S")}',
                                   "data": {"channel": "Alarmstatus", "tag": self.notification_tag(d, i),
                                            "priority": "high", "ttl": 0, "alert_once": True,
                                            "push": {"sound": "none"}, "url": "/alarm-system", "clickAction": "/alarm-system",
                                            "actions": [{"action": f'AS_COMING:{i["id"]}', "title": "Ich komme"}, {"action": "URI", "title": "Fehlalarm / Details", "uri": "/alarm-system"}] if i["status"] in ("open", "claimed") else []}}, i)
            if popup and d.get("popup"):
                visible = self.primary_for_device(d)
                if visible:
                    self.spawn(self.show_popup(d, visible, launch=False))
        await self.save()

    async def show_popup(self, d, i, launch):
        browsers = d.get('browsers', [])
        if not browsers or all(self.open_popups.get(b['id']) == i['id'] for b in browsers):
            return
        visible = any(self.sensor(b.get('visibility_sensor')) == 'visible' for b in browsers)
        if launch and not visible and d["platform"] == "android" and d.get("notify_action"):
            await self.command(d, "command_screen_on")
            await self.command(d, "command_webview", command=f"/alarm-system?alarm={i['id']}")
            sensors = [b.get("visibility_sensor") for b in browsers if b.get("visibility_sensor")]
            if sensors:
                deadline = time()+3
                while time() < deadline and not any(self.sensor(sensor) == "visible" for sensor in sensors):
                    await asyncio.sleep(0.1)
                if not any(self.sensor(sensor) == "visible" for sensor in sensors):
                    return  # Reopened by the visibility transition when the browser connects.
            else:
                await asyncio.sleep(0.5)
        if i["status"] not in ("open", "claimed") or not self.device_active(d, i) or not self.model.authorized(d["user_id"], i):
            return
        changed = False
        async with self.popup_lock:
            for browser in browsers:
                bid = browser['id']
                if self.open_popups.get(bid) == i['id']:
                    continue
                if i['status'] not in ('open', 'claimed'):
                    return
                data = {"browser_id": [bid], "tag": "alarm_system",
                        "title": f'{LABELS[i["type"]]} · {i["site_id"]}',
                        "initial_style": "fullscreen", "dismissable": False,
                        "content": {"type": "custom:alarm-system-card", "incident_id": i["id"]}}
                try:
                    await self.hass.services.async_call("browser_mod", "popup", data, blocking=True)
                    self.open_popups[bid] = i['id']
                    self.delivery(i, d, "popup_requested", bid)
                    self.model.log("popup_requested", incident=i, device=d, browser_id=bid)
                except Exception as err:
                    self.delivery(i, d, "popup_error", str(err))
                    self.model.log("popup_error", incident=i, device=d, browser_id=bid, text=str(err))
                changed = True
        if changed:
            await self.save()

    async def false_alarm_notice(self, i, text):
        """One quiet status popup per recipient browser, excluding the confirming account."""
        if i.get("test_device"):
            return
        actor_browsers = {b["id"] for d in self.recipients(i) if d.get("user_id") == i.get("ended_by") for b in d.get("browsers", [])}
        sent = set(actor_browsers)
        for d in deepcopy(self.recipients(i)):
            if not d.get("popup") or d.get("user_id") == i.get("ended_by"):
                continue
            for browser in d.get("browsers", []):
                if browser["id"] in sent:
                    continue
                sent.add(browser["id"])
                try:
                    await self.hass.services.async_call("browser_mod", "popup", {
                        "browser_id": [browser["id"]], "tag": "alarm_system_status",
                        "title": "Fehlalarm bestätigt", "dismissable": True,
                        "content": {"type": "markdown", "content":
                            f'{text}\n\n{i["site_id"]} · {i["title"]}\n\n'
                            f'{dt_util.as_local(dt_util.utcnow()).strftime("%d.%m.%Y %H:%M:%S")}\n\nDieses Ereignis ist beendet.'},
                        "right_button": "VERSTANDEN", "right_button_close": True,
                    }, blocking=True)
                    self.delivery(i, d, "popup_status_requested", browser["id"])
                    self.model.log("popup_status_requested", incident=i, device=d, browser_id=browser["id"], text=text)
                except Exception as err:
                    self.delivery(i, d, "popup_error", str(err))
                    self.model.log("popup_error", incident=i, device=d, browser_id=browser["id"], text=str(err))
        await self.save()

    async def confirm_popup(self, incident_id, user_id, browser_id):
        token = await self.respond(incident_id, "request_false", user_id)
        await self.hass.services.async_call("browser_mod", "popup", {
            "browser_id": [browser_id], "tag": "alarm_system", "title": "Fehlalarm bestätigen",
            "dismissable": False, "content": {"type": "markdown", "content": "## Wirklich Fehlalarm?\nAlle Quellen dieses Ereignisses werden beendet."},
            "left_button": "ABBRECHEN", "right_button": "JA, FEHLALARM",
            "left_button_action": {"service": f"{DOMAIN}.respond", "data": {"incident_id": incident_id, "action": "cancel_false", "confirmation_token": token}},
            "right_button_action": {"service": f"{DOMAIN}.respond", "data": {"incident_id": incident_id, "action": "false_alarm", "confirmation_token": token}},
        }, blocking=True)

    async def close_popups(self, i, exclude_user=None):
        self.open_popups = {bid: iid for bid, iid in self.open_popups.items() if iid != i['id']}
        for d in self.recipients(i):
            if exclude_user is not None and d.get("user_id") == exclude_user:
                continue
            for b in d.get("browsers", []):
                try:
                    await self.hass.services.async_call("browser_mod", "close_popup", {"browser_id": [b["id"]], "tag": "alarm_system"}, blocking=True)
                except Exception:
                    pass
        for d in list(self.model.data["devices"].values()):
            visible = self.primary_for_device(d)
            if visible and d.get("popup"):
                self.spawn(self.show_popup(d, visible, launch=False))

    async def mobile_response(self, event):
        action = event.data.get("action", "")
        if not action.startswith("AS_COMING:"):
            return
        try:
            await self.respond(action.split(":", 1)[1], "coming", event.context.user_id)
        except Exception as err:
            self.hass.bus.async_fire("alarm_system_response_error", {"error": str(err)})

    async def receive_signal(self, entity_id, state):
        incident, result, message = None, None, None
        async with self.lock:
            binding = next((s for s in self.model.data["sources"].values() if s["entity_id"] == entity_id), None)
            previous = self.model.data["signal_values"].get(binding["id"]) if binding else None
            payload = self.model.signal_update(entity_id, state)
            if binding and previous != state:
                self.model.log("signal_changed", kind=binding["type"], source=binding,
                    details={"previous": previous, "state": state})
            if payload:
                if payload["type"] in ("FIRE", "INTRUSION"):
                    incident, result = self.model.raise_alarm(payload)
                    self.model.log("alarm_raised" if result == "new" else result, kind=binding["type"], incident=incident, source=binding)
                else:
                    message = payload
            # Signal edge and created incident are persisted in the same snapshot.
            if binding and (previous != state or payload):
                await self.save()
        if result == "new":
            self.spawn(self.cycle(incident["id"]))
        elif result == "source_added":
            self.spawn(self.status(incident, f'Zusätzliche Meldung: {payload["source_name"]}', popup=True))
        elif message:
            await self.simple_message(message)

    async def state_changed(self, event):
        state = event.data.get("new_state")
        if not state:
            return
        async with self.lock:
            dirty = False
            if state.state == "off":
                for i in self.model.data["incidents"].values():
                    for s in i["sources"].values():
                        if s.get("entity_id") == state.entity_id and s["signal_active"]:
                            self.model.normal(i["alarm_key"], s["id"])
                            dirty = True
            if dirty:
                await self.save()
        if state.entity_id.startswith("binary_sensor."):
            await self.receive_signal(state.entity_id, state.state)
            if state.state not in ("on", "off") and any(s["entity_id"] == state.entity_id for s in self.model.data["sources"].values()):
                self.publish()
        old_state = event.data.get('old_state')
        # Browser Mod also updates attributes while visibility stays unchanged.
        # Only a visibility transition may reopen the alarm window.
        if state.state != 'visible':
            for d in self.model.data['devices'].values():
                for b in d.get('browsers', []):
                    if b.get('visibility_sensor') == state.entity_id:
                        self.open_popups.pop(b['id'], None)
        if state.state == "visible" and (not old_state or old_state.state != 'visible'):
            for d in self.model.data["devices"].values():
                if any(b.get("visibility_sensor") == state.entity_id for b in d.get("browsers", [])) and self.device_active(d):
                    visible = self.primary_for_device(d)
                    if visible and d.get("popup"):
                        self.spawn(self.show_popup(d, visible, launch=False))

    async def simple_message(self, data):
        data = dict(data)
        self.model.log("message_raised", kind=data["type"], text=data.get("message", ""), source={"id": data.get("source_id", ""), "name": data.get("source_name", ""), **data}, details={"url": data.get("url", ""), "graph_entity": data.get("graph_entity", ""), "camera": data.get("camera", "")})
        await self.save()
        if data.get("graph_entity"):
            from .charts import history_image
            try:
                data["image"] = await history_image(self.hass, data["graph_entity"], data.get("graph_minutes", 15), data["type"])
            except Exception as err:
                _LOGGER.warning("Alarmdiagramm konnte nicht erzeugt werden: %s", err)
                data["message"] = data.get("message", "") + "\nVerlaufsbild derzeit nicht verfügbar."
        if data.get("camera") and not data.get("image"):
            data["image"] = "/api/camera_proxy/" + data["camera"]
        for d in self.model.recipients(data["type"]):
            if not d.get("push"):
                continue
            payload = {"title": data.get("title", LABELS[data["type"]]), "message": data.get("message", ""),
                       "data": {"channel": CHANNELS[data["type"]], "url": data.get("url") or "/alarm-system", "clickAction": data.get("url") or "/alarm-system"}}
            if data.get("image"):
                payload["data"]["image"] = data["image"]
            if data.get("silent"):
                payload["data"]["push"] = {"sound": "none"}
                if d["platform"] == "android":
                    payload["data"]["channel"] = "Alarmstatus"
            await self.send(d, payload, source={"id": data.get("source_id", ""), "name": data.get("source_name", ""), **data}, kind=data["type"])
