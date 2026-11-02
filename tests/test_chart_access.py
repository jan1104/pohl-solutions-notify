"""Private chart lifecycle and application authorization (no live HA HTTP server)."""
import asyncio
import importlib
from pathlib import Path
import tempfile
import types
import unittest

from ha_test_support import load_runtime_modules

runtime, views = load_runtime_modules()
storage = importlib.import_module("_alarm_runtime_under_test.chart_storage")


class ChartStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.private = self.root / "private"
        self.legacy = self.root / "legacy"

    def test_chart_round_trip_retains_required_alarm_type(self):
        name = storage.write_chart(self.private, b"PNG", "WARNING", now=100)
        self.assertEqual(storage.read_chart(self.private, name, now=101), ("WARNING", b"PNG"))

    def test_expired_chart_is_not_served_even_before_cleanup(self):
        name = storage.write_chart(self.private, b"PNG", "WARNING", now=100)
        with self.assertRaises(FileNotFoundError):
            storage.read_chart(self.private, name, now=100+storage.CHART_TTL)

    def test_chart_names_cannot_escape_private_directory(self):
        for name in ("../secrets.yaml", "..\\secrets.yaml", "/etc/passwd", "a.png", "A"*32+".png"):
            with self.subTest(name=name), self.assertRaises(FileNotFoundError):
                storage.read_chart(self.private, name)

    def test_cleanup_removes_expired_chart_and_only_generated_legacy_names(self):
        expired = storage.write_chart(self.private, b"expired", "WARNING", now=0)
        fresh = storage.write_chart(self.private, b"fresh", "INFO", now=storage.CHART_TTL)
        self.legacy.mkdir()
        generated = self.legacy / ("a"*32+".png")
        generated.write_bytes(b"old public chart")
        unrelated = self.legacy / "user-image.png"
        unrelated.write_bytes(b"keep")
        storage.cleanup_charts(self.private, self.legacy, now=storage.CHART_TTL+1)
        self.assertFalse((self.private / expired).exists())
        self.assertFalse((self.private / (expired+".json")).exists())
        self.assertTrue((self.private / fresh).exists())
        self.assertFalse(generated.exists())
        self.assertTrue(unrelated.exists())

    def test_cleanup_does_not_delete_chart_while_metadata_is_being_written(self):
        self.private.mkdir()
        pending = self.private / ("b"*32+".png")
        pending.write_bytes(b"in flight")
        storage.cleanup_charts(self.private, self.legacy)
        self.assertTrue(pending.exists())


class ChartAccessTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.model = runtime.AlarmModel(site_id="TEST")
        self.model.data["users"] = {
            "allowed": {"id": "allowed", "types": ["WARNING"], "enabled": True},
            "wrong": {"id": "wrong", "types": ["FIRE"], "enabled": True},
            "disabled": {"id": "disabled", "types": ["WARNING"], "enabled": False}}
        async def executor(function, *args):
            return function(*args)
        self.hass = types.SimpleNamespace(
            data={"alarm_system": types.SimpleNamespace(model=self.model)},
            config=types.SimpleNamespace(path=lambda *parts: str(self.root.joinpath(*parts))),
            async_add_executor_job=executor)
        self.view = views.AlarmChartView(self.hass)
        self.name = storage.write_chart(self.root / ".storage" / "alarm_system_charts", b"PNG", "WARNING")

    def request(self, user_id, admin=False, active=True):
        return {"hass_user": types.SimpleNamespace(id=user_id, is_admin=admin, is_active=active)}

    async def test_view_requires_authentication_and_rejects_missing_user(self):
        self.assertTrue(self.view.requires_auth)
        with self.assertRaises(views.web.HTTPUnauthorized):
            await self.view.get({}, self.name)

    async def test_authorized_account_receives_non_cacheable_image(self):
        response = await self.view.get(self.request("allowed"), self.name)
        self.assertEqual(response.body, b"PNG")
        self.assertEqual(response.content_type, "image/png")
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    async def test_wrong_alarm_type_disabled_and_unknown_accounts_are_denied(self):
        for user_id in ("wrong", "disabled", "unknown"):
            with self.subTest(user_id=user_id), self.assertRaises(views.web.HTTPForbidden):
                await self.view.get(self.request(user_id), self.name)

    async def test_inactive_ha_user_is_denied(self):
        with self.assertRaises(views.web.HTTPUnauthorized):
            await self.view.get(self.request("allowed", active=False), self.name)

    async def test_active_admin_can_access_chart(self):
        self.assertEqual((await self.view.get(self.request("admin", admin=True), self.name)).body, b"PNG")

    async def test_unloaded_integration_and_invalid_path_return_not_found(self):
        with self.assertRaises(views.web.HTTPNotFound):
            await self.view.get(self.request("allowed"), "../secrets.yaml")
        self.hass.data.clear()
        with self.assertRaises(views.web.HTTPNotFound):
            await self.view.get(self.request("allowed"), self.name)
