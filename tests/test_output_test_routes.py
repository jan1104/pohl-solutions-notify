"""Administrator boundaries and integration of one-shot output tests."""
import importlib
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch
from ha_test_support import load_runtime_modules, load_entry_module

runtime, _ = load_runtime_modules()
entry = load_entry_module()


class OutputTestRoutes(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.hass = types.SimpleNamespace(data={}, states=types.SimpleNamespace(get=lambda _: None))
        self.engine = runtime.AlarmEngine(self.hass, types.SimpleNamespace(data={'site_id': 'TEST'}))
        self.engine.actor = AsyncMock()
        self.engine.save = AsyncMock()
        self.hass.data['alarm_system'] = self.engine
        self.device = {'id': 'phone', 'user_id': 'user', 'name': 'Phone', 'enabled': True,
                       'tested': True, 'platform': 'android', 'notify_action': 'notify.mobile_app_phone',
                       'push': True, 'sound': True, 'speech': True, 'popup': False}
        self.engine.model.data['devices']['phone'] = self.device
        self.engine.model.data['users']['user'] = {'id': 'user', 'enabled': True, 'types': ['FIRE', 'INFO']}
        self.connection = types.SimpleNamespace(user=types.SimpleNamespace(id='admin',name='Admin'), send_result=Mock())

    async def manage(self, action, data):
        await entry.ws_manage(self.hass, self.connection, {'id': 1, 'action': action, 'data': data})

    async def test_run_routes_to_backend_after_admin_check_and_returns_test_identity(self):
        with patch.object(entry, 'run_output_test', AsyncMock(return_value={'test_id': 'token', 'state': 'requested'})) as run:
            payload = {'id': 'phone', 'alarm_type': 'FIRE', 'output': 'push'}
            await self.manage('output_test', payload)
            self.engine.actor.assert_awaited_once_with('admin', admin=True)
            run.assert_awaited_once_with(self.engine, payload)
            self.assertEqual(self.connection.send_result.call_args.args[1]['test_id'], 'token')
            self.engine.save.assert_awaited_once()

    async def test_stop_routes_with_exact_test_token(self):
        with patch.object(entry, 'stop_output_test', AsyncMock(return_value={'state': 'stopped'})) as stop:
            payload = {'id': 'phone', 'test_id': 'token'}
            await self.manage('output_test_stop', payload)
            stop.assert_awaited_once_with(self.engine, payload)

    async def test_normal_user_cannot_run_or_stop_output_test(self):
        self.engine.actor.side_effect = runtime.Unauthorized('Admin required')
        for action, payload in [('output_test', {'id': 'phone', 'alarm_type': 'FIRE', 'output': 'push'}),
                                ('output_test_stop', {'id': 'phone', 'test_id': 'token'})]:
            with self.subTest(action=action), patch.object(entry, 'run_output_test', AsyncMock()) as run, patch.object(entry, 'stop_output_test', AsyncMock()) as stop:
                with self.assertRaises(runtime.Unauthorized):
                    await self.manage(action, payload)
                run.assert_not_awaited()
                stop.assert_not_awaited()
        self.engine.save.assert_not_awaited()

    async def test_malformed_test_identifiers_are_rejected_before_transport(self):
        for field in ('id', 'alarm_type', 'output'):
            for value in (None, [], {}, '', '  ', 42):
                with self.subTest(field=field, value=value):
                    payload = {'id': 'phone', 'alarm_type': 'FIRE', 'output': 'push', field: value}
                    with patch.object(entry, 'run_output_test', AsyncMock()) as run:
                        with self.assertRaises((entry.HomeAssistantError, runtime.HomeAssistantError)):
                            await self.manage('output_test', payload)
                        run.assert_not_awaited()

    async def test_device_and_profile_changes_are_blocked_during_output_test(self):
        self.engine.output_tests['phone'] = {'test_id': 'current'}
        for action, payload in [('device_remove', {'id': 'phone'}), ('device_test_begin', {'id': 'phone'}),
                                ('alarm_type_upsert', {'id': 'FIRE', 'name': 'New'})]:
            with self.subTest(action=action), self.assertRaises((entry.HomeAssistantError, runtime.HomeAssistantError)):
                await self.manage(action, payload)
        self.assertIn('phone', self.engine.model.data['devices'])
        self.assertTrue(self.device['tested'])
        self.engine.save.assert_not_awaited()

    async def test_normal_message_cannot_take_audio_away_from_current_output_test(self):
        self.engine.model.upsert_alarm_type({'id': 'INFO', 'speech': True, 'sound': True, 'popup': True})
        self.engine.output_tests['phone'] = {'test_id': 'current'}
        self.engine.send = AsyncMock(return_value=True)
        self.engine.message_popup = AsyncMock()
        await self.engine.simple_message({'type': 'INFO', 'message': 'Normal information'})
        self.assertEqual(self.engine.send.await_count, 1)
        self.assertEqual(self.engine.send.await_args.args[1]['data']['channel'], 'Alarmstatus')
        self.engine.message_popup.assert_not_awaited()

    async def test_category_setup_and_baseline_confirmation_wait_for_output_test(self):
        self.engine.output_tests['phone'] = {'test_id': 'current'}
        with self.assertRaises((entry.HomeAssistantError, runtime.HomeAssistantError)):
            await self.engine.prepare_categories('phone')
        with self.assertRaises((entry.HomeAssistantError, runtime.HomeAssistantError)):
            self.engine.ensure_test_ready(self.device)
