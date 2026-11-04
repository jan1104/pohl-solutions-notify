"""Local, per-instance alarm management."""
import asyncio
import logging
from functools import partial
from pathlib import Path
from uuid import uuid4
import probatio as vol
from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN, VERSION
from .engine import AlarmEngine
from .model import stamp
from .discovery import connections, complete_device
from .configuration import prepare_import, completed_device_tests, user_view, device_outputs
from .identity import resolve_name
from .chart_view import AlarmChartView
from .output_tests import run_output_test, stop_output_test

_LOGGER = logging.getLogger(__name__)

JS_URL = f"/alarm-system-static/panel.js?v={VERSION}"


async def async_setup_entry(hass, entry):
    if DOMAIN in hass.data:
        raise HomeAssistantError("Integration ist bereits geladen")
    if entry.title == "Alarm System":
        hass.config_entries.async_update_entry(entry, title="Pohl Solutions Alarm Notify")
    engine = AlarmEngine(hass, entry)
    hass.data[DOMAIN] = engine
    js_added = False
    panel_attempted = False
    try:
        if not hass.data.get(f"{DOMAIN}_static"):
            await hass.http.async_register_static_paths([StaticPathConfig(
                "/alarm-system-static", str(Path(__file__).parent / "frontend"), False)])
            hass.data[f"{DOMAIN}_static"] = True
        if not hass.data.get(f"{DOMAIN}_chart_view"):
            hass.http.register_view(AlarmChartView(hass))
            hass.data[f"{DOMAIN}_chart_view"] = True
        frontend.add_extra_js_url(hass, JS_URL)
        js_added = True
        panel_attempted = True
        await panel_custom.async_register_panel(
            hass, "alarm-system", "alarm-system-panel", sidebar_title="Alarme",
            sidebar_icon="mdi:alarm-light", module_url=JS_URL, require_admin=False,
        )
        await engine.start()

        async def dispatch(call):
            await engine.dispatch(dict(call.data), call.context.user_id)

        async def normal(call):
            if call.context.user_id:
                await engine.actor(call.context.user_id, admin=True)
            async with engine.lock:
                engine.model.normal(call.data["alarm_key"], call.data["source_id"])
                engine.model.log("signal_normal", user_id=call.context.user_id,
                    source={"id": call.data["source_id"]}, details=dict(call.data))
                await engine.save()

        async def response(call):
            actor_id = call.context.user_id
            # THIS is supplemental; never accept a different or missing authenticated actor.
            if call.data.get("user_id") not in (None, actor_id):
                raise HomeAssistantError("Benutzer-ID stimmt nicht mit dem angemeldeten Account überein")
            await engine.respond(call.data["incident_id"], call.data["action"], actor_id,
                                 call.data.get("source_id"), call.data.get("confirmation_token"))

        async def confirm(call):
            if call.data.get("user_id") not in (None, call.context.user_id):
                raise HomeAssistantError("Benutzer-ID stimmt nicht mit dem Account überein")
            await engine.confirm_popup(call.data["incident_id"], call.context.user_id, call.data["browser_id"])

        hass.services.async_register(DOMAIN, "raise_alarm", dispatch, schema=vol.Schema({
            vol.Required("type"): str,
            vol.Optional("alarm_key", default="message"): str,
            vol.Optional("source_id", default="manual"): str,
            vol.Optional("source_name"): str, vol.Optional("entity_id"): str,
            vol.Optional("title"): str, vol.Optional("message"): str,
            vol.Optional("area"): str, vol.Optional("detection"): str,
            vol.Optional("camera"): str, vol.Optional("image"): str,
            vol.Optional("graph_entity"): str, vol.Optional("graph_minutes", default=15): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
            vol.Optional("url"): str, vol.Optional("silent", default=False): bool,
        }))
        hass.services.async_register(DOMAIN, "source_normal", normal, schema=vol.Schema({
            vol.Required("alarm_key"): str, vol.Required("source_id"): str}))
        hass.services.async_register(DOMAIN, "respond", response, schema=vol.Schema({
            vol.Required("incident_id"): str, vol.Required("action"): vol.In(["coming", "seen", "false_alarm", "cancel_false", "end_source"]),
            vol.Optional("source_id"): str, vol.Optional("confirmation_token"): str, vol.Optional("user_id"): str}))
        hass.services.async_register(DOMAIN, "confirm_false_alarm", confirm, schema=vol.Schema({
            vol.Required("incident_id"): str, vol.Required("browser_id"): str, vol.Optional("user_id"): str}))
        websocket_api.async_register_command(hass, ws_get)
        websocket_api.async_register_command(hass, ws_manage)
        websocket_api.async_register_command(hass, ws_respond)
        return True

    except (Exception, asyncio.CancelledError):
        # Never persist a partially loaded/default model after a failed startup.
        # Existing durable playback leases must remain available to the next load.
        try:
            await engine.cancel_workers()
        except Exception:
            _LOGGER.exception("Hintergrundaufgaben nach fehlgeschlagenem Start nicht vollständig beendet")
        finally:
            hass.data.pop(DOMAIN, None)
            cleanup_failed_setup(hass, panel_attempted=panel_attempted, js_added=js_added)
        raise


