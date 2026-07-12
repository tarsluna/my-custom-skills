#!/usr/bin/env python3
"""
audit_heuristic.py — LLM-free quality gate for V2 creatives.

Checks each PNG against Meta hard constraints + basic quality signals:
  - dimensions in {1080x1080, 1080x1350, 1080x1920}  (FAIL if not)
  - file weight in [80 KB, 8 MB]                       (WARN if out)
  - global contrast (stddev of luma)                   (WARN if flat)
  - bottom 14% safe-zone "busyness" (text likely too low) (WARN, heuristic)

It does NOT judge aesthetics or AI artifacts — that's the Council's job (seat #5).
Auto-resizes/pads to the nearest valid Meta dimension when --fix is passed.

USAGE
  python audit_heuristic.py --dir creatives-v2/locked
  python audit_heuristic.py --dir creatives-v2/raw --fix
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageStat  # pip install pillow

VALID = {(1080, 1080), (1080, 1350), (1080, 1920)}
NEAREST = [(1080, 1080), (1080, 1350), (1080, 1920)]
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def nearest_dim(w: int, h: int) -> tuple[int, int]:
    ratio = h / w if w else 1
    targets = {1.0: (1080, 1080), 1.25: (1080, 1350), 1.777: (1080, 1920)}
    best = min(targets, key=lambda r: abs(r - ratio))
    return targets[best]


def fit_cover(im: Image.Image, w: int, h: int) -> Image.Image:
    sr, dr = im.width / im.height, w / h
    if sr > dr:
        nw, nh = int(h * sr), h
    else:
        nw, nh = w, int(w / sr)
    im = im.resize((nw, nh), Image.LANCZOS)
    l, t = (nw - w) // 2, (nh - h) // 2
    return im.crop((l, t, l + w, t + h))


def audit_one(p: Path, fix: bool) -> dict:
    im = Image.open(p).convert("RGB")
    w, h = im.size
    weight = p.stat().st_size
    res = {"file": p.name, "dim": f"{w}x{h}", "weight_kb": round(weight / 1024)}
    flags = []

    if (w, h) not in VALID:
        if fix:
            tw, th = nearest_dim(w, h)
            fit_cover(im, tw, th).save(p, "PNG")
            res["fixed_to"] = f"{tw}x{th}"
            w, h = tw, th
        else:
            flags.append(f"DIM_FAIL({w}x{h})")

    if weight < 80 * 1024:
        flags.append("WEIGHT_LOW(<80KB)")
    elif weight > 8 * 1024 * 1024:
        flags.append("WEIGHT_HIGH(>8MB)")

    gray = im.convert("L")
    stdev = ImageStat.Stat(gray).stddev[0]
    res["contrast_stddev"] = round(stdev, 1)
    if stdev < 20:
        flags.append("CONTRAST_FLAT")
    elif stdev > 90:
        flags.append("CONTRAST_HARSH")

    # bottom 14% busyness: high local variance => text likely in the Meta safe zone
    bw, bh = im.size
    bottom = gray.crop((0, int(bh * 0.86), bw, bh))
    if ImageStat.Stat(bottom).stddev[0] > 55:
        flags.append("BOTTOM_SAFEZONE_BUSY")

    res["flags"] = flags
    res["status"] = "PASS" if not any(f.endswith("FAIL") or f == "DIM_FAIL" for f in flags) \
        and not any("DIM_FAIL" in f for f in flags) else "FAIL"
    res["status"] = "FAIL" if any("DIM_FAIL" in f for f in flags) else ("WARN" if flags else "PASS")
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--fix", action="store_true", help="resize/pad au format Meta le plus proche")
    args = ap.parse_args()

    files = [p for p in sorted(Path(args.dir).rglob("*")) if p.suffix.lower() in IMG_EXT]
    if not files:
        raise SystemExit(f"Aucune image dans {args.dir}")

    npass = nwarn = nfail = 0
    for p in files:
        r = audit_one(p, args.fix)
        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}[r["status"]]
        extra = (" " + " ".join(r["flags"])) if r["flags"] else ""
        fixed = f" -> {r['fixed_to']}" if r.get("fixed_to") else ""
        print(f"{icon} {r['file']:40s} {r['dim']}{fixed} {r['weight_kb']}KB"
              f" σ={r['contrast_stddev']}{extra}")
        npass += r["status"] == "PASS"
        nwarn += r["status"] == "WARN"
        nfail += r["status"] == "FAIL"

    print(f"\n{npass} PASS · {nwarn} WARN · {nfail} FAIL  (sur {len(files)})")
    if nfail and not args.fix:
        print("→ relance avec --fix pour corriger les dimensions.")


if __name__ == "__main__":
    main()
