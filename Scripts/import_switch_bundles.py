#!/usr/bin/env python3
"""Build the Nintendo Switch layered-filesystem translation patch."""

from __future__ import annotations

import sys
from pathlib import Path

import import_bundles


ROOT = Path(__file__).resolve().parent.parent
SWITCH_BUNDLE_DIR = Path(
    r"D:\Games\Emuladores\Citron\user\dump\01002D601ADBA000\romfs\Data\StreamingAssets\AssetBundles"
)
SWITCH_OUTPUT_DIR = (
    ROOT
    / "Patches"
    / "SWITCH"
    / "PT-BR_Phantasie"
    / "romfs"
    / "Data"
    / "StreamingAssets"
    / "AssetBundles"
)


if __name__ == "__main__":
    raise SystemExit(
        import_bundles.main(
            [
                "--bundle-dir",
                str(SWITCH_BUNDLE_DIR),
                "--output-dir",
                str(SWITCH_OUTPUT_DIR),
                *sys.argv[1:],
            ]
        )
    )
