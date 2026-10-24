#!/usr/bin/env python3
"""Generate side-by-side EN vs TR texture comparison previews."""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS_DIR = Path(r"C:\Windows\Fonts")
FONT_SERIF_REG = str(FONTS_DIR / "pala.ttf")
FONT_SERIF_BOLD = str(FONTS_DIR / "palab.ttf")
FONT_SERIF_ITA = str(FONTS_DIR / "palai.ttf")
FONT_GEORGIA_BOLD = str(FONTS_DIR / "georgiab.ttf")
FONT_SANS_ITA = str(FONTS_DIR / "ariali.ttf")

TEX_DIR = Path(r"d:\ceviri\raidou-remastered-ptbr\Content\Texturas")
OUT_DIR = Path(r"C:\Users\Kuroneko\.gemini\antigravity\brain\21698f62-8727-4996-829b-133f4a8e4d5f")


def fit_font(font_path: str, text: str, max_w: int, start_size: int, min_size: int = 12):
    size = start_size
    while size >= min_size:
        f = ImageFont.truetype(font_path, size)
        bbox = f.getbbox(text)
        w = bbox[2] - bbox[0]
        if w <= max_w:
            return f
        size -= 1
    return ImageFont.truetype(font_path, min_size)


def render_loading_tr(orig: Image.Image) -> Image.Image:
    w, h = orig.size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dots = orig.crop((186, 0, w, h))

    font = fit_font(FONT_GEORGIA_BOLD, "Yükleniyor", 168, 30)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    bbox = font.getbbox("Yükleniyor")
    th = bbox[3] - bbox[1]
    tx = 16 - bbox[0]
    ty = (h - th) // 2 - bbox[1] - 2
    d.text((tx, ty), "Yükleniyor", font=font, fill=255)

    glow_mask = mask.filter(ImageFilter.GaussianBlur(radius=3.0))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow.putalpha(glow_mask)
    canvas.alpha_composite(glow)
    canvas.alpha_composite(glow)

    fg = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    fg.putalpha(mask)
    canvas.alpha_composite(fg)
    canvas.paste(dots, (186, 0), dots)
    return canvas


def render_centered_serif(
    size: tuple[int, int], text: str, font_size: int, rgb: tuple[int, int, int]
) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    font = fit_font(FONT_SERIF_REG, text, int(w * 0.85), font_size)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (w - tw) // 2 - bbox[0]
    ty = (h - th) // 2 - bbox[1]
    d.text((tx, ty), text, font=font, fill=255)
    fg = Image.new("RGBA", (w, h), (*rgb, 0))
    fg.putalpha(mask)
    canvas.alpha_composite(fg)
    return canvas


def render_agency_sign(size: tuple[int, int], text: str) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    font = fit_font(FONT_SERIF_ITA, text, w - 16, 62)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (w - tw) // 2 - bbox[0]
    ty = (h - th) // 2 - bbox[1]
    d.text((tx, ty), text, font=font, fill=255)

    glow_m = mask.filter(ImageFilter.GaussianBlur(radius=2.8))
    glow = Image.new("RGBA", (w, h), (38, 12, 14, 0))
    glow.putalpha(glow_m)
    canvas.alpha_composite(glow)
    canvas.alpha_composite(glow)

    grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gpx = grad.load()
    y0, y1 = max(0, ty + bbox[1]), min(h - 1, ty + bbox[3])
    span = max(1, y1 - y0)
    for y in range(h):
        t = max(0.0, min(1.0, (y - y0) / span))
        if t < 0.55:
            u = t / 0.55
            r = int(202 * (1 - u) + 115 * u)
            g = int(190 * (1 - u) + 102 * u)
            b = int(185 * (1 - u) + 98 * u)
        else:
            u = (t - 0.55) / 0.45
            r = int(115 * (1 - u) + 165 * u)
            g = int(102 * (1 - u) + 150 * u)
            b = int(98 * (1 - u) + 145 * u)
        for x in range(w):
            gpx[x, y] = (r, g, b, 255)
    grad.putalpha(mask)
    canvas.alpha_composite(grad)
    return canvas


def render_moon(size: tuple[int, int], text: str) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    font = fit_font(FONT_SERIF_REG, text, w - 20, 44)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (w - tw) // 2 - bbox[0]
    ty = (h - th) // 2 - bbox[1]
    d.text((tx, ty), text, font=font, fill=255)

    sh_m = mask.filter(ImageFilter.GaussianBlur(radius=2.5))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh.putalpha(sh_m)
    canvas.alpha_composite(sh, (2, 2))
    canvas.alpha_composite(sh, (0, 1))

    fg = Image.new("RGBA", (w, h), (214, 207, 198, 0))
    fg.putalpha(mask)
    canvas.alpha_composite(fg)
    return canvas


def render_saveload_tag(
    size: tuple[int, int], text: str, rgb: tuple[int, int, int] = (198, 56, 57)
) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    font = fit_font(FONT_SANS_ITA, text, w - 24, 30)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (w - tw) // 2 - bbox[0]
    ty = (h - th) // 2 - bbox[1]
    d.text((tx, ty), text, font=font, fill=255)

    sh_m = mask.filter(ImageFilter.GaussianBlur(radius=1.5))
    sh = Image.new("RGBA", (w, h), (10, 15, 10, 0))
    sh.putalpha(sh_m)
    canvas.alpha_composite(sh)

    fg = Image.new("RGBA", (w, h), (*rgb, 0))
    fg.putalpha(mask)
    canvas.alpha_composite(fg)
    return canvas


