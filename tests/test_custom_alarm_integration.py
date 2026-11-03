"""Custom alarms across real engine/entry/import boundaries with HA adapters."""
import asyncio
from copy import deepcopy
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

from ha_test_support import load_runtime_modules, load_entry_module

runtime, _ = load_runtime_modules()
entry = load_entry_module()


class CustomAlarmIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.hass = types.SimpleNamespace(
            data={}, states=types.SimpleNamespace(get=lambda entity: None),
            async_create_background_task=lambda coro, name: asyncio.create_task(coro))
        self.engine = runtime.AlarmEngine(self.hass, types.SimpleNamespace(data={"site_id": "TEST"}))
        self.engine.save = AsyncMock()
        self.engine.actor = AsyncMock()
        self.engine.schedule_category_setup = Mock()
        self.hass.data['alarm_system'] = self.engine
        self.profile = self.engine.model.upsert_alarm_type({'name': 'Hausalarm'})
        self.kind = self.profile['id']
        self.engine.model.data['users'] = {'user': {'id': 'user', 'name': 'User', 'enabled': True, 'types': [self.kind]}}
        self.device = {'id': 'phone', 'user_id': 'user', 'platform': 'android', 'enabled': True,
                       'tested': True, 'notify_action': 'notify.mobile_app_phone',
                       'push': True, 'sound': True, 'speech': True, 'popup': True}
        self.engine.model.data['devices'] = {'phone': self.device}
        self.connection = types.SimpleNamespace(user=types.SimpleNamespace(id='admin',name='Admin'), send_result=Mock())

    async def asyncTearDown(self):
        tasks = list(self.engine.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    def incident(self):
        return self.engine.model.raise_alarm({'type': self.kind, 'alarm_key': 'house',
            'source_id': 'door', 'source_name': 'Tür', 'area': 'EG'})[0]

    async def manage(self, action, data):
        await entry.ws_manage(self.hass, self.connection, {'id': 1, 'action': action, 'data': data})

    async def test_admin_creation_and_edit_retest_only_assigned_devices(self):
        await self.manage('alarm_type_upsert', {'id': self.kind, 'name': 'Hausalarm neu', 'speech': False})
        self.assertEqual(self.engine.model.label(self.kind), 'Hausalarm neu')
        self.assertFalse(self.device['tested'])
        self.assertEqual(self.connection.send_result.call_args.args[1]['alarm_type_id'], self.kind)
        self.engine.save.assert_awaited_once()

    async def test_registry_changes_are_blocked_during_incident(self):
        self.incident()
        before = self.engine.model.snapshot()
        with self.assertRaises(entry.HomeAssistantError):
            await self.manage('alarm_type_upsert', {'id': self.kind, 'name': 'Changed'})
        self.assertEqual(self.engine.model.snapshot(), before)
        self.engine.save.assert_not_awaited()

    async def test_registry_changes_are_blocked_during_pending_recovery(self):
        self.engine.model.data['leases']['phone'] = {'incident_id': 'ended', 'restore_pending': True}
        with self.assertRaises(entry.HomeAssistantError):
            await self.manage('alarm_type_upsert', {'name': 'Amokalarm'})
        self.engine.save.assert_not_awaited()

    async def test_regular_account_cannot_manage_alarm_registry(self):
        user = types.SimpleNamespace(id='user', is_active=True, is_admin=False)
        self.hass.auth = types.SimpleNamespace(async_get_user=AsyncMock(return_value=user))
        del self.engine.actor
        with self.assertRaises(runtime.Unauthorized):
            await self.manage('alarm_type_upsert', {'name': 'Amokalarm'})
        self.engine.save.assert_not_awaited()

    def test_profile_output_flags_respect_device_off_switches(self):
        self.engine.model.upsert_alarm_type({'id': self.kind, 'sound': False, 'popup': False})
        self.device['speech'] = False
        effective = self.engine.recipients(self.incident())[0]
        self.assertFalse(effective['sound'])
        self.assertFalse(effective['popup'])
        self.assertFalse(effective['speech'])
        self.assertTrue(effective['push'])

    def test_custom_priority_applies_per_device(self):
        self.engine.model.upsert_alarm_type({'id': self.kind, 'priority': 5})
        self.engine.model.data['users']['user']['types'].append('INTRUSION')
        custom = self.incident()
        self.engine.model.raise_alarm({'type': 'INTRUSION', 'alarm_key': 'intrusion', 'source_id': 'motion'})
        self.assertEqual(self.engine.primary_for_device(self.device)['id'], custom['id'])

    async def test_unknown_action_type_is_controlled_error(self):
        with self.assertRaises(runtime.HomeAssistantError):
            await self.engine.dispatch({'type': 'NOT_CONFIGURED'})
        self.engine.save.assert_not_awaited()

    async def test_custom_dispatch_creates_real_event_and_cycle(self):
        self.engine.cycle = AsyncMock()
        await self.engine.dispatch({'type': self.kind, 'alarm_key': 'house', 'source_id': 'door'})
        await asyncio.sleep(0)
        self.assertEqual(len(self.engine.model.active()), 1)
        self.engine.cycle.assert_awaited_once()

    async def test_custom_notify_uses_own_name_and_stable_android_channel(self):
        self.engine.model.upsert_alarm_type({'id': self.kind, 'name': 'Neuer Hausalarm'})
        self.engine.send = AsyncMock(return_value=True)
        await self.engine.notify(self.device, self.incident(), loud=True)
        payload = self.engine.send.await_args.args[1]
        self.assertIn('Neuer Hausalarm', payload['title'])
        self.assertEqual(payload['data']['channel'], 'Hausalarm')

    async def test_custom_speech_template_and_duration_are_used(self):
        self.engine.model.upsert_alarm_type({'id': self.kind, 'sound': False, 'speech_seconds': 2,
            'speech_template': '{name}: {site}; {areas}'})
        device = self.engine.effective_device(self.device, self.kind)
        incident = self.incident()
        self.engine.model.data['leases']['phone'] = {'incident_id': incident['id'], 'playback_id': 'speech', 'speech_only': True}
        self.engine.command = AsyncMock(return_value=True)
        with patch.object(runtime.asyncio, 'sleep', new_callable=AsyncMock) as sleep:
            await self.engine.finish_android_cycle(device, incident, 'speech')
        self.assertEqual(self.engine.command.await_args.kwargs['tts_text'], 'Hausalarm: TEST; EG')
        sleep.assert_awaited_once_with(2.0)

    def test_custom_voice_only_profile_needs_no_tone_sensor_setup(self):
        self.engine.model.upsert_alarm_type({'id': self.kind, 'sound': False})
        self.assertEqual(self.engine.required_categories(self.device), [])

    def backup(self):
        return {'format': 'alarm_system_configuration', 'schema_version': 2, 'site_id': 'TEST',
                'alarm_types': deepcopy(self.engine.model.data['alarm_types']),
                'users': deepcopy(self.engine.model.data['users']),
                'devices': deepcopy(self.engine.model.data['devices']), 'sources': {}}

    def test_custom_configuration_round_trip_revalidates_devices(self):
        data = entry.prepare_import(self.engine.model.snapshot(), self.backup(), {'user': 'User'}, {}, {'notify.mobile_app_phone'})
        self.assertEqual(data['alarm_types'][self.kind]['name'], 'Hausalarm')
        self.assertIn(self.kind, data['users']['user']['types'])
        self.assertFalse(data['devices']['phone']['tested'])

    def test_schema_two_requires_profile_definitions_and_stays_atomic(self):
        backup = self.backup()
        del backup['alarm_types']
        before = self.engine.model.snapshot()
        with self.assertRaises(ValueError):
            entry.prepare_import(before, backup, {'user': 'User'}, {}, {'notify.mobile_app_phone'})
        self.assertEqual(self.engine.model.snapshot(), before)

    def test_custom_registry_is_filtered_for_normal_accounts(self):
        self.engine.model.upsert_alarm_type({'name': 'Amokalarm'})
        view = entry.user_view(self.engine.model.snapshot(), 'user')
        self.assertEqual(set(view['alarm_types']), {self.kind})

    def test_unassigned_or_disabled_accounts_get_no_custom_profile_names(self):
        self.engine.model.data['users']['user']['enabled'] = False
        self.assertEqual(entry.user_view(self.engine.model.snapshot(), 'user')['alarm_types'], {})
        self.assertEqual(entry.user_view(self.engine.model.snapshot(), 'unknown')['alarm_types'], {})

    def baseline_test(self, device_id='phone', key='baseline'):
        incident = self.engine.model.raise_alarm({'type': 'FIRE', 'alarm_key': key, 'source_id': 'test'})[0]
        incident['test_device'] = device_id
        return incident

    async def test_custom_only_user_can_respond_to_own_baseline_device_test(self):
        incident = self.baseline_test()
        self.hass.auth = types.SimpleNamespace(async_get_user=AsyncMock(return_value=types.SimpleNamespace(
            id='user', name='User', is_active=True, is_admin=False)))
        del self.engine.actor
        self.engine.finish_response = AsyncMock()
        await self.engine.respond(incident['id'], 'coming', 'user')
        self.assertEqual(incident['status'], 'claimed')

    async def test_custom_only_user_cannot_respond_to_regular_fire(self):
        incident = self.baseline_test()
        del incident['test_device']
        self.hass.auth = types.SimpleNamespace(async_get_user=AsyncMock(return_value=types.SimpleNamespace(
            id='user', is_active=True, is_admin=False)))
        del self.engine.actor
        with self.assertRaises(runtime.Unauthorized):
            await self.engine.respond(incident['id'], 'coming', 'user')
        self.assertEqual(incident['status'], 'open')

    def test_custom_only_view_includes_own_test_but_hides_other_tests(self):
        own = self.baseline_test()
        self.engine.model.data['devices']['other'] = {'id': 'other', 'user_id': 'other'}
        other = self.baseline_test('other', 'other-baseline')
        view = entry.user_view(self.engine.model.snapshot(), 'user')
        self.assertIn(own['id'], view['incidents'])
        self.assertNotIn(other['id'], view['incidents'])

    async def test_own_baseline_test_can_open_assigned_browser_popup(self):
        incident = self.baseline_test()
        self.device['browsers'] = [{'id': 'own-browser'}]
        self.hass.services = types.SimpleNamespace(async_call=AsyncMock())
        await self.engine.show_popup(self.device, incident, launch=False)
        self.hass.services.async_call.assert_awaited_once()

    async def test_disabled_user_cannot_use_own_test_exception(self):
        incident = self.baseline_test()
        self.engine.model.data['users']['user']['enabled'] = False
        self.hass.auth = types.SimpleNamespace(async_get_user=AsyncMock(return_value=types.SimpleNamespace(
            id='user', is_active=True, is_admin=False)))
        del self.engine.actor
        with self.assertRaises(runtime.Unauthorized):
            await self.engine.respond(incident['id'], 'coming', 'user')
        self.assertEqual(entry.user_view(self.engine.model.snapshot(), 'user')['incidents'], {})

    async def test_custom_sensor_signal_creates_incident_not_plain_message(self):
        self.engine.model.register_source({'id': 'door', 'name': 'Tür', 'entity_id': 'binary_sensor.door', 'type': self.kind}, 'off')
        self.engine.cycle = AsyncMock()
        self.engine.simple_message = AsyncMock()
        await self.engine.receive_signal('binary_sensor.door', 'on')
        await asyncio.sleep(0)
        self.assertEqual(self.engine.model.active()[0]['type'], self.kind)
        self.engine.cycle.assert_awaited_once()
        self.engine.simple_message.assert_not_awaited()

    def test_legacy_backup_keeps_registered_types_for_existing_history(self):
        incident = self.incident()
        self.engine.model.end_source(incident['id'], 'door', 'user')
        backup = {'format': 'alarm_system_configuration', 'schema_version': 1,
                  'site_id': 'TEST', 'users': {}, 'devices': {}, 'sources': {}}
        restored = entry.prepare_import(self.engine.model.snapshot(), backup, {}, {}, set())
        self.assertIn(self.kind, restored['alarm_types'])
        self.assertIn(incident['id'], restored['incidents'])

    def test_schema_two_preserves_profiles_referenced_by_retained_history(self):
        incident = self.incident()
        self.engine.model.end_source(incident['id'], 'door', 'user')
        backup = {'format': 'alarm_system_configuration', 'schema_version': 2,
                  'site_id': 'TEST', 'alarm_types': {}, 'users': {}, 'devices': {}, 'sources': {}}
        restored = entry.prepare_import(self.engine.model.snapshot(), backup, {}, {}, set())
        self.assertEqual(restored['alarm_types'][self.kind]['name'], 'Hausalarm')
        self.assertIn(incident['id'], restored['incidents'])

    def test_profile_referenced_only_by_journal_cannot_disappear(self):
        self.engine.model.data['users'] = {}
        self.engine.model.log('notification_requested', kind=self.kind)
        with self.assertRaises(ValueError):
            self.engine.model.remove_alarm_type(self.kind)

    async def test_tone_notification_gets_final_status_even_with_normal_push_off(self):
        self.engine.model.upsert_alarm_type({'id': self.kind, 'push': False, 'sound': True})
        incident = self.incident()
        self.engine.model.end_source(incident['id'], 'door', 'user')
        self.engine.send = AsyncMock(return_value=True)
        await self.engine.status(incident, 'Beendet', popup=False)
        self.engine.send.assert_awaited_once()
        self.assertEqual(self.engine.send.await_args.args[1]['data']['actions'], [])

    async def test_profile_popup_off_is_enforced_for_raw_browser_visibility_routes(self):
        self.engine.model.upsert_alarm_type({'id': self.kind, 'popup': False})
        incident = self.incident()
        self.device['browsers'] = [{'id': 'own-browser'}]
        self.hass.services = types.SimpleNamespace(async_call=AsyncMock())
        await self.engine.show_popup(self.device, incident, launch=False)
        self.hass.services.async_call.assert_not_awaited()


class MessageOutputIntegration(unittest.IsolatedAsyncioTestCase):
    """Exercise the real one-shot message transport, not the alarm cycle."""

    def setUp(self):
        CustomAlarmIntegration.setUp(self)
        self.engine.model.data['users']['user']['types'] = ['INFO', 'FIRE']
        self.engine.send = AsyncMock(return_value=True)
        self.engine.command = AsyncMock(return_value=True)
        self.engine.defer_transport_save = Mock()
        self.hass.services = types.SimpleNamespace(async_call=AsyncMock())

    async def asyncTearDown(self):
        await CustomAlarmIntegration.asyncTearDown(self)

    def configure(self, **flags):
        self.engine.model.upsert_alarm_type({'id': 'INFO', **flags})

    async def test_message_speech_works_without_push_and_without_incident_or_volume_commands(self):
        self.configure(push=False, speech=True)
        await self.engine.dispatch({'type': 'INFO', 'message': 'Garagentor offen'})
        payload = self.engine.send.await_args.args[1]
        self.assertEqual(payload, {'message': 'TTS', 'data': {'tts_text': 'Garagentor offen', 'media_stream': 'music_stream'}})
        self.assertEqual(self.engine.send.await_count, 1)
        self.engine.command.assert_not_awaited()
        self.assertFalse(self.engine.model.active())
        self.assertFalse(self.engine.model.data['leases'])

    async def test_message_custom_speech_template_is_expanded(self):
        self.configure(push=False, speech=True, speech_template='{name}: {areas} am Standort {site}')
        await self.engine.simple_message({'type': 'INFO', 'message': 'Text', 'area': 'Küche'})
        self.assertEqual(self.engine.send.await_args.args[1]['data']['tts_text'], 'Information: Küche am Standort TEST')

    async def test_device_speech_off_and_non_android_prevent_tts(self):
        self.configure(push=False, speech=True)
        for platform, speech in [('android', False), ('ios', True), ('browser', True)]:
            with self.subTest(platform=platform):
                self.device.update(platform=platform, speech=speech)
                await self.engine.simple_message({'type': 'INFO', 'message': 'Text'})
        self.engine.send.assert_not_awaited()

    async def test_normal_message_sound_respects_profile_device_and_silent(self):
        self.configure(sound=True)
        for device_sound, silent, audible in [(True, False, True), (False, False, False), (True, True, False)]:
            self.device['sound'] = device_sound
            await self.engine.simple_message({'type': 'INFO', 'message': 'Text', 'silent': silent})
            payload = self.engine.send.await_args.args[1]['data']
            self.assertEqual(payload['channel'], self.engine.model.profile('INFO')['channel'] if audible else 'Alarmstatus')
            self.assertEqual(payload.get('push', {}).get('sound') == 'none', not audible)
        self.engine.command.assert_not_awaited()

    async def test_message_popup_without_push_is_dismissable_and_escapes_content(self):
        self.configure(push=False, popup=True)
        self.device['browsers'] = [{'id': 'browser'}]
        await self.engine.simple_message({'type': 'INFO', 'message': '<script>alert(1)</script>'})
        call = self.hass.services.async_call.await_args
        self.assertEqual(call.args[:2], ('browser_mod', 'popup'))
        self.assertTrue(call.args[2]['dismissable'])
        self.assertIn('&lt;script&gt;', call.args[2]['content']['content'])
        self.engine.send.assert_not_awaited()

    async def test_alarm_has_priority_over_message_speech_sound_and_popup(self):
        self.configure(sound=True, speech=True, popup=True)
        self.device['browsers'] = [{'id': 'browser'}]
        self.engine.model.raise_alarm({'type': 'FIRE', 'alarm_key': 'fire', 'source_id': 'smoke'})
        await self.engine.simple_message({'type': 'INFO', 'message': 'Text'})
        self.assertEqual(self.engine.send.await_count, 1)
        self.assertEqual(self.engine.send.await_args.args[1]['data']['channel'], 'Alarmstatus')
        self.hass.services.async_call.assert_not_awaited()

    async def test_alarm_starting_during_push_prevents_following_message_audio(self):
        self.configure(speech=True, popup=True)
        async def push_then_alarm(*args, **kwargs):
            self.engine.model.raise_alarm({'type': 'FIRE', 'alarm_key': 'fire', 'source_id': 'smoke'})
            return True
        self.engine.send.side_effect = push_then_alarm
        await self.engine.simple_message({'type': 'INFO', 'message': 'Text'})
        self.assertEqual(self.engine.send.await_count, 1)
        self.hass.services.async_call.assert_not_awaited()

    async def test_disabled_user_receives_no_message_outputs(self):
        self.configure(sound=True, speech=True, popup=True)
        self.engine.model.data['users']['user']['enabled'] = False
        await self.engine.simple_message({'type': 'INFO', 'message': 'Text'})
        self.engine.send.assert_not_awaited()
        self.hass.services.async_call.assert_not_awaited()

    async def test_silent_message_does_not_speak(self):
        self.configure(speech=True)
        await self.engine.simple_message({'type': 'INFO', 'message': 'Text', 'silent': True})
        self.assertEqual(self.engine.send.await_count, 1)
        self.assertNotEqual(self.engine.send.await_args.args[1]['message'], 'TTS')

    async def test_later_recipient_revoked_during_first_transport_gets_no_message(self):
        self.engine.model.data['users']['later'] = {'id': 'later', 'enabled': True, 'types': ['INFO']}
        self.engine.model.data['devices']['later'] = {**self.device, 'id': 'later', 'user_id': 'later'}
        async def revoke_later(*args, **kwargs):
            self.engine.model.data['users']['later']['enabled'] = False
            return True
        self.engine.send.side_effect = revoke_later
        await self.engine.simple_message({'type': 'INFO', 'message': 'Text'})
        self.assertEqual(self.engine.send.await_count, 1)
        self.assertEqual(self.engine.send.await_args.args[0]['id'], 'phone')

    async def test_warning_can_speak_without_enabling_other_outputs(self):
        self.engine.model.data['users']['user']['types'] = ['WARNING']
        self.engine.model.upsert_alarm_type({'id': 'WARNING', 'push': False, 'speech': True})
        await self.engine.dispatch({'type': 'WARNING', 'message': 'Fenster noch offen'})
        self.assertEqual(self.engine.send.await_count, 1)
        self.assertEqual(self.engine.send.await_args.args[1]['data']['tts_text'], 'Fenster noch offen')


class AutomaticSourceGroupingIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        CustomAlarmIntegration.setUp(self)
        self.engine.cycle = AsyncMock()
        self.engine.status = AsyncMock()

    async def asyncTearDown(self):
        await CustomAlarmIntegration.asyncTearDown(self)

    def bind(self, sid, kind=None, **extra):
        return self.engine.model.register_source({'id': sid, 'name': sid,
            'entity_id': 'binary_sensor.' + sid, 'type': kind or self.kind, **extra}, 'off')

    async def test_two_custom_sources_share_event_without_user_group_key(self):
        self.bind('door', area='Eingang')
        self.bind('window', area='Büro')
        await self.engine.receive_signal('binary_sensor.door', 'on')
        await self.engine.receive_signal('binary_sensor.window', 'on')
        await asyncio.sleep(0)
        incidents = self.engine.model.active()
        self.assertEqual(len(incidents), 1)
        self.assertEqual(set(incidents[0]['sources']), {'door', 'window'})
        self.assertEqual(incidents[0]['title'], 'Hausalarm')
        self.engine.cycle.assert_awaited_once()
        self.engine.status.assert_awaited_once()

    async def test_different_source_types_remain_independent_events(self):
        self.bind('door')
        self.bind('smoke', 'FIRE')
        await self.engine.receive_signal('binary_sensor.door', 'on')
        await self.engine.receive_signal('binary_sensor.smoke', 'on')
        self.assertEqual(len(self.engine.model.active()), 2)
        self.assertEqual({i['type'] for i in self.engine.model.active()}, {self.kind, 'FIRE'})

    def test_import_old_manual_groups_normalizes_same_type_without_mutating_input(self):
        self.bind('door')
        self.bind('window')
        document = CustomAlarmIntegration.backup(self)
        document['sources'] = deepcopy(self.engine.model.data['sources'])
        document['sources']['door']['alarm_key'] = 'Old first'
        document['sources']['window']['alarm_key'] = 'Old second'
        original = deepcopy(document)
        states = {s['entity_id']: 'off' for s in document['sources'].values()}
        data = entry.prepare_import(self.engine.model.snapshot(), document, {'user': 'User'}, states, {'notify.mobile_app_phone'})
        self.assertEqual(data['sources']['door']['alarm_key'], data['sources']['window']['alarm_key'])
        self.assertEqual(document, original)
        self.assertFalse(data['devices']['phone']['tested'])

    async def test_info_sources_stay_one_shot_messages(self):
        self.bind('info1', 'INFO')
        self.bind('info2', 'INFO')
        self.engine.simple_message = AsyncMock()
        await self.engine.receive_signal('binary_sensor.info1', 'on')
        await self.engine.receive_signal('binary_sensor.info2', 'on')
        self.assertEqual(self.engine.simple_message.await_count, 2)
        self.assertFalse(self.engine.model.active())
