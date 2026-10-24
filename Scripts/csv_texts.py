#!/usr/bin/env python3
"""Export categorized Raidou JSON text to CSV and import edited text back."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from collections import Counter, defaultdict, deque
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
JSON_DIR = ROOT / "Content" / "JSON"
DLC_JSON_DIR = ROOT / "Content" / "DLC" / "JSON"
JSON_DIRS = (JSON_DIR, DLC_JSON_DIR)
MANIFEST = ROOT / "Config" / "JSON_Categories.json"
DIALOGUE_CSV = ROOT / "Spreadsheets" / "Dialogue.csv"
TEXT_CSV = ROOT / "Spreadsheets" / "Text.csv"
PLACEHOLDERS = {"", "NULL", "ER100"}
COMMAND_ONLY = re.compile(r"^\s*(?:<[^<>]+>\s*)+$", re.DOTALL)
DLC_JSON_NAME = re.compile(r"^DLC\d{4}-")


class ImportValidationError(Exception):
    pass


def load_json(path: Path) -> tuple[dict, bool, bool]:
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    has_final_newline = raw.endswith((b"\n", b"\r"))
    return json.loads(raw.decode("utf-8-sig")), has_bom, has_final_newline


def entries(document: dict, filename: str) -> list[dict]:
    try:
        value = document["_TextMsgData"]["Array"]
    except (KeyError, TypeError) as exc:
        raise ImportValidationError(f"{filename}: missing _TextMsgData.Array") from exc
    if not isinstance(value, list):
        raise ImportValidationError(f"{filename}: _TextMsgData.Array is not a list")
    return value


def json_path(filename: str) -> Path:
    matches = [
        path
        for directory in JSON_DIRS
        if directory.is_dir()
        for path in directory.rglob(filename)
        if path.is_file()
    ]
    if len(matches) != 1:
        raise ImportValidationError(
            f"{filename}: expected exactly one source JSON file, found {len(matches)}"
        )
    return matches[0]


def load_manifest() -> tuple[list[str], list[str]]:
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
        dialogue_files = list(manifest["dialogues"])
        common_files = list(manifest["commonTexts"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ImportValidationError(f"Cannot read {MANIFEST.name}: {exc}") from exc

    categorized = dialogue_files + common_files
    if len(categorized) != len(set(categorized)):
        raise ImportValidationError(f"{MANIFEST.name} contains duplicate filenames")

    actual_paths = [path for directory in JSON_DIRS if directory.is_dir() for path in directory.rglob("*.json")]
    actual = {path.name for path in actual_paths}
    if len(actual) != len(actual_paths):
        raise ImportValidationError("Duplicate JSON filenames exist across Content source directories")
    missing = set(categorized) - actual
    uncategorized = actual - set(categorized)
    if missing or uncategorized:
        details = []
        if missing:
            details.append("missing: " + ", ".join(sorted(missing)))
        if uncategorized:
            details.append("uncategorized: " + ", ".join(sorted(uncategorized)))
        raise ImportValidationError("Manifest/source mismatch (" + "; ".join(details) + ")")
    return dialogue_files, common_files


def has_lowercase(value: object) -> bool:
    return any(character.islower() for character in str(value))


def is_real_text(value: object) -> bool:
    return value is not None and str(value).strip() not in PLACEHOLDERS


def should_export_text(value: object) -> bool:
    """Exclude placeholders and records made entirely of angle-bracket commands."""
    return is_real_text(value) and COMMAND_ONLY.fullmatch(str(value)) is None


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    # utf-8-sig makes non-ASCII text open correctly in Excel without an import wizard.
    with path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_dialogue_rows(dialogue_files: list[str]) -> list[dict[str, str]]:
    dialogue_rows: list[dict[str, str]] = []

    for filename in dialogue_files:
        document, _, _ = load_json(json_path(filename))
        data = entries(document, filename)
        active_speaker: tuple[str, str] | None = None
        for index, item in enumerate(data):
            message_id = str(item.get("msgID", ""))
            if has_lowercase(message_id):
                active_speaker = None
                if is_real_text(item.get("msgStr")):
                    next_text = data[index + 1].get("msgStr") if index + 1 < len(data) else None
                    next_id = str(data[index + 1].get("msgID", "")) if index + 1 < len(data) else ""
                    if should_export_text(next_text) and not has_lowercase(next_id):
                        active_speaker = (message_id, str(item.get("msgStr", "")))
                    else:
                        dialogue_rows.append(
                            {
                                "JsonFile": filename,
                                "msgID": f"{message_id}/",
                                "Speaker": str(item.get("msgStr", "")),
                                "Dialogue": "",
                                "Translation": "",
                            }
                        )
                continue
            if not should_export_text(item.get("msgStr")):
                continue

            speaker = ""
            output_id = message_id
            if active_speaker is not None:
                speaker_id, speaker = active_speaker
                output_id = f"{speaker_id}/{message_id}"

            dialogue_rows.append(
                {
                    "JsonFile": filename,
                    "msgID": output_id,
                    "Speaker": speaker,
                    "Dialogue": str(item.get("msgStr", "")),
                    "Translation": "",
                }
            )

    return dialogue_rows


def build_text_rows(common_files: list[str]) -> list[dict[str, str]]:
    text_rows: list[dict[str, str]] = []
    for filename in common_files:
        document, _, _ = load_json(json_path(filename))
        for item in entries(document, filename):
            if not should_export_text(item.get("msgStr")):
                continue
            text_rows.append(
                {
                    "JsonFile": filename,
                    "msgID": str(item.get("msgID", "")),
                    "msgStr": str(item.get("msgStr", "")),
                    "Translation": "",
                }
            )
    return text_rows


def sync_csv_rows() -> None:
    """Add newly discovered text rows without disturbing existing CSV edits."""
    dialogue_files, common_files = load_manifest()
    existing_rows = read_csv(
        DIALOGUE_CSV, ["JsonFile", "msgID", "Speaker", "Dialogue", "Translation"]
    )
    # Continuation labels are useful for the compact DLC conversations. Keep
    # base-game rows in their established one-speaker/one-dialogue format.
    source_indices: dict[str, dict[str, int]] = {}
    dissociated = 0
    for row in existing_rows:
        if DLC_JSON_NAME.match(row["JsonFile"]) or "/" not in row["msgID"]:
            continue
        speaker_id, dialogue_id = row["msgID"].split("/", 1)
        if not dialogue_id:
            continue
        if row["JsonFile"] not in source_indices:
            document, _, _ = load_json(json_path(row["JsonFile"]))
            source_indices[row["JsonFile"]] = {
                str(item.get("msgID", "")): index
                for index, item in enumerate(entries(document, row["JsonFile"]))
            }
        indices = source_indices[row["JsonFile"]]
        if indices.get(dialogue_id) != indices.get(speaker_id, -2) + 1:
            row["msgID"] = dialogue_id
            row["Speaker"] = ""
            dissociated += 1

    generated_dialogue = build_dialogue_rows(dialogue_files)
    generated_by_dialogue = {
        (row["JsonFile"], row["msgID"].split("/", 1)[1]): row
        for row in generated_dialogue
        if "/" in row["msgID"] and not row["msgID"].endswith("/")
    }
    edited_speakers = {
        (row["JsonFile"], row["msgID"].split("/", 1)[0]): row["Speaker"]
        for row in existing_rows
        if "/" in row["msgID"] and row["Speaker"]
    }
    upgraded = 0
    for row in existing_rows:
        if (
            not DLC_JSON_NAME.match(row["JsonFile"])
            or "/" in row["msgID"]
            or row["Speaker"]
        ):
            continue
        generated = generated_by_dialogue.get((row["JsonFile"], row["msgID"]))
        if generated is None:
            continue
        speaker_id = generated["msgID"].split("/", 1)[0]
        row["msgID"] = generated["msgID"]
        row["Speaker"] = edited_speakers.get(
            (row["JsonFile"], speaker_id), generated["Speaker"]
        )
        upgraded += 1

    existing_counts = Counter((row["JsonFile"], row["msgID"]) for row in existing_rows)
    existing_files = {row["JsonFile"] for row in existing_rows}
    generated_counts: Counter[tuple[str, str]] = Counter()
    merged_rows = [
        {
            "JsonFile": row["JsonFile"],
            "msgID": row["msgID"],
            "Speaker": row["Speaker"],
            "Dialogue": row["Dialogue"],
            "Translation": row["Translation"],
        }
        for row in existing_rows
    ]
    dialogue_added = 0
    for generated in generated_dialogue:
        key = (generated["JsonFile"], generated["msgID"])
        generated_counts[key] += 1
        is_new_file = generated["JsonFile"] not in existing_files
        is_standalone_speaker = generated["msgID"].endswith("/")
        if generated_counts[key] > existing_counts[key] and (is_new_file or is_standalone_speaker):
            if generated["Speaker"] == "Herald of Yatagarasu":
                generated["Speaker"] = "Arauto de Yatagarasu"
            merged_rows.append(generated)
            existing_counts[key] += 1
            dialogue_added += 1

    write_csv(
        DIALOGUE_CSV,
        ["JsonFile", "msgID", "Speaker", "Dialogue", "Translation"],
        merged_rows,
    )

    existing_text = read_csv(TEXT_CSV, ["JsonFile", "msgID", "msgStr", "Translation"])
    text_counts = Counter((row["JsonFile"], row["msgID"]) for row in existing_text)
    existing_files = {row["JsonFile"] for row in existing_text}
    generated_counts.clear()
    text_added = 0
    for generated in build_text_rows(common_files):
        key = (generated["JsonFile"], generated["msgID"])
        generated_counts[key] += 1
        if generated_counts[key] > text_counts[key] and generated["JsonFile"] not in existing_files:
            existing_text.append(generated)
            text_counts[key] += 1
            text_added += 1
    write_csv(TEXT_CSV, ["JsonFile", "msgID", "msgStr", "Translation"], existing_text)
    print(
        f"Added {dialogue_added} dialogue and {text_added} common-text row(s); "
        f"associated {upgraded} DLC continuation dialogue(s) with their speakers"
        + (f" and restored {dissociated} base-game row(s)." if dissociated else ".")
    )


def export_csv() -> None:
    dialogue_files, common_files = load_manifest()
    dialogue_rows = build_dialogue_rows(dialogue_files)
    text_rows = build_text_rows(common_files)

    write_csv(
        DIALOGUE_CSV,
        ["JsonFile", "msgID", "Speaker", "Dialogue", "Translation"],
        dialogue_rows,
    )
    write_csv(TEXT_CSV, ["JsonFile", "msgID", "msgStr", "Translation"], text_rows)
    print(f"Wrote {DIALOGUE_CSV.name}: {len(dialogue_rows)} rows from {len(dialogue_files)} files")
    print(f"Wrote {TEXT_CSV.name}: {len(text_rows)} rows from {len(common_files)} files")


def read_csv(path: Path, required_fields: list[str]) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            missing_fields = set(required_fields) - set(reader.fieldnames or [])
            if missing_fields:
                raise ImportValidationError(
                    f"{path.name}: missing column(s): {', '.join(sorted(missing_fields))}"
                )
            return [dict(row) for row in reader]
    except OSError as exc:
        raise ImportValidationError(f"Cannot read {path.name}: {exc}") from exc


def group_rows(rows: list[dict[str, str]], allowed_files: set[str], csv_name: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row_number, row in enumerate(rows, start=2):
        filename = row.get("JsonFile", "")
        if filename not in allowed_files:
            raise ImportValidationError(
                f"{csv_name} row {row_number}: unknown or incorrectly categorized JsonFile {filename!r}"
            )
        row["_row_number"] = str(row_number)
        grouped[filename].append(row)
    return grouped


def build_occurrences(data: list[dict]) -> dict[str, deque[int]]:
    result: dict[str, deque[int]] = defaultdict(deque)
    for index, item in enumerate(data):
        result[str(item.get("msgID", ""))].append(index)
    return result


def take_occurrence(
    occurrences: dict[str, deque[int]], message_id: str, csv_name: str, row_number: str, filename: str
) -> int:
    if not occurrences[message_id]:
        raise ImportValidationError(
            f"{csv_name} row {row_number}: msgID {message_id!r} not found (or used too many times) in {filename}"
        )
    return occurrences[message_id].popleft()


def import_csv() -> None:
    dialogue_files, common_files = load_manifest()
    dialogue_rows = read_csv(
        DIALOGUE_CSV, ["JsonFile", "msgID", "Speaker", "Dialogue", "Translation"]
    )
    text_rows = read_csv(TEXT_CSV, ["JsonFile", "msgID", "msgStr", "Translation"])
    grouped_dialogue = group_rows(dialogue_rows, set(dialogue_files), DIALOGUE_CSV.name)
    grouped_text = group_rows(text_rows, set(common_files), TEXT_CSV.name)

    loaded: dict[str, tuple[dict, bool, bool]] = {}
    changed: set[str] = set()

    for filename in dialogue_files:
        document_info = load_json(json_path(filename))
        loaded[filename] = document_info
        data = entries(document_info[0], filename)
        occurrences = build_occurrences(data)
        all_indices = {message_id: list(indices) for message_id, indices in occurrences.items()}
        speaker_edits: dict[int, str] = {}

        for row in grouped_dialogue.get(filename, []):
            combined_id = row["msgID"]
            if "/" in combined_id:
                speaker_id, dialogue_id = combined_id.split("/", 1)
                if dialogue_id:
                    dialogue_index = take_occurrence(
                        occurrences, dialogue_id, DIALOGUE_CSV.name, row["_row_number"], filename
                    )
                    preceding_speakers = [
                        index for index in all_indices.get(speaker_id, []) if index < dialogue_index
                    ]
                    if not preceding_speakers:
                        raise ImportValidationError(
                            f"{DIALOGUE_CSV.name} row {row['_row_number']}: speaker ID "
                            f"{speaker_id!r} was not found before {dialogue_id!r} in {filename}"
                        )
                    speaker_index = preceding_speakers[-1]
                else:
                    speaker_index = take_occurrence(
                        occurrences, speaker_id, DIALOGUE_CSV.name, row["_row_number"], filename
                    )
                previous_edit = speaker_edits.get(speaker_index)
                if previous_edit is not None and previous_edit != row["Speaker"]:
                    raise ImportValidationError(
                        f"{DIALOGUE_CSV.name} row {row['_row_number']}: inconsistent Speaker "
                        f"for repeated speaker ID {speaker_id!r} in {filename}"
                    )
                speaker_edits[speaker_index] = row["Speaker"]
                if data[speaker_index].get("msgStr") != row["Speaker"]:
                    data[speaker_index]["msgStr"] = row["Speaker"]
                    changed.add(filename)
                if not dialogue_id:
                    if row["Dialogue"] or row["Translation"]:
                        raise ImportValidationError(
                            f"{DIALOGUE_CSV.name} row {row['_row_number']}: standalone speaker rows must have blank Dialogue and Translation"
                        )
                    continue
            else:
                dialogue_id = combined_id
                dialogue_index = take_occurrence(
                    occurrences, dialogue_id, DIALOGUE_CSV.name, row["_row_number"], filename
                )
                if row["Speaker"]:
                    raise ImportValidationError(
                        f"{DIALOGUE_CSV.name} row {row['_row_number']}: Speaker must be blank when msgID has no speaker ID"
                    )

            translated_dialogue = row["Translation"] if row["Translation"] else row["Dialogue"]
            if data[dialogue_index].get("msgStr") != translated_dialogue:
                data[dialogue_index]["msgStr"] = translated_dialogue
                changed.add(filename)

    for filename in common_files:
        document_info = load_json(json_path(filename))
        loaded[filename] = document_info
        data = entries(document_info[0], filename)
        occurrences = build_occurrences(data)

        for row in grouped_text.get(filename, []):
            item_index = take_occurrence(
                occurrences, row["msgID"], TEXT_CSV.name, row["_row_number"], filename
            )
            translated_text = row["Translation"] if row["Translation"] else row["msgStr"]
            if data[item_index].get("msgStr") != translated_text:
                data[item_index]["msgStr"] = translated_text
                changed.add(filename)

    if not changed:
        print("No JSON text changes were found.")
        return

    backup_dir = ROOT / "Backups" / "JSON" / datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir.mkdir(parents=True)
    for filename in sorted(changed):
        source_path = json_path(filename)
        shutil.copy2(source_path, backup_dir / filename)

    for filename in sorted(changed):
        document, has_bom, has_final_newline = loaded[filename]
        serialized = json.dumps(document, ensure_ascii=False, indent=2)
        if has_final_newline:
            serialized += "\n"
        encoding = "utf-8-sig" if has_bom else "utf-8"
        target = json_path(filename)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(serialized, encoding=encoding, newline="\n")
        temporary.replace(target)

    print(f"Updated {len(changed)} JSON file(s).")
    print(f"Backups: {backup_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("export", "import", "sync", "sync-speakers"))
    arguments = parser.parse_args()
    try:
        if arguments.command == "export":
            export_csv()
        elif arguments.command == "import":
            import_csv()
        else:
            sync_csv_rows()
    except (ImportValidationError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