def render_map_title(size: tuple[int, int], line1: str, line2: str) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    f1 = fit_font(FONT_SERIF_REG, line1, w - 120, 68)
    f2 = fit_font(FONT_SERIF_REG, line2, w - 120, 68)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    b1 = f1.getbbox(line1)
    b2 = f2.getbbox(line2)
    d.text((72 - b1[0], 62 - b1[1]), line1, font=f1, fill=255)
    w2 = b2[2] - b2[0]
    d.text((w - 72 - w2 - b2[0], 162 - b2[1]), line2, font=f2, fill=255)
    fg = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    fg.putalpha(mask)
    canvas.alpha_composite(fg)
    return canvas


def render_episode_title(size: tuple[int, int], ep_text: str, title_text: str) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    f_ep = fit_font(FONT_SERIF_REG, ep_text, w - 200, 92)
    f_ti = fit_font(FONT_SERIF_REG, title_text, w - 200, 146)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    b1 = f_ep.getbbox(ep_text)
    w1 = b1[2] - b1[0]
    d.text(((w - w1) // 2 - b1[0], 383 - b1[1]), ep_text, font=f_ep, fill=255)

    b2 = f_ti.getbbox(title_text)
    w2 = b2[2] - b2[0]
    d.text(((w - w2) // 2 - b2[0], 555 - b2[1]), title_text, font=f_ti, fill=255)

    fg = Image.new("RGBA", (w, h), (41, 16, 13, 0))
    fg.putalpha(mask)
    canvas.alpha_composite(fg)
    return canvas


def make_comparison_card(
    en_img: Image.Image, tr_img: Image.Image, title: str, bg_color=(28, 28, 36)
) -> Image.Image:
    w, h = en_img.size
    if w > 640:
        scale = 600 / w
        disp_w, disp_h = int(w * scale), int(h * scale)
    else:
        disp_w, disp_h = w, h

    def prep(im):
        bg = Image.new("RGBA", im.size, (*bg_color, 255))
        if im.mode == "RGBA":
            bg.alpha_composite(im)
        else:
            bg.paste(im, (0, 0))
        if im.size != (disp_w, disp_h):
            bg = bg.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
        return bg.convert("RGB")

    left = prep(en_img)
    right = prep(tr_img)

    card_w = max(760, disp_w * 2 + 60)
    card_h = disp_h + 76
    card = Image.new("RGB", (card_w, card_h), (18, 18, 24))
    draw = ImageDraw.Draw(card)
    lbl_font = ImageFont.truetype(str(FONTS_DIR / "segoeuib.ttf"), 16)
    draw.text(
        (20, 12),
        f"{title} — SOL: Orijinal (EN)   |   SAĞ: Türkçe (TR)",
        font=lbl_font,
        fill=(230, 190, 95),
    )

    x1 = (card_w // 2 - disp_w) // 2
    x2 = card_w // 2 + (card_w // 2 - disp_w) // 2
    card.paste(left, (x1, 48))
    card.paste(right, (x2, 48))
    draw.rectangle([x1 - 1, 47, x1 + disp_w, 48 + disp_h], outline=(80, 80, 100))
    draw.rectangle([x2 - 1, 47, x2 + disp_w, 48 + disp_h], outline=(180, 140, 65))
    return card


def main() -> None:
    p_load = next(TEX_DIR.glob("Loading_moji*"))
    im_load_en = Image.open(p_load)
    im_load_tr = render_loading_tr(im_load_en)
    make_comparison_card(im_load_en, im_load_tr, "1. Yükleme Ekranı (loadmes.en)").save(
        OUT_DIR / "preview_01_loading.png"
    )

    p_narumi = next(TEX_DIR.glob("shop_parts_moji_narumi*"))
    im_narumi_en = Image.open(p_narumi)
    im_narumi_tr = render_agency_sign(im_narumi_en.size, "Narumi Dedektiflik Bürosu")
    make_comparison_card(im_narumi_en, im_narumi_tr, "2. Büro Tabelası (ui_office_tex.en)").save(
        OUT_DIR / "preview_02_narumi.png"
    )

    p_nodata = next(TEX_DIR.glob("saveload_nodata-*"))
    im_nodata_en = Image.open(p_nodata)
    im_nodata_tr = render_saveload_tag(im_nodata_en.size, "VERİ YOK")
    make_comparison_card(
        im_nodata_en, im_nodata_tr, "3. Kayıt Ekranı Etiketi (saveloadui_tex.en)"
    ).save(OUT_DIR / "preview_03_saveload.png")

    p_map = next(TEX_DIR.glob("m_name003_00*"))
    im_map_en = Image.open(p_map)
    im_map_tr = render_map_title(im_map_en.size, "Eğlence Mahallesi", "Senju-Ku")
    make_comparison_card(im_map_en, im_map_tr, "4. Bölge Giriş Başlığı (maptitle_tex.en)").save(
        OUT_DIR / "preview_04_maptitle.png"
    )

    p_ep1 = next(TEX_DIR.glob("title01_start*--7353591269587420270.png"))
    im_ep1_en = Image.open(p_ep1)
    im_ep1_tr = render_episode_title(im_ep1_en.size, "1. Bölüm", "Kayıp Kız")
    make_comparison_card(
        im_ep1_en,
        im_ep1_tr,
        "5. Bölüm Başlangıç Ekranı (cutin_tex.en)",
        bg_color=(215, 198, 165),
    ).save(OUT_DIR / "preview_05_episode1.png")

    p_fail = next(TEX_DIR.glob("Investigation_Failed*"))
    im_fail_en = Image.open(p_fail)
    im_fail_tr = render_centered_serif(im_fail_en.size, "Soruşturma Başarısız", 156, (255, 255, 255))
    make_comparison_card(im_fail_en, im_fail_tr, "6. Oyun Bitti Ekranı (failed_sousa.en)").save(
        OUT_DIR / "preview_06_failed.png"
    )
    print("UTF-8 Previews generated.")


if __name__ == "__main__":
    main()
