"""Package a Home Assistant integration snapshot from a Git tag."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path


COMPONENT = "custom_components/alarm_system"
VERSION_PATTERN = re.compile(r"\A[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\Z")


def git(*args, text=True):
    result = subprocess.run(["git", *args], check=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=text)
    return result.stdout


def package(ref, output_dir):
    tag_ref = f"refs/tags/{ref}"
    try:
        git("show-ref", "--verify", "--quiet", tag_ref)
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"'{ref}' is not an existing local Git tag") from exc

    manifest = json.loads(git("show", f"{tag_ref}:{COMPONENT}/manifest.json"))
    version = manifest.get("version")
    if not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
        raise ValueError("Tagged manifest version must be numeric major.minor.patch with optional pre-release/build metadata")

    names = git("ls-tree", "-r", "-z", "--name-only", tag_ref, "--", COMPONENT).split("\0")
    paths = [name for name in names if name and not any(
        part == "__pycache__" for part in name.split("/"))
        and not name.endswith((".pyc", ".pyo"))]
    if not paths:
        raise ValueError("Tag contains no component files")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"alarm_system-{version}.zip"
    if archive.exists():
        raise FileExistsError(f"Refusing to overwrite {archive}")

    raw = archive.open("xb")
    try:
        with raw:
            with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                for name in paths:
                    content = git("show", f"{tag_ref}:{name}", text=False)
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    bundle.writestr(info, content)
    except Exception:
        archive.unlink(missing_ok=True)
        raise
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    return archive, digest, version


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", required=True, help="existing local Git tag")
    parser.add_argument("--output-dir", default="dist", help="destination directory (default: dist)")
    args = parser.parse_args(argv)
    try:
        archive, digest, version = package(args.ref, args.output_dir)
    except (ValueError, FileExistsError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Created {archive} (version {version}, sha256 {digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
