#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate all Turkish localized textures for RAIDOU Remastered: The Mystery of the Soulless Army.
Reads original English textures from Backups/Textures_EN to guarantee exact filenames,
dimensions (width, height), and color modes (RGBA / RGB), and writes localized PNGs
into Content/Texturas.
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
BAK_DIR = BASE_DIR / "Backups" / "Textures_EN"
OUT_DIR = BASE_DIR / "Content" / "Texturas"

FONTS_DIR = Path(r"C:\Windows\Fonts")
FONT_SERIF_REG = str(FONTS_DIR / "pala.ttf")
FONT_SERIF_BOLD = str(FONTS_DIR / "palab.ttf")
FONT_SERIF_ITA = str(FONTS_DIR / "palai.ttf")
FONT_SERIF_BI = str(FONTS_DIR / "palabi.ttf")
FONT_GEORGIA_BOLD = str(FONTS_DIR / "georgiab.ttf")
FONT_SANS_ITA = str(FONTS_DIR / "ariali.ttf")
FONT_SANS_BI = str(FONTS_DIR / "arialbi.ttf")
FONT_SANS_BOLD = str(FONTS_DIR / "arialbd.ttf")


def find_orig(prefix: str) -> Path:
    matches = sorted(BAK_DIR.glob(f"{prefix}*"))
    if not matches:
        raise FileNotFoundError(f"Could not find texture matching prefix: {prefix}")
    return matches[0]


def fit_font(font_path: str, text: str, max_w: int, start_size: int, min_size: int = 10) -> ImageFont.FreeTypeFont:
    size = start_size
    while size >= min_size:
        f = ImageFont.truetype(font_path, size)
        bbox = f.getbbox(text)
        if (bbox[2] - bbox[0]) <= max_w:
            return f
        size -= 1
    return ImageFont.truetype(font_path, min_size)


def save_verified(orig_path: Path, img: Image.Image) -> None:
    with Image.open(orig_path) as orig:
        expected_size = orig.size
        expected_mode = orig.mode
    if img.size != expected_size:
        img = img.resize(expected_size, Image.Resampling.LANCZOS)
    if img.mode != expected_mode:
        img = img.convert(expected_mode)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUT_DIR / orig_path.name)


# ---------------------------------------------------------------------------
# 1. Cutin Episode Titles & Story Transitions (cutin_tex.en)
# ---------------------------------------------------------------------------
EPISODES = {
    "01": ("1. Bölüm", "Kayıp Kız", "Kayıp Kız"),
    "02": ("2. Bölüm", "Kırmızı Pelerin", "Kırmızı Pelerin"),
    "03": ("3. Bölüm", "Karanlık Çağıran", "Karanlık Çağıran"),
    "04": ("4. Bölüm", "Kayıp Sevkiyat Vakası", "Kayıp Sevkiyat Vakası"),
    "05": ("5. Bölüm", "Yüzleşme", "Yüzleşme"),
    "06": ("6. Bölüm", "Işıltılı Muhafızların Sırrı", "Işıltılı Muhafızların Sırrı"),
    "07": ("7. Bölüm", "Lanetli Dedektif", "Lanetli Dedektif"),
    "08": ("8. Bölüm", "İblis ve Çelik Kule", "İblis ve Çelik Kule"),
    "09": ("9. Bölüm", "İki Çağıran", "İki Çağıran"),
    "10": ("10. Bölüm", "Başkent Alevler İçinde!", "Başkent Alevler İçinde!"),
    "11": ("11. Bölüm", "Uzay Görevi", "Uzay Görevi"),
    "12": ("Final Bölümü", "Bugünde, Gelecek İçin", "Aramızdaki Bağlar"),
}