def cleanup_failed_setup(hass, *, panel_attempted, js_added):
    """Attempt every cleanup step without replacing the original setup exception."""
    cleanup_resources(hass, panel_attempted=panel_attempted, js_added=js_added)


def cleanup_resources(hass, *, panel_attempted, js_added):
    """Attempt every resource removal and return the first failure for a retry."""
    actions = [partial(hass.services.async_remove, DOMAIN, name)
               for name in ("raise_alarm", "source_normal", "respond", "confirm_false_alarm")]
    if panel_attempted:
        actions.append(partial(frontend.async_remove_panel, hass, "alarm-system"))
    if js_added:
        actions.append(partial(frontend.remove_extra_js_url, hass, JS_URL))
    actions.append(partial(hass.states.async_remove, "sensor.alarm_system_active"))
    first_error = None
    for cleanup in actions:
        try:
            cleanup()
        except Exception as err:
            if first_error is None:
                first_error = err
            _LOGGER.exception("Alarm-Ressource nicht vollständig entfernt")
    return first_error


async def async_unload_entry(hass, entry):
    engine = hass.data.get(DOMAIN)
    if engine is None:
        return True
    await engine.stop()
    failure = cleanup_resources(hass, panel_attempted=True, js_added=True)
    if failure is not None:
        # Retain the stopped engine so another unload retries unfinished cleanup.
        # Its stop flag rejects new requests while resources are partly removed.
        raise failure
    hass.data.pop(DOMAIN, None)
    return True


def get_engine(hass):
    """Reject requests during/after unload instead of leaking an internal KeyError."""
    engine = hass.data.get(DOMAIN)
    if engine is None or getattr(engine, "stopping", False):
        raise HomeAssistantError("Integration ist nicht geladen")
    return engine


def validate_manage_payload(engine, action, payload):
    """Validate nested identifiers before logging, saving or indexing configuration."""
    required = {
        "source_upsert": ("entity_id", "name"), "source_remove": ("id",),
        "user_upsert": ("id",), "user_remove": ("id",),
        "device_upsert": ("user_id",), "device_remove": ("id",),
        "device_test_begin": ("id",), "device_test_stop": ("id",),
        "device_confirm": ("id",), "device_setup": ("id",), "device_test": ("id",),
        "alarm_type_remove": ("id",), "output_test": ("id", "alarm_type", "output"),
        "output_test_stop": ("id", "test_id"),
    }
    if not isinstance(payload, dict):
        raise HomeAssistantError("Verwaltungsdaten müssen ein Objekt sein")
    keys = set(required.get(action, ()))
    if "id" in payload:
        keys.add("id")
    for key in keys:
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise HomeAssistantError("Fehlende oder ungültige Angabe: " + key)
    if action in ("device_test_begin", "device_test_stop", "device_confirm", "device_setup", "device_test", "output_test", "output_test_stop"):
        if payload["id"] not in engine.model.data["devices"]:
            raise HomeAssistantError("Gerät nicht gefunden")


