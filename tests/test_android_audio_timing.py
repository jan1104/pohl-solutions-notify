"""Receipt diagnostics must not insert an extra pause before Android speech."""
import asyncio
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch
from ha_test_support import load_runtime_modules

runtime, _ = load_runtime_modules()


class AndroidAudioTiming(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        hass = types.SimpleNamespace(async_create_background_task=lambda coro, _: asyncio.create_task(coro))
        self.engine = runtime.AlarmEngine(hass, types.SimpleNamespace(data={'site_id': 'TEST'}))
        self.engine.save = AsyncMock()
        self.engine.defer_transport_save = Mock()
        self.engine.command = AsyncMock(return_value=True)
        self.engine.restore_device = AsyncMock()
        self.engine.tone_seconds = Mock(return_value=.02)
        self.engine.speech_seconds = Mock(return_value=.01)
        self.device = {'id': 'phone', 'user_id': 'owner', 'platform': 'android',
                       'enabled': True, 'tested': True, 'sound': True, 'speech': True, 'push': True}
        self.engine.model.data['users']['owner'] = {'id': 'owner', 'enabled': True, 'types': ['FIRE']}
        self.engine.model.data['devices']['phone'] = self.device
        self.incident, _ = self.engine.model.raise_alarm({'type': 'FIRE', 'alarm_key': 'house', 'source_id': 'smoke'})
        self.engine.model.data['leases']['phone'] = {'incident_id': self.incident['id'], 'playback_id': 'old'}
        self.receipt = asyncio.get_running_loop().create_future()
        self.tag = self.engine.notification_tag(self.device, self.incident)
        self.engine.playback_receipts[self.tag] = ('old', self.receipt)

    async def asyncTearDown(self):
        for task in list(self.engine.tasks):
            task.cancel()
        await asyncio.gather(*list(self.engine.tasks), return_exceptions=True)

    async def run_cycle(self):
        await self.engine.finish_android_cycle(self.device, self.incident, 'old', self.receipt)

    async def test_missing_receipt_does_not_delay_speech_by_the_confirmation_timeout(self):
        spoken = asyncio.Event()
        async def command(*args, **kwargs):
            self.assertFalse(self.receipt.done())
            spoken.set()
            return True
        self.engine.command.side_effect = command
        worker = asyncio.create_task(self.run_cycle())
        try:
            await asyncio.wait_for(spoken.wait(), timeout=1)
            await asyncio.wait_for(worker, timeout=1)
        finally:
            if not worker.done():
                worker.cancel()
                await asyncio.gather(worker, return_exceptions=True)
        self.engine.command.assert_awaited_once()
        self.assertTrue(self.receipt.cancelled())
        self.assertNotIn(self.tag, self.engine.playback_receipts)

    async def test_received_callback_is_still_recorded_without_claiming_playback(self):
        self.receipt.set_result(True)
        await self.run_cycle()
        rows = [row for row in self.incident['delivery'] if row['state'] == 'notification_received']
        self.assertEqual(len(rows), 1)
        self.assertIn('kein Wiedergabenachweis', rows[0]['detail'])
        self.engine.command.assert_awaited_once()

    async def test_receipt_timeout_is_diagnostic_and_does_not_restart_tone_phase(self):
        with patch.object(runtime, '_PLAYBACK_RECEIPT_TIMEOUT', .001):
            await self.run_cycle()
        rows = [row for row in self.incident['delivery'] if row['state'] == 'receipt_timeout']
        self.assertEqual(len(rows), 1)
        self.assertNotIn('Tonfrist beginnt jetzt', rows[0]['detail'])
        self.engine.tone_seconds.assert_called_once()
        self.engine.command.assert_awaited_once()

    async def test_coming_during_tone_prevents_speech_and_cleans_observer(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def pause(_):
            entered.set()
            await release.wait()
        with patch.object(runtime.asyncio, 'sleep', side_effect=pause):
            worker = asyncio.create_task(self.run_cycle())
            await entered.wait()
            self.incident['status'] = 'claimed'
            release.set()
            await worker
        self.engine.command.assert_not_awaited()
        self.engine.restore_device.assert_awaited_once()
        self.assertTrue(self.receipt.cancelled())

    async def test_old_worker_does_not_cancel_new_generation_receipt(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def pause(_):
            entered.set()
            await release.wait()
        newer = asyncio.get_running_loop().create_future()
        with patch.object(runtime.asyncio, 'sleep', side_effect=pause):
            worker = asyncio.create_task(self.run_cycle())
            await entered.wait()
            self.engine.model.data['leases']['phone']['playback_id'] = 'new'
            self.engine.playback_receipts[self.tag] = ('new', newer)
            release.set()
            await worker
        self.assertIs(self.engine.playback_receipts[self.tag][1], newer)
        self.assertFalse(newer.done())
        self.assertTrue(self.receipt.cancelled())
        self.engine.command.assert_not_awaited()
        newer.cancel()

    async def test_cancelled_audio_worker_leaves_no_receipt_observer(self):
        entered = asyncio.Event()
        async def pause(_):
            entered.set()
            await asyncio.Event().wait()
        with patch.object(runtime.asyncio, 'sleep', side_effect=pause):
            worker = asyncio.create_task(self.run_cycle())
            await entered.wait()
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)
        self.assertTrue(self.receipt.cancelled())
        self.assertNotIn(self.tag, self.engine.playback_receipts)
        self.assertTrue(all(task.done() for task in self.engine.tasks))
