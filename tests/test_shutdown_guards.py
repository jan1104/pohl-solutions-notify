"""Shutdown regressions using the real engine and explicit HA boundaries."""
import asyncio
import types
import unittest
from unittest.mock import AsyncMock, Mock

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
