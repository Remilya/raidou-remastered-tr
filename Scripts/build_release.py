#!/usr/bin/env python3
"""
Tek komutla:
1. Spreadsheets/Dialogue.csv ve Spreadsheets/Text.csv içindeki çevirileri JSON dosyalarına aktarır.
2. Ana oyun ve DLC (.en) bundle dosyalarını yeniden derleyip Raidou_PC_Release/update klasörüne yazar.
3. Türkçe karakter yamalı font dosyalarını (fontsdf_e, fontbase) doğrular/üretir.
4. İsteğe bağlı olarak (--zip) dağıtıma hazır Raidou_TR_Yama.zip paketini oluşturur.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import UnityPy

import csv_texts
import import_bundles


ROOT = Path(__file__).resolve().parent.parent
STEAM_GAME_DIR = Path(r"D:\SteamLibrary\steamapps\common\Raidou TMOTSA")
RELEASE_DIR = ROOT.parent / "Raidou_PC_Release"
BASE_BACKUP_DIR = ROOT / "Backups" / "Bundles" / "Original"
DLC_BACKUP_DIR = ROOT / "Backups" / "DLC" / "Original"
DLC_JSON_DIR = ROOT / "Content" / "DLC" / "JSON"

BASE_OUTPUT_DIR = (
    RELEASE_DIR / "update" / "Raidou TMOTSA_Data" / "StreamingAssets" / "AssetBundles"
)
DLC_OUTPUT_DIR = RELEASE_DIR / "update" / "dlc"
ZIP_OUTPUT_PATH = ROOT.parent / "Raidou_TR_Yama.zip"


def ensure_turkish_fonts() -> None:
    steam_bundles = STEAM_GAME_DIR / "Raidou TMOTSA_Data" / "StreamingAssets" / "AssetBundles"
    fontsdf_out = BASE_OUTPUT_DIR / "fontsdf_e"
    fontbase_out = BASE_OUTPUT_DIR / "fontbase"
    if fontsdf_out.is_file() and fontbase_out.is_file():
        return
    if not steam_bundles.is_dir():
        return

    BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    src_e = steam_bundles / "fontsdf_e"
    if src_e.is_file() and not fontsdf_out.is_file():
        env = UnityPy.load(src_e.read_bytes())
        bundle = next(iter(env.files.values()))
        for serialized in bundle.files.values():
            if type(serialized).__name__ != "SerializedFile":
                continue
            for reader in serialized.objects.values():
                if reader.type.name != "MonoBehaviour":
                    continue
                tree = reader.read_typetree()
                if "m_CharacterTable" not in tree:
                    continue
                chars = {c["m_Unicode"]: c for c in tree["m_CharacterTable"]}
                glyphs = {g["m_Index"]: g for g in tree["m_GlyphTable"]}
                changed = False
                for target_u, source_u in ((0x015E, 0x0218), (0x015F, 0x0219)):
                    if target_u not in chars and source_u in chars:
                        new_char = dict(chars[source_u])
                        new_char["m_Unicode"] = target_u
                        tree["m_CharacterTable"].append(new_char)
                        changed = True
                if 0x0131 not in chars and 0x69 in chars:
                    i_char = chars[0x69]
                    i_glyph = glyphs[i_char["m_GlyphIndex"]]
                    ref_u = 0x6E if 0x6E in chars else 0x73
                    x_height = glyphs[chars[ref_u]["m_GlyphIndex"]]["m_Metrics"]["m_HorizontalBearingY"]
                    crop_px = max(1, round(i_glyph["m_Metrics"]["m_HorizontalBearingY"] - x_height))
                    new_glyph_index = max(glyphs.keys()) + 1
                    new_glyph = {
                        "m_Index": new_glyph_index,
                        "m_Metrics": {
                            "m_Width": i_glyph["m_Metrics"]["m_Width"],
                            "m_Height": i_glyph["m_Metrics"]["m_Height"] - crop_px,
                            "m_HorizontalBearingX": i_glyph["m_Metrics"]["m_HorizontalBearingX"],
                            "m_HorizontalBearingY": i_glyph["m_Metrics"]["m_HorizontalBearingY"] - crop_px,
                            "m_HorizontalAdvance": i_glyph["m_Metrics"]["m_HorizontalAdvance"],
                        },
                        "m_GlyphRect": {
                            "m_X": i_glyph["m_GlyphRect"]["m_X"],
                            "m_Y": i_glyph["m_GlyphRect"]["m_Y"],
                            "m_Width": i_glyph["m_GlyphRect"]["m_Width"],
                            "m_Height": i_glyph["m_GlyphRect"]["m_Height"] - crop_px,
                        },
                        "m_Scale": i_glyph.get("m_Scale", 1.0),
                        "m_AtlasIndex": i_glyph.get("m_AtlasIndex", 0),
                        "m_ClassDefinitionType": i_glyph.get("m_ClassDefinitionType", 0),
                    }
                    tree["m_GlyphTable"].append(new_glyph)
                    tree["m_CharacterTable"].append({
                        "m_ElementType": 1,
                        "m_Unicode": 0x0131,
                        "m_GlyphIndex": new_glyph_index,
                        "m_Scale": 1.0,
                    })
                    changed = True
                if changed:
                    tree["m_CharacterTable"].sort(key=lambda c: c["m_Unicode"])
                    reader.save_typetree(tree)
        fontsdf_out.write_bytes(bundle.save(packer="original"))

    src_base = steam_bundles / "fontbase"
    if src_base.is_file() and not fontbase_out.is_file():
        env = UnityPy.load(src_base.read_bytes())
        bundle = next(iter(env.files.values()))
        for serialized in bundle.files.values():
            if type(serialized).__name__ != "SerializedFile":
                continue
            for reader in serialized.objects.values():
                if reader.type.name != "MonoBehaviour":
                    continue
                tree = reader.read_typetree()
                if "m_CharacterTable" not in tree or not tree["m_CharacterTable"]:
                    continue
                chars = {c["m_Unicode"]: c for c in tree["m_CharacterTable"]}
                changed = False
                for target_u, source_u in (
                    (0x015E, 0x53),
                    (0x015F, 0x73),
                    (0x011E, 0x47),
                    (0x011F, 0x67),
                    (0x0130, 0x49),
                    (0x0131, 0x69),
                ):
                    if target_u not in chars and source_u in chars:
                        new_char = dict(chars[source_u])
                        new_char["m_Unicode"] = target_u
                        tree["m_CharacterTable"].append(new_char)
                        changed = True
                if changed:
                    tree["m_CharacterTable"].sort(key=lambda c: c["m_Unicode"])
                    reader.save_typetree(tree)
        fontbase_out.write_bytes(bundle.save(packer="original"))


def build_all(with_textures: bool = False, create_zip: bool = False) -> int:
    print("=== [1/4] CSV Çevirileri JSON Dosyalarına Aktarılıyor ===")
    csv_texts.import_csv()

    print("\n=== [2/4] Türkçe Font Dosyaları Kontrol Ediliyor ===")
    ensure_turkish_fonts()

    print("\n=== [3/4] Ana Oyun Bundle Dosyaları Derleniyor ===")
    base_args = [
        "--bundle-dir",
        str(BASE_BACKUP_DIR),
        "--output-dir",
        str(BASE_OUTPUT_DIR),
    ]
    if not with_textures:
        base_args.append("--no-textures")
    res = import_bundles.main(base_args)
    if res != 0:
        return res

    print("\n=== [4/4] DLC Bundle Dosyaları Derleniyor ===")
    if DLC_BACKUP_DIR.is_dir():
        dlc_dirs = sorted(
            p for p in DLC_BACKUP_DIR.iterdir() if p.is_dir() and any(p.glob("*.en"))
        )
        for dlc_dir in dlc_dirs:
            json_dir = DLC_JSON_DIR / dlc_dir.name
            if not json_dir.is_dir() or not any(json_directory.glob("*.json") for json_directory in [json_dir]):
                continue
            dlc_args = [
                "--bundle-dir",
                str(dlc_dir),
                "--json-dir",
                str(json_dir),
                "--no-textures",
                "--skip-ui-patches",
                "--output-dir",
                str(DLC_OUTPUT_DIR / dlc_dir.name),
            ]
            res = import_bundles.main(dlc_args)
            if res != 0:
                return res

    if create_zip:
        print(f"\n=== Dağıtım Paketi Oluşturuluyor: {ZIP_OUTPUT_PATH.name} ===")
        with zipfile.ZipFile(ZIP_OUTPUT_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(RELEASE_DIR.rglob("*")):
                if file_path.is_file():
                    arcname = file_path.relative_to(RELEASE_DIR)
                    zf.write(file_path, arcname)
        print(f"Hazır: {ZIP_OUTPUT_PATH}")

    print("\n[TAMAMLANDI] Yama dosyaları güncellendi:", RELEASE_DIR)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-textures",
        action="store_true",
        help="Content/Texturas içindeki PNG dokularını da bundle'lara yeniden gömer (varsayılan: sadece metinler)",
    )
    parser.add_argument(
        "--zip",
        action="store_true",
        help="Derleme sonunda Raidou_TR_Yama.zip arşivini oluşturur",
    )
    args = parser.parse_args()
    return build_all(with_textures=args.with_textures, create_zip=args.zip)


if __name__ == "__main__":
    raise SystemExit(main())
