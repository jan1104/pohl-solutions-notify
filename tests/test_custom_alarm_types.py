"""Profile validation and incident behavior, without Home Assistant imports."""
import importlib
from pathlib import Path
import sys
import types
import unittest

PACKAGE = "_custom_alarm_types_under_test"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components" / "alarm_system")]
sys.modules[PACKAGE] = package
profiles = importlib.import_module(f"{PACKAGE}.alarm_types")
AlarmModel = importlib.import_module(f"{PACKAGE}.model").AlarmModel


class AlarmTypeTests(unittest.TestCase):
    def setUp(self):
        self.model = AlarmModel(site_id="TEST")

    def custom(self, **fields):
        return self.model.upsert_alarm_type(dict(name="Wasseralarm", **fields))

    def test_old_data_gains_independent_builtin_profiles_without_losing_state(self):
        old = {"site_id": "ALT", "users": {"u": {"types": ["FIRE"]}}, "journal": [{"text": "Alt"}]}
        model = AlarmModel(old)
        self.assertEqual(model.type_ids(), ("INFO", "WARNING", "FIRE", "INTRUSION"))
        self.assertEqual(model.data["users"], old["users"])
        self.assertEqual(model.data["journal"], old["journal"])
        self.assertNotIn("alarm_types", old)
        self.assertEqual(model.profile("FIRE")["priority"], 20)
        self.assertEqual(model.profile("INTRUSION")["priority"], 10)
        self.assertIsNone(model.profile("FIRE")["tone_seconds"])
        self.assertFalse(model.is_alarm("INFO"))
        self.assertTrue(model.profile("INFO")["push"])
        for key in ("sound", "speech", "popup"):
            self.assertFalse(model.profile("WARNING")[key])
        model.profile("FIRE")["name"] = "Lokal"
        self.assertEqual(profiles.default_alarm_types()["FIRE"]["name"], "Feueralarm")

    def test_partial_profile_migrates_and_full_registry_roundtrips(self):
        registry = profiles.normalize_alarm_types({"FIRE": {"push": False}})
        self.assertFalse(registry["FIRE"]["push"])
        self.assertTrue(registry["FIRE"]["sound"])
        self.assertEqual(profiles.normalize_alarm_types(registry), registry)

    def test_custom_id_defaults_and_persistent_channel_survive_rename_and_reload(self):
        record = self.custom()
        kind = record["id"]
        self.assertRegex(kind, r"^CUSTOM_[0-9A-F]{12}$")
        self.assertEqual(record["channel"], "Wasseralarm")
        self.assertEqual((record["mode"], record["priority"], record["tone_seconds"], record["speech_seconds"]), ("alarm", 30, 5, 8))
        renamed = self.model.upsert_alarm_type({"id": kind, "name": "Wasser im Keller", "push": False, "priority": 25})
        self.assertEqual(renamed["channel"], "Wasseralarm")
        reloaded = AlarmModel(self.model.snapshot())
        self.assertEqual(reloaded.profile(kind), renamed)
        self.assertEqual(reloaded.label(kind), "Wasser im Keller")
        self.assertEqual(reloaded.label("UNKNOWN"), "UNKNOWN")
        self.assertFalse(reloaded.is_alarm("UNKNOWN"))
        with self.assertRaises(ValueError):
            reloaded.profile("UNKNOWN")

    def test_names_are_required_bounded_unique_and_case_insensitive(self):
        self.custom()
        for name in ("", "   ", "x" * 81, None, 23, "wasseralarm", " Feueralarm "):
            before = self.model.snapshot()
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.model.upsert_alarm_type({"name": name})
            self.assertEqual(self.model.snapshot(), before)

    def test_creation_channel_cannot_reuse_builtin_or_renamed_profile_channel(self):
        custom = self.custom()
        self.model.upsert_alarm_type({"id": custom["id"], "name": "Neuer Wassername"})
        for name in ("Info", "info", "Wasseralarm", "WASSERALARM"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.model.upsert_alarm_type({"name": name})
        with self.assertRaises(ValueError):
            self.model.upsert_alarm_type({"id": custom["id"], "channel": "Neuer Kanal"})

    def test_malformed_profile_fields_are_rejected_atomically(self):
        cases = {"priority": [True, 0, 101, 2.5, "3"],
                 "tone_seconds": [True, 0, 16, float("nan"), float("inf"), None, "5", 10 ** 400],
                 "speech_seconds": [False, 0, 13, float("nan")],
                 "push": ["false", 0, None], "sound": [1], "speech": ["yes"], "popup": [[]],
                 "mode": ["message"], "builtin": [True, "false"], "channel": ["another"]}
        before = self.model.snapshot()
        for field, values in cases.items():
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.custom(**{field: value})
                self.assertEqual(self.model.snapshot(), before)

    def test_templates_allow_only_safe_named_placeholders(self):
        valid = "{name}: {site}, {areas}. {{Hinweis}}"
        self.assertEqual(self.custom(speech_template=valid)["speech_template"], valid)
        invalid = ("{name.__class__}", "{site[0]}", "{name!r}", "{areas:>20}", "{name:{site}}", "{}", "{0}", "{missing}", "{name", "}", "x" * 241, None)
        for template in invalid:
            with self.subTest(template=template), self.assertRaises(ValueError):
                self.model.upsert_alarm_type({"id": self.model.type_ids()[-1], "speech_template": template})

    def test_empty_speech_template_uses_default_without_relaxing_validation(self):
        custom = self.custom(speech_template="{name}")
        for template in ("", "   ", "\t\n"):
            updated = self.model.upsert_alarm_type({"id": custom["id"], "speech_template": template})
            self.assertEqual(updated["speech_template"], profiles.DEFAULT_SPEECH_TEMPLATE)
        before = self.model.snapshot()
        for template in (None, False, 0, [], "{name.__class__}", "{invalid}"):
            with self.subTest(template=template), self.assertRaises(ValueError):
                self.model.upsert_alarm_type({"id": custom["id"], "speech_template": template})
            self.assertEqual(self.model.snapshot(), before)

    def test_registry_rejects_invalid_ids_mismatches_types_and_custom_count(self):
        for records in (None, [], {"OTHER": {}}, {"CUSTOM_123456789abc": {"name": "Bad"}}, {"FIRE": []}, {"FIRE": {"id": "INTRUSION"}}):
            with self.subTest(records=records), self.assertRaises(ValueError):
                profiles.normalize_alarm_types(records)
        records = {f"CUSTOM_{n:012X}": {"name": f"Alarm {n}"} for n in range(32)}
        self.assertEqual(len(profiles.normalize_alarm_types(records)), 36)
        records["CUSTOM_FFFFFFFFFFFF"] = {"name": "Zu viel"}
        with self.assertRaises(ValueError):
            profiles.normalize_alarm_types(records)

    def test_builtin_invariants_and_unknown_ids_are_not_editable(self):
        for field, value in (("id", "CUSTOM_123456789ABC"), ("priority", 21), ("mode", "message"), ("channel", "Neu"), ("builtin", False), ("tone_seconds", 5), ("speech_seconds", 8)):
            payload = {"id": "FIRE", field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.model.upsert_alarm_type(payload)
        updated = self.model.upsert_alarm_type({"id": "FIRE", "push": False, "speech": False})
        self.assertFalse(updated["push"])
        self.assertFalse(updated["speech"])
        self.assertEqual(updated["priority"], 20)

    def test_custom_source_generates_incident_and_group_must_keep_type(self):
        kind = self.custom()["id"]
        source = self.model.register_source({"id": "water", "entity_id": "binary_sensor.water", "name": "Keller", "type": kind, "alarm_key": "Wasser"}, "off")
        payload = self.model.signal_update(source["entity_id"], "on")
        incident, state = self.model.raise_alarm(payload)
        self.assertEqual((incident["type"], state), (kind, "new"))
        with self.assertRaises(ValueError):
            self.model.register_source({"entity_id": "binary_sensor.smoke", "name": "Rauch", "type": "FIRE", "alarm_key": "Wasser"})
        with self.assertRaises(ValueError):
            self.model.raise_alarm({"type": "FIRE", "source_id": "smoke", "alarm_key": "Wasser"})
        for kind in ("UNKNOWN", "INFO", "WARNING"):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.model.raise_alarm({"type": kind, "alarm_key": "message", "source_id": "message"})

    def test_custom_recipients_and_authorization_follow_user_type_membership(self):
        kind = self.custom()["id"]
        self.model.data["users"] = {"u": {"id": "u", "types": [kind], "enabled": True}, "v": {"id": "v", "types": ["FIRE"], "enabled": True}}
        device = {"id": "phone", "user_id": "u", "enabled": True, "tested": True}
        self.model.data["devices"] = {"phone": device}
        incident, _ = self.model.raise_alarm({"type": kind, "alarm_key": "water", "source_id": "water"})
        self.assertEqual(self.model.recipients(kind), [device])
        self.assertEqual(self.model.audience(kind), [self.model.data["users"]["u"]])
        self.assertTrue(self.model.authorized("u", incident))
        self.assertFalse(self.model.authorized("v", incident))
        self.model.data["users"]["u"]["enabled"] = False
        self.assertEqual(self.model.recipients(kind), [])
        self.assertFalse(self.model.authorized("u", incident))

    def test_any_active_incident_blocks_all_profile_edits_and_removals(self):
        kind = self.custom()["id"]
        incident, _ = self.model.raise_alarm({"type": "FIRE", "alarm_key": "fire", "source_id": "smoke"})
        before = self.model.snapshot()
        for status in ("open", "claimed"):
            incident["status"] = status
            with self.assertRaises(ValueError):
                self.model.upsert_alarm_type({"id": kind, "sound": False})
            with self.assertRaises(ValueError):
                self.model.remove_alarm_type(kind)
        incident["status"] = "open"
        self.assertEqual(self.model.snapshot(), before)

    def test_removal_requires_custom_type_without_user_source_or_history_references(self):
        for builtin in self.model.type_ids():
            with self.assertRaises(ValueError):
                self.model.remove_alarm_type(builtin)
        kind = self.custom()["id"]
        for table, record in (("users", {"types": [kind]}), ("sources", {"type": kind}), ("incidents", {"type": kind, "status": "ended"})):
            self.model.data[table]["reference"] = record
            with self.subTest(table=table), self.assertRaises(ValueError):
                self.model.remove_alarm_type(kind)
            del self.model.data[table]["reference"]
        self.model.remove_alarm_type(kind)
        self.assertNotIn(kind, self.model.type_ids())


if __name__ == "__main__":
    unittest.main()
