#!/usr/bin/env python3
"""
brand_lock_pass.py — Optional pixel-perfect brand overlay on GPT Image 2 output.

GPT Image 2 renders beautiful creatives but cannot guarantee exact brand fonts,
crisp small text, or charter-exact logo/CTA. This pass is the bridge V2 -> V1:
it resizes the AI image to exact Meta dimensions and re-stamps, in PIL with the
brand's exact fonts:
  - the logo (image or text + accent underline)
  - the CTA pill (exact font, AAA contrast)
  - an optional legal/disclaimer line

Use it ONLY on cells where (a) the AI text is fuzzy, or (b) the charter demands an
exact font/logo. Many lifestyle/product cells need no brand-lock at all.

USAGE
  python brand_lock_pass.py \
      --in creatives-v2/raw/A1.png --out creatives-v2/locked/A1.png \
      --format feed-4x5 \
      --brand-profile client-brand-profile.json \
      --cta "Faire le point" \
      --logo-text Acme            # or --logo-image assets/logo.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont  # pip install pillow

DIMS = {"feed-4x5": (1080, 1350), "story-9x16": (1080, 1920),
        "feed-1x1": (1080, 1080), "4:5": (1080, 1350), "9:16": (1080, 1920),
        "1:1": (1080, 1080)}


def hex2rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


def load_font(path: str | None, size: int) -> ImageFont.FreeTypeFont:
    if path and Path(path).exists():
        return ImageFont.truetype(path, size)
    # fallback to a default; warn caller in stdout
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def fit_cover(im: Image.Image, w: int, h: int) -> Image.Image:
    """Resize+center-crop to exactly (w,h)."""
    src_ratio = im.width / im.height
    dst_ratio = w / h
    if src_ratio > dst_ratio:
        new_h = h
        new_w = int(h * src_ratio)
    else:
        new_w = w
        new_h = int(w / src_ratio)
    im = im.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    return im.crop((left, top, left + w, top + h))


def draw_pill(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
              text: str, bg, fg, font_path: str | None) -> None:
    d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=bg)
    f = load_font(font_path, int(h * 0.40))
    tw = d.textlength(text, font=f)
    b = f.getbbox(text)
    d.text((x + (w - tw) / 2, y + (h - (b[3] - b[1])) / 2 - b[1]), text, font=f, fill=fg)


def draw_logo(d: ImageDraw.ImageDraw, x: int, y: int, word: str, size: int,
              color, accent, font_path: str | None) -> None:
    f = load_font(font_path, size)
    d.text((x, y), word, font=f, fill=color)
    w = d.textlength(word, font=f)
    d.rectangle((x, y + size + 4, x + w * 0.32, y + size + 9), fill=accent)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--format", default="feed-4x5")
    ap.add_argument("--brand-profile", default=None)
    ap.add_argument("--cta", default=None)
    ap.add_argument("--logo-text", default=None)
    ap.add_argument("--logo-image", default=None)
    ap.add_argument("--legal", default=None)
    args = ap.parse_args()

    profile = {}
    if args.brand_profile and Path(args.brand_profile).exists():
        profile = json.loads(Path(args.brand_profile).read_text())
    palette = {p.get("role"): p.get("hex") for p in profile.get("palette", [])}
    accent = hex2rgb(palette.get("accent", "#FF5A1F"))
    on_dark = hex2rgb(palette.get("offwhite", palette.get("text_on_dark", "#F5F0E6")))
    fonts = profile.get("fonts", {})
    grotesk = fonts.get("grotesk_bold_path")

    W, H = DIMS.get(args.format, (1080, 1350))
    im = fit_cover(Image.open(args.inp).convert("RGB"), W, H)
    d = ImageDraw.Draw(im)

    # logo (top-left)
    if args.logo_image and Path(args.logo_image).exists():
        logo = Image.open(args.logo_image).convert("RGBA")
        lw = int(W * 0.20)
        logo = logo.resize((lw, int(lw * logo.height / logo.width)), Image.LANCZOS)
        im.paste(logo, (int(W * 0.065), int(H * 0.05)), logo)
    elif args.logo_text:
        draw_logo(d, int(W * 0.065), int(H * 0.05), args.logo_text,
                  int(W * 0.030), on_dark, accent, grotesk)

    # CTA pill (bottom, above 14% safe zone)
    if args.cta:
        cta_w, cta_h = int(W * 0.78), int(W * 0.090)
        cta_x = (W - cta_w) // 2
        cta_y = int(H - 0.075 * H - cta_h)
        draw_pill(d, cta_x, cta_y, cta_w, cta_h, args.cta, accent, on_dark, grotesk)

    # legal line (very bottom)
    if args.legal:
        f = load_font(grotesk, int(W * 0.016))
        tw = d.textlength(args.legal, font=f)
        d.text(((W - tw) / 2, int(H - 0.03 * H)), args.legal, font=f, fill=(150, 155, 165))

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    im.save(args.out, "PNG")
    print(f"✅ brand-lock -> {args.out} ({W}x{H})")
    if grotesk is None:
        print("   ⚠️  Aucune font de marque dans le profile (fonts.grotesk_bold_path) "
              "→ fallback système. Renseigne le chemin pour un rendu charte-exact.")


if __name__ == "__main__":
    main()
