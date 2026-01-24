#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION_FILE = ROOT / "VERSION"
PYPROJECT_FILE = ROOT / "pyproject.toml"
PACKAGE_JSON_FILE = ROOT / "package.json"

SEMVER_RE = re.compile(r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$")


def read_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def write_version(version: str) -> None:
    VERSION_FILE.write_text(f"{version}\n", encoding="utf-8")


def bump(version: str, part: str) -> str:
    m = SEMVER_RE.match(version)
    if not m:
        raise ValueError(f"Invalid version in VERSION: {version!r}")

    major = int(m.group("major"))
    minor = int(m.group("minor"))
    patch = int(m.group("patch"))

    if part == "patch":
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError("part must be one of: patch, minor, major")

    return f"{major}.{minor}.{patch}"


def replace_version_in_pyproject(version: str) -> None:
    if not PYPROJECT_FILE.exists():
        return
    content = PYPROJECT_FILE.read_text(encoding="utf-8")
    new_content, n = re.subn(r"(?m)^(version\s*=\s*)\"[^\"]+\"\s*$", rf'\g<1>"{version}"', content)
    if n == 0:
        raise RuntimeError("Could not find project version in pyproject.toml")
    PYPROJECT_FILE.write_text(new_content, encoding="utf-8")


def replace_version_in_package_json(version: str) -> None:
    if not PACKAGE_JSON_FILE.exists():
        return
    data = json.loads(PACKAGE_JSON_FILE.read_text(encoding="utf-8"))
    data["version"] = version
    PACKAGE_JSON_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"patch", "minor", "major"}:
        print("Usage: python bump_version.py [patch|minor|major]", file=sys.stderr)
        return 2

    part = sys.argv[1]
    current = read_version()
    new = bump(current, part)

    write_version(new)
    replace_version_in_pyproject(new)
    replace_version_in_package_json(new)

    print(new)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
