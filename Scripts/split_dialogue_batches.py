#!/usr/bin/env python3
"""Split Dialogue.csv unique dialogue strings into 10 batches for parallel translation and merge back."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIALOGUE_CSV = ROOT / "Spreadsheets" / "Dialogue.csv"
SPEAKERS_JSON = ROOT / "Config" / "Speakers_TR.json"
BATCH_DIR = ROOT / "Spreadsheets" / "dlg_batches"


def split_batches(num_batches: int = 10) -> None:
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    with DIALOGUE_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    unique_map: dict[str, dict] = {}
    for r in rows:
        text = r["Dialogue"]
        if not text.strip():
            continue
        prefix = r["JsonFile"].split("-CAB-")[0]
        if text not in unique_map:
            unique_map[text] = {
                "id": len(unique_map),
                "ctx": prefix,
                "sp": r["Speaker"],
                "en": text,
                "tr": r["Translation"],
            }

    items = list(unique_map.values())
    chunk_size = (len(items) + num_batches - 1) // num_batches
    for b in range(num_batches):
        start = b * chunk_size
        end = min(len(items), (b + 1) * chunk_size)
        batch_items = items[start:end]
        out_path = BATCH_DIR / f"dlg_batch_{b + 1:02d}.json"
        out_path.write_text(
            json.dumps(batch_items, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {out_path.name}: {len(batch_items)} unique dialogues (IDs {start}..{end - 1})")


def merge_batches() -> None:
    with DIALOGUE_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    speakers_map: dict[str, str] = json.loads(SPEAKERS_JSON.read_text(encoding="utf-8"))
    # Also create a reverse lookup so already-translated speakers remain valid
    tr_lookup: dict[str, str] = {}
    for batch_file in sorted(BATCH_DIR.glob("dlg_batch_*.json")):
        batch_items = json.loads(batch_file.read_text(encoding="utf-8"))
        for item in batch_items:
            tr = item.get("tr", "").strip()
            if tr:
                tr_lookup[item["en"]] = item["tr"]

    speaker_updated = 0
    dlg_updated = 0
    for r in rows:
        sp = r["Speaker"]
        if sp in speakers_map:
            r["Speaker"] = speakers_map[sp]
            speaker_updated += 1
        text = r["Dialogue"]
        if text.strip() and text in tr_lookup:
            r["Translation"] = tr_lookup[text]
            dlg_updated += 1

    with DIALOGUE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["JsonFile", "msgID", "Speaker", "Dialogue", "Translation"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Merged {dlg_updated} dialogue rows and {speaker_updated} speaker labels into {DIALOGUE_CSV.name}"
    )


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "split"
    if cmd == "split":
        split_batches()
    elif cmd == "merge":
        merge_batches()
