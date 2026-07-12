#!/usr/bin/env python3
"""
build_variations.py — Orchestrate GPT Image 2 generation across the variation matrix.

Reads variation-matrix.json (Phase C/E output), generates each cell via
gpt_image2_generate.generate(), with:
  - prompt-hash caching (no refacturation of identical prompts)
  - --dry-run cost estimate (no credits) before a billed batch
  - per-cell try/except (one failure never kills the batch)
  - append-only logs

USAGE
  # estimate cost first (no credits)
  python build_variations.py --client studease --matrix variation-matrix.json --dry-run

  # run the batch (after G approves cost + slug confirmed)
  python build_variations.py --client studease --matrix variation-matrix.json \
      --resolution 2k --model-slug "openai/gpt-image-2/text-to-image"

Cost note: GPT Image 2 per-image credit cost depends on resolution. The estimate
uses --cost-per-image (default placeholder); set it to your real Higgsfield credit
rate. ALWAYS confirm the batch cost with the user before running billed.
"""
from __future__ import annotations

import argparse
import datetime as _dt  # noqa: F401  (only for type clarity; value passed in, not now())
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gpt_image2_generate as gen  # noqa: E402
import photoshoot_cli as cli  # noqa: E402
import engine_fal as falgen  # noqa: E402

# matrix format -> CLI aspect ratio
AR = {"feed-4x5": "4:5", "story-9x16": "9:16", "feed-1x1": "1:1",
      "4:5": "4:5", "9:16": "9:16", "1:1": "1:1"}


