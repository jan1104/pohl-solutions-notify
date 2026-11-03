"""Real entry handlers with mocked HA registration and engine boundaries.

Decorators/schema conversion, HTTP and actual HA startup are not emulated here.
"""
import asyncio
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

from ha_test_support import load_entry_module

entry_module = load_entry_module()


class EntryLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.hass = types.SimpleNamespace(
            data={},
            http=types.SimpleNamespace(async_register_static_paths=AsyncMock(), register_view=Mock()),
            services=types.SimpleNamespace(async_register=Mock(), async_remove=Mock()),
            states=types.SimpleNamespace(async_remove=Mock()),
            config_entries=types.SimpleNamespace(async_update_entry=Mock()))
        self.entry = types.SimpleNamespace(title="Pohl Solutions Alarm Notify", data={"site_id": "TEST"})
        self.engine = types.SimpleNamespace(start=AsyncMock(), stop=AsyncMock(), cancel_workers=AsyncMock())
        for target, value in (
            ("AlarmEngine", Mock(return_value=self.engine)),
        ):
            patcher = patch.object(entry_module, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for module, attribute, replacement in (
            (entry_module.frontend, "add_extra_js_url", Mock()),
            (entry_module.frontend, "remove_extra_js_url", Mock()),
            (entry_module.frontend, "async_remove_panel", Mock()),
            (entry_module.panel_custom, "async_register_panel", AsyncMock()),
            (entry_module.websocket_api, "async_register_command", Mock()),
        ):
            patcher = patch.object(module, attribute, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)

    async def test_setup_registers_once_and_reload_reuses_static_resources(self):
        self.assertTrue(await entry_module.async_setup_entry(self.hass, self.entry))
        self.assertIs(self.hass.data["alarm_system"], self.engine)
        self.assertEqual(self.hass.services.async_register.call_count, 4)
        self.assertTrue(await entry_module.async_unload_entry(self.hass, self.entry))
        self.assertNotIn("alarm_system", self.hass.data)
        self.assertTrue(await entry_module.async_setup_entry(self.hass, self.entry))
        self.hass.http.async_register_static_paths.assert_awaited_once()
        self.hass.http.register_view.assert_called_once()
        self.assertEqual(entry_module.websocket_api.async_register_command.call_count, 6)

    async def test_duplicate_setup_does_not_replace_live_engine(self):
        previous = object()
        self.hass.data["alarm_system"] = previous
        with self.assertRaises(entry_module.HomeAssistantError):
            await entry_module.async_setup_entry(self.hass, self.entry)
        self.assertIs(self.hass.data["alarm_system"], previous)
        entry_module.AlarmEngine.assert_not_called()

    async def test_failed_engine_start_removes_listeners_panel_and_engine_without_save(self):
        self.engine.start.side_effect = RuntimeError("storage unavailable")
        with self.assertRaisesRegex(RuntimeError, "storage unavailable"):
            await entry_module.async_setup_entry(self.hass, self.entry)
        self.assertNotIn("alarm_system", self.hass.data)
        self.engine.cancel_workers.assert_awaited_once()
        self.engine.stop.assert_not_awaited()
        entry_module.frontend.async_remove_panel.assert_called_once_with(self.hass, "alarm-system")
        entry_module.frontend.remove_extra_js_url.assert_called_once()

    async def test_failed_panel_registration_is_cleaned_up_and_can_retry(self):
        entry_module.panel_custom.async_register_panel.side_effect = RuntimeError("panel failed")
        with self.assertRaisesRegex(RuntimeError, "panel failed"):
            await entry_module.async_setup_entry(self.hass, self.entry)
        self.assertNotIn("alarm_system", self.hass.data)
        entry_module.panel_custom.async_register_panel.side_effect = None
        self.assertTrue(await entry_module.async_setup_entry(self.hass, self.entry))

    async def test_unloaded_handlers_return_controlled_error(self):
        connection = types.SimpleNamespace(user=types.SimpleNamespace(id="admin", is_admin=True))
        for handler, message in (
            (entry_module.ws_get, {"id": 1}),
            (entry_module.ws_respond, {"id": 2, "incident_id": "missing", "action": "coming"}),
            (entry_module.ws_manage, {"id": 3, "action": "settings", "data": {}}),
        ):
            with self.subTest(handler=handler.__name__), self.assertRaisesRegex(
                    entry_module.HomeAssistantError, "nicht geladen"):
                await handler(self.hass, connection, message)

    async def test_unloading_missing_entry_is_idempotent(self):
        self.assertTrue(await entry_module.async_unload_entry(self.hass, self.entry))
        self.engine.stop.assert_not_awaited()


    async def test_failed_static_registration_does_not_remove_unregistered_frontend(self):
        self.hass.http.async_register_static_paths.side_effect = RuntimeError("static failed")
        with self.assertRaisesRegex(RuntimeError, "static failed"):
            await entry_module.async_setup_entry(self.hass, self.entry)
        self.assertNotIn("alarm_system", self.hass.data)
        entry_module.frontend.remove_extra_js_url.assert_not_called()
        entry_module.frontend.async_remove_panel.assert_not_called()

    async def test_cancelled_setup_cleans_up_and_propagates_cancellation(self):
        self.engine.start.side_effect = asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            await entry_module.async_setup_entry(self.hass, self.entry)
        self.assertNotIn("alarm_system", self.hass.data)
        self.engine.cancel_workers.assert_awaited_once()

    async def test_stopping_engine_is_not_available_to_websocket_clients(self):
        self.hass.data["alarm_system"] = types.SimpleNamespace(stopping=True)
        with self.assertRaisesRegex(entry_module.HomeAssistantError, "nicht geladen"):
            await entry_module.ws_get(self.hass, types.SimpleNamespace(), {"id": 1})


    async def test_setup_cleanup_error_preserves_original_failure_and_attempts_rest(self):
        self.engine.start.side_effect = RuntimeError("original startup error")
        self.hass.services.async_remove.side_effect = [RuntimeError("service cleanup failed"), None, None, None]
        with self.assertLogs(entry_module._LOGGER.name, level="ERROR"):
            with self.assertRaisesRegex(RuntimeError, "original startup error"):
                await entry_module.async_setup_entry(self.hass, self.entry)
        self.assertNotIn("alarm_system", self.hass.data)
        self.assertEqual(self.hass.services.async_remove.call_count, 4)
        entry_module.frontend.async_remove_panel.assert_called_once()
        entry_module.frontend.remove_extra_js_url.assert_called_once()
        self.hass.states.async_remove.assert_called_once()

    async def test_panel_cleanup_error_does_not_skip_script_and_sensor_cleanup(self):
        self.engine.start.side_effect = RuntimeError("original startup error")
        entry_module.frontend.async_remove_panel.side_effect = RuntimeError("panel cleanup failed")
        with self.assertLogs(entry_module._LOGGER.name, level="ERROR"):
            with self.assertRaisesRegex(RuntimeError, "original startup error"):
                await entry_module.async_setup_entry(self.hass, self.entry)
        entry_module.frontend.remove_extra_js_url.assert_called_once()
        self.hass.states.async_remove.assert_called_once()


class ManageValidationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Real model and handler; external persistence/identity boundaries are explicit.
        from ha_test_support import load_runtime_modules
        runtime, _ = load_runtime_modules()
        self.engine = runtime.AlarmEngine(types.SimpleNamespace(), types.SimpleNamespace(data={"site_id": "TEST"}))
        self.engine.actor = AsyncMock()
        self.engine.save = AsyncMock()
        self.engine.missing_categories = lambda device: []
        self.engine.schedule_category_setup = Mock()
        self.hass = types.SimpleNamespace(data={"alarm_system": self.engine})
        self.connection = types.SimpleNamespace(user=types.SimpleNamespace(id="admin", name="Admin"), send_result=Mock())

    async def test_missing_nested_ids_raise_controlled_error_before_mutation(self):
        before = self.engine.model.snapshot()
        for action in ("device_confirm", "device_test_begin", "device_test_stop", "device_test", "device_setup",
                       "device_remove", "user_remove", "user_upsert", "source_remove"):
            with self.subTest(action=action), self.assertRaises(entry_module.HomeAssistantError):
                await entry_module.ws_manage(self.hass, self.connection, {"id": 1, "action": action, "data": {}})
        self.assertEqual(self.engine.model.snapshot(), before)
        self.engine.save.assert_not_awaited()

    async def test_unknown_device_gets_controlled_error(self):
        for action in ("device_confirm", "device_test_begin", "device_test", "device_setup", "device_test_stop"):
            with self.subTest(action=action), self.assertRaises(entry_module.HomeAssistantError):
                await entry_module.ws_manage(self.hass, self.connection, {"id": 1, "action": action, "data": {"id": "unknown"}})
        self.engine.save.assert_not_awaited()

    async def test_confirmation_without_session_or_without_both_tests_is_rejected(self):
        device = {"id": "phone", "user_id": "user", "tested": False}
        self.engine.model.data["devices"]["phone"] = device
        for session in (None, "current"):
            if session:
                device["test_session"] = session
            with self.subTest(session=session), self.assertRaises(entry_module.HomeAssistantError):
                await entry_module.ws_manage(self.hass, self.connection, {"id": 1, "action": "device_confirm", "data": {"id": "phone"}})
            self.assertFalse(device["tested"])
        self.engine.save.assert_not_awaited()

    async def test_confirmation_with_both_current_completed_tests_succeeds(self):
        device = {"id": "phone", "user_id": "user", "tested": False, "test_session": "current"}
        self.engine.model.data["devices"]["phone"] = device
        self.engine.model.data["incidents"] = {
            kind: {"type": kind, "test_device": "phone", "test_session": "current", "status": "ended"}
            for kind in ("FIRE", "INTRUSION")}
        await entry_module.ws_manage(self.hass, self.connection, {"id": 1, "action": "device_confirm", "data": {"id": "phone"}})
        self.assertTrue(device["tested"])
        self.engine.save.assert_awaited_once()
        self.connection.send_result.assert_called_once()

    async def test_non_string_identifiers_are_rejected_before_indexing(self):
        for identifier in (None, [], {}, 0, "   "):
            with self.subTest(identifier=identifier), self.assertRaises(entry_module.HomeAssistantError):
                await entry_module.ws_manage(self.hass, self.connection,
                    {"id": 1, "action": "device_confirm", "data": {"id": identifier}})
        self.engine.save.assert_not_awaited()

    def configure_import_environment(self):
        user = types.SimpleNamespace(id="user", name="User", is_active=True, system_generated=False)
        self.hass.auth = types.SimpleNamespace(async_get_users=AsyncMock(return_value=[user]))
        self.hass.states = types.SimpleNamespace(async_all=lambda: [])
        self.hass.services = types.SimpleNamespace(async_services=lambda: {})
        return {"format": "alarm_system_configuration", "schema_version": 1,
                "site_id": "TEST", "users": {"user": {"id": "user", "types": ["FIRE", "INTRUSION"]}},
                "devices": {"phone": {"id": "phone", "user_id": "user", "platform": "browser",
                    "test_session": "old", "tested": True, "setup_retry_at": 9999999999,
                    "restore_pending": True}}, "sources": {}}

    async def test_import_preview_is_atomic_and_does_not_save(self):
        backup = self.configure_import_environment()
        before = self.engine.model.snapshot()
        await entry_module.ws_manage(self.hass, self.connection,
            {"id": 1, "action": "configuration_preview", "data": {"backup": backup}})
        self.assertEqual(self.engine.model.snapshot(), before)
        self.engine.save.assert_not_awaited()
        result = self.connection.send_result.call_args.args[1]
        self.assertEqual(result["counts"], {"users": 1, "devices": 1, "sources": 0})

    async def test_import_requires_fresh_test_session_and_discards_transient_state(self):
        backup = self.configure_import_environment()
        await entry_module.ws_manage(self.hass, self.connection,
            {"id": 1, "action": "configuration_import", "data": {"backup": backup}})
        device = self.engine.model.data["devices"]["phone"]
        self.assertFalse(device["tested"])
        for key in ("test_session", "setup_retry_at", "restore_pending"):
            self.assertNotIn(key, device)
        self.engine.save.assert_awaited_once()
        self.engine.schedule_category_setup.assert_called_once()

    async def test_invalid_import_keeps_existing_configuration(self):
        backup = self.configure_import_environment()
        backup["site_id"] = "OTHER"
        before = self.engine.model.snapshot()
        with self.assertRaises(entry_module.HomeAssistantError):
            await entry_module.ws_manage(self.hass, self.connection,
                {"id": 1, "action": "configuration_import", "data": {"backup": backup}})
        self.assertEqual(self.engine.model.snapshot(), before)
        self.engine.save.assert_not_awaited()

    async def save_output_device(self, platform="android", **overrides):
        self.engine.model.data["users"]["user"] = {"id": "user", "name": "User", "types": ["FIRE"]}
        self.hass.services = types.SimpleNamespace(has_service=lambda *args: True)
        payload = {"user_id": "user", "platform": platform, "name": "Phone",
                   "notify_action": "notify.mobile_app_phone" if platform != "browser" else "",
                   "browsers": [], "push": True, "popup": False, "sound": False, "speech": True,
                   **overrides}
        with patch.object(entry_module, "connections", return_value=({}, [])):
            await entry_module.ws_manage(self.hass, self.connection,
                {"id": 1, "action": "device_upsert", "data": payload})
        return self.engine.model.data["devices"][self.connection.send_result.call_args.args[1]["device_id"]]

    async def test_speech_change_requires_new_device_verification(self):
        device = await self.save_output_device()
        device.update(tested=True, test_session="verified")
        updated = await self.save_output_device(**{**device, "speech": False})
        self.assertFalse(updated["speech"])
        self.assertFalse(updated["tested"])
        self.assertNotIn("test_session", updated)

    async def test_ios_cannot_persist_unsupported_speech_switch(self):
        device = await self.save_output_device(platform="ios", speech=True)
        self.assertFalse(device["speech"])

    async def test_browser_cannot_persist_phone_outputs(self):
        device = await self.save_output_device(platform="browser", push=True, sound=True, speech=True)
        self.assertFalse(device["push"])
        self.assertFalse(device["sound"])
        self.assertFalse(device["speech"])
