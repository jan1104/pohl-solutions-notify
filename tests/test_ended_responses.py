"""Reject stale actions without changing completed incident history or tokens."""
from copy import deepcopy
import types
import unittest
from unittest.mock import AsyncMock, Mock

from ha_test_support import load_runtime_modules

runtime, _ = load_runtime_modules()


class EndedResponses(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = runtime.AlarmEngine(types.SimpleNamespace(data={}),
            types.SimpleNamespace(data={'site_id': 'TEST'}))
        self.engine.save = AsyncMock()
        self.engine.defer_transport_save = Mock()
        self.engine.finish_response = AsyncMock()
        self.engine.actor = AsyncMock(return_value=types.SimpleNamespace(id='owner', name='Owner'))
        self.engine.model.data['users']['owner'] = {'id': 'owner', 'enabled': True, 'types': ['FIRE']}
        self.incident, _ = self.engine.model.raise_alarm({'type': 'FIRE', 'alarm_key': 'house', 'source_id': 'smoke'})

    def close(self, status):
        if status == 'false_alarm':
            self.engine.model.false_alarm(self.incident['id'], 'owner')
        else:
            self.engine.model.end_source(self.incident['id'], 'smoke', 'owner')

    async def respond(self, action, **extra):
        return await self.engine.respond(self.incident['id'], action, 'owner', **extra)

    async def test_completed_incident_rejects_new_actions_without_side_effects(self):
        for status in ('ended', 'false_alarm'):
            self.setUp()
            self.close(status)
            for action, extra in (('request_false', {}), ('coming', {}),
                                  ('cancel_false', {'token': 'unknown'}),
                                  ('end_source', {'source_id': 'missing'})):
                with self.subTest(status=status, action=action):
                    before = self.engine.model.snapshot()
                    tokens = deepcopy(self.engine.confirmations)
                    completed = deepcopy(self.engine.completed_confirmations)
                    with self.assertRaisesRegex(runtime.HomeAssistantError, 'bereits beendet'):
                        await self.respond(action, **extra)
                    self.assertEqual(self.engine.model.snapshot(), before)
                    self.assertEqual(self.engine.confirmations, tokens)
                    self.assertEqual(self.engine.completed_confirmations, completed)
                    self.engine.save.assert_not_awaited()
                    self.engine.defer_transport_save.assert_not_called()
                    self.engine.finish_response.assert_not_awaited()

    async def test_pending_confirmation_is_not_consumed_or_marked_complete_after_event_ends(self):
        for status in ('ended', 'false_alarm'):
            self.setUp()
            token = await self.respond('request_false')
            self.close(status)
            before = self.engine.model.snapshot()
            self.engine.save.reset_mock()
            self.engine.defer_transport_save.reset_mock()
            for action in ('false_alarm', 'cancel_false', 'request_false'):
                with self.subTest(status=status, action=action):
                    with self.assertRaisesRegex(runtime.HomeAssistantError, 'bereits beendet'):
                        await self.respond(action, token=token)
                    self.assertIn(token, self.engine.confirmations)
                    self.assertNotIn(token, self.engine.completed_confirmations)
                    self.assertEqual(self.engine.model.snapshot(), before)
            self.engine.save.assert_not_awaited()
            self.engine.defer_transport_save.assert_not_called()
            self.engine.finish_response.assert_not_awaited()

    async def test_viewing_completed_incident_remains_a_noop(self):
        self.close('ended')
        before = self.engine.model.snapshot()
        self.assertIsNone(await self.respond('seen'))
        self.assertEqual(self.engine.model.snapshot(), before)
        self.engine.save.assert_not_awaited()
        self.engine.finish_response.assert_not_awaited()

    async def test_repeated_coming_remains_a_noop_after_completion(self):
        self.engine.model.come(self.incident['id'], 'owner', 'Owner')
        self.close('ended')
        before = self.engine.model.snapshot()
        self.assertIsNone(await self.respond('coming'))
        self.assertEqual(self.engine.model.snapshot(), before)
        self.engine.save.assert_not_awaited()
        self.engine.finish_response.assert_not_awaited()

    async def test_repeated_closed_source_action_remains_a_noop(self):
        self.close('ended')
        before = self.engine.model.snapshot()
        self.assertIsNone(await self.respond('end_source', source_id='smoke'))
        self.assertEqual(self.engine.model.snapshot(), before)
        self.engine.save.assert_not_awaited()
        self.engine.finish_response.assert_not_awaited()

    async def test_successful_false_alarm_retry_remains_idempotent(self):
        token = await self.respond('request_false')
        await self.respond('false_alarm', token=token)
        before = self.engine.model.snapshot()
        self.engine.save.reset_mock()
        self.engine.finish_response.reset_mock()
        self.assertIsNone(await self.respond('false_alarm', token=token))
        self.assertEqual(self.engine.model.snapshot(), before)
        self.engine.save.assert_not_awaited()
        self.engine.finish_response.assert_not_awaited()
