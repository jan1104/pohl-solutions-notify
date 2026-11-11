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

    def restart_from_snapshot(self):
        snapshot = self.engine.model.snapshot()
        self.engine = runtime.AlarmEngine(
            self.hass, types.SimpleNamespace(data={"site_id": "TEST"}))
        self.engine.model = runtime.AlarmModel(snapshot)
        self.engine.save = AsyncMock()
        self.engine.cycle = AsyncMock()
        return snapshot

    async def asyncTearDown(self):
        tasks = list(self.engine.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def test_snapshot_recovery_keeps_real_alarm_and_aborts_only_device_test(self):
        self.engine.model.register_source({"id": "smoke", "name": "Rauchmelder",
            "entity_id": "binary_sensor.smoke", "type": "FIRE"}, "off")
        payload = self.engine.model.signal_update("binary_sensor.smoke", "on")
        regular, _ = self.engine.model.raise_alarm(payload)
        regular["next_due"] = 9999999999
        test = self.alarm("Test", "test-source")
        test["test_device"] = "phone"
        self.states["binary_sensor.smoke"] = types.SimpleNamespace(state="off")
        before = self.restart_from_snapshot()

        await self.engine.recover()

        recovered = self.engine.model.data["incidents"][regular["id"]]
        self.assertEqual(recovered["status"], "open")
        self.assertEqual(recovered["started_at"], before["incidents"][regular["id"]]["started_at"])
        self.assertEqual(recovered["next_due"], 0)
        self.assertTrue(recovered["sources"]["smoke"]["active"])
        self.assertFalse(recovered["sources"]["smoke"]["signal_active"])
        self.assertEqual(self.engine.model.data["incidents"][test["id"]]["status"], "ended")
        self.assertEqual(len(self.engine.model.data["incidents"]), 2)
        self.engine.cycle.assert_not_called()

    async def test_speech_only_snapshot_keeps_failed_stop_and_retries_without_volume_commands(self):
        self.engine.model.data["devices"]["phone"] = {"id": "phone", "platform": "android"}
        self.engine.model.data["leases"]["phone"] = {
            "incident_id": "interrupted", "speech_only": True, "playback_id": "old-playback"}
        self.restart_from_snapshot()
        self.engine.command = AsyncMock(return_value=False)

        await self.engine.recover()

        lease = self.engine.model.data["leases"]["phone"]
        self.assertTrue(lease["restore_pending"])
        self.assertTrue(lease["speech_only"])
        self.assertGreater(lease["retry_at"], runtime.time())
        self.assertEqual([call.args[1] for call in self.engine.command.await_args_list], ["command_stop_tts"])
        self.restart_from_snapshot()
        self.engine.command = AsyncMock(return_value=True)

        await self.engine.recover()

        self.assertNotIn("phone", self.engine.model.data["leases"])
        self.assertEqual([call.args[1] for call in self.engine.command.await_args_list], ["command_stop_tts"])

    async def test_snapshot_suppression_survives_restart_until_real_off_then_new_on(self):
        self.engine.model.register_source({"id": "smoke", "name": "Rauchmelder",
            "entity_id": "binary_sensor.smoke", "type": "FIRE"}, "off")
        payload = self.engine.model.signal_update("binary_sensor.smoke", "on")
        ended, _ = self.engine.model.raise_alarm(payload)
        self.engine.model.end_source(ended["id"], "smoke", "user")
        self.states["binary_sensor.smoke"] = types.SimpleNamespace(state="on")
        before = self.restart_from_snapshot()

        await self.engine.recover()
        await self.engine.receive_signal("binary_sensor.smoke", "unavailable")
        await self.engine.receive_signal("binary_sensor.smoke", "on")

        self.assertEqual(self.engine.model.data["suppressed"], before["suppressed"])
        self.assertFalse(self.engine.model.active())
        self.assertEqual(len(self.engine.model.data["incidents"]), 1)
        await self.engine.receive_signal("binary_sensor.smoke", "off")
        self.assertFalse(self.engine.model.data["suppressed"])
        await self.engine.receive_signal("binary_sensor.smoke", "on")
        await asyncio.sleep(0)

        self.assertEqual(len(self.engine.model.active()), 1)
        self.assertNotEqual(self.engine.model.active()[0]["id"], ended["id"])
        self.engine.cycle.assert_awaited_once()

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
