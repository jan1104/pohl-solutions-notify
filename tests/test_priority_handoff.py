"""Priority handoff regressions for the Android tone-to-speech boundary."""
import asyncio
import types
import unittest
from unittest.mock import AsyncMock

from ha_test_support import load_runtime_modules

runtime, _ = load_runtime_modules()


class PriorityHandoff(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.hass = types.SimpleNamespace(
            states=types.SimpleNamespace(get=lambda _entity: None, async_set=lambda *_args: None),
            bus=types.SimpleNamespace(async_fire=lambda *_args: None),
            async_create_background_task=lambda coroutine, _name: asyncio.create_task(coroutine))
        self.engine = runtime.AlarmEngine(self.hass, types.SimpleNamespace(data={"site_id": "TEST"}))
        self.engine.save = AsyncMock()
        self.engine.notify = AsyncMock()
        self.device = self.phone("shared", "owner")
        self.other = self.phone("other", "other")
        self.engine.model.data["users"] = {
            "owner": {"id": "owner", "enabled": True, "types": ["FIRE"]},
            "other": {"id": "other", "enabled": True, "types": ["INTRUSION"]},
        }
        self.engine.model.data["devices"] = {"shared": self.device, "other": self.other}
        self.fire = self.alarm("FIRE", "fire", "smoke")
        self.intrusion = self.alarm("INTRUSION", "intrusion", "door")

    async def asyncTearDown(self):
        pending = list(self.engine.tasks)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    @staticmethod
    def phone(device_id, user_id):
        return {"id": device_id, "user_id": user_id, "platform": "android", "enabled": True,
                "tested": True, "push": False, "popup": False, "sound": True, "speech": True,
                "fire_seconds": 3, "intrusion_seconds": 3,
                "ringer_sensor": "sensor.ringer", "volume_sensor": "sensor.volume"}

    def alarm(self, kind, key, source):
        return self.engine.model.raise_alarm({"type": kind, "alarm_key": key, "source_id": source})[0]

    def start_fire_lease(self):
        self.engine.model.data["leases"]["shared"] = {
            "ringer": "normal", "volume": 2, "incident_id": self.fire["id"], "playback_id": "fire-play"}

    async def test_same_phone_handoff_suppresses_fire_tts_and_restores_its_lease(self):
        self.engine.model.data["users"]["owner"]["types"].append("INTRUSION")
        self.engine.model.data["incidents"].pop(self.intrusion["id"])
        self.start_fire_lease()
        self.engine.command = AsyncMock(return_value=True)
        self.engine.wait_for_restored_state = AsyncMock(return_value=True)

        async def tone_elapsed(_seconds):
            # A new alarm arrives while the earlier tone worker is waiting.
            self.intrusion = self.alarm("INTRUSION", "intrusion", "door")

        with unittest.mock.patch.object(runtime.asyncio, "sleep", side_effect=tone_elapsed):
            await self.engine.finish_android_cycle(self.device, self.fire, "fire-play")

        tts_calls = [c for c in self.engine.command.await_args_list if c.args[1] == "TTS"]
        self.assertEqual(tts_calls, [])
        self.engine.wait_for_restored_state.assert_awaited_once()
        self.assertNotIn("shared", self.engine.model.data["leases"])

    async def test_intrusion_on_disjoint_phone_does_not_suppress_fire_tts(self):
        self.start_fire_lease()
        self.engine.command = AsyncMock(return_value=True)

        async def tone_elapsed(_seconds):
            self.intrusion["status"] = "open"

        with unittest.mock.patch.object(runtime.asyncio, "sleep", side_effect=tone_elapsed):
            await self.engine.finish_android_cycle(self.device, self.fire, "fire-play")

        tts_calls = [c for c in self.engine.command.await_args_list if c.args[1] == "TTS"]
        self.assertEqual(len(tts_calls), 1)
        self.assertIn("Feueralarm", tts_calls[0].kwargs["tts_text"])

    async def test_old_worker_does_not_restore_or_remove_newer_playback_lease(self):
        self.start_fire_lease()
        self.engine.command = AsyncMock(return_value=True)
        newer_lease = {"ringer": "vibrate", "volume": 4, "incident_id": self.fire["id"],
                       "playback_id": "new-play"}

        async def tone_elapsed(_seconds):
            self.engine.model.data["leases"]["shared"] = newer_lease

        with unittest.mock.patch.object(runtime.asyncio, "sleep", side_effect=tone_elapsed):
            await self.engine.finish_android_cycle(self.device, self.fire, "fire-play")

        self.assertIs(self.engine.model.data["leases"]["shared"], newer_lease)
        self.engine.command.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
