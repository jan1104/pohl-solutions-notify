"""Reject malformed sensor references before an imported device reaches runtime."""
from copy import deepcopy
import unittest

import test_import_switches as support


class ImportSensorReferences(unittest.TestCase):
    def setUp(self):
        self.current = support.AlarmModel(site_id="TEST").snapshot()
        self.helper = support.ImportSwitchTests()
        self.helper.setUp()

    def document(self, schema):
        document = self.helper.document(schema)
        document["devices"]["browser"].update(
            platform="android", notify_action="notify.mobile_app_phone", sound=True)
        return document

    def prepare(self, document):
        return support.configuration.prepare_import(self.current, document, {"user": "User"},
            {"binary_sensor.smoke": "off"}, {"notify.mobile_app_phone"})

    def assert_rejected_without_mutation(self, document):
        before_document, before_current = deepcopy(document), deepcopy(self.current)
        with self.assertRaises(ValueError):
            self.prepare(document)
        self.assertEqual(document, before_document)
        self.assertEqual(self.current, before_current)

    def test_device_sensor_references_reject_nonempty_containers_and_scalar_types(self):
        for schema in (1, 2):
            for field in ("ringer_sensor", "volume_sensor"):
                for value in (["sensor.phone"], {"entity_id": "sensor.phone"}, True, 1):
                    with self.subTest(schema=schema, field=field, value=value):
                        document = self.document(schema)
                        document["devices"]["browser"][field] = value
                        self.assert_rejected_without_mutation(document)

    def test_browser_visibility_reference_rejects_invalid_types_atomically(self):
        for schema in (1, 2):
            for value in (["sensor.browser"], {"entity_id": "sensor.browser"}, True, 1):
                with self.subTest(schema=schema, value=value):
                    document = self.document(schema)
                    document["devices"]["browser"]["browsers"][0]["visibility_sensor"] = value
                    self.assert_rejected_without_mutation(document)

    def test_optional_and_unavailable_sensor_references_remain_compatible(self):
        for schema in (1, 2):
            for value in ("", None, "sensor.not_currently_available"):
                with self.subTest(schema=schema, value=value):
                    document = self.document(schema)
                    device = document["devices"]["browser"]
                    device.update(ringer_sensor=value, volume_sensor=value)
                    device["browsers"][0]["visibility_sensor"] = value
                    before = deepcopy(document)
                    imported = self.prepare(document)["devices"]["browser"]
                    self.assertEqual(imported["ringer_sensor"], value)
                    self.assertEqual(imported["volume_sensor"], value)
                    self.assertEqual(imported["browsers"][0]["visibility_sensor"], value)
                    self.assertEqual(document, before)
                    self.assertFalse(imported["tested"])

    def test_missing_legacy_sensor_references_do_not_become_required(self):
        for schema in (1, 2):
            with self.subTest(schema=schema):
                document = self.document(schema)
                imported = self.prepare(document)["devices"]["browser"]
                self.assertNotIn("ringer_sensor", imported)
                self.assertNotIn("volume_sensor", imported)
                self.assertNotIn("visibility_sensor", imported["browsers"][0])
