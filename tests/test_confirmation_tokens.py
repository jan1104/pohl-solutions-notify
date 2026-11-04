"""Confirmation ownership and lifetime through the real response handler."""
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

from ha_test_support import load_runtime_modules

runtime, _ = load_runtime_modules()


class ConfirmationTokens(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.hass = types.SimpleNamespace(data={})
        self.engine = runtime.AlarmEngine(self.hass, types.SimpleNamespace(data={'site_id': 'TEST'}))
        self.engine.save = AsyncMock()
        self.engine.defer_transport_save = Mock()
        self.engine.finish_response = AsyncMock()
        self.engine.schedule_category_setup = Mock()
        self.engine.actor = AsyncMock(side_effect=lambda uid, incident: types.SimpleNamespace(id=uid, name=uid))
        self.engine.model.data['users'] = {
            uid: {'id': uid, 'name': uid, 'enabled': True, 'types': ['FIRE']}
            for uid in ('owner', 'other')}
        self.first = self.incident('first')
        self.second = self.incident('second')

    def incident(self, key):
        incident = self.engine.model.raise_alarm({'type': 'FIRE', 'alarm_key': key, 'source_id': key})[0]
        incident['next_due'] = 100000
        return incident

    async def request(self, incident=None):
        return await self.engine.respond((incident or self.first)['id'], 'request_false', 'owner')

    async def test_other_recipient_cannot_cancel_owners_confirmation(self):
        token = await self.request()
        with self.assertRaises(runtime.HomeAssistantError):
            await self.engine.respond(self.first['id'], 'cancel_false', 'other', token=token)
        self.assertIn(token, self.engine.confirmations)
        await self.engine.respond(self.first['id'], 'cancel_false', 'owner', token=token)
        self.assertNotIn(token, self.engine.confirmations)
        self.assertEqual(self.first['status'], 'open')

    async def test_other_recipient_cannot_consume_token_by_confirming(self):
        token = await self.request()
        with self.assertRaises(runtime.HomeAssistantError):
            await self.engine.respond(self.first['id'], 'false_alarm', 'other', token=token)
        self.assertIn(token, self.engine.confirmations)
        await self.engine.respond(self.first['id'], 'false_alarm', 'owner', token=token)
        self.assertEqual(self.first['status'], 'false_alarm')
        self.assertEqual(self.second['status'], 'open')

    async def test_token_for_another_event_cannot_be_consumed(self):
        for action in ('cancel_false', 'false_alarm'):
            with self.subTest(action=action):
                token = await self.request()
                with self.assertRaises(runtime.HomeAssistantError):
                    await self.engine.respond(self.second['id'], action, 'owner', token=token)
                self.assertIn(token, self.engine.confirmations)
                await self.engine.respond(self.first['id'], 'cancel_false', 'owner', token=token)

    async def test_repeated_current_request_reuses_confirmation(self):
        first = await self.request()
        self.assertEqual(await self.request(), first)
        self.assertEqual(len(self.engine.confirmations), 1)

    async def test_request_prunes_expired_confirmations_without_removing_valid_ones(self):
        with patch.object(runtime, 'time', return_value=1000):
            self.engine.confirmations = {'expired': ('owner', self.first['id'], 999),
                                         'valid': ('owner', self.second['id'], 1100)}
            self.engine.completed_confirmations = {'old_done': ('owner', self.first['id'], 999),
                                                   'valid_done': ('owner', self.second['id'], 1100)}
            token = await self.request()
        self.assertEqual(set(self.engine.confirmations), {'valid', token})
        self.assertEqual(set(self.engine.completed_confirmations), {'valid_done'})

    async def test_tick_expires_tokens_at_deadline_without_new_requests(self):
        with patch.object(runtime, 'time', return_value=1000):
            self.engine._last_purge = 1000
            self.engine.confirmations = {'expired': ('owner', self.first['id'], 1000),
                                         'valid': ('owner', self.second['id'], 1001)}
            self.engine.completed_confirmations = {'old_done': ('owner', self.first['id'], 1000)}
            await self.engine.tick(None)
        self.assertEqual(set(self.engine.confirmations), {'valid'})
        self.assertEqual(self.engine.completed_confirmations, {})

    async def test_expired_confirmation_cannot_cancel_or_confirm_at_deadline(self):
        for action in ('cancel_false', 'false_alarm'):
            with self.subTest(action=action), patch.object(runtime, 'time', return_value=1000):
                self.engine.confirmations['expired'] = ('owner', self.first['id'], 1000)
                with self.assertRaises(runtime.HomeAssistantError):
                    await self.engine.respond(self.first['id'], action, 'owner', token='expired')
                self.assertEqual(self.first['status'], 'open')

    async def test_completed_confirmation_remains_idempotent_until_expiry(self):
        with patch.object(runtime, 'time', return_value=1000):
            token = await self.request()
            await self.engine.respond(self.first['id'], 'false_alarm', 'owner', token=token)
            calls = self.engine.finish_response.await_count
            await self.engine.respond(self.first['id'], 'false_alarm', 'owner', token=token)
            self.assertEqual(self.engine.finish_response.await_count, calls)
            self.assertEqual(self.first['status'], 'false_alarm')
        with patch.object(runtime, 'time', return_value=1300):
            with self.assertRaises(runtime.HomeAssistantError):
                await self.engine.respond(self.first['id'], 'false_alarm', 'owner', token=token)
            self.assertNotIn(token, self.engine.completed_confirmations)
            self.assertEqual(self.first['status'], 'false_alarm')
