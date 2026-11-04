"""Validated, persistent alarm profiles without Home Assistant dependencies."""
from __future__ import annotations

from math import isfinite
import re
from string import Formatter

from .const import CHANNELS, LABELS, TYPES

MAX_CUSTOM_TYPES = 32
DEFAULT_SPEECH_TEMPLATE = "Achtung. {name}. Standort {site}. {areas}."
_CUSTOM_ID = re.compile(r"CUSTOM_[0-9A-F]{12}\Z")
_PRIORITIES = {"INFO": 100, "WARNING": 90, "FIRE": 20, "INTRUSION": 10}


def _text(value, field, maximum, *, nonempty=False):
    if not isinstance(value, str) or len(value) > maximum or (nonempty and not value.strip()):
        raise ValueError("Ungültiger Text: " + field)
    return value.strip() if nonempty else value


def validate_speech_template(value):
    """Allow only three named placeholders, never attribute/index/format access."""
    value = _text(value, "speech_template", 240)
    if not value.strip():
        return DEFAULT_SPEECH_TEMPLATE
    try:
        for _, field, spec, conversion in Formatter().parse(value):
            if field is not None and (field not in {"name", "site", "areas"} or spec or conversion):
                raise ValueError("Nur {name}, {site} und {areas} sind als Sprachplatzhalter erlaubt")
    except ValueError as err:
        raise ValueError("Ungültige Sprachvorlage") from err
    return value


def _seconds(value, field, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 1 <= value <= maximum or not isfinite(value):
        raise ValueError("Ungültige Dauer: " + field)
    return value


def normalize_alarm_type(kind, record):
    """Normalize one profile; omitted fields receive compatible defaults."""
    if not isinstance(kind, str) or (kind not in TYPES and not _CUSTOM_ID.fullmatch(kind)):
        raise ValueError("Ungültige Alarmarten-ID")
    if not isinstance(record, dict) or record.get("id", kind) != kind:
        raise ValueError("Ungültiges Alarmartenprofil oder abweichende ID")
    builtin = kind in TYPES
    mode = "message" if kind in ("INFO", "WARNING") else "alarm"
    if record.get("mode", mode) != mode or type(record.get("builtin", builtin)) is not bool or record.get("builtin", builtin) != builtin:
        raise ValueError("Alarmmodus und Systemkennzeichnung sind unveränderlich")
    name = _text(record.get("name", LABELS.get(kind, "")), "name", 80, nonempty=True)
    channel = _text(record.get("channel", CHANNELS.get(kind, name)), "channel", 80, nonempty=True)
    if builtin and channel != CHANNELS[kind]:
        raise ValueError("Der Systemkanal ist unveränderlich")
    priority = record.get("priority", _PRIORITIES.get(kind, 30))
    if type(priority) is not int or not 1 <= priority <= 100:
        raise ValueError("Priorität muss eine ganze Zahl von 1 bis 100 sein")
    if builtin and priority != _PRIORITIES[kind]:
        raise ValueError("Die Systempriorität ist unveränderlich")
    result = {"id": kind, "name": name, "mode": mode, "priority": priority,
              "channel": channel, "builtin": builtin}
    for field in ("push", "sound", "speech", "popup"):
        value = record.get(field, field == "push" or mode == "alarm")
        if type(value) is not bool:
            raise ValueError("Schalter muss ein/aus sein: " + field)
        result[field] = value
    for field, default, maximum in (("tone_seconds", 5, 15), ("speech_seconds", 8, 12)):
        value = record.get(field, None if builtin else default)
        if builtin and value is None:
            pass  # Old profiles retain each device's existing times until explicitly changed.
        elif mode == "message":
            raise ValueError("Einmalige Meldungen verwenden keine Ablaufzeit: " + field)
        else:
            value = _seconds(value, field, maximum)
        result[field] = value
    result["speech_template"] = validate_speech_template(record.get("speech_template", DEFAULT_SPEECH_TEMPLATE))
    return result


def default_alarm_types():
    """Return independent built-in profiles for an old or empty installation."""
    return {kind: normalize_alarm_type(kind, {}) for kind in TYPES}


def normalize_alarm_types(records):
    """Validate a registry and migrate absent built-ins/fields using defaults."""
    if not isinstance(records, dict):
        raise ValueError("Alarmarten müssen als Zuordnung vorliegen")
    result = default_alarm_types()
    for kind, record in records.items():
        result[kind] = normalize_alarm_type(kind, record)
    if sum(not record["builtin"] for record in result.values()) > MAX_CUSTOM_TYPES:
        raise ValueError("Höchstens 32 eigene Alarmarten sind erlaubt")
    names = [record["name"].casefold() for record in result.values()]
    if len(names) != len(set(names)):
        raise ValueError("Alarmnamen müssen eindeutig sein")
    channels = [record["channel"].casefold() for record in result.values()]
    if len(channels) != len(set(channels)):
        raise ValueError("Benachrichtigungskanäle müssen eindeutig sein")
    return result
