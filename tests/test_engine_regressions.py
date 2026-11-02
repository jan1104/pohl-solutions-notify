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

    async def test_cancel_workers_cleans_listeners_and_tasks_without_saving(self):
        unsubscribe = Mock()
        self.engine.unsub = [unsubscribe]
        entered = asyncio.Event()
        cancelled = asyncio.Event()
        async def worker():
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        task = self.engine.spawn(worker())
        await entered.wait()
        await self.engine.cancel_workers()
        self.assertTrue(task.cancelled())
        self.assertTrue(cancelled.is_set())
        self.assertTrue(self.engine.stopping)
        self.assertEqual(self.engine.unsub, [])
        self.engine.save.assert_not_awaited()
        await self.engine.cancel_workers()
        unsubscribe.assert_called_once()

    async def test_speech_without_tone_or_push_runs_without_changing_phone_volume(self):
        self.fire_phone.update(sound=False, speech=True, push=False, speech_seconds=1)
        self.engine.command = AsyncMock(return_value=True)
        self.engine.spawn = Mock(side_effect=asyncio.create_task)
        with patch.object(runtime.asyncio, "sleep", new_callable=AsyncMock):
            task = await self.engine.play_device(self.fire_phone, self.fire)
            self.assertIsNotNone(task)
            await task
        self.engine.notify.assert_not_awaited()
        calls = self.engine.command.await_args_list
        self.assertEqual([call.args[1] for call in calls], ["TTS"])
        self.assertEqual(calls[0].kwargs["media_stream"], "alarm_stream_max")
        self.assertTrue(self.engine.model.data["leases"]["fire-phone"]["speech_only"])

    async def test_speech_off_never_sends_tts_during_tone_cycle(self):
        self.fire_phone.update(sound=True, speech=False)
        self.engine.model.data["leases"]["fire-phone"] = {
            "incident_id": self.fire["id"], "playback_id": "tone", "ringer": "normal", "volume": 2}
        self.engine.command = AsyncMock(return_value=True)
        with patch.object(runtime.asyncio, "sleep", new_callable=AsyncMock):
            await self.engine.finish_android_cycle(self.fire_phone, self.fire, "tone")
        self.engine.command.assert_not_awaited()

    async def test_all_outputs_off_does_not_send_or_start_audio(self):
        self.fire_phone.update(sound=False, speech=False, push=False, popup=False)
        self.engine.command = AsyncMock(return_value=True)
        self.assertIsNone(await self.engine.play_device(self.fire_phone, self.fire))
        self.engine.notify.assert_not_awaited()
        self.engine.command.assert_not_awaited()
        self.assertEqual(self.engine.model.data["leases"], {})

    async def test_push_only_sends_quiet_notification_without_audio_worker(self):
        self.fire_phone.update(sound=False, speech=False, push=True)
        self.assertIsNone(await self.engine.play_device(self.fire_phone, self.fire))
        self.engine.notify.assert_awaited_once_with(self.fire_phone, self.fire, loud=False)
        self.assertEqual(self.engine.model.data["leases"], {})

    async def test_stopping_speech_only_never_needs_ringer_or_volume_values(self):
        self.engine.model.data["leases"]["fire-phone"] = {
            "incident_id": self.fire["id"], "playback_id": "voice", "speech_only": True}
        self.engine.command = AsyncMock(return_value=True)
        await self.engine.restore_device(self.fire_phone)
        self.engine.command.assert_awaited_once_with(self.fire_phone, "command_stop_tts")
        self.assertNotIn("fire-phone", self.engine.model.data["leases"])

    async def test_failed_speech_stop_is_retained_for_retry(self):
        self.engine.model.data["leases"]["fire-phone"] = {
            "incident_id": self.fire["id"], "playback_id": "voice", "speech_only": True}
        self.engine.command = AsyncMock(return_value=False)
        await self.engine.restore_device(self.fire_phone)
        lease = self.engine.model.data["leases"]["fire-phone"]
        self.assertTrue(lease["restore_pending"])
        self.assertGreater(lease["retry_at"], runtime.time())

    def test_no_tone_requires_no_muting_or_sensor_setup(self):
        self.fire_phone.update(sound=False, speech=True, notify_action="notify.mobile_app_phone")
        self.assertEqual(self.engine.required_categories(self.fire_phone), [])
        self.engine.ensure_test_ready(self.fire_phone)

    async def test_quiet_android_alarm_requests_low_importance_channel(self):
        del self.engine.notify  # Exercise the real payload builder.
        self.engine.send = AsyncMock(return_value=True)
        await self.engine.notify(self.fire_phone, self.fire, loud=False)
        payload = self.engine.send.await_args.args[1]
        self.assertEqual(payload["data"]["channel"], "Alarmstatus")
        self.assertEqual(payload["data"]["importance"], "low")

    async def test_speech_only_worker_cancellation_stops_tts(self):
        self.fire_phone.update(sound=False, speech=True, push=False)
        self.engine.command = AsyncMock(return_value=True)
        waiting = asyncio.Event()
        started = asyncio.Event()
        async def wait_for_voice(seconds):
            started.set()
            await waiting.wait()
        with patch.object(runtime.asyncio, "sleep", side_effect=wait_for_voice):
            task = await self.engine.play_device(self.fire_phone, self.fire)
            await started.wait()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        self.assertTrue(task.cancelled())
        self.assertEqual([call.args[1] for call in self.engine.command.await_args_list], ["TTS", "command_stop_tts"])
        self.assertNotIn("fire-phone", self.engine.model.data["leases"])

    async def test_tone_and_speech_keep_configured_sequence(self):
        self.fire_phone.update(sound=True, speech=True, fire_seconds=3, speech_seconds=4)
        self.engine.model.data["leases"]["fire-phone"] = {
            "incident_id": self.fire["id"], "playback_id": "both", "ringer": "normal", "volume": 2}
        self.engine.command = AsyncMock(return_value=True)
        with patch.object(runtime.asyncio, "sleep", new_callable=AsyncMock) as sleep:
            await self.engine.finish_android_cycle(self.fire_phone, self.fire, "both")
        self.assertEqual([call.args[0] for call in sleep.await_args_list], [3.0, 4.0])
        self.engine.command.assert_awaited_once()
        self.assertEqual(self.engine.command.await_args.args[1], "TTS")

    async def test_disabled_push_skips_info_and_warning_delivery(self):
        self.fire_phone.update(push=False, sound=False, speech=False)
        self.engine.model.data["users"]["fire"]["types"].extend(["INFO", "WARNING"])
        self.engine.send = AsyncMock()
        await self.engine.simple_message({"type": "INFO", "message": "Info"})
        await self.engine.simple_message({"type": "WARNING", "message": "Warning"})
        self.engine.send.assert_not_awaited()

    async def test_speech_only_does_not_replace_unconfirmed_volume_recovery(self):
        self.fire_phone.update(sound=False, speech=True, push=False)
        lease = {"ringer": "silent", "volume": 2, "incident_id": "old", "restore_pending": True}
        self.engine.model.data["leases"]["fire-phone"] = lease
        self.engine.restore_device = AsyncMock()
        self.assertIsNone(await self.engine.play_device(self.fire_phone, self.fire))
        self.assertIs(self.engine.model.data["leases"]["fire-phone"], lease)
        self.engine.notify.assert_not_awaited()
