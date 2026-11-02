"""Narrow import adapters for testing real engine code without installing HA.

These adapters do not implement Home Assistant behavior or HTTP authentication.
Tests explicitly replace transport/storage boundaries and exercise our own methods.
"""
from datetime import datetime, timezone
import importlib
import importlib.util
from pathlib import Path
import sys
import types
from unittest.mock import AsyncMock, Mock, patch


def import_adapters():
    modules = {key: types.ModuleType(key) for key in (
        "homeassistant", "homeassistant.core", "homeassistant.exceptions",
        "homeassistant.helpers", "homeassistant.helpers.storage", "homeassistant.helpers.event",
        "homeassistant.util", "homeassistant.util.dt", "homeassistant.components",
        "homeassistant.components.http", "homeassistant.components.http.const", "aiohttp",
        "homeassistant.components.frontend", "homeassistant.components.panel_custom",
        "homeassistant.components.websocket_api", "probatio")}
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
    modules["homeassistant.core"].callback = lambda function: function
    modules["homeassistant.components.http"].StaticPathConfig = lambda *args: args
    frontend = modules["homeassistant.components.frontend"]
    frontend.add_extra_js_url = Mock()
    frontend.remove_extra_js_url = Mock()
    frontend.async_remove_panel = Mock()
    modules["homeassistant.components.panel_custom"].async_register_panel = AsyncMock()
    websocket = modules["homeassistant.components.websocket_api"]
    websocket.websocket_command = lambda schema: lambda function: function
    websocket.async_response = lambda function: function
    websocket.async_register_command = Mock()
    # Import/schema placeholders only: these tests do not claim schema validation.
    schema = modules["probatio"]
    schema.Required = schema.Optional = lambda key, **kwargs: key
    schema.Schema = lambda value: value
    schema.In = schema.Range = schema.Coerce = lambda *args, **kwargs: None
    schema.All = lambda *args: None
    return modules


def load_runtime_modules():
    name = "_alarm_runtime_under_test"
    if f"{name}.engine" in sys.modules:
        return sys.modules[f"{name}.engine"], sys.modules[f"{name}.chart_view"]
    package = types.ModuleType(name)
    package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components/alarm_system")]
    sys.modules[name] = package
    with patch.dict(sys.modules, import_adapters()):
        engine = importlib.import_module(f"{name}.engine")
        view = importlib.import_module(f"{name}.chart_view")
    return engine, view


def load_entry_module():
    name = "_alarm_entry_under_test"
    if name in sys.modules:
        return sys.modules[name]
    path = Path(__file__).resolve().parents[1] / "custom_components/alarm_system/__init__.py"
    spec = importlib.util.spec_from_file_location(name, path, submodule_search_locations=[str(path.parent)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    with patch.dict(sys.modules, import_adapters()):
        spec.loader.exec_module(module)
    return module
