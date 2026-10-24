#!/usr/bin/env python3
"""Extract English DLC TextMsgData assets into editable JSON files."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

try:
    import UnityPy
except ImportError as exc:  # pragma: no cover
    raise SystemExit("UnityPy is required to extract DLC text bundles.") from exc


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DLC_DIR = ROOT.parent / "dlc"
OUTPUT_DIR = ROOT / "Content" / "DLC" / "JSON"


def extract(dlc_dir: Path = DEFAULT_DLC_DIR) -> int:
    bundles = sorted(dlc_dir.rglob("*.en"))
    if not bundles:
        print(f"Error: no .en DLC bundles found in {dlc_dir}", file=sys.stderr)
        return 1

    staging = OUTPUT_DIR.with_name("JSON.extracting")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    extracted = 0

    try:
        for bundle_path in bundles:
            try:
                dlc_id = bundle_path.relative_to(dlc_dir).parts[0]
            except (ValueError, IndexError):
                dlc_id = bundle_path.parent.name
            bundle_output = staging / dlc_id
            bundle_output.mkdir(parents=True, exist_ok=True)
            environment = UnityPy.load(bundle_path.read_bytes())
            bundle_file = next(iter(environment.files.values()))
            serialized_files = [
                (name, child)
                for name, child in bundle_file.files.items()
                if type(child).__name__ == "SerializedFile"
            ]
            for internal_name, serialized in serialized_files:
                for reader in serialized.objects.values():
                    if reader.type.name != "MonoBehaviour":
                        continue
                    tree = reader.read_typetree()
                    if "_TextMsgData" not in tree:
                        continue
                    text_data = tree["_TextMsgData"]
                    if isinstance(text_data, list):
                        tree["_TextMsgData"] = {"Array": text_data}
                    asset_name = str(tree.get("m_Name", "TextMsgData"))
                    filename = f"DLC{dlc_id}-{asset_name}-{internal_name}-{reader.path_id}.json"
                    (bundle_output / filename).write_text(
                        json.dumps(tree, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8-sig",
                        newline="\n",
                    )
                    extracted += 1

        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)
        staging.replace(OUTPUT_DIR)
    finally:
        if staging.exists():
            shutil.rmtree(staging)

    print(f"Extracted {extracted} text assets from {len(bundles)} English DLC bundles.")
    print(f"Output: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(extract())
