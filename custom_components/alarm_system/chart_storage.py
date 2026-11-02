"""Private, expiring chart files; independent of Home Assistant."""
import json
from pathlib import Path
import re
from time import time
from uuid import uuid4

CHART_TTL = 24 * 60 * 60
IMAGE_NAME = re.compile(r"[0-9a-f]{32}\.png")


def write_chart(folder, image, kind, now=None):
    now = time() if now is None else now
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    name = uuid4().hex + ".png"
    (folder / name).write_bytes(image)
    (folder / (name + ".json")).write_text(
        json.dumps({"type": kind, "expires_at": now + CHART_TTL}), encoding="utf-8")
    return name


def read_chart(folder, name, now=None):
    if not IMAGE_NAME.fullmatch(name):
        raise FileNotFoundError(name)
    folder = Path(folder)
    metadata = json.loads((folder / (name + ".json")).read_text(encoding="utf-8"))
    if metadata["expires_at"] <= (time() if now is None else now):
        raise FileNotFoundError(name)
    return metadata["type"], (folder / name).read_bytes()


def cleanup_charts(folder, legacy_folder, now=None):
    """Remove expired private files and only recognized legacy generated PNGs."""
    now = time() if now is None else now
    folder, legacy_folder = Path(folder), Path(legacy_folder)
    if folder.is_dir():
        for path in folder.glob("*.png"):
            if not IMAGE_NAME.fullmatch(path.name):
                continue
            metadata_path = folder / (path.name + ".json")
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                expired = metadata["expires_at"] <= now
            except (OSError, ValueError, KeyError, TypeError):
                # A concurrent writer may not have published metadata yet.
                expired = path.stat().st_mtime <= now - CHART_TTL
            if expired:
                path.unlink(missing_ok=True)
                metadata_path.unlink(missing_ok=True)
        for path in folder.glob("*.png.json"):
            if (IMAGE_NAME.fullmatch(path.name[:-5]) and not path.with_suffix("").exists()
                    and path.stat().st_mtime <= now - CHART_TTL):
                path.unlink(missing_ok=True)
    if legacy_folder.is_dir():
        for path in legacy_folder.glob("*.png"):
            if IMAGE_NAME.fullmatch(path.name):
                path.unlink(missing_ok=True)
