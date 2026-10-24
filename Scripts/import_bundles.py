#!/usr/bin/env python3
"""Inject translated JSON and PNG files into Raidou's English Unity bundles."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

try:
    import UnityPy
    from PIL import Image
except ImportError as exc:  # pragma: no cover - provides a useful one-click error
    raise SystemExit(f"Missing Python dependency: {exc.name}. Install UnityPy and Pillow first.") from exc


ROOT = Path(__file__).resolve().parent.parent
JSON_DIR = ROOT / "Content" / "JSON"
TEXTURE_DIR = ROOT / "Content" / "Texturas"
BACKUP_DIR = ROOT / "Backups" / "Bundles" / "Original"
DEFAULT_BUNDLE_DIR = (
    ROOT.parent
    / "Raidou TMOTSA_Data"
    / "StreamingAssets"
    / "AssetBundles"
)
STANDARD_NAME = re.compile(
    r"-(?P<internal>CAB-[0-9a-f]{32})-(?P<path_id>-?\d+)\.(?P<extension>json|png)$",
    re.IGNORECASE,
)
PATH_ID_SUFFIX = re.compile(r"-(?P<path_id>-?\d+)$")


class BundleImportError(Exception):
    pass


@dataclass(frozen=True)
class SerializedLocation:
    bundle_name: str
    internal_name: str


@dataclass(frozen=True)
class Replacement:
    kind: str
    source: Path
    location: SerializedLocation
    path_id: int


def serialized_files(bundle_file):
    return {
        name: child
        for name, child in bundle_file.files.items()
        if type(child).__name__ == "SerializedFile"
    }


def scan_bundle_index(bundle_dir: Path) -> dict[str, SerializedLocation]:
    bundles = sorted(bundle_dir.glob("*.en"))
    if not bundles:
        raise BundleImportError(f"No .en bundles found in {bundle_dir}")

    index: dict[str, SerializedLocation] = {}
    for bundle_path in bundles:
        try:
            environment = UnityPy.load(bundle_path.read_bytes())
            bundle_file = next(iter(environment.files.values()))
        except Exception as exc:
            raise BundleImportError(f"Cannot load {bundle_path.name}: {exc}") from exc

        for internal_name in serialized_files(bundle_file):
            key = internal_name.lower()
            location = SerializedLocation(bundle_path.name, internal_name)
            if key in index and index[key] != location:
                raise BundleImportError(f"Duplicate serialized filename: {internal_name}")
            index[key] = location
    return index


def resolve_source(path: Path, index: dict[str, SerializedLocation], kind: str) -> Replacement:
    standard = STANDARD_NAME.search(path.name)
    if standard:
        internal_key = standard.group("internal").lower()
        location = index.get(internal_key)
        if location is None:
            raise BundleImportError(f"{path.name}: {standard.group('internal')} was not found in any .en bundle")
        return Replacement(kind, path, location, int(standard.group("path_id")))

    suffix = PATH_ID_SUFFIX.search(path.stem)
    if not suffix:
        raise BundleImportError(f"{path.name}: filename does not contain an asset PathID")
    path_id = int(suffix.group("path_id"))
    stem_without_id = path.stem[: suffix.start()]
    matches = [
        location
        for internal_name, location in index.items()
        if stem_without_id.lower().endswith("-" + internal_name)
    ]
    if len(matches) != 1:
        raise BundleImportError(
            f"{path.name}: could not uniquely determine its internal serialized file"
        )
    return Replacement(kind, path, matches[0], path_id)


def collect_replacements(
    index: dict[str, SerializedLocation],
    json_dir: Path,
    texture_dir: Path | None,
    patch_ui: bool,
) -> dict[str, list[Replacement]]:
    if not json_dir.is_dir():
        raise BundleImportError(f"JSON directory not found: {json_dir}")
    if texture_dir is not None and not texture_dir.is_dir():
        raise BundleImportError(f"Texture directory not found: {texture_dir}")

    replacements = [
        resolve_source(path, index, "json") for path in sorted(json_dir.glob("*.json"))
    ]
    if texture_dir is not None:
        replacements.extend(
            resolve_source(path, index, "texture") for path in sorted(texture_dir.glob("*.png"))
        )
    if not replacements:
        raise BundleImportError("No JSON or PNG replacement files were found")

    seen: set[tuple[str, str, int]] = set()
    grouped: dict[str, list[Replacement]] = defaultdict(list)
    for replacement in replacements:
        identity = (
            replacement.location.bundle_name.lower(),
            replacement.location.internal_name.lower(),
            replacement.path_id,
        )
        if identity in seen:
            raise BundleImportError(
                f"More than one replacement targets {replacement.location.internal_name} PathID {replacement.path_id}"
            )
        seen.add(identity)
        grouped[replacement.location.bundle_name].append(replacement)

    # The localized Save/Load scene stores date fields as separate UI objects.
    if patch_ui:
        if "buildplayer-ui_saveload" not in index:
            raise BundleImportError("Save/Load scene was not found in the .en bundles")
        grouped.setdefault(index["buildplayer-ui_saveload"].bundle_name, [])
    return grouped


def unwrap_exported_arrays(value):
    if isinstance(value, dict) and set(value) == {"Array"}:
        return [unwrap_exported_arrays(item) for item in value["Array"]]
    if isinstance(value, dict):
        return {key: unwrap_exported_arrays(item) for key, item in value.items()}
    if isinstance(value, list):
        return [unwrap_exported_arrays(item) for item in value]
    return value


def merge_text_entries(original, edited, context: str):
    edited_entries = unwrap_exported_arrays(edited)
    if not isinstance(original, list) or not isinstance(edited_entries, list):
        raise BundleImportError(f"{context}: expected text-entry arrays")

    by_id: dict[str, deque[dict]] = defaultdict(deque)
    for item in edited_entries:
        if not isinstance(item, dict):
            raise BundleImportError(f"{context}: source entry is not an object")
        by_id[str(item.get("msgID", ""))].append(item)

    matched = 0
    merged = []
    for original_item in original:
        message_id = str(original_item.get("msgID", ""))
        if by_id[message_id]:
            source_item = by_id[message_id].popleft()
            updated_item = dict(original_item)
            if "msgStr" in source_item:
                updated_item["msgStr"] = source_item["msgStr"]
            merged.append(updated_item)
            matched += 1
        else:
            merged.append(original_item)
    if matched == 0 and original:
        raise BundleImportError(f"{context}: no matching msgIDs were found")
    return merged


def replace_json(reader, source: Path) -> None:
    if reader.type.name != "MonoBehaviour":
        raise BundleImportError(
            f"{source.name}: PathID {reader.path_id} is {reader.type.name}, not MonoBehaviour"
        )
    try:
        edited = json.loads(source.read_text(encoding="utf-8-sig"))
        edited_text = edited["_TextMsgData"]
        tree = reader.read_typetree()
        tree["_TextMsgData"] = merge_text_entries(
            tree["_TextMsgData"], edited_text, f"{source.name}._TextMsgData"
        )
        reader.save_typetree(tree)
    except BundleImportError:
        raise
    except Exception as exc:
        raise BundleImportError(f"{source.name}: could not import JSON: {exc}") from exc


def replace_texture(reader, source: Path) -> None:
    if reader.type.name != "Texture2D":
        raise BundleImportError(
            f"{source.name}: PathID {reader.path_id} is {reader.type.name}, not Texture2D"
        )
    try:
        texture = reader.read()
        mip_count = max(1, int(getattr(texture, "m_MipCount", 1) or 1))
        with Image.open(source) as image:
            image.load()
            texture.set_image(image, target_format=texture.m_TextureFormat, mipmap_count=mip_count)
        texture.save()
    except Exception as exc:
        raise BundleImportError(f"{source.name}: could not import texture: {exc}") from exc


def rect_transform_for_component(serialized, component_pointer: dict):
    component = serialized.objects[component_pointer["m_PathID"]].read_typetree()
    game_object = serialized.objects[component["m_GameObject"]["m_PathID"]].read_typetree()
    for entry in game_object["m_Component"]:
        reader = serialized.objects[entry["component"]["m_PathID"]]
        if reader.type.name == "RectTransform":
            return reader, reader.read_typetree()
    raise BundleImportError(f"{game_object.get('m_Name', '<unnamed>')}: RectTransform is missing")


def patch_saveload_date_layout(files_lower: dict[str, object]) -> int:
    """Change the Save/Load date display from YYYY/MM/DD to DD/MM/YYYY."""
    serialized = files_lower.get("buildplayer-ui_saveload")
    if serialized is None:
        raise BundleImportError("saveload.en: BuildPlayer-UI_saveload is missing")

    patched_slots = 0
    slash_objects: set[int] = set()
    for reader in serialized.objects.values():
        if reader.type.name != "MonoBehaviour":
            continue
        try:
            slot = reader.read_typetree()
        except Exception:
            continue
        if not all(field in slot for field in ("saveYear", "saveMonth", "saveDay")):
            continue

        year_reader, year_rect = rect_transform_for_component(serialized, slot["saveYear"])
        month_reader, month_rect = rect_transform_for_component(serialized, slot["saveMonth"])
        day_reader, day_rect = rect_transform_for_component(serialized, slot["saveDay"])
        year_x = float(year_rect["m_AnchoredPosition"]["x"])
        month_x = float(month_rect["m_AnchoredPosition"]["x"])
        day_x = float(day_rect["m_AnchoredPosition"]["x"])

        if day_x < month_x < year_x:
            patched_slots += 1
            continue
        if not year_x < month_x < day_x:
            raise BundleImportError(
                f"saveload.en: unexpected date layout in slotData PathID {reader.path_id}"
            )

        year_width = float(year_rect["m_SizeDelta"]["x"])
        month_width = float(month_rect["m_SizeDelta"]["x"])
        day_width = float(day_rect["m_SizeDelta"]["x"])
        first_gap = month_x - (year_x + year_width)
        second_gap = day_x - (month_x + month_width)

        # Optical corrections for the EFIGS font and the final group placement.
        # The whole date is shifted 15 px right; the year then receives an
        # additional 5 px left correction.
        group_shift = 15.0
        new_day_x = year_x + 10.0 + group_shift
        base_month_x = year_x + day_width + first_gap + group_shift
        new_month_x = base_month_x + 3.0
        new_year_x = base_month_x + month_width + second_gap - 33.0
        day_rect["m_AnchoredPosition"]["x"] = new_day_x
        month_rect["m_AnchoredPosition"]["x"] = new_month_x
        year_rect["m_AnchoredPosition"]["x"] = new_year_x
        day_reader.save_typetree(day_rect)
        month_reader.save_typetree(month_rect)
        year_reader.save_typetree(year_rect)

        # The slash images use a sibling coordinate space, so move both left by
        # the difference between the four-digit and two-digit field widths.
        slash_shift = year_width - day_width - group_shift
        slot_slashes = []
        for pointer in slot.get("item", []):
            path_id = pointer.get("m_PathID", 0)
            object_reader = serialized.objects.get(path_id)
            if object_reader is None or object_reader.type.name != "GameObject":
                continue
            game_object = object_reader.read_typetree()
            if game_object.get("m_Name") not in {
                "Image__record_slash1",
                "Image__record_slash2",
            }:
                continue
            rect_reader = None
            for component_entry in game_object["m_Component"]:
                candidate = serialized.objects[component_entry["component"]["m_PathID"]]
                if candidate.type.name == "RectTransform":
                    rect_reader = candidate
                    break
            if rect_reader is None:
                raise BundleImportError(f"saveload.en: slash PathID {path_id} has no RectTransform")
            rect = rect_reader.read_typetree()
            rect["m_AnchoredPosition"]["x"] = float(rect["m_AnchoredPosition"]["x"]) - slash_shift
            rect_reader.save_typetree(rect)
            slot_slashes.append(path_id)
            slash_objects.add(path_id)
        if len(slot_slashes) != 2:
            raise BundleImportError(
                f"saveload.en: expected two date slashes in slotData PathID {reader.path_id}"
            )
        patched_slots += 1

    if patched_slots != 22:
        raise BundleImportError(f"saveload.en: expected 22 date slots, found {patched_slots}")
    if slash_objects and len(slash_objects) != 44:
        raise BundleImportError(f"saveload.en: expected 44 date slashes, found {len(slash_objects)}")
    return patched_slots


def verify_saveload_date_layout(files_lower: dict[str, object]) -> None:
    serialized = files_lower["buildplayer-ui_saveload"]
    verified = 0
    for reader in serialized.objects.values():
        if reader.type.name != "MonoBehaviour":
            continue
        try:
            slot = reader.read_typetree()
        except Exception:
            continue
        if not all(field in slot for field in ("saveYear", "saveMonth", "saveDay")):
            continue
        _, year_rect = rect_transform_for_component(serialized, slot["saveYear"])
        _, month_rect = rect_transform_for_component(serialized, slot["saveMonth"])
        _, day_rect = rect_transform_for_component(serialized, slot["saveDay"])
        positions = (
            float(day_rect["m_AnchoredPosition"]["x"]),
            float(month_rect["m_AnchoredPosition"]["x"]),
            float(year_rect["m_AnchoredPosition"]["x"]),
        )
        if not positions[0] < positions[1] < positions[2]:
            raise BundleImportError(
                f"saveload.en: DD/MM/YYYY layout did not verify for PathID {reader.path_id}"
            )
        verified += 1
    if verified != 22:
        raise BundleImportError(f"saveload.en: verified {verified} date slots instead of 22")


def patch_expanded_sprites(
    files_lower: dict[str, object], target_names: set[str], context: str
) -> int:
    """Expand selected Sprite rectangles to their full replacement textures."""
    patched = 0
    for serialized in files_lower.values():
        if not hasattr(serialized, "objects"):
            continue
        for reader in serialized.objects.values():
            if reader.type.name != "Sprite":
                continue
            tree = reader.read_typetree()
            if tree.get("m_Name") not in target_names:
                continue
            texture_id = tree["m_RD"]["texture"]["m_PathID"]
            texture = serialized.objects.get(texture_id)
            if texture is None or texture.type.name != "Texture2D":
                raise BundleImportError(
                    f"{context}: texture for {tree['m_Name']} was not found"
                )
            texture_tree = texture.read_typetree()
            width = float(texture_tree["m_Width"])
            height = float(texture_tree["m_Height"])
            tree["m_RD"]["textureRect"] = {
                "x": 0.0,
                "y": 0.0,
                "width": width,
                "height": height,
            }
            tree["m_RD"]["textureRectOffset"] = {"x": 0.0, "y": 0.0}
            reader.save_typetree(tree)
            patched += 1
    if patched != len(target_names):
        raise BundleImportError(
            f"{context}: expected {len(target_names)} expanded sprites, found {patched}"
        )
    return patched


def verify_expanded_sprites(
    files_lower: dict[str, object], target_names: set[str], context: str
) -> None:
    verified = 0
    for serialized in files_lower.values():
        if not hasattr(serialized, "objects"):
            continue
        for reader in serialized.objects.values():
            if reader.type.name != "Sprite":
                continue
            tree = reader.read_typetree()
            if tree.get("m_Name") not in target_names:
                continue
            texture = serialized.objects[tree["m_RD"]["texture"]["m_PathID"]].read_typetree()
            rect = tree["m_RD"]["textureRect"]
            offset = tree["m_RD"]["textureRectOffset"]
            expected = (0.0, 0.0, float(texture["m_Width"]), float(texture["m_Height"]))
            actual = (
                float(rect["x"]),
                float(rect["y"]),
                float(rect["width"]),
                float(rect["height"]),
            )
            if actual != expected or float(offset["x"]) != 0.0 or float(offset["y"]) != 0.0:
                raise BundleImportError(
                    f"{context}: textureRect did not verify for {tree['m_Name']}"
                )
            verified += 1
    if verified != len(target_names):
        raise BundleImportError(
            f"{context}: verified {verified} expanded sprites instead of {len(target_names)}"
        )


def build_bundle(source_bundle: Path, output_bundle: Path, replacements: list[Replacement]) -> None:
    try:
        # Loading bytes avoids keeping Windows file handles open during atomic replacement/cleanup.
        environment = UnityPy.load(source_bundle.read_bytes())
        bundle_file = next(iter(environment.files.values()))
        files = serialized_files(bundle_file)
        files_lower = {name.lower(): file for name, file in files.items()}

        for replacement in replacements:
            serialized = files_lower.get(replacement.location.internal_name.lower())
            if serialized is None:
                raise BundleImportError(
                    f"{source_bundle.name}: internal file {replacement.location.internal_name} is missing"
                )
            reader = serialized.objects.get(replacement.path_id)
            if reader is None:
                raise BundleImportError(
                    f"{replacement.source.name}: PathID {replacement.path_id} was not found"
                )
            if replacement.kind == "json":
                replace_json(reader, replacement.source)
            else:
                replace_texture(reader, replacement.source)

        if source_bundle.name.lower() == "saveload.en":
            patch_saveload_date_layout(files_lower)
        if source_bundle.name.lower() == "saveloadui_tex.en":
            patch_expanded_sprites(
                files_lower, {"saveload_nodata", "saveload_nodata_sel"}, "saveloadui_tex.en"
            )
        if source_bundle.name.lower() == "maptitle_tex.en":
            patch_expanded_sprites(files_lower, {"m_name014_00"}, "maptitle_tex.en")

        output_bundle.write_bytes(bundle_file.save(packer="original"))
        # Reload the completed file before allowing it to replace the game bundle.
        validated = UnityPy.load(output_bundle.read_bytes())
        validated_bundle = next(iter(validated.files.values()))
        validated_files = {
            name.lower(): file for name, file in serialized_files(validated_bundle).items()
        }
        if source_bundle.name.lower() == "saveload.en":
            verify_saveload_date_layout(validated_files)
        if source_bundle.name.lower() == "saveloadui_tex.en":
            verify_expanded_sprites(
                validated_files, {"saveload_nodata", "saveload_nodata_sel"}, "saveloadui_tex.en"
            )
        if source_bundle.name.lower() == "maptitle_tex.en":
            verify_expanded_sprites(validated_files, {"m_name014_00"}, "maptitle_tex.en")
        for replacement in replacements:
            serialized = validated_files[replacement.location.internal_name.lower()]
            reader = serialized.objects[replacement.path_id]
            if replacement.kind == "json":
                source_tree = json.loads(replacement.source.read_text(encoding="utf-8-sig"))
                rebuilt_text = reader.read_typetree()["_TextMsgData"]
                expected_text = merge_text_entries(
                    rebuilt_text,
                    source_tree["_TextMsgData"],
                    f"{replacement.source.name} verification",
                )
                if rebuilt_text != expected_text:
                    raise BundleImportError(
                        f"{replacement.source.name}: rebuilt JSON did not verify"
                    )
            else:
                texture = reader.read()
                with Image.open(replacement.source) as image:
                    expected_size = image.size
                if (texture.m_Width, texture.m_Height) != expected_size:
                    raise BundleImportError(
                        f"{replacement.source.name}: rebuilt texture dimensions did not verify"
                    )
    except BundleImportError:
        raise
    except Exception as exc:
        raise BundleImportError(f"Could not rebuild {source_bundle.name}: {exc}") from exc


def install(args: argparse.Namespace) -> None:
    bundle_dir = args.bundle_dir.resolve()
    json_dir = args.json_dir.resolve()
    texture_dir = None if args.no_textures else args.texture_dir.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else None
    baseline_dir = args.baseline_dir.resolve() if args.baseline_dir else None
    if args.refresh_originals and (output_dir or baseline_dir):
        raise BundleImportError("--refresh-originals cannot be combined with output/baseline directories")
    if baseline_dir and not baseline_dir.is_dir():
        raise BundleImportError(f"Baseline directory not found: {baseline_dir}")
    index = scan_bundle_index(bundle_dir)
    grouped = collect_replacements(index, json_dir, texture_dir, not args.skip_ui_patches)
    json_count = sum(r.kind == "json" for values in grouped.values() for r in values)
    texture_count = sum(r.kind == "texture" for values in grouped.values() for r in values)
    print(
        f"Matched {json_count} JSON files and {texture_count} textures "
        f"across {len(grouped)} bundles."
    )

    if not args.dry_run and output_dir is None:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        for bundle_name in grouped:
            live = bundle_dir / bundle_name
            backup = BACKUP_DIR / bundle_name
            if args.refresh_originals or not backup.exists():
                shutil.copy2(live, backup)

    staging_parent = ROOT / "Backups" / "Bundles"
    staging_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="build-", dir=staging_parent) as temporary:
        staging = Path(temporary)
        for position, bundle_name in enumerate(sorted(grouped), start=1):
            if baseline_dir:
                baseline = baseline_dir / bundle_name
                if not baseline.is_file():
                    raise BundleImportError(f"Baseline bundle not found: {baseline}")
            elif output_dir:
                baseline = bundle_dir / bundle_name
            elif args.dry_run:
                pristine_backup = BACKUP_DIR / bundle_name
                baseline = pristine_backup if pristine_backup.exists() else bundle_dir / bundle_name
            else:
                baseline = BACKUP_DIR / bundle_name
            output = staging / bundle_name
            print(f"[{position}/{len(grouped)}] Building {bundle_name}...")
            build_bundle(baseline, output, grouped[bundle_name])

        if args.dry_run:
            print("Validation build succeeded; game files were not changed.")
            return

        destination_dir = output_dir or bundle_dir
        destination_dir.mkdir(parents=True, exist_ok=True)
        for bundle_name in sorted(grouped):
            destination = destination_dir / bundle_name
            temporary_destination = destination.with_name(destination.name + ".translation.tmp")
            try:
                shutil.copy2(staging / bundle_name, temporary_destination)
                os.replace(temporary_destination, destination)
            finally:
                if temporary_destination.exists():
                    temporary_destination.unlink()
        if output_dir:
            print(f"Wrote {len(grouped)} rebuilt bundles to: {output_dir}")
        else:
            print(f"Installed {len(grouped)} rebuilt bundles successfully.")
            print(f"Original bundle backups: {BACKUP_DIR}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle-dir",
        type=Path,
        default=DEFAULT_BUNDLE_DIR,
        help=f"AssetBundles directory (default: {DEFAULT_BUNDLE_DIR})",
    )
    parser.add_argument(
        "--json-dir",
        type=Path,
        default=JSON_DIR,
        help=f"Directory containing JSON replacements (default: {JSON_DIR})",
    )
    parser.add_argument(
        "--texture-dir",
        type=Path,
        default=TEXTURE_DIR,
        help=f"Directory containing PNG replacements (default: {TEXTURE_DIR})",
    )
    parser.add_argument(
        "--no-textures",
        action="store_true",
        help="Do not collect PNG replacements",
    )
    parser.add_argument(
        "--skip-ui-patches",
        action="store_true",
        help="Skip the base-game Save/Load layout and sprite patches",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and validate every target bundle without changing the game",
    )
    parser.add_argument(
        "--refresh-originals",
        action="store_true",
        help="Replace stored pristine backups with the current game bundles",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Write rebuilt bundles here instead of modifying the source bundle directory",
    )
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        help="Read pristine target bundles from this directory while using --bundle-dir for indexing",
    )
    args = parser.parse_args(argv)
    try:
        install(args)
    except (BundleImportError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