def log(line: str, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")
    print(line)


def prompt_hash(cell: dict) -> str:
    blob = json.dumps({
        "prompt": cell.get("prompt", ""),
        "render": cell.get("render", {}),
        "refs": sorted(cell.get("brand_assets", []) + ([cell["style_ref"]] if cell.get("style_ref") else [])),
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def cell_refs(cell: dict) -> list[str]:
    refs = list(cell.get("brand_assets", []))
    if cell.get("style_ref"):
        refs.append(cell["style_ref"])
    return refs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", default=None)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--out-dir", default=None, help="défaut: <matrix_dir>/creatives-v2/raw")
    ap.add_argument("--resolution", default=None, help="override la résolution de toutes les cellules")
    ap.add_argument("--engine", default="fal", choices=["fal", "cli", "sdk"],
                    help="fal = GPT Image 2 via fal.ai (qualité max, scalable, DÉFAUT) ; "
                         "cli = `higgsfield product-photoshoot` (legacy, non scalable) ; "
                         "sdk = gpt_image_2 brut via Higgsfield (fallback)")
    ap.add_argument("--model-slug", default=None,
                    help="(engine fal/sdk) slug du modèle ; fal défaut = openai/gpt-image-2")
    ap.add_argument("--dry-run", action="store_true", help="estime le coût, ne génère rien")
    ap.add_argument("--cost-per-image", type=float, default=1.0,
                    help="crédits/image (vérifié mai 2026: GPT Image 2 = 1 cr ≈ $0.07 ; "
                         "Soul 2.0 = 0.12 cr ≈ $0.009 ; Nano Banana Pro = 2 cr)")
    ap.add_argument("--only-status", default="pending",
                    help="ne traiter que les cellules à ce status (défaut: pending)")
    ap.add_argument("--max", type=int, default=0, help="cap nb de cellules (0=illimité)")
    args = ap.parse_args()

    matrix_path = Path(args.matrix)
    matrix = json.loads(matrix_path.read_text())
    cells = matrix.get("cells", matrix if isinstance(matrix, list) else [])
    todo = [c for c in cells if c.get("status", "pending") == args.only_status]
    if args.max:
        todo = todo[: args.max]

    out_dir = Path(args.out_dir) if args.out_dir else matrix_path.parent / "creatives-v2" / "raw"
    cache_dir = matrix_path.parent / "creatives-v2" / ".cache"
    log_path = matrix_path.parent / "creatives-v2" / "logs" / "build.log"

    # ---- dry-run: cost estimate, no credits --------------------------------
    print(f"Cellules à traiter: {len(todo)} (status={args.only_status})")
    if args.dry_run:
        est = len(todo) * args.cost_per_image
        by_res: dict[str, int] = {}
        for c in todo:
            r = args.resolution or c.get("render", {}).get("resolution", "2k")
            by_res[r] = by_res.get(r, 0) + 1
        if args.engine == "fal":
            usd = len(todo) * 0.21  # GPT Image 2 high via fal.ai ≈ $0.21/image
            print("— DRY RUN — aucun appel fal")
            print(f"  par résolution: {by_res}")
            print(f"  coût estimé (fal · GPT Image 2 high): ~${usd:.2f} (~$0.21/image)")
            print("  ➜ Clé FAL_KEY requise (alimentée). Plus de CLI Higgsfield.")
            return
        print("— DRY RUN — aucun crédit consommé")
        print(f"  par résolution: {by_res}")
        if args.cost_per_image:
            usd = est * 0.0714  # basic plan: $5 / 70 credits ≈ $0.0714/credit
            print(f"  coût estimé: {est:.1f} crédits ≈ ${usd:.2f} "
                  f"({args.cost_per_image} cr/image · tarif basic plan)")
        else:
            print("  ⚠️  --cost-per-image=0 → mets ton tarif réel pour estimer.")
        print("  ➜ Crédits TOUJOURS consommés en API (pas d'unlimited hors web app).")
        print("  ➜ Fais valider ce coût + le slug GPT Image 2 à G AVANT le batch facturé.")
        return

    # ---- real batch --------------------------------------------------------
    if args.engine == "cli":
        if not cli.check():
            print("❌ Engine cli indisponible. Installe/auth la CLI higgsfield, "
                  "ou relance avec --engine fal.", file=sys.stderr)
            sys.exit(1)
        slug = "cli:product-photoshoot"
    elif args.engine == "fal":
        slug = falgen.default_model(args.model_slug)
    else:
        slug = gen.resolve_gpt_image2_slug(args.model_slug)
    log(f"=== batch start engine={args.engine} slug={slug} cells={len(todo)} ===", log_path)
    done = skipped = failed = 0
    results = []

    for i, cell in enumerate(todo, 1):
        cid = cell.get("id", f"cell-{i}")
        h = prompt_hash(cell)
        ext = ".png"
        out_path = out_dir / f"{cid}{ext}"
        cache_hit = cache_dir / f"{h}{ext}"

        needs = "mode/intent" if args.engine == "cli" else "prompt"
        ok = (cell.get("mode") and cell.get("intent")) if args.engine == "cli" else cell.get("prompt")
        if not ok:
            log(f"[{i}/{len(todo)}] {cid} SKIP (pas de {needs})", log_path)
            skipped += 1
            continue

        if cache_hit.exists():
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(cache_hit.read_bytes())
            cell["status"] = "generated"
            cell["output"] = str(out_path)
            log(f"[{i}/{len(todo)}] {cid} CACHE {h}", log_path)
            skipped += 1
            continue

        res = args.resolution or cell.get("render", {}).get("resolution", "2k")
        ar = AR.get(cell.get("render", {}).get("aspect_ratio") or cell.get("format", "4:5"), "4:5")
        try:
            if args.engine == "cli":
                count = cell.get("count", 1)
                meta = cli.generate(cell["mode"], cell["intent"], cell_refs(cell),
                                    count, ar, str(out_path))
            elif args.engine == "fal":
                meta = falgen.generate(
                    slug, cell["prompt"], res, ar,
                    cell_refs(cell), None, str(out_path))
            else:
                meta = gen.generate(
                    slug, cell["prompt"], res, ar,
                    cell_refs(cell), None, str(out_path))
            # populate cache
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_hit.write_bytes(Path(out_path).read_bytes())
            cell["status"] = "generated"
            cell["output"] = str(out_path)
            cell["render_meta"] = meta
            results.append(meta)
            done += 1
            log(f"[{i}/{len(todo)}] {cid} OK {meta['seconds']}s -> {out_path}", log_path)
        except Exception as e:  # noqa
            cell["status"] = "error"
            cell["error"] = str(e)[:300]
            failed += 1
            log(f"[{i}/{len(todo)}] {cid} FAIL {str(e)[:200]}", log_path)
        time.sleep(0.5)  # gentle pacing

    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2))
    log(f"=== batch done ok={done} cache/skip={skipped} fail={failed} ===", log_path)
    print(f"\n✅ {done} générées · {skipped} cache/skip · {failed} échecs")
    print(f"   raw: {out_dir}")
    print(f"   matrice mise à jour: {matrix_path}")


if __name__ == "__main__":
    main()
