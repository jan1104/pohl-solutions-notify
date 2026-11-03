"""One-shot output checks with real engine/model code and substituted HA transport."""
import asyncio
from copy import deepcopy
import importlib
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

from ha_test_support import import_adapters, load_runtime_modules

runtime, _ = load_runtime_modules()
with patch.dict("sys.modules", import_adapters()):
    output_tests = importlib.import_module(runtime.__package__ + ".output_tests")


class OutputTestTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.hass = types.SimpleNamespace(data={}, states=types.SimpleNamespace(get=lambda entity: None),
            services=types.SimpleNamespace(async_call=AsyncMock()),
            async_create_background_task=lambda coro, name: asyncio.create_task(coro))
        self.engine = runtime.AlarmEngine(self.hass, types.SimpleNamespace(data={"site_id": "TEST"}))
        self.engine.send = AsyncMock(return_value=True)
        self.engine.save = AsyncMock()
        self.profile = self.engine.model.upsert_alarm_type({"name": "Hausalarm"})
        self.kind = self.profile["id"]
        self.engine.model.data['users']['user'] = {'id': 'user', 'enabled': True, 'types': [self.kind, 'INFO']}
        self.device = {'id': 'phone', 'user_id': 'user', 'name': 'Handy', 'enabled': True, 'tested': False,
            'platform': 'android', 'notify_action': 'notify.mobile_app_phone', 'browsers': [{'id': 'browser'}],
            'push': True, 'sound': True, 'speech': True, 'popup': True}
        self.engine.model.data['devices']['phone'] = self.device

    async def asyncTearDown(self):
        tasks = list(self.engine.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    def payload(self, output='speech', **extra):
        return {'id': 'phone', 'alarm_type': self.kind, 'output': output, **extra}

    async def run_test(self, output='speech', **extra):
        return await output_tests.run_output_test(self.engine, self.payload(output, **extra))

    async def test_speech_is_once_marked_test_and_never_grants_baseline_approval(self):
        snapshot = self.engine.model.snapshot()
        result = await self.run_test()
        self.assertTrue(result['requested'])
        self.assertEqual(result['state'], 'requested')
        self.assertTrue(result['example'])
        self.assertEqual(self.engine.send.await_count, 1)
        payload = self.engine.send.await_args.args[1]
        self.assertEqual(payload['message'], 'TTS')
        self.assertEqual(payload['data']['media_stream'], 'music_stream')
        self.assertEqual(payload['data']['tts_text'], 'Test. Achtung. Hausalarm. Standort TEST. Beispielbereich.')
        self.assertFalse(self.device['tested'])
        self.assertEqual(self.engine.model.data['incidents'], snapshot['incidents'])
        self.assertEqual(self.engine.model.data['signal_values'], snapshot['signal_values'])
        self.assertFalse(self.engine.model.data['leases'])
        self.assertNotIn('test_session', self.device)

    async def test_message_test_uses_real_source_text_and_never_pushes_as_side_effect(self):
        self.engine.model.upsert_alarm_type({'id': 'INFO', 'speech': True})
        source = self.engine.model.register_source({'id': 'garage', 'name': 'Tor', 'entity_id': 'binary_sensor.garage',
            'type': 'INFO', 'area': 'Hof', 'message': 'Das Tor steht offen.'}, 'off')
        before = deepcopy(self.engine.model.data['signal_values'])
        result = await output_tests.run_output_test(self.engine, self.payload('speech', alarm_type='INFO', source_id=source['id']))
        self.assertFalse(result['example'])
        self.assertEqual(self.engine.send.await_args.args[1]['data']['tts_text'], 'Test. Das Tor steht offen.')
        self.assertEqual(self.engine.send.await_count, 1)
        self.assertEqual(self.engine.model.data['signal_values'], before)

    async def test_profile_and_device_switches_must_both_allow_output(self):
        for target in ('profile', 'device'):
            with self.subTest(target=target):
                if target == 'profile':
                    self.engine.model.upsert_alarm_type({'id': self.kind, 'speech': False})
                else:
                    self.engine.model.upsert_alarm_type({'id': self.kind, 'speech': True})
                    self.device['speech'] = False
                with self.assertRaises(ValueError):
                    await self.run_test()
        self.engine.send.assert_not_awaited()
        self.assertFalse(getattr(self.engine, 'output_tests', {}))

    async def test_disabled_or_unassigned_user_or_device_cannot_be_tested(self):
        for target in ('device', 'user', 'membership'):
            with self.subTest(target=target):
                self.device['enabled'] = target != 'device'
                self.engine.model.data['users']['user']['enabled'] = target != 'user'
                self.engine.model.data['users']['user']['types'] = [] if target == 'membership' else [self.kind]
                with self.assertRaises(ValueError):
                    await self.run_test()
        self.engine.send.assert_not_awaited()

    async def test_unsupported_platform_or_missing_browser_is_rejected(self):
        self.device['platform'] = 'ios'
        with self.assertRaises(ValueError):
            await self.run_test()
        self.device['platform'] = 'browser'
        with self.assertRaises(ValueError):
            await self.run_test('push')
        self.device['browsers'] = []
        with self.assertRaises(ValueError):
            await self.run_test('popup')
        self.engine.send.assert_not_awaited()

    async def test_actual_alarm_recovery_or_setup_blocks_tests_before_transport(self):
        for target in ('alarm', 'lease', 'setup', 'stopping', 'recovering'):
            with self.subTest(target=target):
                self.engine.model.data['incidents'] = {}
                self.engine.model.data['leases'] = {}
                self.engine.setup_running.clear()
                self.engine.stopping = target == 'stopping'
                self.engine.recovering = target == 'recovering'
                if target == 'alarm':
                    self.engine.model.raise_alarm({'type': self.kind, 'alarm_key': 'real', 'source_id': 'real'})
                elif target == 'lease':
                    self.engine.model.data['leases']['phone'] = {'restore_pending': True}
                elif target == 'setup':
                    self.engine.setup_running.add('phone')
                with self.assertRaises(ValueError):
                    await self.run_test()
        self.engine.send.assert_not_awaited()

    async def test_validation_is_rechecked_after_waiting_for_transport_lock(self):
        async with self.engine.transport:
            task = asyncio.create_task(self.run_test())
            await asyncio.sleep(0)
            self.engine.model.data['users']['user']['enabled'] = False
        with self.assertRaises(ValueError):
            await task
        self.engine.send.assert_not_awaited()

    async def test_push_is_quiet_and_sound_uses_only_normal_channel(self):
        push = await self.run_test('push')
        payload = self.engine.send.await_args.args[1]
        self.assertTrue(payload['title'].startswith('TEST'))
        self.assertEqual(payload['data']['push']['sound'], 'none')
        self.assertEqual(payload['data']['channel'], 'Alarmstatus')
        await output_tests.stop_output_test(self.engine, {'id': 'phone', 'test_id': push['test_id']})
        await self.run_test('sound')
        payload = self.engine.send.await_args.args[1]
        self.assertEqual(payload['data']['channel'], self.profile['channel'])
        self.assertNotIn('command', payload['data'])
        self.assertFalse(self.engine.model.data['leases'])

    async def test_popup_is_tagged_dismissable_escaped_and_closed_only_by_its_tag(self):
        self.engine.model.upsert_alarm_type({'id': self.kind, 'speech_template': '<script>Text</script>'})
        result = await self.run_test('popup')
        payload = self.hass.services.async_call.await_args.args[2]
        self.assertTrue(payload['dismissable'])
        self.assertEqual(payload['timeout'], 30000)
        self.assertTrue(payload['tag'].startswith('alarm_system_output_test_'))
        self.assertIn('&lt;script&gt;', payload['content']['content'])
        tag = payload['tag']
        await output_tests.stop_output_test(self.engine, {'id': 'phone', 'test_id': result['test_id']})
        call = self.hass.services.async_call.await_args
        self.assertEqual(call.args[:2], ('browser_mod', 'close_popup'))
        self.assertEqual(call.args[2]['tag'], tag)
        self.engine.send.assert_not_awaited()

    async def test_stale_stop_cannot_stop_newer_test_and_finished_stop_is_idempotent(self):
        first = await self.run_test()
        with self.assertRaises(ValueError):
            await self.run_test()
        await output_tests.stop_output_test(self.engine, {'id': 'phone', 'test_id': first['test_id']})
        again = await output_tests.stop_output_test(self.engine, {'id': 'phone', 'test_id': first['test_id']})
        self.assertEqual(again['state'], 'already_finished')
        newer = await self.run_test()
        self.engine.send.reset_mock()
        with self.assertRaises(ValueError):
            await output_tests.stop_output_test(self.engine, {'id': 'phone', 'test_id': first['test_id']})
        self.engine.send.assert_not_awaited()
        self.assertEqual(self.engine.output_tests['phone']['test_id'], newer['test_id'])

    async def test_cleanup_never_stops_actual_alarm_and_remains_retriable(self):
        result = await self.run_test()
        incident, _ = self.engine.model.raise_alarm({'type': self.kind, 'alarm_key': 'real', 'source_id': 'real'})
        self.engine.send.reset_mock()
        with self.assertRaises(ValueError):
            await output_tests.stop_output_test(self.engine, {'id': 'phone', 'test_id': result['test_id']})
        self.engine.send.assert_not_awaited()
        self.assertIn('phone', self.engine.output_tests)
        self.engine.model.false_alarm(incident['id'], None)
        await output_tests.stop_output_test(self.engine, {'id': 'phone', 'test_id': result['test_id']})
        self.assertEqual(self.engine.send.await_args.args[1]['message'], 'command_stop_tts')
        self.assertNotIn('phone', self.engine.output_tests)

    async def test_failed_transport_retains_token_and_cleanup_can_retry(self):
        self.engine.send.return_value = False
        with self.assertRaises(ValueError):
            await self.run_test()
        session = self.engine.output_tests['phone']
        self.assertEqual(session['state'], 'cleanup_pending')
        with self.assertRaises(ValueError):
            await output_tests.stop_output_test(self.engine, {'id': 'phone', 'test_id': session['test_id']})
        self.assertIn('phone', self.engine.output_tests)
        self.engine.send.return_value = True
        await output_tests.stop_output_test(self.engine, {'id': 'phone', 'test_id': session['test_id']})
        self.assertNotIn('phone', self.engine.output_tests)

    async def test_source_type_enabled_and_silent_rules_are_enforced(self):
        self.engine.model.upsert_alarm_type({'id': 'INFO', 'speech': True, 'sound': True})
        source = self.engine.model.register_source({'id': 'door', 'name': 'Tür', 'entity_id': 'binary_sensor.door',
            'type': 'INFO', 'silent': True}, 'off')
        for output in ('speech', 'sound'):
            with self.subTest(output=output), self.assertRaises(ValueError):
                await self.run_test(output, alarm_type='INFO', source_id='door')
        source['silent'] = False
        source['enabled'] = False
        with self.assertRaises(ValueError):
            await self.run_test('push', alarm_type='INFO', source_id='door')
        source['enabled'] = True
        source['type'] = 'INFO'
        with self.assertRaises(ValueError):
            await self.run_test('push', source_id='door')
        self.engine.send.assert_not_awaited()

    async def test_expiry_cleans_only_current_test_and_no_approval_changes(self):
        with patch.object(output_tests, 'TEST_LIFETIME_SECONDS', 0):
            result = await self.run_test()
            await self.engine.output_tests['phone']['worker']
        self.assertNotIn('phone', self.engine.output_tests)
        self.assertFalse(self.device['tested'])
        self.assertEqual(self.engine.send.await_args.args[1]['message'], 'command_stop_tts')

    async def test_shutdown_cleanup_allows_stopping_but_never_active_alarms(self):
        result = await self.run_test('push')
        self.engine.stopping = True
        cleaned = await output_tests.cleanup_output_tests(self.engine)
        self.assertEqual(cleaned['phone']['state'], 'stop_requested')
        self.assertFalse(self.engine.output_tests)
        self.assertEqual(self.engine.send.await_args.args[1]['data']['tag'], 'alarm_system_output_test_' + result['test_id'])

    async def test_stale_silent_flag_does_not_disable_real_alarm_source_speech(self):
        self.engine.model.register_source({'id': 'door', 'name': 'Tür', 'entity_id': 'binary_sensor.door',
            'type': self.kind, 'silent': True}, 'off')
        result = await self.run_test('speech', source_id='door')
        self.assertTrue(result['requested'])
        self.assertEqual(self.engine.send.await_args.args[1]['message'], 'TTS')

    async def test_cancelled_request_during_unload_does_not_spawn_new_timer(self):
        async def interrupted(*args, **kwargs):
            self.engine.stopping = True
            raise asyncio.CancelledError()
        self.engine.send.side_effect = interrupted
        with self.assertRaises(asyncio.CancelledError):
            await self.run_test()
        self.assertEqual(self.engine.output_tests['phone']['state'], 'cleanup_pending')
        self.assertFalse(self.engine.tasks)

    async def test_pending_test_transport_yields_promptly_when_real_alarm_arrives(self):
        entered = asyncio.Event()
        cancelled = asyncio.Event()
        async def hanging_send(*args, **kwargs):
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        self.engine.send.side_effect = hanging_send
        test = asyncio.create_task(self.run_test())
        await asyncio.wait_for(entered.wait(), timeout=1)
        self.engine.model.raise_alarm({'type': self.kind, 'alarm_key': 'real', 'source_id': 'real'})
        with self.assertRaises(ValueError):
            await asyncio.wait_for(test, timeout=1)
        self.assertTrue(cancelled.is_set())
        self.assertFalse(self.engine.transport.locked())
        async with asyncio.timeout(1):
            async with self.engine.transport:
                pass
        self.assertEqual(self.engine.output_tests['phone']['state'], 'cleanup_pending')

    async def test_hanging_test_transport_has_bounded_deadline(self):
        async def hanging_send(*args, **kwargs):
            await asyncio.Event().wait()
        self.engine.send.side_effect = hanging_send
        with patch.object(output_tests, 'ACTION_TIMEOUT_SECONDS', .02):
            with self.assertRaisesRegex(ValueError, 'Zeitlimit'):
                await asyncio.wait_for(self.run_test(), timeout=1)
        self.assertFalse(self.engine.transport.locked())
        self.assertTrue(self.engine.output_tests['phone']['pending_operation'].cancelled())

    async def test_save_wait_does_not_hold_transport_lock(self):
        entered = asyncio.Event()
        release = asyncio.Event()
        async def slow_save():
            entered.set()
            await release.wait()
        self.engine.save.side_effect = slow_save
        test = asyncio.create_task(self.run_test())
        await asyncio.wait_for(entered.wait(), timeout=1)
        self.assertFalse(self.engine.transport.locked())
        release.set()
        await test

    async def test_popup_lock_is_released_when_alarm_arrives_at_acquire_completion(self):
        lock = self.engine.popup_lock
        async def acquire_then_alarm():
            await lock.acquire()
            self.engine.model.raise_alarm({'type': self.kind, 'alarm_key': 'real', 'source_id': 'real'})
            return True
        self.engine.popup_lock = types.SimpleNamespace(acquire=acquire_then_alarm, release=lock.release)
        with self.assertRaises(ValueError):
            await self.run_test('popup')
        self.assertFalse(lock.locked())
        self.assertFalse(self.engine.transport.locked())
        self.hass.services.async_call.assert_not_awaited()

    async def test_noncooperative_cancel_retains_session_and_blocks_reuse_without_global_worker(self):
        release = asyncio.Event()
        async def slow_native_boundary(*args, **kwargs):
            try:
                await release.wait()
            except asyncio.CancelledError:
                await release.wait()
            return True
        self.engine.send.side_effect = slow_native_boundary
        with patch.object(output_tests, 'ACTION_TIMEOUT_SECONDS', .01), patch.object(output_tests, 'CANCEL_DRAIN_SECONDS', .01):
            with self.assertRaisesRegex(ValueError, 'Zeitlimit'):
                await self.run_test()
        session = self.engine.output_tests['phone']
        pending = session['pending_operation']
        try:
            self.assertFalse(pending.done())
            self.assertNotIn(pending, self.engine.tasks)
            with self.assertRaisesRegex(ValueError, 'abgebrochen'):
                await output_tests.stop_output_test(self.engine, {'id': 'phone', 'test_id': session['test_id']})
            with self.assertRaisesRegex(ValueError, 'zuerst stoppen'):
                await self.run_test()
            self.assertFalse(self.engine.transport.locked())
        finally:
            release.set()
            await pending
        self.engine.send.side_effect = None
        await output_tests.stop_output_test(self.engine, {'id': 'phone', 'test_id': session['test_id']})
        self.assertFalse(self.engine.output_tests)
