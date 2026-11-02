"""Behavior checks for HA-independent modules; no HA integration emulation."""
import importlib
import sys
import types
import unittest
from pathlib import Path

# Build a namespace package so its __init__ (which requires HA) is not executed.
PACKAGE = "_alarm_rules_under_test"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components" / "alarm_system")]
sys.modules[PACKAGE] = package
AlarmModel = importlib.import_module(f"{PACKAGE}.model").AlarmModel
configuration = importlib.import_module(f"{PACKAGE}.configuration")
identity = importlib.import_module(f"{PACKAGE}.identity")


def alarm(key="fire_house", source="kitchen", kind="FIRE"):
    return {"type": kind, "alarm_key": key, "source_id": source}


class AlarmRulesTests(unittest.TestCase):
    def setUp(self):
        self.model = AlarmModel(site_id="TEST")

    def test_same_group_combines_sources_and_ignores_duplicates(self):
        first, status = self.model.raise_alarm(alarm())
        self.assertEqual(status, "new")
        duplicate, status = self.model.raise_alarm(alarm())
        self.assertIs(duplicate, first)
        self.assertEqual(status, "duplicate")
        combined, status = self.model.raise_alarm(alarm(source="hall"))
        self.assertIs(combined, first)
        self.assertEqual(status, "source_added")
        self.assertEqual(len(self.model.active()), 1)
        self.assertEqual(set(first["sources"]), {"kitchen", "hall"})

    def test_group_cannot_mix_fire_and_intrusion(self):
        self.model.raise_alarm(alarm())
        with self.assertRaises(ValueError):
            self.model.raise_alarm(alarm(source="door", kind="INTRUSION"))

    def test_normal_signal_does_not_end_incident(self):
        incident, _ = self.model.raise_alarm(alarm())
        self.model.normal("fire_house", "kitchen")
        self.assertEqual(incident["status"], "open")
        self.assertTrue(incident["sources"]["kitchen"]["active"])
        self.assertFalse(incident["sources"]["kitchen"]["signal_active"])

    def test_ended_active_source_is_suppressed_until_normal(self):
        incident, _ = self.model.raise_alarm(alarm())
        self.model.end_source(incident["id"], "kitchen", "user")
        self.assertEqual(incident["status"], "ended")
        self.assertEqual(self.model.raise_alarm(alarm()), (None, "suppressed"))
        self.model.normal("fire_house", "kitchen")
        new_incident, status = self.model.raise_alarm(alarm())
        self.assertEqual(status, "new")
        self.assertNotEqual(new_incident["id"], incident["id"])

    def test_response_only_claims_selected_incident(self):
        fire, _ = self.model.raise_alarm(alarm())
        intrusion, _ = self.model.raise_alarm(alarm("intrusion_house", "door", "INTRUSION"))
        self.model.come(fire["id"], "user", "Test User")
        self.assertEqual(fire["status"], "claimed")
        self.assertEqual(intrusion["status"], "open")
        self.assertEqual(len(self.model.active()), 2)

    def test_recipients_require_enabled_user_type_and_tested_device(self):
        self.model.data["users"] = {"user": {"id": "user", "enabled": True, "types": ["FIRE"]}}
        device = {"id": "phone", "user_id": "user", "enabled": True, "tested": False}
        self.model.data["devices"] = {"phone": device}
        self.assertEqual(self.model.recipients("FIRE"), [])
        device["tested"] = True
        self.assertEqual(self.model.recipients("FIRE"), [device])
        self.assertEqual(self.model.recipients("INTRUSION"), [])
        self.model.data["users"]["user"]["enabled"] = False
        self.assertEqual(self.model.recipients("FIRE"), [])

    def test_import_rejects_wrong_site_without_modifying_state(self):
        before = self.model.snapshot()
        document = {"format": "alarm_system_configuration", "schema_version": 1, "site_id": "OTHER"}
        with self.assertRaises(ValueError):
            configuration.prepare_import(self.model.data, document, {}, {}, set())
        self.assertEqual(before, self.model.snapshot())

    def test_user_view_hides_other_accounts_devices_and_admin_discovery(self):
        self.model.data["users"] = {
            "a": {"id": "a", "name": "Alice", "types": ["FIRE"], "enabled": True},
            "b": {"id": "b", "name": "Bob", "types": ["INTRUSION"], "enabled": True},
        }
        self.model.data["devices"] = {"pa": {"id": "pa", "user_id": "a"}, "pb": {"id": "pb", "user_id": "b"}}
        fire, _ = self.model.raise_alarm(alarm())
        self.model.raise_alarm(alarm("intrusion_house", "door", "INTRUSION"))
        data = self.model.snapshot()
        for field in ("available_users", "notify_actions", "phone_connections", "browser_connections"):
            data[field] = ["private"]
        view = configuration.user_view(data, "a")
        self.assertEqual(set(view["incidents"]), {fire["id"]})
        self.assertEqual(set(view["devices"]), {"pa"})
        self.assertEqual(view["users"]["b"], {"id": "b", "name": "Bob"})
        self.assertNotIn("notify_actions", view)
        self.assertNotIn("available_users", view)
        self.assertNotIn("phone_connections", view)
        self.assertNotIn("browser_connections", view)


    def test_disabled_user_cannot_read_incidents_sources_or_other_accounts(self):
        self.model.data["users"] = {
            "a": {"id": "a", "name": "Alice", "enabled": False, "types": ["FIRE"]},
            "b": {"id": "b", "name": "Bob", "enabled": True, "types": ["FIRE"]}}
        self.model.data["devices"] = {"phone": {"id": "phone", "user_id": "a"}}
        self.model.data["sources"] = {"smoke": {"type": "FIRE"}}
        self.model.raise_alarm(alarm())
        self.model.log("alarm_raised", kind="FIRE")
        view = configuration.user_view(self.model.snapshot(), "a")
        for key in ("incidents", "sources", "devices", "signal_values"):
            self.assertEqual(view[key], {})
        self.assertEqual(view["journal"], [])
        self.assertEqual(set(view["users"]), {"a"})

    def test_unknown_user_cannot_read_account_directory(self):
        self.model.data["users"] = {"a": {"id": "a", "name": "Alice", "types": ["FIRE"]}}
        self.assertEqual(configuration.user_view(self.model.snapshot(), "unknown")["users"], {})

    def test_device_test_completion_requires_current_session(self):
        device = {"id": "phone", "test_session": "current"}
        self.model.data["incidents"] = {
            "old": {"type": "FIRE", "test_device": "phone", "test_session": "old", "status": "ended"},
            "open": {"type": "FIRE", "test_device": "phone", "test_session": "current", "status": "open"},
            "done": {"type": "INTRUSION", "test_device": "phone", "test_session": "current", "status": "ended"}}
        self.assertEqual(configuration.completed_device_tests(self.model.data, device), {"INTRUSION"})
        self.assertEqual(configuration.completed_device_tests(self.model.data, {"id": "phone"}), set())

    def test_output_switches_preserve_independent_android_choices(self):
        self.assertEqual(configuration.device_outputs(
            {"push": False, "popup": True, "sound": False, "speech": True}, "android"),
            {"push": False, "popup": True, "sound": False, "speech": True})

    def test_unsupported_outputs_are_disabled_per_platform(self):
        enabled = {key: True for key in ("push", "popup", "sound", "speech")}
        self.assertEqual(configuration.device_outputs(enabled, "browser"),
                         {"push": False, "popup": True, "sound": False, "speech": False})
        self.assertFalse(configuration.device_outputs(enabled, "ios")["speech"])

    def test_string_boolean_is_rejected_instead_of_turning_output_on(self):
        for key in ("push", "popup", "sound", "speech"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                configuration.device_outputs({key: "false"}, "android")

    def test_display_name_never_falls_back_to_uuid(self):
        uid = "0123456789abcdef0123456789abcdef"
        self.assertIsNone(identity.human_name(uid))
        self.assertEqual(identity.resolve_name(uid, {uid: uid}, {}), "Name nicht verfügbar")
        self.assertEqual(identity.resolve_name(uid, {uid: "Alice"}, {}), "Alice")


if __name__ == "__main__":
    unittest.main()
