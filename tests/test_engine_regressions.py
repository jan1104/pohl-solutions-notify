"""Regression tests of the complete engine module with explicit HA boundaries."""
import asyncio
from datetime import datetime, timezone
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

from ha_test_support import load_runtime_modules

runtime, _ = load_runtime_modules()


class EngineRegressions(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.states = {}
        self.hass = types.SimpleNamespace(
            states=types.SimpleNamespace(get=self.states.get, async_set=Mock()),
            bus=types.SimpleNamespace(async_fire=Mock()),
            async_create_background_task=lambda coroutine, name: asyncio.create_task(coroutine))
        self.engine = runtime.AlarmEngine(self.hass, types.SimpleNamespace(data={"site_id": "TEST"}))
        self.engine.save = AsyncMock()
        self.engine.notify = AsyncMock()
        self.engine.show_popup = AsyncMock()
        self.engine.model.data["users"] = {
            "fire": {"id": "fire", "enabled": True, "types": ["FIRE"]},
            "intrusion": {"id": "intrusion", "enabled": True, "types": ["INTRUSION"]}}
        self.fire_phone = self.phone("fire-phone", "fire")
        self.intrusion_phone = self.phone("intrusion-phone", "intrusion")
        self.engine.model.data["devices"] = {
            self.fire_phone["id"]: self.fire_phone, self.intrusion_phone["id"]: self.intrusion_phone}
        self.fire = self.alarm("FIRE", "fire", "smoke")
        self.intrusion = self.alarm("INTRUSION", "intrusion", "door")

    async def asyncTearDown(self):
        pending = list(self.engine.tasks)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    def phone(self, device_id, user_id):
        return {"id": device_id, "user_id": user_id, "platform": "android", "enabled": True,
                "tested": True, "push": True, "popup": False, "sound": False,
                "ringer_sensor": "sensor.ringer", "volume_sensor": "sensor.volume"}

    def alarm(self, kind, key, source):
        return self.engine.model.raise_alarm({"type": kind, "alarm_key": key, "source_id": source})[0]

    async def test_disjoint_fire_recipient_gets_regular_cycle_despite_intrusion(self):
        self.engine.play_device = AsyncMock(return_value=None)
        await self.engine.cycle(self.fire["id"])
        self.engine.play_device.assert_awaited_once()
        self.assertEqual(self.engine.play_device.await_args.args[0]["id"], "fire-phone")
        self.assertIs(self.engine.play_device.await_args.args[1], self.fire)

    async def test_shared_device_gets_quiet_secondary_alarm(self):
        self.engine.model.data["users"]["fire"]["types"].append("INTRUSION")
        self.engine.play_device = AsyncMock(return_value=None)
        await self.engine.cycle(self.fire["id"])
        self.engine.play_device.assert_not_awaited()
        self.engine.notify.assert_awaited_once_with(self.fire_phone, self.fire, loud=False)

    async def test_recipientless_alarm_does_not_block_other_device(self):
        self.engine.model.data["users"]["intrusion"]["enabled"] = False
        self.engine.play_device = AsyncMock(return_value=None)
        await self.engine.cycle(self.fire["id"])
        self.engine.play_device.assert_awaited_once()

    async def test_failed_restore_still_delivers_push(self):
        self.fire_phone["sound"] = True
        self.engine.model.data["leases"]["fire-phone"] = {
            "ringer": "silent", "volume": 2, "incident_id": "ended", "playback_id": "old"}
        self.engine.restore_device = AsyncMock()
        await self.engine.play_device(self.fire_phone, self.fire)
        self.engine.notify.assert_awaited_once_with(self.fire_phone, self.fire, loud=False)

    async def test_restore_keeps_original_values_until_sensor_confirmation(self):
        lease = {"ringer": "silent", "volume": 2, "incident_id": self.fire["id"]}
        self.engine.model.data["leases"]["fire-phone"] = lease
        self.engine.command = AsyncMock(return_value=True)
        self.engine.wait_for_restored_state = AsyncMock(return_value=False)
        await self.engine.restore_device(self.fire_phone)
        self.assertIs(self.engine.model.data["leases"]["fire-phone"], lease)
        self.assertTrue(lease["restore_pending"])
        self.assertGreater(lease["retry_at"], runtime.time())
        self.assertEqual((lease["ringer"], lease["volume"]), ("silent", 2))

    async def test_confirmed_restoration_removes_recovery_state(self):
        self.engine.model.data["leases"]["fire-phone"] = {"ringer": "silent", "volume": 2, "incident_id": self.fire["id"]}
        self.engine.command = AsyncMock(return_value=True)
        self.engine.wait_for_restored_state = AsyncMock(return_value=True)
        await self.engine.restore_device(self.fire_phone)
        self.assertNotIn("fire-phone", self.engine.model.data["leases"])

    async def test_failed_command_does_not_clear_original_state(self):
        self.engine.model.data["leases"]["fire-phone"] = {"ringer": "silent", "volume": 2, "incident_id": "ended"}
        self.engine.command = AsyncMock(return_value=False)
        self.engine.wait_for_restored_state = AsyncMock()
        await self.engine.restore_device(self.fire_phone)
        self.engine.wait_for_restored_state.assert_not_awaited()
        self.assertIn("fire-phone", self.engine.model.data["leases"])

    async def test_retry_ignores_active_playback_but_restores_finished_alarm(self):
        self.engine.model.data["leases"] = {
            "fire-phone": {"incident_id": self.fire["id"]},
            "intrusion-phone": {"incident_id": self.intrusion["id"]}}
        self.intrusion["status"] = "ended"
        self.engine.restore_device = AsyncMock()
        await self.engine.retry_restorations()
        self.engine.restore_device.assert_awaited_once_with(self.intrusion_phone)

    async def test_retry_waits_for_backoff(self):
        self.engine.model.data["leases"] = {"fire-phone": {
            "incident_id": "ended", "restore_pending": True, "retry_at": runtime.time()+100}}
        self.engine.restore_device = AsyncMock()
        await self.engine.retry_restorations()
        self.engine.restore_device.assert_not_awaited()

    async def test_stale_matching_sensor_values_are_not_confirmation(self):
        reported = datetime.fromtimestamp(90, timezone.utc)
        self.states.update({"sensor.volume": types.SimpleNamespace(state="2", last_reported=reported),
                            "sensor.ringer": types.SimpleNamespace(state="silent", last_reported=reported)})
        self.engine.command = AsyncMock(return_value=True)
        with patch.object(runtime, "time", side_effect=[100, 101, 105]), patch.object(runtime.asyncio, "sleep", new_callable=AsyncMock):
            result = await self.engine.wait_for_restored_state(self.fire_phone, {"volume": 2, "ringer": "silent"}, 100)
        self.assertFalse(result)

    async def test_fresh_sensor_reports_confirm_restoration(self):
        reported = datetime.fromtimestamp(110, timezone.utc)
        self.states.update({"sensor.volume": types.SimpleNamespace(state="2", last_reported=reported),
                            "sensor.ringer": types.SimpleNamespace(state="silent", last_reported=reported)})
        self.engine.command = AsyncMock(return_value=True)
        self.assertTrue(await self.engine.wait_for_restored_state(self.fire_phone, {"volume": 2, "ringer": "silent"}, 100))

    async def test_reply_does_not_stop_other_alarm_transport(self):
        self.engine.actor = AsyncMock(return_value=types.SimpleNamespace(id="fire", name="Alice"))
        self.engine.finish_response = AsyncMock()
        await self.engine.respond(self.fire["id"], "coming", "fire")
        self.assertEqual(self.fire["status"], "claimed")
        self.assertEqual(self.intrusion["status"], "open")
        self.assertEqual(self.intrusion["next_due"], 0)
        self.assertEqual(self.engine.finish_response.await_args.args[3], [self.fire["id"]])

    def test_device_activity_rechecks_alarm_type_permissions(self):
        self.assertTrue(self.engine.device_active(self.fire_phone, self.fire))
        self.engine.model.data["users"]["fire"]["types"] = []
        self.assertFalse(self.engine.device_active(self.fire_phone, self.fire))

    def test_public_sensor_contains_only_count_and_generic_attributes(self):
        self.engine.publish()
        args = self.hass.states.async_set.call_args.args
        self.assertEqual(args[1], 2)
        self.assertNotIn("incidents", args[2])
        self.assertNotIn("site_id", args[2])

    def test_pending_alarm_restore_blocks_test_confirmation(self):
        self.engine.missing_categories = lambda device: []
        self.engine.model.data["leases"]["fire-phone"] = {"incident_id": "ended", "restore_pending": True}
        with self.assertRaises(runtime.HomeAssistantError):
            self.engine.ensure_test_ready(self.fire_phone)

    async def test_tick_schedules_pending_recovery_without_duplicate_worker(self):
        self.engine._last_purge = runtime.time()
        self.fire["next_due"] = runtime.time()+100
        self.intrusion["next_due"] = runtime.time()+100
        self.engine.schedule_category_setup = Mock()
        self.engine.model.data["leases"] = {"fire-phone": {"incident_id": "ended", "restore_pending": True}}
        gate = asyncio.Event()
        async def retry():
            await gate.wait()
        self.engine.retry_restorations = AsyncMock(side_effect=retry)
        await self.engine.tick(None)
        first_worker = self.engine.recovery_task
        await self.engine.tick(None)
        self.assertIs(self.engine.recovery_task, first_worker)
        await asyncio.sleep(0)
        self.engine.retry_restorations.assert_awaited_once()
        gate.set()
        await first_worker
