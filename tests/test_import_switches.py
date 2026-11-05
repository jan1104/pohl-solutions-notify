"""Import real configuration switches without truthiness coercion or partial edits."""
from copy import deepcopy
import importlib
from pathlib import Path
import sys
import types
import unittest

PACKAGE = "_import_switches_under_test"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components" / "alarm_system")]
sys.modules[PACKAGE] = package
AlarmModel = importlib.import_module(f"{PACKAGE}.model").AlarmModel
configuration = importlib.import_module(f"{PACKAGE}.configuration")


class ImportSwitchTests(unittest.TestCase):
    def setUp(self):
        self.current = AlarmModel(site_id="TEST").snapshot()

    def document(self, schema):
        document = {
            "format": "alarm_system_configuration", "schema_version": schema, "site_id": "TEST",
            "users": {"user": {"id": "user", "types": ["FIRE"], "enabled": True}},
            "devices": {"browser": {"id": "browser", "user_id": "user", "platform": "browser",
                                     "enabled": True, "tested": True, "browsers": [{"id": "browser-one"}],
                                     "push": False, "sound": False, "speech": False, "popup": True}},
            "sources": {"smoke": {"id": "smoke", "entity_id": "binary_sensor.smoke", "name": "Rauchmelder",
                                  "type": "FIRE", "enabled": True, "silent": False}},
        }
        if schema == 2:
            document["alarm_types"] = deepcopy(self.current["alarm_types"])
        return document

    def prepare(self, document):
        return configuration.prepare_import(self.current, document, {"user": "User"},
                                            {"binary_sensor.smoke": "off"}, set())

    def assert_nonboolean_rejected(self, table, identifier, field):
        for schema in (1, 2):
            for value in ("false", "true", 0, 1, None, [], {}):
                with self.subTest(schema=schema, table=table, field=field, value=value):
                    document = self.document(schema)
                    document[table][identifier][field] = value
                    before_document, before_current = deepcopy(document), deepcopy(self.current)
                    try:
                        with self.assertRaises(ValueError):
                            self.prepare(document)
                    finally:
                        self.assertEqual(document, before_document)
                        self.assertEqual(self.current, before_current)

    def test_user_enabled_rejects_nonboolean_values_atomically(self):
        self.assert_nonboolean_rejected("users", "user", "enabled")

    def test_device_enabled_rejects_nonboolean_values_atomically(self):
        self.assert_nonboolean_rejected("devices", "browser", "enabled")

    def test_source_enabled_rejects_nonboolean_values_atomically(self):
        self.assert_nonboolean_rejected("sources", "smoke", "enabled")

    def test_source_silent_rejects_nonboolean_values_atomically(self):
        self.assert_nonboolean_rejected("sources", "smoke", "silent")

    def test_actual_booleans_are_preserved_and_devices_require_retesting(self):
        for schema in (1, 2):
            for value in (False, True):
                with self.subTest(schema=schema, value=value):
                    document = self.document(schema)
                    for table, identifier, field in (("users", "user", "enabled"),
                                                     ("devices", "browser", "enabled"),
                                                     ("sources", "smoke", "enabled"),
                                                     ("sources", "smoke", "silent")):
                        document[table][identifier][field] = value
                    before = deepcopy(document)
                    result = self.prepare(document)
                    self.assertIs(result["users"]["user"]["enabled"], value)
                    self.assertIs(result["devices"]["browser"]["enabled"], value)
                    self.assertIs(result["sources"]["smoke"]["enabled"], value)
                    self.assertIs(result["sources"]["smoke"]["silent"], value)
                    self.assertFalse(result["devices"]["browser"]["tested"])
                    self.assertEqual(document, before)

    def test_omitted_legacy_flags_keep_defaults_without_activating_device(self):
        for schema in (1, 2):
            with self.subTest(schema=schema):
                document = self.document(schema)
                for table, identifier, field in (("users", "user", "enabled"),
                                                 ("devices", "browser", "enabled"),
                                                 ("sources", "smoke", "enabled"),
                                                 ("sources", "smoke", "silent")):
                    document[table][identifier].pop(field)
                before = deepcopy(document)
                result = self.prepare(document)
                self.assertTrue(result["users"]["user"]["enabled"])
                self.assertTrue(result["sources"]["smoke"]["enabled"])
                self.assertFalse(result["sources"]["smoke"]["silent"])
                self.assertNotIn("enabled", result["devices"]["browser"])
                self.assertEqual(document, before)

    def test_invalid_device_durations_are_rejected_atomically(self):
        for schema in (1, 2):
            for field in ("fire_seconds", "intrusion_seconds", "speech_seconds"):
                for value in (True, False, None, [], {}, "invalid", "nan", "inf", 0, -1, 16):
                    with self.subTest(schema=schema, field=field, value=value):
                        document = self.document(schema)
                        document["devices"]["browser"][field] = value
                        before_document, before_current = deepcopy(document), deepcopy(self.current)
                        with self.assertRaisesRegex(ValueError, "Ton-/Sprachdauer"):
                            self.prepare(document)
                        self.assertEqual(document, before_document)
                        self.assertEqual(self.current, before_current)

    def test_legacy_numeric_durations_and_defaults_remain_compatible(self):
        for schema in (1, 2):
            for value in (1, 2.5, "3.5"):
                with self.subTest(schema=schema, value=value):
                    document = self.document(schema)
                    document["devices"]["browser"]["fire_seconds"] = value
                    result = self.prepare(document)["devices"]["browser"]
                    self.assertEqual(result["fire_seconds"], float(value))
                    self.assertEqual(result["intrusion_seconds"], 5)
                    self.assertEqual(result["speech_seconds"], 8)