def render_episode_start_rgba(size: tuple[int, int], ep_str: str, title_str: str) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    f_ep = fit_font(FONT_SERIF_REG, ep_str, w - 240, 88)
    f_ti = fit_font(FONT_SERIF_REG, title_str, w - 180, 138)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)

    b1 = f_ep.getbbox(ep_str)
    w1 = b1[2] - b1[0]
    d.text(((w - w1) // 2 - b1[0], 383 - b1[1]), ep_str, font=f_ep, fill=255)

    b2 = f_ti.getbbox(title_str)
    w2 = b2[2] - b2[0]
    d.text(((w - w2) // 2 - b2[0], 562 - b2[1]), title_str, font=f_ti, fill=255)

    fg = Image.new("RGBA", (w, h), (41, 16, 13, 0))
    fg.putalpha(mask)
    canvas.alpha_composite(fg)
    return canvas


def render_episode_start_rgb(size: tuple[int, int], ep_str: str, title_str: str) -> Image.Image:
    w, h = size
    canvas = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(canvas)
    f_ep = fit_font(FONT_SERIF_REG, ep_str, w - 300, 84)
    f_ti = fit_font(FONT_SERIF_REG, title_str, w - 200, 128)

    b2 = f_ti.getbbox(title_str)
    w2 = b2[2] - b2[0]
    tx2 = (w - w2) // 2
    d.text((tx2 - b2[0], 490 - b2[1]), title_str, font=f_ti, fill=(255, 255, 255))

    b1 = f_ep.getbbox(ep_str)
    tx1 = max(97, tx2 - 110)
    d.text((tx1 - b1[0], 329 - b1[1]), ep_str, font=f_ep, fill=(255, 255, 255))
    return canvas


def render_episode_end_rgb(size: tuple[int, int], ep_str: str, title_str: str) -> Image.Image:
    w, h = size
    canvas = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(canvas)
    f_ep = fit_font(FONT_SERIF_BOLD, ep_str, 800, 56)
    f_ti = fit_font(FONT_SERIF_BOLD, title_str, 1380, 74)
    f_end = fit_font(FONT_SERIF_BOLD, "Son", 400, 54)

    b2 = f_ti.getbbox(title_str)
    w2 = b2[2] - b2[0]
    tx2 = 1816 - w2
    d.text((tx2 - b2[0], 857 - b2[1]), title_str, font=f_ti, fill=(255, 255, 255))

    b1 = f_ep.getbbox(ep_str)
    tx1 = max(360, tx2 - 80)
    d.text((tx1 - b1[0], 750 - b1[1]), ep_str, font=f_ep, fill=(255, 255, 255))

    b3 = f_end.getbbox("Son")
    w3 = b3[2] - b3[0]
    d.text((1814 - w3 - b3[0], 967 - b3[1]), "Son", font=f_end, fill=(255, 255, 255))
    return canvas


def generate_cutin_textures() -> int:
    count = 0
    for ep_num, (ep_str, title_rgba, title_rgb) in EPISODES.items():
        for p in sorted(BAK_DIR.glob(f"title{ep_num}_start*")):
            with Image.open(p) as orig:
                if orig.mode == "RGBA":
                    im = render_episode_start_rgba(orig.size, ep_str, title_rgba)
                else:
                    im = render_episode_start_rgb(orig.size, ep_str, title_rgb)
            save_verified(p, im)
            count += 1

        p_end = find_orig(f"title{ep_num}_end")
        with Image.open(p_end) as orig:
            im_end = render_episode_end_rgb(orig.size, ep_str, title_rgb)
        save_verified(p_end, im_end)
        count += 1

    # yokujitu ("The next day..." -> "Ertesi gün...")
    p_yok = find_orig("yokujitu")
    with Image.open(p_yok) as orig:
        w, h = orig.size
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        f = fit_font(FONT_SERIF_REG, "Ertesi gün...", w - 200, 118)
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)
        b = f.getbbox("Ertesi gün...")
        tw, th = b[2] - b[0], b[3] - b[1]
        d.text(((w - tw) // 2 - b[0], (h - th) // 2 - b[1]), "Ertesi gün...", font=f, fill=255)
        fg = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        fg.putalpha(mask)
        canvas.alpha_composite(fg)
    save_verified(p_yok, canvas)
    count += 1

    # taisyou ("Taisho 20 / The Capital" -> "Taisho 20 / Başkent")
    p_tai = find_orig("taisyou-CAB")
    with Image.open(p_tai) as orig:
        w, h = orig.size
        canvas = Image.new("RGB", (w, h), (0, 0, 0))
        d = ImageDraw.Draw(canvas)
        f1 = fit_font(FONT_SERIF_REG, "Taisho 20", 600, 74)
        f2 = fit_font(FONT_SERIF_REG, "Başkent", 900, 128)
        b1 = f1.getbbox("Taisho 20")
        b2 = f2.getbbox("Başkent")
        d.text((550 - b1[0], 379 - b1[1]), "Taisho 20", font=f1, fill=(255, 255, 255))
        d.text((740 - b2[0], 561 - b2[1]), "Başkent", font=f2, fill=(255, 255, 255))
    save_verified(p_tai, canvas)
    count += 1

    # taisyou_kuzunoha ("And so the days passed..." -> "Ve günler böylece geçti...")
    p_tk = find_orig("taisyou_kuzunoha")
    with Image.open(p_tk) as orig:
        w, h = orig.size
        canvas = Image.new("RGB", (w, h), (0, 0, 0))
        d = ImageDraw.Draw(canvas)
        txt = "Ve günler böylece geçti..."
        f = fit_font(FONT_SERIF_REG, txt, w - 200, 92)
        b = f.getbbox(txt)
        tw, th = b[2] - b[0], b[3] - b[1]
        d.text(((w - tw) // 2 - b[0], (h - th) // 2 - b[1]), txt, font=f, fill=(255, 255, 255))
    save_verified(p_tk, canvas)
    count += 1

    # caution (Disclaimer screen)
    p_caut = find_orig("caution-CAB")
    with Image.open(p_caut) as orig:
        w, h = orig.size
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)
        lines = [
            (301, "Bu eser tamamen kurmacadır."),
            (406, "İsimler, karakterler, kurumlar, mekânlar, olaylar ve vakalar"),
            (511, "ya yazarın hayal gücünün ürünüdür ya da kurgusal olarak kullanılmıştır."),
            (616, "Yaşayan ya da ölmüş gerçek kişilerle veya gerçek olaylarla olan"),
            (721, "her türlü benzerlik tamamen tesadüftür."),
        ]
        f = fit_font(FONT_SERIF_REG, lines[2][1], 1490, 48)
        for y_pos, line in lines:
            b = f.getbbox(line)
            d.text((216 - b[0], y_pos - b[1]), line, font=f, fill=255)
        fg = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        fg.putalpha(mask)
        canvas.alpha_composite(fg)
    save_verified(p_caut, canvas)
    count += 1

    return count


# ---------------------------------------------------------------------------
# 2. Map Entry Titles (maptitle_tex.en)
# ---------------------------------------------------------------------------
MAP_TITLES_1LINE = {
    "m_name010_00": "Yeraltı Tersanesi",
    "m_name011_00": "Waden Bir",
    "m_name012_00": "Tai-itsu Uydusu",
    "m_name013_00": "Akarana Koridoru",
    "m_name014_00": "Eğitim Salonu",
    "m_name017_00": "Eğitim Salonu Bölümü",
    "s_00-CAB": "Kuzunoha Köyü",
    "t-CAB-e4b15": "Narumi Dedektiflik Bürosu",
}

MAP_TITLES_2LINE = {
    "m-CAB-e4b15": ("Shin-Sekai", "Gazozcusu"),
    "m_name002_01": ("Ryugu Restoranı", "Chujou-Ku"),
    "m_name002_03": ("Shin-Sekai Gazozcusu", "Chujou-Ku"),
    "m_name003_00": ("Eğlence Mahallesi", "Senju-Ku"),
    "m_name004_03": ("Yabancılar Mezarlığı", "Koutou-Ku"),
    "m_name006_00": ("İsimsiz Tapınak", "Shinoda"),
    "m_name007_01": ("Kasumi Açıklığı", "Akasaka-Ku"),
    "m_name008_00": ("Daidouji Konağı", "Yarai-Ku"),
    "m_name009_00": ("Daidouji Tekstil", "Senju-Ku"),
    "m_name010_04": ("4 No'lu Top Bataryası", "Koutou-Ku"),
    "m_name015_00": ("Harika Bilim Laboratuvarı", "Senju-Ku"),
    "s_01-CAB": ("Eğitim Salonu 1", "Kuzunoha Köyü"),
    "s_02-CAB": ("Eğitim Salonu 2", "Kuzunoha Köyü"),
    "s_03-CAB": ("Eğitim Salonu 3", "Kuzunoha Köyü"),
    "s_04-CAB": ("Kuzunoha Köyü", "Eğitim Salonu"),
}


def generate_maptitle_textures() -> int:
    count = 0
    for pref, text in MAP_TITLES_1LINE.items():
        p = find_orig(pref)
        with Image.open(p) as orig:
            w, h = orig.size
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        f = fit_font(FONT_SERIF_REG, text, w - 48, 68)
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)
        b = f.getbbox(text)
        tw = b[2] - b[0]
        d.text(((w - tw) // 2 - b[0], 114 - b[1]), text, font=f, fill=255)
        fg = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        fg.putalpha(mask)
        canvas.alpha_composite(fg)
        save_verified(p, canvas)
        count += 1

    for pref, (line1, line2) in MAP_TITLES_2LINE.items():
        p = find_orig(pref)
        with Image.open(p) as orig:
            w, h = orig.size
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        f1 = fit_font(FONT_SERIF_REG, line1, w - 80, 68)
        f2 = fit_font(FONT_SERIF_REG, line2, w - 80, 68)
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)
        b1 = f1.getbbox(line1)
        b2 = f2.getbbox(line2)
        d.text((36 - b1[0], 63 - b1[1]), line1, font=f1, fill=255)
        w2 = b2[2] - b2[0]
        d.text((w - 36 - w2 - b2[0], 160 - b2[1]), line2, font=f2, fill=255)
        fg = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        fg.putalpha(mask)
        canvas.alpha_composite(fg)
        save_verified(p, canvas)
        count += 1

    return count


# ---------------------------------------------------------------------------
# 3. Save/Load UI Tags (saveloadui_tex.en)
# ---------------------------------------------------------------------------
def render_saveload_tag(
    size: tuple[int, int],
    text: str,
    fill_rgb: tuple[int, int, int],
    glow_rgb: tuple[int, int, int] | None = None,
) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    font = fit_font(FONT_SANS_BI, text, w - 18, 28)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    b = font.getbbox(text)
    tw, th = b[2] - b[0], b[3] - b[1]
    tx = (w - tw) // 2 - b[0]
    ty = (h - th) // 2 - b[1]
    d.text((tx, ty), text, font=font, fill=255)

    if glow_rgb is not None:
        glow_m = mask.filter(ImageFilter.GaussianBlur(radius=3.2))
        glow = Image.new("RGBA", (w, h), (*glow_rgb, 0))
        glow.putalpha(glow_m)
        canvas.alpha_composite(glow)
        canvas.alpha_composite(glow)
    else:
        sh_m = mask.filter(ImageFilter.GaussianBlur(radius=1.5))
        sh = Image.new("RGBA", (w, h), (10, 12, 10, 0))
        sh.putalpha(sh_m)
        canvas.alpha_composite(sh)

    fg = Image.new("RGBA", (w, h), (*fill_rgb, 0))
    fg.putalpha(mask)
    canvas.alpha_composite(fg)
    return canvas


def generate_saveload_textures() -> int:
    specs = [
        ("saveload_autosave-CAB", "OTOMATİK KAYIT", (186, 126, 62), None),
        ("saveload_autosave_sele", "OTOMATİK KAYIT", (255, 232, 155), (215, 145, 20)),
        ("saveload_chudan2", "HIZLI KAYIT", (186, 126, 62), None),
        ("saveload_chudan_sele2", "HIZLI KAYIT", (255, 232, 155), (215, 145, 20)),
        ("saveload_hason-CAB", "BOZUK VERİ", (195, 52, 52), None),
        ("saveload_hason_sele", "BOZUK VERİ", (235, 72, 48), (210, 130, 15)),
        ("saveload_nodata-CAB", "VERİ YOK", (198, 56, 57), None),
        ("saveload_nodata_sel", "VERİ YOK", (235, 75, 50), (210, 130, 15)),
    ]
    count = 0
    for pref, txt, fg_col, glow_col in specs:
        p = find_orig(pref)
        with Image.open(p) as orig:
            im = render_saveload_tag(orig.size, txt, fg_col, glow_col)
        save_verified(p, im)
        count += 1
    return count


# ---------------------------------------------------------------------------
# 4. Moon Phase Labels, Loading, Investigation Failed, Subtitle, Shop Signs
# ---------------------------------------------------------------------------
def render_moon(size: tuple[int, int], text: str) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    font = fit_font(FONT_SERIF_REG, text, w - 16, 44)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    b = font.getbbox(text)
    tw, th = b[2] - b[0], b[3] - b[1]
    d.text(((w - tw) // 2 - b[0], (h - th) // 2 - b[1]), text, font=font, fill=255)

    sh_m = mask.filter(ImageFilter.GaussianBlur(radius=2.5))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh.putalpha(sh_m)
    canvas.alpha_composite(sh, (2, 2))
    canvas.alpha_composite(sh, (0, 1))

    fg = Image.new("RGBA", (w, h), (214, 207, 198, 0))
    fg.putalpha(mask)
    canvas.alpha_composite(fg)
    return canvas


def render_agency_sign(size: tuple[int, int], text: str) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    font = fit_font(FONT_SERIF_ITA, text, w - 16, 62)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    b = font.getbbox(text)
    tw, th = b[2] - b[0], b[3] - b[1]
    tx = (w - tw) // 2 - b[0]
    ty = (h - th) // 2 - b[1]
    d.text((tx, ty), text, font=font, fill=255)

    glow_m = mask.filter(ImageFilter.GaussianBlur(radius=2.8))
    glow = Image.new("RGBA", (w, h), (38, 12, 14, 0))
    glow.putalpha(glow_m)
    canvas.alpha_composite(glow)
    canvas.alpha_composite(glow)

    grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gpx = grad.load()
    y0, y1 = max(0, ty + b[1]), min(h - 1, ty + b[3])
    span = max(1, y1 - y0)
    for y in range(h):
        t = max(0.0, min(1.0, (y - y0) / span))
        if t < 0.55:
            u = t / 0.55
            r = int(202 * (1 - u) + 115 * u)
            g = int(190 * (1 - u) + 102 * u)
            bl = int(185 * (1 - u) + 98 * u)
        else:
            u = (t - 0.55) / 0.45
            r = int(115 * (1 - u) + 165 * u)
            g = int(102 * (1 - u) + 150 * u)
            bl = int(98 * (1 - u) + 145 * u)
        for x in range(w):
            gpx[x, y] = (r, g, bl, 255)
    grad.putalpha(mask)
    canvas.alpha_composite(grad)
    return canvas


def generate_general_ui_textures() -> int:
    count = 0
    # Moon UI
    for pref, txt in [
        ("getsurei_parts_sin", "YENİ"),
        ("getsurei_parts_man", "DOLU"),
        ("getsurei_parts_han", "YARIM"),
    ]:
        p = find_orig(pref)
        with Image.open(p) as orig:
            im = render_moon(orig.size, txt)
        save_verified(p, im)
        count += 1

    # Loading_moji
    p_load = find_orig("Loading_moji")
    with Image.open(p_load) as orig:
        w, h = orig.size
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dots = orig.crop((186, 0, w, h))
        font = fit_font(FONT_GEORGIA_BOLD, "Yükleniyor", 168, 30)
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)
        b = font.getbbox("Yükleniyor")
        th = b[3] - b[1]
        d.text((16 - b[0], (h - th) // 2 - b[1] - 2), "Yükleniyor", font=font, fill=255)
        glow_m = mask.filter(ImageFilter.GaussianBlur(radius=3.0))
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow.putalpha(glow_m)
        canvas.alpha_composite(glow)
        canvas.alpha_composite(glow)
        fg = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        fg.putalpha(mask)
        canvas.alpha_composite(fg)
        canvas.paste(dots, (186, 0), dots)
    save_verified(p_load, canvas)
    count += 1

    # Investigation_Failed
    p_fail = find_orig("Investigation_Failed")
    with Image.open(p_fail) as orig:
        w, h = orig.size
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        txt = "Soruşturma Başarısız"
        f = fit_font(FONT_SERIF_REG, txt, int(w * 0.85), 156)
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)
        b = f.getbbox(txt)
        tw, th = b[2] - b[0], b[3] - b[1]
        d.text(((w - tw) // 2 - b[0], (h - th) // 2 - b[1]), txt, font=f, fill=255)
        fg = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        fg.putalpha(mask)
        canvas.alpha_composite(fg)
    save_verified(p_fail, canvas)
    count += 1

    # Shop / Agency headers
    for pref, txt in [
        ("shop_parts_moji_narumi", "Narumi Dedektiflik Bürosu"),
        ("shop_parts_moji_sinsekai", "Shin-Sekai Gazozcusu"),
    ]:
        p = find_orig(pref)
        with Image.open(p) as orig:
            im = render_agency_sign(orig.size, txt)
        save_verified(p, im)
        count += 1

    # sub_title ("THE MYSTERY OF THE SOULLESS ARMY™" -> "RUHSUZ ORDUNUN GİZEMİ™")
    p_sub = find_orig("sub_title-CAB")
    with Image.open(p_sub) as orig:
        w, h = orig.size
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)
        l1 = "RUHSUZ ORDUNUN"
        l2 = "GİZEMİ™"
        f1 = fit_font(FONT_SERIF_BOLD, l1, 1080, 68)
        f2 = fit_font(FONT_SERIF_BOLD, l2, 1080, 74)
        b1 = f1.getbbox(l1)
        b2 = f2.getbbox(l2)
        d.text(((w - (b1[2] - b1[0])) // 2 - b1[0], 464 - b1[1]), l1, font=f1, fill=255)
        d.text(((w - (b2[2] - b2[0])) // 2 - b2[0], 548 - b2[1]), l2, font=f2, fill=255)
        fg = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        fg.putalpha(mask)
        canvas.alpha_composite(fg)
    save_verified(p_sub, canvas)
    count += 1

    # LEVEL UP! -> SEVİYE ATLADIN!
    p_lvl = find_orig("result_parts_LEVEL UP_")
    with Image.open(p_lvl) as orig:
        w, h = orig.size
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        # Preserve original golden background halo by blurring original and tinting
        bg_halo = orig.filter(ImageFilter.GaussianBlur(radius=8.0))
        canvas.alpha_composite(bg_halo)
        txt = "SEVİYE ATLADIN!"
        f = fit_font(FONT_SERIF_BOLD, txt, w - 36, 30)
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)
        b = f.getbbox(txt)
        tw, th = b[2] - b[0], b[3] - b[1]
        d.text(((w - tw) // 2 - b[0], (h - th) // 2 - b[1]), txt, font=f, fill=255)
        sh_m = mask.filter(ImageFilter.GaussianBlur(radius=2.0))
        sh = Image.new("RGBA", (w, h), (40, 35, 5, 0))
        sh.putalpha(sh_m)
        canvas.alpha_composite(sh)
        fg = Image.new("RGBA", (w, h), (242, 248, 215, 0))
        fg.putalpha(mask)
        canvas.alpha_composite(fg)
    save_verified(p_lvl, canvas)
    count += 1

    return count


# ---------------------------------------------------------------------------
# 5. Opening Movie Titles (op_movie_name.en)
# ---------------------------------------------------------------------------
def render_op_movie_text(size: tuple[int, int], text: str, font_size: int, blur_px: float) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    f = fit_font(FONT_SERIF_REG, text, w - 40, font_size)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    b = f.getbbox(text)
    tw, th = b[2] - b[0], b[3] - b[1]
    tx = (w - tw) // 2 - b[0]
    ty = (h - th) // 2 - b[1]
    d.text((tx, ty), text, font=f, fill=255)

    if blur_px > 0:
        # Horizontal motion-like blur + gaussian blur
        m1 = mask.filter(ImageFilter.GaussianBlur(radius=blur_px))
        fg1 = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        fg1.putalpha(m1)
        canvas.alpha_composite(fg1, (-int(blur_px * 2), 0))
        canvas.alpha_composite(fg1, (int(blur_px * 2), 0))
        canvas.alpha_composite(fg1)
    else:
        fg = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        fg.putalpha(mask)
        canvas.alpha_composite(fg)
    return canvas


def generate_op_movie_textures() -> int:
    specs = [
        ("Detective-CAB", "Dedektif—", 104, 0.0),
        ("Detective Blur1", "Dedektif—", 104, 2.5),
        ("Detective Blur2", "Dedektif—", 104, 4.5),
        ("Detective Blur3", "Dedektif—", 104, 6.5),
        ("Summoner-CAB", "—ve İblis Çağıran—", 86, 0.0),
        ("Summoner Blur1", "—ve İblis Çağıran—", 86, 6.0),
        ("Summoner Blur2", "—ve İblis Çağıran—", 86, 4.0),
        ("Summoner Blur3", "—ve İblis Çağıran—", 86, 2.2),
    ]
    count = 0
    for pref, txt, fsize, blur_r in specs:
        p = find_orig(pref)
        with Image.open(p) as orig:
            im = render_op_movie_text(orig.size, txt, fsize, blur_r)
        save_verified(p, im)
        count += 1
    return count


# ---------------------------------------------------------------------------
# 6. Small Badges (Unreg., Locked, New, Reward, Compass)
# ---------------------------------------------------------------------------
def render_framed_badge(
    orig: Image.Image,
    text: str,
    text_rgb: tuple[int, int, int],
    inner_bg_rgba: tuple[int, int, int, int],
) -> Image.Image:
    w, h = orig.size
    canvas = orig.convert("RGBA").copy()
    draw_bg = ImageDraw.Draw(canvas)
    draw_bg.rectangle([3, 3, w - 4, h - 4], fill=inner_bg_rgba)

    f = fit_font(FONT_SERIF_BOLD, text, w - 10, int(h * 0.62), min_size=11)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    b = f.getbbox(text)
    tw, th = b[2] - b[0], b[3] - b[1]
    d.text(((w - tw) // 2 - b[0], (h - th) // 2 - b[1]), text, font=f, fill=255)

    sh_m = mask.filter(ImageFilter.GaussianBlur(radius=1.2))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh.putalpha(sh_m)
    canvas.alpha_composite(sh)

    fg = Image.new("RGBA", (w, h), (*text_rgb, 0))
    fg.putalpha(mask)
    canvas.alpha_composite(fg)
    return canvas


def render_glow_badge(
    size: tuple[int, int],
    text: str,
    text_rgb: tuple[int, int, int],
    glow_rgb: tuple[int, int, int],
    align_right: bool = False,
) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    max_w = int(w * 0.72) if align_right else w - 8
    f = fit_font(FONT_SERIF_BOLD, text, max_w, int(h * 0.68), min_size=11)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    b = f.getbbox(text)
    tw, th = b[2] - b[0], b[3] - b[1]
    tx = (w - tw - 4 - b[0]) if align_right else ((w - tw) // 2 - b[0])
    ty = (h - th) // 2 - b[1]
    d.text((tx, ty), text, font=f, fill=255)

    glow_m = mask.filter(ImageFilter.GaussianBlur(radius=2.5))
    glow = Image.new("RGBA", (w, h), (*glow_rgb, 0))
    glow.putalpha(glow_m)
    canvas.alpha_composite(glow)
    canvas.alpha_composite(glow)

    fg = Image.new("RGBA", (w, h), (*text_rgb, 0))
    fg.putalpha(mask)
    canvas.alpha_composite(fg)
    return canvas


def render_compass_tr(orig: Image.Image) -> Image.Image:
    canvas = orig.convert("RGBA").copy()
    px = canvas.load()
    # Sample ring background color and overwrite the 4 cardinal letter boxes
    # Center of compass is around (162, 121)
    boxes = [
        # (x0, y0, x1, y1, letter, sample_xy)
        (146, 51, 178, 79, "K", (138, 65)),   # North -> Kuzey
        (146, 162, 178, 191, "G", (138, 175)), # South -> Güney
        (91, 106, 123, 136, "B", (105, 96)),   # West -> Batı
        (202, 106, 232, 136, "D", (215, 96)),  # East -> Doğu
    ]
    draw = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT_SERIF_BOLD, 28)
    for x0, y0, x1, y1, letter, (sx, sy) in boxes:
        bg_col = px[sx, sy]
        draw.rectangle([x0, y0, x1, y1], fill=bg_col)
        b = f.getbbox(letter)
        tw, th = b[2] - b[0], b[3] - b[1]
        cx = (x0 + x1 - tw) // 2 - b[0]
        cy = (y0 + y1 - th) // 2 - b[1]
        draw.text((cx, cy), letter, font=f, fill=(28, 20, 18, 255))
    return canvas


def generate_small_badges_and_compass() -> int:
    count = 0
    # Framed badges
    framed_specs = [
        ("gohma_par2_moji_01", "Kayıtsız", (245, 245, 245), (22, 22, 26, 210)),
        ("gohma_par2_moji_02", "Kilitli", (255, 58, 36), (32, 6, 6, 210)),
        ("info_set_moji_icon_mtrk", "Kayıtsız", (255, 62, 32), (32, 6, 6, 210)),
    ]
    for pref, txt, fg_col, bg_col in framed_specs:
        p = find_orig(pref)
        with Image.open(p) as orig:
            im = render_framed_badge(orig, txt, fg_col, bg_col)
        save_verified(p, im)
        count += 1

    # Glow badges (New / Reward)
    glow_specs = [
        ("gohma_par2_moji_05", "Yeni", (248, 196, 68), (32, 22, 12), True),
        ("field_set_moji_sin", "Yeni", (248, 196, 68), (32, 22, 12), False),
        ("shop_par_new", "Yeni", (248, 196, 68), (32, 22, 12), False),
        ("bekken_moji_housyu", "Ödül", (252, 125, 68), (38, 16, 16), False),
    ]
    for pref, txt, fg_col, gl_col, right_align in glow_specs:
        p = find_orig(pref)
        with Image.open(p) as orig:
            im = render_glow_badge(orig.size, txt, fg_col, gl_col, align_right=right_align)
        save_verified(p, im)
        count += 1

    # Compass (aut_map_bg2)
    p_comp = find_orig("aut_map_bg2")
    with Image.open(p_comp) as orig:
        im_comp = render_compass_tr(orig)
    save_verified(p_comp, im_comp)
    count += 1

    return count


# ---------------------------------------------------------------------------
# 7. Battle Callouts (damage2 & damage2_1 .. damage2_6)
# ---------------------------------------------------------------------------
def render_battle_callout(
    size: tuple[int, int],
    text: str,
    top_rgb: tuple[int, int, int],
    bot_rgb: tuple[int, int, int],
    outline_rgb: tuple[int, int, int],
    glow_rgb: tuple[int, int, int] | None = None,
) -> Image.Image:
    w, h = size
    # Render on larger oversampled canvas then rotate slightly for dynamic comic action look
    ow, oh = w * 2, h * 2
    base = Image.new("RGBA", (ow, oh), (0, 0, 0, 0))
    f = fit_font(FONT_SANS_BI, text, int(ow * 0.82), 86, min_size=28)
    mask = Image.new("L", (ow, oh), 0)
    d = ImageDraw.Draw(mask)
    b = f.getbbox(text)
    tw, th = b[2] - b[0], b[3] - b[1]
    tx = (ow - tw) // 2 - b[0]
    ty = (oh - th) // 2 - b[1]
    d.text((tx, ty), text, font=f, fill=255)

    # Rotate -10 degrees for action slant
    mask = mask.rotate(10, resample=Image.Resampling.BICUBIC, expand=False)

    if glow_rgb is not None:
        glow_m = mask.filter(ImageFilter.GaussianBlur(radius=10.0))
        glow = Image.new("RGBA", (ow, oh), (*glow_rgb, 0))
        glow.putalpha(glow_m)
        base.alpha_composite(glow)
        base.alpha_composite(glow)

    # Thick outline via MaxFilter
    out_m = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(radius=1.2))
    out_layer = Image.new("RGBA", (ow, oh), (*outline_rgb, 0))
    out_layer.putalpha(out_m)
    base.alpha_composite(out_layer)
    base.alpha_composite(out_layer)

    # Gradient fill
    grad = Image.new("RGBA", (ow, oh), (0, 0, 0, 0))
    gpx = grad.load()
    mb = mask.getbbox() or (0, 0, ow, oh)
    y0, y1 = mb[1], max(mb[1] + 1, mb[3])
    for y in range(oh):
        t = max(0.0, min(1.0, (y - y0) / (y1 - y0)))
        r = int(top_rgb[0] * (1 - t) + bot_rgb[0] * t)
        g = int(top_rgb[1] * (1 - t) + bot_rgb[1] * t)
        bl = int(top_rgb[2] * (1 - t) + bot_rgb[2] * t)
        for x in range(ow):
            gpx[x, y] = (r, g, bl, 255)
    grad.putalpha(mask)
    base.alpha_composite(grad)

    return base.resize((w, h), Image.Resampling.LANCZOS)


def generate_battle_callouts() -> int:
    # (prefix, grid_col, grid_row, text, top_rgb, bot_rgb, outline_rgb, glow_rgb)
    specs = [
        ("damage2_1", 0, 0, "ZAYIF!", (255, 255, 245), (255, 210, 120), (235, 85, 10), (255, 110, 15)),
        ("damage2_2", 1, 0, "ETKİSİZ!", (220, 225, 230), (125, 130, 138), (22, 24, 28), None),
        ("damage2_5", 2, 0, "ISKA!", (105, 80, 235), (185, 175, 255), (15, 12, 35), None),
        ("damage2_4", 0, 1, "KRİTİK!", (235, 35, 25), (255, 95, 45), (15, 85, 35), (220, 40, 20)),
        ("damage2_3", 1, 1, "EMİLDİ!", (220, 205, 255), (110, 95, 235), (20, 135, 85), None),
        ("damage2_6", 2, 1, "YANSIDI!", (45, 225, 210), (35, 110, 235), (12, 22, 65), None),
    ]
    count = 0
    p_sheet = find_orig("damage2-CAB")
    with Image.open(p_sheet) as orig_sheet:
        sheet_canvas = orig_sheet.convert("RGBA").copy()

    draw_sheet = ImageDraw.Draw(sheet_canvas)
    for pref, col, row, txt, top_c, bot_c, out_c, glow_c in specs:
        p = find_orig(pref)
        with Image.open(p) as orig:
            tile = render_battle_callout(orig.size, txt, top_c, bot_c, out_c, glow_c)
        save_verified(p, tile)
        count += 1

        # Replace tile in damage2 sheet (columns 0..2; column 3 is kanji and stays untouched)
        x0, y0 = col * 184, row * 152
        draw_sheet.rectangle([x0, y0, x0 + 183, y0 + 151], fill=(0, 0, 0, 0))
        sheet_canvas.alpha_composite(tile, (x0, y0))

    save_verified(p_sheet, sheet_canvas)
    count += 1
    return count


def main() -> None:
    # Clear Content/Texturas first so only localized textures are present
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.png"):
        old.unlink()

    c_cutin = generate_cutin_textures()
    c_map = generate_maptitle_textures()
    c_save = generate_saveload_textures()
    c_gen = generate_general_ui_textures()
    c_op = generate_op_movie_textures()
    c_small = generate_small_badges_and_compass()
    c_btl = generate_battle_callouts()

    total = c_cutin + c_map + c_save + c_gen + c_op + c_small + c_btl
    print(
        f"Generated {total} Turkish textures in {OUT_DIR}:\n"
        f"  - Cutin / Episode titles: {c_cutin}\n"
        f"  - Map entry titles:       {c_map}\n"
        f"  - Save/Load UI tags:      {c_save}\n"
        f"  - General UI / Signs:     {c_gen}\n"
        f"  - Opening movie titles:   {c_op}\n"
        f"  - Badges & Compass:       {c_small}\n"
        f"  - Battle callouts:        {c_btl}"
    )


if __name__ == "__main__":
    main()
