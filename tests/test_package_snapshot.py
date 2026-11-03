"""Focused tests for tag based snapshot packaging."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "package_snapshot.py"


class PackageSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        self.env = os.environ.copy()
        self.env.update({"GIT_AUTHOR_NAME": "Snapshot Test", "GIT_AUTHOR_EMAIL": "snapshot@example.invalid",
                         "GIT_COMMITTER_NAME": "Snapshot Test", "GIT_COMMITTER_EMAIL": "snapshot@example.invalid"})
        self.git("init", "-q")
        self.write("custom_components/alarm_system/manifest.json", json.dumps({"version": "1.2.3"}))
        self.write("custom_components/alarm_system/old.py", "tagged source\n")
        self.write("custom_components/alarm_system/__pycache__/skip.pyc", "cache")
        self.write("custom_components/alarm_system/skip.pyc", "bytecode")
        self.write("elsewhere/private.txt", "must not ship")
        self.git("add", ".")
        self.git("commit", "-qm", "snapshot")
        self.git("tag", "v1.2.3")
        self.write("custom_components/alarm_system/manifest.json", json.dumps({"version": "9.9.9"}))
        self.write("custom_components/alarm_system/old.py", "working tree source\n")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, env=self.env, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def write(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.repo,
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_packages_tag_contents_and_version_only(self):
        out = self.repo / "artifacts"
        result = self.run_cli("--ref", "v1.2.3", "--output-dir", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        archive = out / "alarm_system-1.2.3.zip"
        self.assertTrue(archive.exists())
        self.assertIn("sha256", result.stdout)
        with zipfile.ZipFile(archive) as bundle:
            self.assertEqual(set(bundle.namelist()), {
                "custom_components/alarm_system/manifest.json",
                "custom_components/alarm_system/old.py"})
            self.assertEqual(bundle.read("custom_components/alarm_system/old.py"), b"tagged source\n")
            self.assertEqual(json.loads(bundle.read("custom_components/alarm_system/manifest.json"))["version"], "1.2.3")

    def test_zip_bytes_are_deterministic_across_output_dirs(self):
        first = self.repo / "one"
        second = self.repo / "two"
        for out in (first, second):
            result = self.run_cli("--ref", "v1.2.3", "--output-dir", str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
        a = (first / "alarm_system-1.2.3.zip").read_bytes()
        b = (second / "alarm_system-1.2.3.zip").read_bytes()
        self.assertEqual(a, b)

    def test_rejects_unsafe_manifest_version_without_writing_outside(self):
        self.write("custom_components/alarm_system/manifest.json", json.dumps({"version": "../../escape"}))
        self.git("add", "custom_components/alarm_system/manifest.json")
        self.git("commit", "-qm", "unsafe version")
        self.git("tag", "unsafe-version")
        out = self.repo / "artifacts"
        result = self.run_cli("--ref", "unsafe-version", "--output-dir", str(out))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.repo.parent / "escape.zip").exists())
        self.assertEqual(list(out.glob("*.zip")) if out.exists() else [], [])

    def test_rejects_non_tag_refs_and_existing_output(self):
        out = self.repo / "artifacts"
        for ref in ("HEAD", "main", "missing"):
            result = self.run_cli("--ref", ref, "--output-dir", str(out))
            self.assertNotEqual(result.returncode, 0, ref)
        good = self.run_cli("--ref", "v1.2.3", "--output-dir", str(out))
        self.assertEqual(good.returncode, 0, good.stderr)
        archive = out / "alarm_system-1.2.3.zip"
        before = archive.read_bytes()
        again = self.run_cli("--ref", "v1.2.3", "--output-dir", str(out))
        self.assertNotEqual(again.returncode, 0)
        self.assertEqual(archive.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
