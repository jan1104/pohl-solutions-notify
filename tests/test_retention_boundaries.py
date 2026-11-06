"""Keep unresolved alarms and respect calendar retention cutoffs without HA."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib
from pathlib import Path
import sys
import types
import unittest


PACKAGE = "_retention_boundaries_under_test"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components" / "alarm_system")]
sys.modules[PACKAGE] = package
AlarmModel = importlib.import_module(f"{PACKAGE}.model").AlarmModel


class RetentionBoundaries(unittest.TestCase):
    def incident(self, model, key, status, at):
        incident, _ = model.raise_alarm({"type": "FIRE", "alarm_key": key, "source_id": key})
        incident["started_at"] = at.isoformat()
        if status == "claimed":
            model.come(incident["id"], "user", "User")
        elif status == "ended":
            model.end_source(incident["id"], key, "user")
            incident["ended_at"] = at.isoformat()
        return incident

    def test_bounded_modes_keep_unresolved_alarms_and_their_old_journal(self):
        now = datetime(2026, 5, 31, 12, tzinfo=timezone.utc)
        cutoffs = {
            "30d": datetime(2026, 5, 1, 12, tzinfo=timezone.utc),
            "3m": datetime(2026, 2, 28, 12, tzinfo=timezone.utc),
            "5m": datetime(2025, 12, 31, 12, tzinfo=timezone.utc),
            "12m": datetime(2025, 5, 31, 12, tzinfo=timezone.utc),
            "4y": datetime(2022, 5, 31, 12, tzinfo=timezone.utc),
        }
        for mode, cutoff in cutoffs.items():
            with self.subTest(mode=mode):
                model = AlarmModel(site_id="TEST")
                model.data["retention_mode"] = mode
                old = cutoff - timedelta(seconds=1)
                recent = cutoff + timedelta(seconds=1)
                opened = self.incident(model, "open", "open", old)
                claimed = self.incident(model, "claimed", "claimed", old)
                ended = self.incident(model, "old-ended", "ended", old)
                boundary = self.incident(model, "boundary", "ended", cutoff)
                retained = self.incident(model, "recent-ended", "ended", recent)
                rows = [
                    {"id": "open-history", "incident_id": opened["id"], "at": old.isoformat()},
                    {"id": "claimed-history", "incident_id": claimed["id"], "at": old.isoformat()},
                    {"id": "old-ended-history", "incident_id": ended["id"], "at": old.isoformat()},
                    {"id": "boundary-history", "incident_id": boundary["id"], "at": cutoff.isoformat()},
                    {"id": "recent-ended-history", "incident_id": retained["id"], "at": recent.isoformat()},
                    {"id": "old-message", "at": old.isoformat()},
                    {"id": "recent-message", "at": recent.isoformat()},
                ]
                model.data["journal"] = rows
                before_open, before_claimed = deepcopy(opened), deepcopy(claimed)

                model.purge(now=now)

                self.assertEqual(set(model.data["incidents"]), {opened["id"], claimed["id"], retained["id"]})
                self.assertEqual(opened, before_open)
                self.assertEqual(claimed, before_claimed)
                self.assertEqual([row["id"] for row in model.data["journal"]],
                                 ["open-history", "claimed-history", "recent-ended-history", "recent-message"])

    def test_three_month_cutoff_clamps_may_31_to_february_in_both_year_types(self):
        for year, february_day in ((2023, 28), (2024, 29)):
            with self.subTest(year=year):
                model = AlarmModel(site_id="TEST")
                model.data["retention_mode"] = "3m"
                cutoff = datetime(year, 2, february_day, 12, tzinfo=timezone.utc)
                expired = self.incident(model, "boundary", "ended", cutoff)
                retained = self.incident(model, "after-boundary", "ended", cutoff + timedelta(seconds=1))

                model.purge(now=datetime(year, 5, 31, 12, tzinfo=timezone.utc))

                self.assertNotIn(expired["id"], model.data["incidents"])
                self.assertIn(retained["id"], model.data["incidents"])

    def test_unlimited_retention_preserves_old_completed_history(self):
        model = AlarmModel(site_id="TEST")
        old = datetime(2000, 1, 1, tzinfo=timezone.utc)
        incident = self.incident(model, "old", "ended", old)
        model.data["journal"] = [{"at": old.isoformat(), "incident_id": incident["id"]},
                                 {"at": old.isoformat()}]
        before = model.snapshot()

        model.purge(now=datetime(2026, 5, 31, tzinfo=timezone.utc))

        self.assertEqual(model.snapshot(), before)
