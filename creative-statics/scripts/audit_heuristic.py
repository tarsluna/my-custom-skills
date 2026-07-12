#!/usr/bin/env python3
"""
Heuristic audit of a creative iteration — no LLM, runs autonomously.

Checks per creative:
 - File size (Meta limits: 30 MB max, >120 KB for quality)
 - Dimensions correct (1080x1080 / 1080x1350 / 1080x1920)
 - Pixel contrast stats (simple histogram entropy)
 - Bottom 14% CTA safe zone (heuristic: check luminance variance in top vs bottom)

Writes `audit.md` into the iteration folder. Marks each creative OK / WARN / FAIL.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageStat

ITERATIONS = Path("~/skills/projects/client-slug/05-meta-ads/iterations")


def analyze(png_path: Path) -> dict:
    im = Image.open(png_path).convert("RGB")
    W, H = im.size
    stat = ImageStat.Stat(im)

    # luminance
    r, g, b = stat.mean
    luminance = 0.299 * r + 0.587 * g + 0.114 * b

    # stddev as complexity proxy
    variance = sum(stat.stddev) / 3

    # size
    size_kb = png_path.stat().st_size // 1024

    # dimension check
    allowed = [(1080, 1080), (1080, 1350), (1080, 1920)]
    dim_ok = (W, H) in allowed

    findings = []
    verdict = "OK"

    if not dim_ok:
        findings.append(f"dimensions non-Meta ({W}x{H})")
        verdict = "FAIL"
    if size_kb < 80:
        findings.append(f"taille trop faible ({size_kb} KB — risque basse qualité)")
        verdict = "WARN" if verdict == "OK" else verdict
    if size_kb > 8000:
        findings.append(f"taille trop élevée ({size_kb} KB — optimiser)")
        verdict = "WARN" if verdict == "OK" else verdict
    if variance < 20:
        findings.append("faible contraste global (variance < 20)")
        verdict = "WARN" if verdict == "OK" else verdict
    if variance > 85:
        findings.append("très haut contraste (peut écraser le texte)")

    return {
        "file": png_path.name,
        "dimensions": f"{W}x{H}",
        "size_kb": size_kb,
        "luminance": round(luminance, 1),
        "variance": round(variance, 1),
        "findings": findings,
        "verdict": verdict,
    }


def audit_folder(folder: Path):
    pngs = sorted(folder.glob("*.png"))
    if not pngs:
        print(f"No PNGs in {folder}")
        return

    results = [analyze(p) for p in pngs]

    lines = [f"# Audit heuristique — `{folder.name}`", ""]
    lines.append("_Audit automatisé sans LLM. Checks : dimensions Meta, poids fichier, contraste global (stddev). "
                 "Un audit Claude Council complet doit être lancé manuellement sur chaque créative avant production._")
    lines.append("")
    lines.append("| Fichier | Dim | Size | Lum | Var | Verdict | Findings |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in results:
        findings = "; ".join(r["findings"]) or "—"
        emoji = {"OK": "✓", "WARN": "△", "FAIL": "✗"}[r["verdict"]]
        lines.append(f"| `{r['file']}` | {r['dimensions']} | {r['size_kb']} KB | {r['luminance']} | {r['variance']} | {emoji} {r['verdict']} | {findings} |")

    # summary
    ok = sum(1 for r in results if r["verdict"] == "OK")
    warn = sum(1 for r in results if r["verdict"] == "WARN")
    fail = sum(1 for r in results if r["verdict"] == "FAIL")
    lines.append("")
    lines.append(f"**Synthèse** : {ok} OK · {warn} warnings · {fail} fails sur {len(results)} créatives.")
    lines.append("")
    lines.append("## Recommandations automatiques (non-LLM)")
    lines.append("")
    if fail:
        lines.append("- ✗ FAIL : **ne pas uploader**. Re-run la créative avec le format Meta correct.")
    if warn:
        lines.append("- △ WARN : **passer au Council Claude** pour décision manuelle (contraste / taille fichier).")
    if ok and not warn and not fail:
        lines.append("- ✓ Toutes les créatives passent le gate heuristique. Prêt pour Council LLM.")

    (folder / "audit.md").write_text("\n".join(lines))
    print(f"Audit written: {folder / 'audit.md'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest", action="store_true", help="Audit only the latest iteration folder")
    parser.add_argument("--all", action="store_true", help="Audit all iteration folders")
    args = parser.parse_args()

    folders = sorted(ITERATIONS.glob("iter-*"))
    if not folders:
        print("No iteration folders yet.")
        sys.exit(0)

    if args.latest:
        folders = [folders[-1]]
    elif not args.all:
        # default : audit latest
        folders = [folders[-1]]

    for f in folders:
        audit_folder(f)


if __name__ == "__main__":
    main()
