#!/usr/bin/env python3
"""
Acme Agency — Autonomous creative iteration script.

Pattern:
- Reads angles_pool.json
- Reads state.json to know which angles are already used
- Picks next 5 unused angles (rotates when pool exhausts)
- Renders each via fal.ai + PIL into iterations/iter-N-YYYYMMDD-HHMM/
- Updates state.json (used_angles, last_iteration, timestamps)
- Writes iteration-summary.md with all angles + file paths

Usage:
  FAL_KEY=... python3 build_iteration.py
  FAL_KEY=... python3 build_iteration.py --count 5 --iteration N

Exits with code 0 on success, 1 on failure.
Designed to be invoked by launchd every 2 hours.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import traceback
from datetime import datetime
from pathlib import Path

import fal_client
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PIPELINE = Path("~/skills/projects/client-slug/05-meta-ads/pipeline")
ITERATIONS = Path("~/skills/projects/client-slug/05-meta-ads/iterations")
FONTS = Path("~/skills/projects/client-slug/05-meta-ads/assets/fonts")
POOL_PATH = PIPELINE / "angles_pool.json"
STATE_PATH = PIPELINE / "state.json"
LOG_PATH = PIPELINE / "pipeline.log"

# Palette
NAVY = (10, 22, 40)
NAVY_DEEP = (4, 12, 26)
OFFWHITE = (245, 240, 230)
CREAM = (228, 218, 198)
ORANGE = (255, 90, 31)
LIME = (216, 255, 60)
GREEN = (34, 172, 128)
RED = (220, 48, 36)
GREY = (145, 155, 175)
GREY_DARK = (55, 65, 85)

IS_REG = str(FONTS / "InstrumentSerif-Regular.ttf")
IS_ITA = str(FONTS / "InstrumentSerif-Italic.ttf")
SPG = str(FONTS / "SpaceGrotesk-Bold.ttf")

MAX_ITERATIONS = int(os.environ.get("MAX_ITER", "6"))


def log(msg):
    line = f"[{datetime.now().isoformat()}] {msg}\n"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line)
    print(line, end="")


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"iteration": 0, "used_angles": [], "runs": []}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def load_pool():
    return json.loads(POOL_PATH.read_text())["angles"]


def pick_angles(pool, used, count):
    available = [a for a in pool if a["id"] not in used]
    if len(available) < count:
        # rotate — reset used
        log(f"Pool exhausted ({len(used)}/{len(pool)}). Resetting rotation.")
        used = []
        available = pool[:]
    random.shuffle(available)
    return available[:count]


# ----------------------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------------------

def ft(p, s):
    return ImageFont.truetype(p, s)


def wrap(d, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if d.textlength(t, font=f) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rr(d, xy, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def pill(d, x, y, w, h, text, bg, fg):
    rr(d, (x, y, x + w, y + h), r=h // 2, fill=bg)
    f = ft(SPG, int(h * 0.40))
    tw = d.textlength(text, font=f)
    b = f.getbbox(text)
    d.text((x + (w - tw) / 2, y + (h - (b[3] - b[1])) / 2 - b[1]), text, font=f, fill=fg)


def logo(d, x, y, size, color=OFFWHITE, accent=ORANGE):
    f = ft(SPG, size)
    d.text((x, y), "Acme", font=f, fill=color)
    w = d.textlength("Acme", font=f)
    d.rectangle((x, y + size + 4, x + w * 0.32, y + size + 9), fill=accent)


def chip(d, x, y, label, size, bg, fg, pad=22):
    f = ft(SPG, size)
    tw = d.textlength(label, font=f)
    h = int(size * 2.0)
    rr(d, (x, y, x + tw + pad * 2, y + h), r=h // 2, fill=bg)
    b = f.getbbox(label)
    d.text((x + pad, y + (h - (b[3] - b[1])) / 2 - b[1]), label, font=f, fill=fg)
    return h


def gradient_bg(W, H, top, bottom):
    im = Image.new("RGB", (W, H), top)
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / (H - 1)
        c = tuple(int(top[i] * (1 - k) + bottom[i] * k) for i in range(3))
        d.line((0, y, W, y), fill=c)
    return im


# ----------------------------------------------------------------------
# Background themes
# ----------------------------------------------------------------------

def theme_bg(theme, W, H, prompt=None):
    if theme == "navy_deep":
        return gradient_bg(W, H, NAVY, NAVY_DEEP), {"text": OFFWHITE, "muted": GREY, "accent": ORANGE, "serif_accent": CREAM}
    if theme == "light_cream":
        return gradient_bg(W, H, OFFWHITE, (232, 222, 204)), {"text": NAVY, "muted": GREY_DARK, "accent": ORANGE, "serif_accent": NAVY}
    if theme == "light_editorial":
        return gradient_bg(W, H, (250, 246, 237), (240, 232, 218)), {"text": NAVY, "muted": GREY_DARK, "accent": ORANGE, "serif_accent": NAVY}
    if theme == "portrait_dark" and prompt:
        bg = fal_bg(prompt, W, H)
        if bg.size != (W, H):
            bg = bg.resize((W, H), Image.LANCZOS)
        # Global navy overlay strong enough for text on ANY photo zone
        # Then an accent darker band in the text area (top half) for hero legibility
        overlay = Image.new("RGBA", (W, H), (6, 14, 26, 160))  # navy ~63% alpha global
        od = ImageDraw.Draw(overlay)
        # Reinforced top band covering logo + chip + hero + sub (y 0 to 0.58*H)
        for y in range(int(H * 0.58)):
            extra = int(70 * (1 - y / (H * 0.58)))  # stronger at top, fading down
            od.rectangle((0, y, W, y + 1), fill=(6, 14, 26, min(255, 160 + extra)))
        # Bottom softer gradient to keep portrait visible center
        for y in range(int(H * 0.72), H):
            extra = int(80 * ((y - H * 0.72) / (H * 0.28)))
            od.rectangle((0, y, W, y + 1), fill=(6, 14, 26, min(255, 160 + extra)))
        im = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
        return im, {"text": OFFWHITE, "muted": (200, 210, 225), "accent": ORANGE, "serif_accent": CREAM}
    if theme == "split":
        im = Image.new("RGB", (W, H), OFFWHITE)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, W, H // 2), fill=NAVY)
        return im, {"text": NAVY, "muted": GREY_DARK, "accent": ORANGE, "serif_accent": CREAM, "top_text": OFFWHITE}
    # fallback
    return gradient_bg(W, H, NAVY, NAVY_DEEP), {"text": OFFWHITE, "muted": GREY, "accent": ORANGE, "serif_accent": CREAM}


def fal_bg(prompt, w, h):
    full_prompt = (
        prompt
        + ", editorial magazine photography, 35mm film, muted palette cream and navy, "
        "cinematic depth of field, natural window light, documentary photojournalism"
    )
    result = fal_client.subscribe(
        "fal-ai/flux/schnell",
        arguments={"prompt": full_prompt, "image_size": {"width": w, "height": h},
                   "num_inference_steps": 4, "num_images": 1},
        with_logs=False,
    )
    url = result["images"][0]["url"]
    from io import BytesIO
    return Image.open(BytesIO(requests.get(url, timeout=60).content)).convert("RGB")


# ----------------------------------------------------------------------
# Generic composer — one creative from angle spec
# ----------------------------------------------------------------------

def render_angle(angle, out_folder):
    fmt = angle.get("format", "feed-4x5")
    if fmt == "feed-4x5":
        W, H = 1080, 1350
    elif fmt == "story-9x16":
        W, H = 1080, 1920
    else:
        W, H = 1080, 1080

    # background
    prompt_for_bg = {
        "B-romain-manifesto": "portrait of a mid-30s French tech founder, short dark hair, white shirt, minimalist Paris office, bokeh, looking slightly off-camera",
        "S-reels-teaser-romain": "close-up portrait of a 30s French tech founder, white shirt, talking into the camera, blurred bright Paris office behind",
    }
    im, pal = theme_bg(angle["bg_theme"], W, H, prompt=prompt_for_bg.get(angle["id"]))
    d = ImageDraw.Draw(im)

    # --- logo top-left
    is_dark = angle["bg_theme"] in ("navy_deep", "portrait_dark")
    logo(d, int(W * 0.065), int(H * 0.055), int(W * 0.030),
         color=pal["text"], accent=pal["accent"])

    # --- eyebrow chip
    cat_label = {
        "scarcity": "ACCÈS LIMITÉ",
        "personal_story": "ROMAIN · FONDATEUR",
        "social_proof": "CAS CLIENT · BookNow",
        "case_study": "CAS CLIENT",
        "authority": "LE PACTE Acme",
        "manifesto": "LE PACTE Acme",
        "comparative": "COMPARATIF",
        "transparency": "DEVIS Acme",
        "lead_magnet": "FAIS LE TEST",
        "before_after": "AVANT · APRÈS",
        "product_showcase": "CE QU'ON LIVRE",
        "common_enemy": "VÉRITÉ OPÉRATIONNELLE",
        "video_teaser": "REELS · 30 S",
        "trust_seal": "GARANTIE Acme",
    }.get(angle["category"], "LE PACTE Acme")
    chip_bg = pal["accent"] if is_dark else NAVY
    chip_fg = OFFWHITE
    chip(d, int(W * 0.065), int(H * 0.15), cat_label, int(W * 0.018), chip_bg, chip_fg)

    # --- hero hook (Instrument Serif italic)
    hook = angle["hook"]
    hook_size = int(W * 0.070)
    hook_ft = ft(IS_ITA, hook_size)
    # fit : max 3 lines
    hook_lines = wrap(d, hook, hook_ft, int(W * 0.87))
    while len(hook_lines) > 3 and hook_size > 40:
        hook_size -= 4
        hook_ft = ft(IS_ITA, hook_size)
        hook_lines = wrap(d, hook, hook_ft, int(W * 0.87))
    hy = int(H * 0.22)
    line_h = int(hook_size * 1.08)
    for i, ln in enumerate(hook_lines):
        d.text((int(W * 0.065), hy + i * line_h), ln, font=hook_ft, fill=pal["text"])
    hook_end = hy + len(hook_lines) * line_h

    # accent line
    d.rectangle((int(W * 0.065), hook_end + 10,
                 int(W * 0.065) + int(W * 0.14), hook_end + 10 + 6),
                fill=pal["accent"])

    # --- sub line (Instrument Serif italic smaller or cream)
    sub = angle.get("sub", "")
    if sub:
        sub_ft = ft(IS_ITA, int(W * 0.042))
        sub_y = hook_end + int(W * 0.05)
        sub_lines = wrap(d, sub, sub_ft, int(W * 0.87))
        for i, ln in enumerate(sub_lines):
            d.text((int(W * 0.065), sub_y + i * int(W * 0.048)), ln,
                   font=sub_ft, fill=pal["serif_accent"])
        sub_end = sub_y + len(sub_lines) * int(W * 0.048)
    else:
        sub_end = hook_end + int(W * 0.05)

    # --- divider
    div_y = sub_end + int(W * 0.04)
    d.rectangle((int(W * 0.065), div_y, W - int(W * 0.065), div_y + 2),
                fill=(pal["muted"][0]//2 + 50, pal["muted"][1]//2 + 50, pal["muted"][2]//2 + 60) if is_dark else (200, 190, 170))

    # --- body (Space Grotesk regular-ish)
    body = angle.get("body", "")
    body_ft = ft(SPG, int(W * 0.024))
    body_y = div_y + int(W * 0.04)
    # support body with \n
    body_lines_out = []
    for para in body.split("\n"):
        body_lines_out.extend(wrap(d, para, body_ft, int(W * 0.87)))
        body_lines_out.append("")
    if body_lines_out and body_lines_out[-1] == "":
        body_lines_out.pop()
    for i, ln in enumerate(body_lines_out):
        d.text((int(W * 0.065), body_y + i * int(W * 0.033)),
               ln, font=body_ft, fill=pal["muted"])

    # --- CTA
    cta_w = int(W * 0.78)
    cta_h = int(W * 0.085)
    cta_x = (W - cta_w) / 2
    cta_y = H - int(H * 0.085) - cta_h
    cta_bg = pal["accent"]
    cta_fg = OFFWHITE
    pill(d, cta_x, cta_y, cta_w, cta_h, angle.get("cta", "Prendre 30 min"), cta_bg, cta_fg)

    # --- save
    out = out_folder / f"{angle['id']}.png"
    im.save(out, "PNG", optimize=True)
    log(f"Rendered {out.name} ({W}x{H})")
    return out


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--force", action="store_true", help="ignore MAX_ITERATIONS cap")
    args = parser.parse_args()

    if "FAL_KEY" not in os.environ:
        log("ERROR: FAL_KEY not set")
        sys.exit(1)

    state = load_state()
    if state["iteration"] >= MAX_ITERATIONS and not args.force:
        log(f"Reached MAX_ITERATIONS={MAX_ITERATIONS}. Skipping.")
        sys.exit(0)

    pool = load_pool()
    log(f"Pool size: {len(pool)}  used: {len(state['used_angles'])}")

    picked = pick_angles(pool, state["used_angles"], args.count)
    if not picked:
        log("No angles to pick. Exit.")
        sys.exit(0)

    state["iteration"] += 1
    iter_id = state["iteration"]
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    iter_folder = ITERATIONS / f"iter-{iter_id:02d}-{ts}"
    iter_folder.mkdir(parents=True, exist_ok=True)

    log(f"=== Iteration {iter_id} @ {ts} ===")
    log(f"Picked: {[a['id'] for a in picked]}")

    rendered = []
    for angle in picked:
        try:
            path = render_angle(angle, iter_folder)
            rendered.append({"id": angle["id"], "name": angle["name"],
                             "path": str(path), "category": angle["category"]})
            state["used_angles"].append(angle["id"])
        except Exception as e:
            log(f"ERROR rendering {angle['id']}: {e}")
            log(traceback.format_exc())

    # summary
    summary = [f"# Iteration {iter_id} — {ts}", ""]
    summary.append(f"**Créatives générées** : {len(rendered)} / {len(picked)} demandées")
    summary.append("")
    for r in rendered:
        summary.append(f"- **{r['id']}** — {r['name']} · catégorie `{r['category']}` · `{Path(r['path']).name}`")
    summary.append("")
    (iter_folder / "iteration-summary.md").write_text("\n".join(summary))

    state["runs"].append({"iteration": iter_id, "timestamp": ts,
                          "folder": str(iter_folder), "count": len(rendered)})
    save_state(state)

    log(f"Iteration {iter_id} complete. {len(rendered)} creatives in {iter_folder}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log("FATAL: " + traceback.format_exc())
        sys.exit(1)