@websocket_api.websocket_command({vol.Required("type"): "alarm_system/get"})
@websocket_api.async_response
async def ws_get(hass, connection, msg):
    engine = get_engine(hass)
    data = engine.model.snapshot()
    data.pop("leases", None)
    data.pop("suppressed", None)
    # Display names are refreshed from HA, not freely supplied identity labels.
    users = await hass.auth.async_get_users()
    names = {u.id: u.name or u.id for u in users}
    for uid, u in data["users"].items():
        u["name"] = resolve_name(uid, names, data["users"], u.get("name"))
    for i in data["incidents"].values():
        i["ended_by_name"] = resolve_name(i.get("ended_by"), names, data["users"], i.get("ended_by_name"))
        i["silenced_by_name"] = resolve_name(i.get("silenced_by"), names, data["users"], i.get("silenced_by_name"), i["responses"].get(i.get("silenced_by"), {}).get("name"))
        recipients = engine.recipients(i)
        recipient_ids = {d["user_id"] for d in recipients}
        i["audience"] = [{"id": uid, "name": resolve_name(uid, names, data["users"]),
            "transport": engine.model.recipient_transport(i, uid, recipients)} for uid in sorted(recipient_ids)]
        for uid, view in i.get("views", {}).items():
            view["name"] = resolve_name(uid, names, data["users"], view.get("name"))
        for uid, r in i["responses"].items():
            r["name"] = resolve_name(uid, names, data["users"], r.get("name"))
        for audit in i["audit"]:
            audit["name"] = resolve_name(audit.get("user_id"), names, data["users"], audit.get("name")) if audit.get("user_id") else "System"
    for d in data["devices"].values():
        d["setup_pending"] = engine.missing_categories(d)
        d["setup_running"] = d["id"] in engine.setup_running
        lease = engine.model.data["leases"].get(d["id"], {})
        d["setup_restore_pending"] = lease.get("incident_id") == "setup"
        d["restore_pending"] = bool(lease.get("restore_pending"))
        d["setup_categories"] = engine.required_categories(d)
    if connection.user.is_admin:
        data["output_tests_blocked"] = ('Start-Wiederherstellung läuft' if engine.recovering else
            'Vorher alle aktiven Alarme beenden' if engine.model.active() else
            'Wiederherstellung läuft' if engine.model.data['leases'] else
            'Kategorien-Einrichtung läuft' if engine.setup_running else '')
        data["output_test_running"] = list(getattr(engine, "output_tests", {}))
        data["output_test_sessions"] = {did: {key: session.get(key) for key in ('test_id', 'alarm_type', 'output', 'state')}
                                        for did, session in getattr(engine, 'output_tests', {}).items()}
        data["available_users"] = [{"id": u.id, "name": u.name or u.id} for u in users if u.is_active and not u.system_generated]
        data["phone_connections"], data["browser_connections"] = connections(hass)
        data["notify_actions"] = [f"notify.{s}" for s in hass.services.async_services().get("notify", {}) if s.startswith("mobile_app_")]
    else:
        data = user_view(data, connection.user.id)
    connection.send_result(msg["id"], data)


@websocket_api.websocket_command({vol.Required("type"): "alarm_system/respond", vol.Required("incident_id"): str,
                                 vol.Required("action"): str, vol.Optional("source_id"): str,
                                 vol.Optional("confirmation_token"): str})
@websocket_api.async_response
async def ws_respond(hass, connection, msg):
    result = await get_engine(hass).respond(msg["incident_id"], msg["action"], connection.user.id,
                                            msg.get("source_id"), msg.get("confirmation_token"), background=True)
    connection.send_result(msg["id"], {"confirmation_token": result})


@websocket_api.websocket_command({vol.Required("type"): "alarm_system/manage", vol.Required("action"): str,
                                 vol.Optional("data", default={}): dict})
