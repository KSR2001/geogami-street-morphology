"""Smoke-test the Phase 5 software environment and frozen raw inputs.

This script intentionally performs no geometry reconstruction or analysis.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import geopandas
import matplotlib
import networkx
import numpy
import osmnx
import pandas
import pyproj
import pytest
import scipy
import shapely


EXPECTED_PYTHON = (3, 12)
EXPECTED_OSMNX = "2.1.1"
EXPECTED_RAW = {
    "env38_bezier.json": {
        "environment_id": 38,
        "shape_count": 5,
        "total_segment_count": 120,
        "sha256": "43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819",
    },
    "env39_bezier.json": {
        "environment_id": 39,
        "shape_count": 1,
        "total_segment_count": 32,
        "sha256": "e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602",
    },
}


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without changing it."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    raw_directory = repository_root / "data" / "raw"
    errors: list[str] = []

    versions = {
        "Python": platform.python_version(),
        "OSMnx": osmnx.__version__,
        "GeoPandas": geopandas.__version__,
        "Shapely": shapely.__version__,
        "NetworkX": networkx.__version__,
        "NumPy": numpy.__version__,
        "pandas": pandas.__version__,
        "SciPy": scipy.__version__,
        "Matplotlib": matplotlib.__version__,
        "pyproj": pyproj.__version__,
        "pytest": pytest.__version__,
    }

    print("Resolved software versions:")
    for name, version in versions.items():
        print(f"  {name}: {version}")

    if sys.version_info[:2] != EXPECTED_PYTHON:
        errors.append(
            f"Python major/minor is {sys.version_info.major}.{sys.version_info.minor}; "
            f"expected {EXPECTED_PYTHON[0]}.{EXPECTED_PYTHON[1]}"
        )
    if osmnx.__version__ != EXPECTED_OSMNX:
        errors.append(f"OSMnx is {osmnx.__version__}; expected {EXPECTED_OSMNX}")

    manifest_path = raw_directory / "manifest.json"
    if not manifest_path.is_file():
        errors.append(f"Missing required raw manifest: {manifest_path}")
    else:
        try:
            with manifest_path.open("r", encoding="utf-8") as source:
                manifest = json.load(source)
            if not isinstance(manifest, dict):
                errors.append("data/raw/manifest.json does not contain a JSON object")
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"Could not parse data/raw/manifest.json: {exc}")

    hash_checks_passed = True
    for filename, expected in EXPECTED_RAW.items():
        path = raw_directory / filename
        if not path.is_file():
            errors.append(f"Missing canonical raw file: {path}")
            hash_checks_passed = False
            continue

        try:
            with path.open("r", encoding="utf-8") as source:
                data = json.load(source)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"Could not parse {path}: {exc}")
            hash_checks_passed = False
            continue

        for field in ("environment_id", "shape_count", "total_segment_count"):
            actual = data.get(field)
            if actual != expected[field]:
                errors.append(
                    f"{filename} {field} is {actual!r}; expected {expected[field]!r}"
                )

        actual_hash = sha256_file(path)
        if actual_hash != expected["sha256"]:
            errors.append(
                f"{filename} SHA-256 is {actual_hash}; expected {expected['sha256']}"
            )
            hash_checks_passed = False

    print(
        "Canonical raw hash verification: "
        + ("PASS" if hash_checks_passed else "FAIL")
    )

    if errors:
        print("Environment smoke test: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("Environment smoke test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
