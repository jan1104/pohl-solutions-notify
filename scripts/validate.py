"""Validate repository files without importing Home Assistant or writing bytecode."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "alarm_system"


def validate_hacs(root):
    """Check the source-download layout HACS needs at the selected Git ref."""
    hacs = json.loads((root / "hacs.json").read_text(encoding="utf-8"))
    if not isinstance(hacs.get("name"), str) or not hacs["name"].strip():
        raise ValueError("HACS display name is required")
    if hacs.get("content_in_root", False) is not False or hacs.get("zip_release", False) is not False:
        raise ValueError("HACS must use the custom_components source layout")
    components = [p for p in (root / "custom_components").iterdir()
                  if p.is_dir() and p.name != "__pycache__"]
    if len(components) != 1 or components[0].name != "alarm_system":
        raise ValueError("HACS requires one integration in custom_components")
    manifest = json.loads((components[0] / "manifest.json").read_text(encoding="utf-8"))
    for key in ("domain", "documentation", "issue_tracker", "codeowners", "name", "version"):
        if not manifest.get(key):
            raise ValueError(f"HACS integration metadata missing: {key}")


def main():
    validate_hacs(ROOT)
    python_files = (sorted(COMPONENT.rglob("*.py"))
                    + sorted((ROOT / "tests").glob("*.py"))
                    + sorted((ROOT / "scripts").glob("*.py")))
    for path in python_files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    documents = {}
    for path in sorted(COMPONENT.rglob("*.json")):
        documents[path.relative_to(COMPONENT).as_posix()] = json.loads(path.read_text(encoding="utf-8"))
    manifest = documents["manifest.json"]
    if manifest["domain"] != "alarm_system" or not manifest["config_flow"]:
        raise ValueError("Unexpected integration domain or missing config flow")
    constants = ast.parse((COMPONENT / "const.py").read_text(encoding="utf-8"))
    version = next(ast.literal_eval(node.value) for node in constants.body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "VERSION" for t in node.targets))
    if manifest["version"] != version:
        raise ValueError("Manifest and Python version differ")
    frontend = (COMPONENT / "frontend" / "panel.js").read_text(encoding="utf-8")
    if f"Version {version}" not in frontend or f"version:'{version}'" not in frontend:
        raise ValueError("Frontend and configuration export version differ")
    if documents["strings.json"] != documents["translations/de.json"]:
        raise ValueError("German translations differ from source strings")
    print(f"OK: {len(python_files)} Python files, {len(documents)} JSON files; version {version}")


if __name__ == "__main__":
    main()
