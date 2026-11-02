"""Narrow import adapters for testing real engine code without installing HA.

These adapters do not implement Home Assistant behavior or HTTP authentication.
Tests explicitly replace transport/storage boundaries and exercise our own methods.
"""
from datetime import datetime, timezone
import importlib
from pathlib import Path
import sys
import types
from unittest.mock import patch


def load_runtime_modules():
    name = "_alarm_runtime_under_test"
    if f"{name}.engine" in sys.modules:
        return sys.modules[f"{name}.engine"], sys.modules[f"{name}.chart_view"]
    package = types.ModuleType(name)
    package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components/alarm_system")]
    sys.modules[name] = package
    modules = {key: types.ModuleType(key) for key in (
        "homeassistant", "homeassistant.core", "homeassistant.exceptions",
        "homeassistant.helpers", "homeassistant.helpers.storage", "homeassistant.helpers.event",
        "homeassistant.util", "homeassistant.util.dt", "homeassistant.components",
        "homeassistant.components.http", "homeassistant.components.http.const", "aiohttp")}
    class HAError(Exception):
        pass
    class Store:
        def __init__(self, *args, **kwargs):
            pass
    class View:
        pass
    class HTTPError(Exception):
        pass
    class Unauthorized(HTTPError):
        pass
    class Forbidden(HTTPError):
        pass
    class NotFound(HTTPError):
        pass
    modules["homeassistant.core"].Context = lambda **kwargs: types.SimpleNamespace(**kwargs)
    modules["homeassistant.exceptions"].HomeAssistantError = HAError
    modules["homeassistant.exceptions"].Unauthorized = HAError
    modules["homeassistant.helpers.storage"].Store = Store
    modules["homeassistant.helpers.event"].async_track_time_interval = lambda *args: lambda: None
    modules["homeassistant.util.dt"].utcnow = lambda: datetime.now(timezone.utc)
    modules["homeassistant.util.dt"].as_local = lambda value: value.astimezone()
    modules["homeassistant.util"].dt = modules["homeassistant.util.dt"]
    modules["homeassistant.components.http"].HomeAssistantView = View
    modules["homeassistant.components.http.const"].KEY_HASS_USER = "hass_user"
    modules["aiohttp"].web = types.SimpleNamespace(
        HTTPUnauthorized=Unauthorized, HTTPForbidden=Forbidden, HTTPNotFound=NotFound,
        Response=lambda **kwargs: types.SimpleNamespace(**kwargs))
    with patch.dict(sys.modules, modules):
        engine = importlib.import_module(f"{name}.engine")
        view = importlib.import_module(f"{name}.chart_view")
    return engine, view
