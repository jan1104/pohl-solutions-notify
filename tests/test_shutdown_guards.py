"""Shutdown regressions using the real engine and explicit HA boundaries."""
import asyncio
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

from ha_test_support import load_runtime_modules

runtime, _ = load_runtime_modules()


class ShutdownGuards(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        hass = types.SimpleNamespace(async_create_background_task=lambda coro, name: asyncio.create_task(coro))
        self.engine = runtime.AlarmEngine(hass, types.SimpleNamespace(data={"site_id": "TEST"}))
        self.engine.save = AsyncMock()

    async def asyncTearDown(self):
        tasks = list(self.engine.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def test_bad_unsubscribe_does_not_skip_other_listeners_and_workers(self):
        good = Mock()
        bad = Mock(side_effect=RuntimeError("unsubscribe failed"))
        self.engine.unsub = [good, bad]
        started = asyncio.Event()
        async def worker():
            started.set()
            await asyncio.Event().wait()
        task = self.engine.spawn(worker())
        await started.wait()
        with self.assertLogs(runtime._LOGGER.name, level="ERROR"):
            await self.engine.cancel_workers()
        good.assert_called_once()
        bad.assert_called_once()
        self.assertEqual(self.engine.unsub, [])
        self.assertTrue(task.cancelled())
        self.engine.save.assert_not_awaited()

    async def test_bad_unsubscribe_does_not_skip_device_restoration_on_stop(self):
        self.engine.unsub = [Mock(side_effect=RuntimeError("unsubscribe failed"))]
        self.engine.stop_devices = AsyncMock()
        with self.assertLogs(runtime._LOGGER.name, level="ERROR"):
            await self.engine.stop()
        self.engine.stop_devices.assert_awaited_once()
        self.engine.save.assert_awaited_once()

    async def test_late_sensor_event_does_not_restart_alarm_processing(self):
        self.engine.stopping = True
        self.engine.receive_signal = AsyncMock()
        event = types.SimpleNamespace(data={"new_state": types.SimpleNamespace(
            state="on", entity_id="binary_sensor.smoke")})
        await self.engine.state_changed(event)
        self.engine.receive_signal.assert_not_awaited()
        self.engine.save.assert_not_awaited()

    def smoke_alarm_event(self):
        entity_id = "binary_sensor.smoke"
        self.engine.model.register_source({
            "id": "smoke", "entity_id": entity_id, "name": "Rauchmelder", "type": "FIRE",
        }, "off")
        return types.SimpleNamespace(data={
            "old_state": types.SimpleNamespace(state="off", entity_id=entity_id),
            "new_state": types.SimpleNamespace(state="on", entity_id=entity_id),
        })

    async def test_sensor_event_waiting_for_model_lock_does_not_raise_alarm_during_stop(self):
        event = self.smoke_alarm_event()
        before = self.engine.model.snapshot()
        self.engine.cycle = AsyncMock()
        started = asyncio.Event()

        async def process_event():
            started.set()
            await self.engine.state_changed(event)

        async with self.engine.lock:
            listener = asyncio.create_task(process_event())
            await asyncio.wait_for(started.wait(), timeout=1)
            self.assertFalse(listener.done())
            await self.engine.cancel_workers()
        await listener

        self.assertEqual(self.engine.model.snapshot(), before)
        self.engine.save.assert_not_awaited()
        self.engine.cycle.assert_not_called()

    async def test_sensor_event_finishing_save_does_not_start_dispatch_during_stop(self):
        event = self.smoke_alarm_event()
        self.engine.cycle = AsyncMock()
        save_started = asyncio.Event()
        release_save = asyncio.Event()
        saved = []

        async def save():
            snapshot = self.engine.model.snapshot()
            save_started.set()
            await release_save.wait()
            saved.append(snapshot)

        self.engine.save.side_effect = save
        listener = asyncio.create_task(self.engine.state_changed(event))
        try:
            await asyncio.wait_for(save_started.wait(), timeout=1)
            await self.engine.cancel_workers()
        finally:
            release_save.set()
            await listener

        self.engine.save.assert_awaited_once()
        self.assertEqual(self.engine.model.snapshot(), saved[0])
        self.assertEqual(saved[0]["signal_values"]["smoke"], "on")
        self.assertEqual(len(saved[0]["incidents"]), 1)
        self.engine.cycle.assert_not_called()

    async def test_tick_resuming_after_cleanup_does_not_start_workers_during_stop(self):
        incident, _ = self.engine.model.raise_alarm({
            "type": "FIRE", "alarm_key": "fire", "source_id": "smoke",
        })
        incident["next_due"] = 0
        self.engine.model.data["leases"]["phone"] = {"incident_id": incident["id"]}
        self.engine.cycle = AsyncMock()
        self.engine.retry_restorations = AsyncMock()
        cleanup_started = asyncio.Event()
        release_cleanup = asyncio.Event()

        async def cleanup(_hass):
            cleanup_started.set()
            await release_cleanup.wait()

        with patch.object(runtime, "cleanup_history_images", new=cleanup):
            # The timer callback belongs to HA rather than the engine's worker set.
            tick = asyncio.create_task(self.engine.tick(None))
            try:
                await asyncio.wait_for(cleanup_started.wait(), timeout=1)
                await self.engine.cancel_workers()
            finally:
                release_cleanup.set()
                await tick

        self.engine.cycle.assert_not_called()
        self.engine.retry_restorations.assert_not_called()
        self.assertEqual(incident["next_due"], 0)

    async def test_tick_waiting_for_model_lock_does_not_purge_during_stop(self):
        self.engine.model.purge = Mock(wraps=self.engine.model.purge)
        started = asyncio.Event()

        async def run_tick():
            started.set()
            await self.engine.tick(None)

        with patch.object(runtime, "cleanup_history_images", new_callable=AsyncMock) as cleanup:
            async with self.engine.lock:
                tick = asyncio.create_task(run_tick())
                await asyncio.wait_for(started.wait(), timeout=1)
                await self.engine.cancel_workers()
            await tick

        self.engine.model.purge.assert_not_called()
        self.engine.save.assert_not_awaited()
        cleanup.assert_not_awaited()

    async def test_late_notification_receipt_does_not_complete_pending_future(self):
        self.engine.stopping = True
        future = asyncio.get_running_loop().create_future()
        self.engine.setup_receipts["tag"] = future
        await self.engine.setup_received(types.SimpleNamespace(data={"tag": "tag"}))
        self.assertFalse(future.done())
        future.cancel()

    async def test_late_mobile_reply_does_not_change_incident(self):
        self.engine.stopping = True
        self.engine.respond = AsyncMock()
        event = types.SimpleNamespace(data={"action": "AS_COMING:incident"},
                                      context=types.SimpleNamespace(user_id="user"))
        await self.engine.mobile_response(event)
        self.engine.respond.assert_not_awaited()

    async def test_reply_waiting_for_account_does_not_change_alarm_during_stop(self):
        incident, _ = self.engine.model.raise_alarm({
            "type": "FIRE", "alarm_key": "fire", "source_id": "smoke",
        })
        before = self.engine.model.snapshot()
        checking_account = asyncio.Event()
        release_account = asyncio.Event()

        async def actor(*_args):
            checking_account.set()
            await release_account.wait()
            return types.SimpleNamespace(id="user", name="User")

        self.engine.actor = actor
        self.engine.finish_response = AsyncMock()
        reply = asyncio.create_task(self.engine.respond(incident["id"], "coming", "user"))
        try:
            await asyncio.wait_for(checking_account.wait(), timeout=1)
            await self.engine.cancel_workers()
        finally:
            release_account.set()
        with self.assertRaisesRegex(runtime.HomeAssistantError, "entladen"):
            await reply
        self.assertEqual(self.engine.model.snapshot(), before)
        self.engine.save.assert_not_awaited()
        self.engine.finish_response.assert_not_called()

    async def test_saved_reply_does_not_start_transport_during_stop(self):
        incident, _ = self.engine.model.raise_alarm({
            "type": "FIRE", "alarm_key": "fire", "source_id": "smoke",
        })
        self.engine.actor = AsyncMock(return_value=types.SimpleNamespace(id="user", name="User"))
        self.engine.finish_response = AsyncMock()
        saving_reply = asyncio.Event()
        release_save = asyncio.Event()
        saved = []

        async def save():
            saving_reply.set()
            await release_save.wait()
            saved.append(self.engine.model.snapshot())

        self.engine.save.side_effect = save
        reply = asyncio.create_task(self.engine.respond(incident["id"], "coming", "user", background=True))
        try:
            await asyncio.wait_for(saving_reply.wait(), timeout=1)
            await self.engine.cancel_workers()
        finally:
            release_save.set()
            await reply

        self.assertEqual(saved[0]["incidents"][incident["id"]]["responses"]["user"]["answer"], "coming")
        self.assertEqual(incident["status"], "claimed")
        self.engine.finish_response.assert_not_called()
