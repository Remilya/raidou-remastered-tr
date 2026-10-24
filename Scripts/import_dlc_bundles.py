#!/usr/bin/env python3
"""Build translated PC DLC bundles into the patch update directory."""

from __future__ import annotations

import sys
from pathlib import Path

import import_bundles


ROOT = Path(__file__).resolve().parent.parent
DLC_ROOT = ROOT.parent / "dlc"
DLC_JSON_DIR = ROOT / "Content" / "DLC" / "JSON"
DLC_OUTPUT_ROOT = ROOT / "Patches" / "PC" / "update" / "dlc"


def main() -> int:
    dlc_directories = sorted(
        path for path in DLC_ROOT.iterdir() if path.is_dir() and any(path.glob("*.en"))
    )
    if not dlc_directories:
        print(f"No English DLC bundles found in {DLC_ROOT}")
        return 1

    for dlc_directory in dlc_directories:
        json_directory = DLC_JSON_DIR / dlc_directory.name
        if not json_directory.is_dir() or not any(json_directory.glob("*.json")):
            print(f"Skipping DLC {dlc_directory.name}: no extracted text assets.")
            continue
        result = import_bundles.main(
            [
                "--bundle-dir",
                str(dlc_directory),
                "--json-dir",
                str(json_directory),
                "--no-textures",
                "--skip-ui-patches",
                "--output-dir",
                str(DLC_OUTPUT_ROOT / dlc_directory.name),
                *sys.argv[1:],
            ]
        )
        if result:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
