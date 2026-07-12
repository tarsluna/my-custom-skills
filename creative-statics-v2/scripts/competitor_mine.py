#!/usr/bin/env python3
"""
competitor_mine.py — Turn 02-competitor-ads/data.csv into creative fuel.

Reads the competitor ads CSV and produces competitor-insights.json:
  - top_angles    : most frequent primary/secondary angles (+ their sample hooks)
  - saturated     : angles used by >= threshold competitors (banlist, unless twisted)
  - angle_hooks   : observed hooks per angle (to DETECT saturation, never to copy)
  - style_refs    : best competitor ad screenshots found in creatives/ (STYLE only)
  - white_space_candidates : ICP-relevant angles NOT present in the CSV (needs
                             human/Claude cross-ref with 01-deep-search/analysis.md)

CSV columns expected:
  competitor, category, observed_status, primary_angle, secondary_angle,
  likely_audience, sample_hook, inference_confidence, notes

USAGE
  python competitor_mine.py --client studease
  python competitor_mine.py --csv path/to/data.csv --creatives path/to/creatives \
      --out competitor-insights.json --saturation-threshold 3
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def find_client_paths(client: str) -> tuple[Path | None, Path | None]:
    """Locate data.csv and creatives/ for a client under projects."""
    for root in (Path.cwd(), *Path.cwd().parents):
        base = root / "Projects" / "the platform" / client / "02-competitor-ads"
        if base.exists():
            csv_p = base / "data.csv"
            cre_p = base / "creatives"
            return (csv_p if csv_p.exists() else None,
                    cre_p if cre_p.exists() else None)
    return None, None


def parse_csv(csv_path: Path) -> list[dict]:
    rows: list[dict] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({k: (v or "").strip() for k, v in r.items()})
    return rows


def mine(rows: list[dict], saturation_threshold: int) -> dict:
    angle_counter: Counter = Counter()
    angle_competitors: dict[str, set] = defaultdict(set)
    angle_hooks: dict[str, list] = defaultdict(list)
    confidence_weight = {"high": 1.0, "medium": 0.6, "low": 0.3}

    for r in rows:
        comp = r.get("competitor", "")
        conf = confidence_weight.get(norm(r.get("inference_confidence", "")), 0.5)
        for col in ("primary_angle", "secondary_angle"):
            a = norm(r.get(col, ""))
            if not a:
                continue
            angle_counter[a] += conf
            angle_competitors[a].add(comp)
            hook = r.get("sample_hook", "").strip()
            if hook:
                angle_hooks[a].append({"competitor": comp, "hook": hook,
                                       "confidence": r.get("inference_confidence", "")})

    top_angles = [
        {"angle": a, "weighted_score": round(score, 2),
         "n_competitors": len(angle_competitors[a]),
         "sample_hooks": [h["hook"] for h in angle_hooks[a][:3]]}
        for a, score in angle_counter.most_common()
    ]

    saturated = [a["angle"] for a in top_angles
                 if a["n_competitors"] >= saturation_threshold]

    return {
        "n_rows": len(rows),
        "n_competitors": len({r.get("competitor", "") for r in rows}),
        "verified_captures": sum(1 for r in rows
                                 if norm(r.get("observed_status", "")) == "verified_capture"),
        "top_angles": top_angles,
        "saturated": saturated,
        "angle_hooks": {a: angle_hooks[a] for a in angle_hooks},
    }


def find_style_refs(creatives_dir: Path | None, limit: int = 3) -> list[str]:
    if not creatives_dir or not creatives_dir.exists():
        return []
    imgs = [str(p) for p in sorted(creatives_dir.rglob("*"))
            if p.suffix.lower() in IMG_EXT]
    # heuristic: prefer larger files (usually higher-quality captures)
    imgs.sort(key=lambda p: Path(p).stat().st_size, reverse=True)
    return imgs[:limit]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", default=None)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--creatives", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--saturation-threshold", type=int, default=3)
    args = ap.parse_args()

    csv_path = Path(args.csv) if args.csv else None
    cre_path = Path(args.creatives) if args.creatives else None
    if args.client and not csv_path:
        csv_path, cre_path = find_client_paths(args.client)

    if not csv_path or not csv_path.exists():
        raise SystemExit(f"❌ data.csv introuvable (client={args.client} csv={args.csv}). "
                         "Lance d'abord competitor-ads-research.")

    rows = parse_csv(csv_path)
    insights = mine(rows, args.saturation_threshold)
    insights["style_refs"] = find_style_refs(cre_path)
    insights["white_space_candidates"] = []  # filled by Claude via analysis.md cross-ref
    insights["_note"] = ("white_space_candidates et le choix final des angles se font "
                         "en croisant top_angles/saturated avec 01-deep-search/analysis.md "
                         "(framework 02). style_refs = inspiration de STYLE uniquement, "
                         "jamais de copy concurrent.")

    out = Path(args.out) if args.out else csv_path.parent.parent / "05-meta-ads" / "competitor-insights.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(insights, ensure_ascii=False, indent=2))

    print(f"✅ {out}")
    print(f"   {insights['n_competitors']} concurrents, {insights['verified_captures']} captures vérifiées")
    print(f"   {len(insights['top_angles'])} angles, {len(insights['saturated'])} saturés, "
          f"{len(insights['style_refs'])} style_refs")
    if insights["saturated"]:
        print("   ⚠️  saturés (à éviter sans twist): " + ", ".join(insights["saturated"][:6]))


if __name__ == "__main__":
    main()
