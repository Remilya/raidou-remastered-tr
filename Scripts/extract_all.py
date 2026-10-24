#!/usr/bin/env python3
"""Extract all TextMsgData JSONs (base game + DLC) and optionally Texture2D PNGs from Raidou .en bundles."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

try:
    import UnityPy
except ImportError as exc:
    raise SystemExit("UnityPy is required. Run: py -3.12 -m pip install UnityPy Pillow") from exc


ROOT = Path(__file__).resolve().parent.parent
STEAM_GAME_DIR = Path(r"D:\SteamLibrary\steamapps\common\Raidou TMOTSA")
RELEASE_UPDATE_DIR = ROOT.parent / "Raidou_PC_Release" / "update"

DEFAULT_BASE_BUNDLE_DIR = (
    STEAM_GAME_DIR / "Raidou TMOTSA_Data" / "StreamingAssets" / "AssetBundles"
    if (STEAM_GAME_DIR / "Raidou TMOTSA_Data" / "StreamingAssets" / "AssetBundles").is_dir()
    else RELEASE_UPDATE_DIR / "Raidou TMOTSA_Data" / "StreamingAssets" / "AssetBundles"
)
DEFAULT_DLC_DIR = (
    STEAM_GAME_DIR / "dlc"
    if (STEAM_GAME_DIR / "dlc").is_dir()
    else RELEASE_UPDATE_DIR / "dlc"
)

BASE_JSON_DIR = ROOT / "Content" / "JSON"
DLC_JSON_DIR = ROOT / "Content" / "DLC" / "JSON"
TEXTURE_DIR = ROOT / "Content" / "Texturas"

BACKUP_BASE_DIR = ROOT / "Backups" / "Bundles" / "Original"
BACKUP_DLC_DIR = ROOT / "Backups" / "DLC" / "Original"


def sanitize_name(name: str) -> str:
    invalid = '<>:"/\\|?*'
    cleaned = "".join("_" if ch in invalid else ch for ch in name.strip())
    return cleaned or "Asset"


def extract_base_bundles(
    bundle_dir: Path, extract_textures: bool = False, overwrite: bool = False
) -> tuple[int, int]:
    bundles = sorted(bundle_dir.glob("*.en"))
    if not bundles:
        raise RuntimeError(f"No .en bundles found in {bundle_dir}")

    if overwrite:
        if BASE_JSON_DIR.exists():
            shutil.rmtree(BASE_JSON_DIR)
        if BACKUP_BASE_DIR.exists():
            shutil.rmtree(BACKUP_BASE_DIR)
        if extract_textures and TEXTURE_DIR.exists():
            shutil.rmtree(TEXTURE_DIR)

    BASE_JSON_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_BASE_DIR.mkdir(parents=True, exist_ok=True)
    if extract_textures:
        TEXTURE_DIR.mkdir(parents=True, exist_ok=True)

    json_count = 0
    tex_count = 0

    for bundle_path in bundles:
        backup_target = BACKUP_BASE_DIR / bundle_path.name
        if overwrite or not backup_target.exists():
            shutil.copy2(bundle_path, backup_target)

        environment = UnityPy.load(bundle_path.read_bytes())
        bundle_file = next(iter(environment.files.values()))
        serialized_files = [
            (name, child)
            for name, child in bundle_file.files.items()
            if type(child).__name__ == "SerializedFile"
        ]
        for internal_name, serialized in serialized_files:
            for reader in serialized.objects.values():
                if reader.type.name == "MonoBehaviour":
                    try:
                        tree = reader.read_typetree()
                    except Exception:
                        continue
                    if "_TextMsgData" not in tree:
                        continue
                    text_data = tree["_TextMsgData"]
                    if isinstance(text_data, list):
                        tree["_TextMsgData"] = {"Array": text_data}
                    asset_name = sanitize_name(str(tree.get("m_Name", "TextMsgData")))
                    filename = f"{asset_name}-{internal_name}-{reader.path_id}.json"
                    (BASE_JSON_DIR / filename).write_text(
                        json.dumps(tree, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8-sig",
                        newline="\n",
                    )
                    json_count += 1
                elif extract_textures and reader.type.name == "Texture2D":
                    try:
                        tex = reader.read()
                        asset_name = sanitize_name(str(getattr(tex, "m_Name", "Texture2D")))
                        filename = f"{asset_name}-{internal_name}-{reader.path_id}.png"
                        tex.image.save(TEXTURE_DIR / filename)
                        tex_count += 1
                    except Exception as exc:
                        print(
                            f"Warning: could not extract texture PathID {reader.path_id} in {bundle_path.name}: {exc}",
                            file=sys.stderr,
                        )
    return json_count, tex_count


def extract_dlc_bundles(dlc_dir: Path, overwrite: bool = False) -> int:
    bundles = sorted(dlc_dir.rglob("*.en"))
    if not bundles:
        print(f"Warning: no .en DLC bundles found in {dlc_dir}", file=sys.stderr)
        return 0

    DLC_JSON_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DLC_DIR.mkdir(parents=True, exist_ok=True)
    extracted = 0

    for bundle_path in bundles:
        try:
            dlc_id = bundle_path.relative_to(dlc_dir).parts[0]
        except (ValueError, IndexError):
            dlc_id = bundle_path.parent.name

        backup_sub = BACKUP_DLC_DIR / dlc_id
        backup_sub.mkdir(parents=True, exist_ok=True)
        backup_target = backup_sub / bundle_path.name
        if overwrite or not backup_target.exists():
            shutil.copy2(bundle_path, backup_target)

        bundle_output = DLC_JSON_DIR / dlc_id
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
                try:
                    tree = reader.read_typetree()
                except Exception:
                    continue
                if "_TextMsgData" not in tree:
                    continue
                text_data = tree["_TextMsgData"]
                if isinstance(text_data, list):
                    tree["_TextMsgData"] = {"Array": text_data}
                asset_name = sanitize_name(str(tree.get("m_Name", "TextMsgData")))
                filename = f"DLC{dlc_id}-{asset_name}-{internal_name}-{reader.path_id}.json"
                (bundle_output / filename).write_text(
                    json.dumps(tree, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8-sig",
                    newline="\n",
                )
                extracted += 1
    return extracted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", type=Path, default=DEFAULT_BASE_BUNDLE_DIR)
    parser.add_argument("--dlc-dir", type=Path, default=DEFAULT_DLC_DIR)
    parser.add_argument(
        "--extract-textures",
        action="store_true",
        help="Also extract Texture2D assets as PNG",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing backups, JSONs, and textures with fresh extraction",
    )
    args = parser.parse_args()

    print(f"Extracting base bundles from: {args.base_dir}")
    print(f"Extracting DLC bundles from:  {args.dlc_dir}")
    base_jsons, base_tex = extract_base_bundles(
        args.base_dir, args.extract_textures, overwrite=args.overwrite
    )
    dlc_jsons = extract_dlc_bundles(args.dlc_dir, overwrite=args.overwrite)
    print(f"Base game JSONs extracted: {base_jsons} -> {BASE_JSON_DIR}")
    if args.extract_textures:
        print(f"Base game Textures extracted: {base_tex} -> {TEXTURE_DIR}")
    print(f"DLC JSONs extracted: {dlc_jsons} -> {DLC_JSON_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
