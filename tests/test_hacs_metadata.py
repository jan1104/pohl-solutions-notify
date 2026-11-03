"""Regression coverage for the source-layout HACS download contract."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repository_validate", ROOT / "scripts/validate.py")
VALIDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATE)


class HacsMetadataTests(unittest.TestCase):
    def test_repository_is_valid(self):
        VALIDATE.validate_hacs(ROOT)

    def test_invalid_download_contract_is_rejected(self):
        for case in ("missing", "invalid_json", "root_layout", "release_zip", "missing_issue_tracker", "two_integrations"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                component = root / "custom_components/alarm_system"
                component.mkdir(parents=True)
                manifest = json.loads((ROOT / "custom_components/alarm_system/manifest.json").read_text())
                hacs = {"name": "Notify"}
                if case == "root_layout":
                    hacs["content_in_root"] = True
                if case == "release_zip":
                    hacs["zip_release"] = True
                if case == "missing_issue_tracker":
                    manifest.pop("issue_tracker")
                if case == "two_integrations":
                    (root / "custom_components/other").mkdir()
                (component / "manifest.json").write_text(json.dumps(manifest))
                if case != "missing":
                    (root / "hacs.json").write_text("{" if case == "invalid_json" else json.dumps(hacs))
                with self.assertRaises((ValueError, FileNotFoundError)):
                    VALIDATE.validate_hacs(root)
