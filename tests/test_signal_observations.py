"""Observe sensor availability without changing the last valid alarm flank."""
import asyncio
import types
import unittest
from unittest.mock import AsyncMock

from ha_test_support import load_runtime_modules

runtime, _ = load_runtime_modules()


class SignalObservationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        hass = types.SimpleNamespace(
            async_create_background_task=lambda coro, name: asyncio.create_task(coro))
        self.engine = runtime.AlarmEngine(hass, types.SimpleNamespace(data={"site_id": "TEST"}))
        self.engine.save = AsyncMock()
        self.engine.cycle = AsyncMock()
        self.engine.status = AsyncMock()
        self.entity = "binary_sensor.smoke"
        self.engine.model.register_source({"id": "smoke", "entity_id": self.entity,
            "name": "Rauchmelder", "type": "FIRE"}, "off")

    async def asyncTearDown(self):
        await asyncio.gather(*list(self.engine.tasks), return_exceptions=True)

    async def observe(self, *states):
        for state in states:
            await self.engine.receive_signal(self.entity, state)
        await asyncio.sleep(0)

    def changes(self):
        return [entry["details"] for entry in self.engine.model.data["journal"]
                if entry["action"] == "signal_changed"]

    async def test_repeated_unavailable_is_not_a_second_transition_or_save(self):
        await self.observe("unavailable", "unavailable")
        self.assertEqual(self.changes(), [{"previous": "off", "state": "unavailable"}])
        self.engine.save.assert_awaited_once()
        self.assertEqual(self.engine.model.data["signal_values"]["smoke"], "off")

    async def test_unknown_transition_refers_to_last_observation_not_last_flank(self):
        await self.observe("unavailable", "unknown")
        self.assertEqual(self.changes(), [
            {"previous": "off", "state": "unavailable"},
            {"previous": "unavailable", "state": "unknown"}])
        self.assertEqual(self.engine.save.await_count, 2)
        self.assertEqual(self.engine.model.data["signal_values"]["smoke"], "off")

    async def test_rebound_source_does_not_inherit_old_entity_observation(self):
        await self.observe("unavailable")
        self.entity = "binary_sensor.replacement_smoke"
        self.engine.model.register_source({"id": "smoke", "entity_id": self.entity,
            "name": "Ersatzmelder", "type": "FIRE"}, "off")
        await self.observe("unavailable")
        self.assertEqual(self.changes(), [
            {"previous": "off", "state": "unavailable"},
            {"previous": "off", "state": "unavailable"}])
        self.assertEqual(self.engine.save.await_count, 2)
        self.assertEqual(self.engine.model.data["signal_values"]["smoke"], "off")

    async def test_availability_recovery_does_not_repeat_an_active_alarm(self):
        await self.observe("on", "unknown", "unavailable", "on")
        incidents = self.engine.model.data["incidents"]
        self.assertEqual(len(incidents), 1)
        incident = next(iter(incidents.values()))
        self.assertEqual(incident["status"], "open")
        self.assertTrue(incident["sources"]["smoke"]["active"])
        self.assertTrue(incident["sources"]["smoke"]["signal_active"])
        self.engine.cycle.assert_awaited_once_with(incident["id"])

    async def test_only_real_off_releases_suppression_after_manual_end(self):
        await self.observe("on")
        incident = next(iter(self.engine.model.data["incidents"].values()))
        self.engine.model.end_source(incident["id"], "smoke", "user")
        suppressed = dict(self.engine.model.data["suppressed"])
        self.assertTrue(suppressed)
        await self.observe("unavailable", "unknown", "on")
        self.assertEqual(self.engine.model.data["suppressed"], suppressed)
        self.assertEqual(len(self.engine.model.data["incidents"]), 1)
        self.assertEqual(incident["status"], "ended")
        await self.observe("off")
        self.assertFalse(self.engine.model.data["suppressed"])
        self.assertEqual(len(self.engine.model.data["incidents"]), 1)
        await self.observe("on")
        self.assertEqual(len(self.engine.model.data["incidents"]), 2)
        self.assertEqual(len(self.engine.model.active()), 1)
        self.assertEqual(self.engine.cycle.await_count, 2)
