"""Real unload handler with explicit service/frontend/engine adapters."""
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

from ha_test_support import load_entry_module

entry = load_entry_module()
SERVICES = ('raise_alarm', 'source_normal', 'respond', 'confirm_false_alarm')
ALL_ACTIONS = [*('service:' + name for name in SERVICES), 'panel', 'javascript', 'sensor']


class UnloadCleanupTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.calls = []
        self.failures = {}
        self.engine = types.SimpleNamespace(stop=AsyncMock(), stopping=True,
            model=types.SimpleNamespace(data={'leases': {'phone': {'volume': 4}}}))
        self.hass = types.SimpleNamespace(data={'alarm_system': self.engine},
            services=types.SimpleNamespace(async_remove=Mock(side_effect=self.remove_service)),
            states=types.SimpleNamespace(async_remove=Mock(side_effect=lambda _: self.cleanup('sensor'))))
        logger = patch.object(entry._LOGGER, 'exception', Mock())
        logger.start()
        self.addCleanup(logger.stop)
        for name, callback in (
            ('async_remove_panel', lambda *_: self.cleanup('panel')),
            ('remove_extra_js_url', lambda *_: self.cleanup('javascript')),
        ):
            patcher = patch.object(entry.frontend, name, Mock(side_effect=callback))
            patcher.start()
            self.addCleanup(patcher.stop)

    def cleanup(self, action):
        self.calls.append(action)
        if action in self.failures:
            raise self.failures[action]

    def remove_service(self, domain, name):
        self.assertEqual(domain, 'alarm_system')
        self.cleanup('service:' + name)

    async def test_each_resource_failure_still_attempts_every_other_cleanup(self):
        for target in ('service:raise_alarm', 'panel', 'javascript', 'sensor'):
            with self.subTest(target=target):
                self.calls.clear()
                error = RuntimeError(target + ' failed')
                self.failures = {target: error}
                self.hass.data['alarm_system'] = self.engine
                with self.assertRaises(RuntimeError) as caught:
                    await entry.async_unload_entry(self.hass, None)
                self.assertIs(caught.exception, error)
                self.assertEqual(self.calls, ALL_ACTIONS)
                self.assertIs(self.hass.data.get('alarm_system'), self.engine)

    async def test_first_cleanup_exception_is_preserved_when_later_cleanup_also_fails(self):
        first = RuntimeError('service failed')
        self.failures = {'service:raise_alarm': first, 'panel': OSError('panel failed')}
        with self.assertRaises(RuntimeError) as caught:
            await entry.async_unload_entry(self.hass, None)
        self.assertIs(caught.exception, first)
        self.assertEqual(self.calls, ALL_ACTIONS)
        self.assertIs(self.hass.data.get('alarm_system'), self.engine)

    async def test_failed_cleanup_can_be_retried_instead_of_silently_succeeding(self):
        self.failures = {'service:raise_alarm': RuntimeError('retry required')}
        with self.assertRaises(RuntimeError):
            await entry.async_unload_entry(self.hass, None)
        self.assertIs(self.hass.data.get('alarm_system'), self.engine)
        self.failures.clear()
        self.calls.clear()
        self.assertTrue(await entry.async_unload_entry(self.hass, None))
        self.assertEqual(self.calls, ALL_ACTIONS)
        self.assertNotIn('alarm_system', self.hass.data)
        self.assertEqual(self.engine.stop.await_count, 2)

    async def test_failed_engine_stop_preserves_engine_and_recovery_without_resource_cleanup(self):
        error = OSError('storage unavailable')
        lease = self.engine.model.data['leases']['phone']
        self.engine.stop.side_effect = error
        with self.assertRaises(OSError) as caught:
            await entry.async_unload_entry(self.hass, None)
        self.assertIs(caught.exception, error)
        self.assertIs(self.hass.data.get('alarm_system'), self.engine)
        self.assertIs(self.engine.model.data['leases']['phone'], lease)
        self.assertEqual(self.calls, [])

    async def test_successful_unload_cleans_all_resources_and_removes_engine(self):
        self.assertTrue(await entry.async_unload_entry(self.hass, None))
        self.engine.stop.assert_awaited_once()
        self.assertEqual(self.calls, ALL_ACTIONS)
        self.assertNotIn('alarm_system', self.hass.data)

    async def test_missing_engine_unload_is_idempotent_without_other_cleanup(self):
        self.hass.data.clear()
        self.assertTrue(await entry.async_unload_entry(self.hass, None))
        self.engine.stop.assert_not_awaited()
        self.assertEqual(self.calls, [])