@websocket_api.async_response
async def ws_manage(hass, connection, msg):
    engine = get_engine(hass)
    await engine.actor(connection.user.id, admin=True)
    action, payload = msg["action"], msg["data"]
    validate_manage_payload(engine, action, payload)
    if action in ('output_test', 'output_test_stop'):
        try:
            result = await (run_output_test(engine, payload) if action == 'output_test' else stop_output_test(engine, payload))
        except (ValueError, TypeError, KeyError) as err:
            raise HomeAssistantError(str(err)) from err
        engine.model.log(action, kind=payload.get('alarm_type'), device=engine.model.data['devices'].get(payload['id']),
                         user_id=connection.user.id, user_name=connection.user.name,
                         details={'output': payload.get('output'), 'test_id': result.get('test_id'), 'state': result.get('state')})
        await engine.save()
        connection.send_result(msg['id'], result)
        return
    if action in ('alarm_type_upsert', 'alarm_type_remove'):
        async with engine.lock:
            if engine.model.active() or engine.model.data['leases'] or engine.setup_running or getattr(engine, 'output_tests', {}):
                raise HomeAssistantError('Alarmarten erst nach Ende aller Alarme und Wiederherstellungen ändern')
            try:
                if action == 'alarm_type_upsert':
                    profile = engine.model.upsert_alarm_type(payload)
                    profile_id = profile['id']
                else:
                    profile_id = payload['id']
                    engine.model.remove_alarm_type(profile_id)
            except (ValueError, TypeError, KeyError) as err:
                raise HomeAssistantError(str(err)) from err
            for device in engine.model.data['devices'].values():
                user = engine.model.data['users'].get(device.get('user_id'), {})
                if profile_id in user.get('types', []):
                    device['tested'] = False
                    device.pop('tested_at', None)
                    device.pop('test_session', None)
            engine.model.log(action, user_id=connection.user.id, user_name=connection.user.name,
                             details={'alarm_type_id': profile_id})
            await engine.save()
        engine.schedule_category_setup()
        connection.send_result(msg['id'], {'ok': True, 'alarm_type_id': profile_id})
        return
    if action == 'device_test_stop':
        await engine.abort_test(payload['id'], connection.user.id)
        connection.send_result(msg['id'], {'ok': True})
        return
    async with engine.lock:
        if action in ("configuration_preview", "configuration_import"):
            if engine.setup_running or getattr(engine, "output_tests", {}):
                raise HomeAssistantError("Eine Einrichtung oder Ausgabeprobe läuft noch. Danach erneut importieren.")
            accounts = {u.id: u.name or "Unbenanntes HA-Konto" for u in await hass.auth.async_get_users() if u.is_active and not u.system_generated}
            try:
                staged = prepare_import(engine.model.snapshot(), payload.get("backup"), accounts,
                    {s.entity_id: s.state for s in hass.states.async_all()},
                    {f"notify.{s}" for s in hass.services.async_services().get("notify", {}) if s.startswith("mobile_app_")})
            except (ValueError, TypeError, KeyError) as err:
                raise HomeAssistantError(str(err)) from err
            counts = {key: len(staged[key]) for key in ("users", "devices", "sources")}
            if action == "configuration_import":
                engine.model.data = staged
                engine.model.log(action, user_id=connection.user.id, user_name=connection.user.name, details=counts)
                await engine.save()
                engine.schedule_category_setup()
            connection.send_result(msg["id"], {"ok": True, "counts": counts, "retest_required": True})
            return
        prior_source = engine.model.data["sources"].get(payload.get("id"), {})
        prior_device = engine.model.data["devices"].get(payload.get("id"), {})
        saved_source = None
        if action == "source_upsert":
            entity_id = payload.get("entity_id", "")
            if not hass.states.get(entity_id):
                raise HomeAssistantError("Zuerst den Binary-Sensor aus Node-RED in HA anlegen")
            try:
                saved_source = engine.model.register_source(payload, engine.sensor(entity_id))
            except (ValueError, TypeError) as err:
                raise HomeAssistantError(str(err)) from err
        elif action == "source_remove":
            try:
                engine.model.remove_source(payload["id"])
            except ValueError as err:
                raise HomeAssistantError(str(err)) from err
        elif action == "user_upsert":
            user = await hass.auth.async_get_user(payload["id"])
            if not user or not user.is_active or user.system_generated:
                raise HomeAssistantError("Aktiven HA-Benutzer auswählen")
            if (not isinstance(payload.get("types", []), list)
                    or any(not isinstance(t, str) or t not in engine.model.type_ids() for t in payload.get("types", []))):
                raise HomeAssistantError("Unbekannte Alarmart")
            engine.model.data["users"][user.id] = {"id": user.id, "name": user.name or user.id,
                "enabled": bool(payload.get("enabled", True)), "types": list(dict.fromkeys(payload.get("types", [])))}
        elif action == "user_remove":
            uid = payload["id"]
            for device in engine.model.data["devices"].values():
                if device["user_id"] == uid:
                    engine.ensure_device_idle(device["id"])
            for d in list(engine.model.data["devices"].values()):
                if d["user_id"] == uid:
                    await engine.restore_device(d)
                    engine.model.data["devices"].pop(d["id"])
            engine.model.data["users"].pop(uid, None)
        elif action == "device_upsert":
            phones, browsers_found = connections(hass)
            payload = complete_device(payload, phones, browsers_found)
            uid = payload["user_id"]
            if uid not in engine.model.data["users"]:
                raise HomeAssistantError("Zuerst Benutzer hinzufügen")
            device_id = payload.get("id") or uuid4().hex
            old = engine.model.data["devices"].get(device_id, {})
            if old:
                engine.ensure_device_idle(device_id)
            platform = payload.get("platform", "android")
            if platform not in ("android", "ios", "browser"):
                raise HomeAssistantError("Unbekannte Plattform")
            notify = payload.get("notify_action", "")
            if platform != "browser" and (not notify.startswith("notify.mobile_app_") or not hass.services.has_service(*notify.split(".", 1))):
                raise HomeAssistantError("Vorhandenen Companion-Notify-Dienst auswählen")
            if notify and any(d.get("notify_action") == notify and d["id"] != device_id for d in engine.model.data["devices"].values()):
                raise HomeAssistantError("Dieses Handy ist bereits zugeordnet")
            browsers = payload.get("browsers", [])
            if any(not isinstance(b, dict) or not b.get("id") for b in browsers):
                raise HomeAssistantError("Browserliste enthält einen ungültigen Eintrag")
            if len({b["id"] for b in browsers}) != len(browsers) or any(b["id"] == existing["id"] for b in browsers for other in engine.model.data["devices"].values() if other["id"] != device_id for existing in other.get("browsers", [])):
                raise HomeAssistantError("Ein Browser darf nur einem Gerät zugeordnet werden")
            try:
                outputs = device_outputs(payload, platform)
            except ValueError as err:
                raise HomeAssistantError(str(err)) from err
            critical_keys = ("user_id", "platform", "notify_action", "browsers", "ringer_sensor", "volume_sensor",
                             "push", "popup", "sound", "speech", "fire_seconds", "intrusion_seconds",
                             "speech_seconds", "fire_sound", "intrusion_sound")
            # Keep legacy device values when the simplified editor omits them.
            timings = {field: max(1, min(maximum, float(payload.get(field, old.get(field, default)))))
                       for field, default, maximum in (("fire_seconds", 5, 15),
                                                      ("intrusion_seconds", 5, 15),
                                                      ("speech_seconds", 8, 12))}
            compared = {**payload, **outputs, **timings}
            changed = any(old.get(k) != compared.get(k) for k in critical_keys)
            device = {"id": device_id, "user_id": uid, "name": payload.get("name", "Gerät"), "platform": platform,
                      "notify_action": notify, "browsers": browsers,
                      **outputs,
                      "ringer_sensor": payload.get("ringer_sensor", ""), "volume_sensor": payload.get("volume_sensor", ""),
                      **timings,
                      "fire_sound": payload.get("fire_sound", "default"), "intrusion_sound": payload.get("intrusion_sound", "default"),
                      "enabled": bool(payload.get("enabled", True)), "tested": old.get("tested", False) and not changed}
            same_handset = old.get("notify_action") == notify and old.get("platform") == platform
            device["category_setup"] = old.get("category_setup", {}) if same_handset else {}
            if not changed:
                for field in ("tested_at", "test_session", "setup_retry_at"):
                    if field in old:
                        device[field] = old[field]
            engine.model.data["devices"][device_id] = device
        elif action == "device_remove":
            d = engine.model.data["devices"].get(payload["id"])
            if d:
                engine.ensure_device_idle(d["id"])
                await engine.restore_device(d)
                engine.model.data["devices"].pop(d["id"])
        elif action == "device_test_begin":
            engine.ensure_device_idle(payload["id"])
            d = engine.model.data["devices"][payload["id"]]
            if any(i.get("test_device") == d["id"] for i in engine.model.active()):
                raise HomeAssistantError("Den laufenden Gerätetest zuerst beenden")
            d["test_session"] = uuid4().hex
            d["tested"] = False
            d.pop("tested_at", None)
        elif action == "device_confirm":
            d = engine.model.data["devices"][payload["id"]]
            engine.ensure_test_ready(d)
            if not d.get("test_session") or not {"FIRE", "INTRUSION"} <= completed_device_tests(engine.model.data, d):
                raise HomeAssistantError("Feuer und Einbruch in dieser Prüfung testen und beenden")
            d["tested"] = True
            d["tested_at"] = stamp()
        elif action == "settings":
            mode = payload.get("retention_mode", "unlimited")
            if mode not in ("unlimited", "30d", "3m", "5m", "12m", "4y"):
                raise HomeAssistantError("Ungültige Aufbewahrungsdauer")
            engine.model.data["retention_mode"] = mode
            engine.model.purge()
        elif action not in ("device_setup", "device_test"):
            raise HomeAssistantError("Unbekannte Verwaltungsaktion")
        engine.model.log(action, user_id=connection.user.id, user_name=connection.user.name,
            source=(saved_source or prior_source) if action.startswith("source_") else None,
            device=(engine.model.data["devices"].get(device_id if action == "device_upsert" else payload.get("id"), {}) or prior_device) if action.startswith("device_") else None,
            details={"configured_id": device_id if action == "device_upsert" else payload.get("id", ""),
                     "name": payload.get("name", ""), "user_id": payload.get("user_id", ""),
                     "types": payload.get("types", []), "enabled": payload.get("enabled"), "retention_mode": payload.get("retention_mode", "")})
        await engine.save()
    if action == "device_setup":
        await engine.prepare_categories(payload["id"])
    elif action == "device_test":
        d = engine.model.data["devices"][payload["id"]]
        engine.ensure_test_ready(d)
        if engine.model.active():
            raise HomeAssistantError("Vor dem Gerätetest alle aktiven Ereignisse beenden")
        kind = payload.get("alarm_type", "FIRE")
        if not engine.model.is_alarm(kind):
            raise HomeAssistantError("Ungültiger Testtyp")
        i, _ = engine.model.raise_alarm({"type": kind, "alarm_key": f'test_{d["id"]}',
                                        "source_id": uuid4().hex, "source_name": "Testmelder", "title": "Gerätetest", "area": "Erdgeschoss"})
        i["test_device"] = d["id"]
        i["test_session"] = d.get("test_session")
        i["next_due"] = 0
        engine.model.log("alarm_raised", incident=i, device=d,
            user_id=connection.user.id, user_name=connection.user.name,
            text="Gerätetest", details={"test": True})
        await engine.save()
        engine.spawn(engine.cycle(i["id"]))
    if action in ("user_upsert", "device_upsert", "device_confirm"):
        engine.schedule_category_setup()
    # Newly added/confirmed recipients get a snapshot of current incidents.
    if action in ("device_confirm", "user_upsert"):
        for i in engine.model.active():
            if not i.get("test_device"):
                if i["status"] == "open":
                    i["next_due"] = 0
                else:
                    engine.spawn(engine.status(i, "Aktueller Alarmstatus", popup=True))
    connection.send_result(msg["id"], {"ok": True, "device_id": device_id if action == "device_upsert" else payload.get("id")})
