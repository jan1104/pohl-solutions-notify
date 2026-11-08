"""Check popup handoff with the real engine and a local transport adapter."""
import asyncio
import types
import unittest
from unittest.mock import AsyncMock

from ha_test_support import load_runtime_modules

runtime, _ = load_runtime_modules()


class PopupHandoffTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.windows = {}
        self.service = AsyncMock(side_effect=self.browser_service)
        hass = types.SimpleNamespace(
            states=types.SimpleNamespace(get=lambda _: None),
            services=types.SimpleNamespace(async_call=self.service),
            async_create_background_task=lambda coro, name: asyncio.create_task(coro),
        )
        self.engine = runtime.AlarmEngine(hass, types.SimpleNamespace(data={"site_id": "TEST"}))
        self.engine.save = AsyncMock()
        self.engine.defer_transport_save = lambda: None
        self.fire = self.alarm("FIRE", "smoke")
        self.door = self.alarm("INTRUSION", "door")

    def alarm(self, kind, source):
        return self.engine.model.raise_alarm({
            "type": kind, "alarm_key": source, "source_id": source,
        })[0]

    def browser(self, browser_id, kinds):
        self.engine.model.data["users"][browser_id] = {
            "id": browser_id, "types": kinds, "enabled": True,
        }
        device = {"id": browser_id, "user_id": browser_id, "enabled": True,
                  "tested": True, "popup": True, "platform": "browser",
                  "browsers": [{"id": browser_id}]}
        self.engine.model.data["devices"][browser_id] = device
        return device

    async def browser_service(self, domain, service, data, *, blocking):
        self.assertEqual(domain, "browser_mod")
        for browser_id in data["browser_id"]:
            key = (browser_id, data["tag"])
            if service == "popup":
                self.windows[key] = data["content"]["incident_id"]
            elif service == "close_popup":
                self.windows.pop(key, None)
            else:
                self.fail(f"Unexpected browser service: {service}")

    async def drain(self):
        await asyncio.gather(*self.engine.tasks)

    async def test_ending_old_alarm_keeps_newer_popup_on_shared_browser(self):
        device = self.browser("shared", ["FIRE", "INTRUSION"])
        await self.engine.show_popup(device, self.fire, launch=False)
        await self.engine.show_popup(device, self.door, launch=False)
        self.assertEqual(self.windows[("shared", "alarm_system")], self.door["id"])

        self.engine.model.end_source(self.fire["id"], "smoke", "shared")
        await self.engine.close_popups(self.fire)
        await self.drain()

        self.assertEqual(self.windows.get(("shared", "alarm_system")), self.door["id"])
        self.assertEqual(self.engine.open_popups["shared"], self.door["id"])
        self.assertEqual([call.args[1] for call in self.service.await_args_list], ["popup", "popup"])

    async def test_close_ends_own_and_untracked_popups_except_excluded_user(self):
        for browser_id in ("tracked", "untracked", "excluded"):
            self.browser(browser_id, ["FIRE"])
            self.windows[(browser_id, "alarm_system")] = self.fire["id"]
        self.engine.open_popups = {"tracked": self.fire["id"], "excluded": self.fire["id"]}
        self.engine.model.end_source(self.fire["id"], "smoke", "excluded")

        await self.engine.close_popups(self.fire, exclude_user="excluded")
        await self.drain()

        self.assertEqual(self.windows, {("excluded", "alarm_system"): self.fire["id"]})
        self.assertEqual(self.engine.open_popups, {})
        self.assertEqual([call.args[2]["browser_id"] for call in self.service.await_args_list],
                         [["tracked"], ["untracked"]])

    async def test_delayed_close_cannot_remove_parallel_new_popup(self):
        device = self.browser("shared", ["FIRE", "INTRUSION"])
        await self.engine.show_popup(device, self.fire, launch=False)
        self.engine.model.end_source(self.fire["id"], "smoke", "shared")
        close_started = asyncio.Event()
        finish_close = asyncio.Event()
        open_attempted = asyncio.Event()

        async def delayed_service(domain, service, data, *, blocking):
            if service == "close_popup":
                close_started.set()
                await finish_close.wait()
            await self.browser_service(domain, service, data, blocking=blocking)

        async def open_new_popup():
            open_attempted.set()
            await self.engine.show_popup(device, self.door, launch=False)

        self.service.side_effect = delayed_service
        close_task = asyncio.create_task(self.engine.close_popups(self.fire))
        try:
            await asyncio.wait_for(close_started.wait(), timeout=1)
            open_task = asyncio.create_task(open_new_popup())
            await asyncio.wait_for(open_attempted.wait(), timeout=1)
        finally:
            finish_close.set()
            await close_task
        await open_task
        await self.drain()

        self.assertEqual(self.windows.get(("shared", "alarm_system")), self.door["id"])
        self.assertEqual(self.engine.open_popups["shared"], self.door["id"])
