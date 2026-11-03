"""Bounded, one-shot output checks; never grant a device alarm-test approval."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from contextlib import asynccontextmanager
from html import escape
from uuid import uuid4

from .alarm_types import DEFAULT_SPEECH_TEMPLATE

TEST_LIFETIME_SECONDS = 30
ACTION_TIMEOUT_SECONDS = 5
GUARD_POLL_SECONDS = .05
CANCEL_DRAIN_SECONDS = .1
_OUTPUTS = {"push", "sound", "speech", "popup"}


def _sessions(engine):
    if not hasattr(engine, "output_tests"):
        engine.output_tests = {}
    return engine.output_tests


def _idle(engine, *, allow_stopping=False):
    if (getattr(engine, "stopping", False) and not allow_stopping) or getattr(engine, "recovering", False):
        raise ValueError("Einzelausgabe während Start oder Entladen nicht verfügbar")
    if engine.model.active() or engine.model.data.get("leases") or engine.setup_running:
        raise ValueError("Zuerst laufende Alarme, Einrichtung und Wiederherstellung abschließen")


def _context(engine, payload):
    if not isinstance(payload, dict):
        raise ValueError("Ungültige Testdaten")
    did, kind, output = payload.get("id"), payload.get("alarm_type"), payload.get("output")
    if not isinstance(did, str) or not isinstance(kind, str) or not isinstance(output, str) or output not in _OUTPUTS:
        raise ValueError("Gerät, Alarmart und eine gültige Ausgabe auswählen")
    device = engine.model.data["devices"].get(did)
    if not device or not device.get("enabled"):
        raise ValueError("Ein aktiviertes Gerät auswählen")
    user = engine.model.data["users"].get(device.get("user_id"), {})
    if not user or not user.get("enabled", True) or kind not in user.get("types", []):
        raise ValueError("Der Benutzer erhält diese Alarmart nicht")
    profile = engine.model.profile(kind)
    device = deepcopy(engine.effective_device(device, kind))
    if not device.get(output):
        raise ValueError("Diese Ausgabe ist an der Alarmart oder am Gerät ausgeschaltet")
    if output in ("push", "sound", "speech"):
        if device.get("platform") not in ("android", "ios") or not device.get("notify_action"):
            raise ValueError("Für diese Ausgabe eine Handy-Verbindung auswählen")
    if output == "speech" and device.get("platform") != "android":
        raise ValueError("Sprachansage wird nur auf Android unterstützt")
    if output == "popup" and not device.get("browsers"):
        raise ValueError("Für das Meldungsfenster fehlt eine Browser-Zuordnung")
    source_id = payload.get("source_id")
    if source_id is not None and (not isinstance(source_id, str) or not source_id):
        raise ValueError("Ungültige Melderauswahl")
    source = engine.model.data["sources"].get(source_id) if source_id else None
    if source_id and (not source or source.get("type") != kind):
        raise ValueError("Der ausgewählte Melder gehört nicht zu dieser Alarmart")
    if source and not source.get("enabled", True):
        raise ValueError("Der ausgewählte Melder ist deaktiviert")
    if source and profile["mode"] == "message" and source.get("silent") and output in ("sound", "speech"):
        raise ValueError("Der ausgewählte Melder ist auf stumm gestellt")
    return device, profile, deepcopy(source) if source else None


def _text(engine, profile, source):
    example = source is None
    area = source.get("area", "") if source else "Beispielbereich"
    template = profile["speech_template"]
    if profile["mode"] == "message" and template == DEFAULT_SPEECH_TEMPLATE:
        body = ((source.get("message") or f'{source.get("name", "Melder")} · {area}')
                if source else "Dies ist eine Beispielmeldung.")
    else:
        body = template.format(name=profile["name"], site=engine.model.data["site_id"], areas=area)
    return "Test. " + body, example


def _still_current(engine, did, session):
    return _sessions(engine).get(did) is session


def _consume_result(task):
    if not task.cancelled():
        task.exception()


async def _operation(engine, session, factory, deadline, *, allow_stopping=False):
    """Bound the local await and yield immediately to an arriving real alarm.

    Cancellation cannot undo a command already accepted by HA/the handset. A
    non-cooperative operation stays referenced by the session, blocking reuse,
    but is not added to engine.tasks where it could delay global unload.
    """
    _idle(engine, allow_stopping=allow_stopping)
    async def invoke():
        _idle(engine, allow_stopping=allow_stopping)
        return await factory()
    task = asyncio.create_task(invoke())
    session["pending_operation"] = task
    task.add_done_callback(_consume_result)
    try:
        while True:
            _idle(engine, allow_stopping=allow_stopping)
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise ValueError("Zeitlimit der Testausgabe erreicht; Bereinigung später erneut versuchen")
            done, _ = await asyncio.wait({task}, timeout=min(GUARD_POLL_SECONDS, remaining))
            if done:
                result = task.result()
                _idle(engine, allow_stopping=allow_stopping)
                return result
    finally:
        if not task.done():
            task.cancel()
            await asyncio.wait({task}, timeout=CANCEL_DRAIN_SECONDS)


@asynccontextmanager
async def _popup_guard(engine, session, deadline, *, allow_stopping=False):
    state = {"acquired": False, "closed": False}
    async def acquire():
        await engine.popup_lock.acquire()
        if state["closed"]:
            engine.popup_lock.release()
            return False
        state["acquired"] = True
        return True
    try:
        await _operation(engine, session, acquire, deadline, allow_stopping=allow_stopping)
        yield
    finally:
        state["closed"] = True
        if state["acquired"]:
            engine.popup_lock.release()


async def _send(engine, session, device, payload, kind, deadline, *, allow_stopping=False):
    if not await _operation(engine, session, lambda: engine.send(device, payload, kind=kind), deadline,
                            allow_stopping=allow_stopping):
        raise ValueError("Testausgabe konnte nicht angefordert werden; Bereinigung erneut versuchen")


async def run_output_test(engine, payload):
    """Request exactly one chosen output; callers must enforce administrator access."""
    _idle(engine)
    device, profile, source = _context(engine, payload)
    did, kind, output = device["id"], profile["id"], payload["output"]
    async with engine.transport:
        _idle(engine)
        device, profile, source = _context(engine, payload)
        sessions = _sessions(engine)
        if did in sessions:
            raise ValueError("Den bisherigen Einzeltest zuerst stoppen")
        test_id = uuid4().hex
        session = {"test_id": test_id, "device_id": did, "alarm_type": kind,
                   "output": output, "device": device, "tag": "alarm_system_output_test_" + test_id,
                   "state": "requesting", "popup_browsers": []}
        text, example = _text(engine, profile, source)
        sessions[did] = session
        deadline = asyncio.get_running_loop().time() + ACTION_TIMEOUT_SECONDS
        try:
            if output in ("push", "sound"):
                data = {"tag": session["tag"], "channel": profile["channel"], "priority": "high", "ttl": 0}
                if output == "push":
                    data["push"] = {"sound": "none"}
                    if device["platform"] == "android":
                        data.update(channel="Alarmstatus", importance="low")
                elif device["platform"] == "ios":
                    data["push"] = {"sound": "default"}
                await _send(engine, session, device, {"title": "TEST · " + profile["name"],
                            "message": text, "data": data}, kind, deadline)
            elif output == "speech":
                await _send(engine, session, device, {"message": "TTS", "data": {
                    "tts_text": text, "media_stream": "music_stream", "priority": "high", "ttl": 0}}, kind, deadline)
            else:
                async with _popup_guard(engine, session, deadline):
                    for browser in device["browsers"]:
                        _idle(engine)
                        _context(engine, payload)
                        bid = browser["id"]
                        if engine.open_popups.get(bid):
                            raise ValueError("Ein Alarmfenster ist noch geöffnet")
                        # Record before awaiting: the service might act before reporting failure.
                        session["popup_browsers"].append(bid)
                        await _operation(engine, session, lambda: engine.hass.services.async_call("browser_mod", "popup", {
                            "browser_id": [bid], "tag": session["tag"], "title": "TEST · " + profile["name"],
                            "dismissable": True, "timeout": TEST_LIFETIME_SECONDS * 1000, "content": {"type": "markdown", "content": escape(text)}}, blocking=True), deadline)
            session["state"] = "requested"
            engine.model.log("output_test_requested", kind=kind, device=device,
                source=source, text=text, details={"test_id": test_id, "output": output, "example": example})
        except BaseException:
            session["state"] = "cleanup_pending"
            _schedule_expiry(engine, did, session)
            raise
        _schedule_expiry(engine, did, session)
    try:
        await engine.save()
    except BaseException:
        if _still_current(engine, did, session):
            session["state"] = "cleanup_pending"
        raise
    return {"ok": True, "test_id": test_id, "device_id": did, "alarm_type": kind,
                "output": output, "state": "requested", "requested": True, "example": example,
                "message": "Testausgabe angefordert; Empfang und Wiedergabe sind damit nicht bestätigt."}


def _schedule_expiry(engine, did, session):
    if getattr(engine, "stopping", False):
        return  # Unload cleanup owns this session; do not spawn a new worker after cancellation.
    async def expire():
        await asyncio.sleep(TEST_LIFETIME_SECONDS)
        if not _still_current(engine, did, session):
            return
        try:
            await stop_output_test(engine, {"id": did, "test_id": session["test_id"]}, _automatic=True)
        except Exception:
            # A new real alarm blocks cleanup commands. Keep the token for a later retry.
            if _still_current(engine, did, session):
                session["state"] = "cleanup_pending"
    session["worker"] = engine.spawn(expire())


async def stop_output_test(engine, payload, *, _automatic=False, _shutdown=False):
    """Clean only the current token's test, without touching newer alarm playback."""
    if not isinstance(payload, dict) or not isinstance(payload.get("id"), str) or not isinstance(payload.get("test_id"), str):
        raise ValueError("Gerät und aktuelle Testkennung fehlen")
    did = payload["id"]
    async with engine.transport:
        session = _sessions(engine).get(did)
        if not session:
            return {"ok": True, "test_id": payload["test_id"], "device_id": did, "state": "already_finished"}
        if session["test_id"] != payload["test_id"]:
            raise ValueError("Dieser Einzeltest ist nicht mehr aktuell")
        _idle(engine, allow_stopping=_shutdown)
        pending = session.get("pending_operation")
        if pending and not pending.done():
            raise ValueError("Testtransport wird noch abgebrochen; Bereinigung später erneut versuchen")
        device, kind = session["device"], session["alarm_type"]
        deadline = asyncio.get_running_loop().time() + ACTION_TIMEOUT_SECONDS
        session["state"] = "cleanup_pending"
        if session["output"] in ("push", "sound"):
            await _send(engine, session, device, {"message": "clear_notification", "data": {"tag": session["tag"]}}, kind, deadline, allow_stopping=_shutdown)
        elif session["output"] == "speech":
            await _send(engine, session, device, {"message": "command_stop_tts", "data": {}}, kind, deadline, allow_stopping=_shutdown)
        else:
            async with _popup_guard(engine, session, deadline, allow_stopping=_shutdown):
                for bid in session["popup_browsers"]:
                    _idle(engine, allow_stopping=_shutdown)
                    if engine.open_popups.get(bid):
                        raise ValueError("Alarmfenster aktiv; Testbereinigung später erneut versuchen")
                    await _operation(engine, session, lambda: engine.hass.services.async_call("browser_mod", "close_popup", {
                        "browser_id": [bid], "tag": session["tag"]}, blocking=True), deadline, allow_stopping=_shutdown)
        if not _still_current(engine, did, session):
            raise ValueError("Der Einzeltest wurde inzwischen ersetzt")
        del _sessions(engine)[did]
        worker = session.get("worker")
        if worker and worker is not asyncio.current_task() and not worker.done():
            worker.cancel()
        engine.model.log("output_test_stopped", kind=kind, device=device,
                         details={"test_id": session["test_id"], "output": session["output"], "automatic": _automatic})
    await engine.save()
    return {"ok": True, "test_id": session["test_id"], "device_id": did,
                "state": "stop_requested", "message": "Testende angefordert; das tatsächliche Ende am Gerät bitte prüfen."}


async def cleanup_output_tests(engine):
    """Best-effort unload cleanup; never stop a real alarm to clear a test."""
    results = {}
    for did, session in list(_sessions(engine).items()):
        try:
            results[did] = await stop_output_test(engine, {"id": did, "test_id": session["test_id"]}, _shutdown=True)
        except Exception:
            if _still_current(engine, did, session):
                session["state"] = "cleanup_pending"
            results[did] = {"ok": False, "state": "cleanup_pending"}
    return results
