"""Recovery regressions through the real engine with narrow HA boundaries."""
import asyncio
import types
import unittest
from unittest.mock import AsyncMock, Mock

from ha_test_support import load_runtime_modules

runtime, _ = load_runtime_modules()


class RecoveryLifecycle(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.states = {}
        self.hass = types.SimpleNamespace(
            states=types.SimpleNamespace(get=self.states.get),
            bus=types.SimpleNamespace(async_fire=Mock()),
            async_create_background_task=lambda coroutine, name: asyncio.create_task(coroutine))
        self.engine = runtime.AlarmEngine(
            self.hass, types.SimpleNamespace(data={"site_id": "TEST"}))
        self.engine.save = AsyncMock()

    def alarm(self, key, source_id):
        return self.engine.model.raise_alarm({
            "type": "FIRE", "alarm_key": key, "source_id": source_id})[0]

    async def test_recovery_restarts_regular_alarm_and_aborts_device_test(self):
        regular = self.alarm("Fire", "detector")
        regular["next_due"] = 9999999999
        test = self.alarm("Test", "test-source")
        test["test_device"] = "phone"
        self.engine.stop_devices = AsyncMock()
        self.engine.receive_signal = AsyncMock()

        await self.engine.recover()

        self.assertEqual(regular["status"], "open")
        self.assertEqual(regular["next_due"], 0)
        self.assertEqual(test["status"], "ended")
        self.assertTrue(any(row["action"] == "test_aborted" and
                            row["incident_id"] == test["id"]
                            for row in self.engine.model.data["journal"]))
        self.engine.save.assert_awaited_once()
        self.assertFalse(self.engine.recovering)

    async def test_recovery_keeps_original_lease_when_device_restore_fails(self):
        incident = self.alarm("Fire", "detector")
        phone = {"id": "phone", "platform": "android"}
        self.engine.model.data["devices"][phone["id"]] = phone
        lease = {"ringer": "normal", "volume": 3, "incident_id": incident["id"]}
        self.engine.model.data["leases"][phone["id"]] = lease
        self.engine.command = AsyncMock(return_value=False)
        self.engine.receive_signal = AsyncMock()

        await self.engine.recover()

        self.assertIs(self.engine.model.data["leases"]["phone"], lease)
        self.assertTrue(lease["restore_pending"])
        self.assertGreater(lease["retry_at"], runtime.time())
        self.assertEqual((lease["ringer"], lease["volume"]), ("normal", 3))
        self.engine.command.assert_awaited()

    async def test_recovery_flag_resets_when_transport_or_storage_raises(self):
        self.engine.stop_devices = AsyncMock(side_effect=OSError("transport"))
        with self.assertRaises(OSError):
            await self.engine.recover()
        self.assertFalse(self.engine.recovering)

        self.engine.stop_devices = AsyncMock()
        self.engine.save = AsyncMock(side_effect=OSError("storage"))
        with self.assertRaises(OSError):
            await self.engine.recover()
        self.assertFalse(self.engine.recovering)
