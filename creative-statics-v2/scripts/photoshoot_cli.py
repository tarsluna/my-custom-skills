#!/usr/bin/env python3
"""
photoshoot_cli.py — PREFERRED generation engine: drive the official Higgsfield CLI
`higgsfield product-photoshoot create`.

WHY THIS, NOT raw gpt_image2_generate.py:
  The official `higgsfield product-photoshoot create --mode <mode>` command calls a
  SERVER-SIDE prompt enhancer that holds mode-specific photography vocabulary, then
  submits to gpt_image_2. Calling gpt_image_2 directly BYPASSES that enhancer and
  produces "noticeably worse output" (per higgsfield-ai/skills). So for ad-grade
  quality we wrap the CLI and feed it a SHORT intent prompt + mode + reference images;
  the backend assembles the full prompt.

Ported from github.com/higgsfield-ai/skills (MIT, © 2026 Higgsfield AI). See NOTICE.md.

PREREQS
  - higgsfield CLI on PATH:  curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh
  - authenticated:           higgsfield auth login   (interactive — ask the user)
  - paid plan for some modes; credits are ALWAYS consumed via CLI (no unlimited).

USAGE
  # one cell
  python photoshoot_cli.py \
      --mode ad_creative_pack \
      --intent "cold-brew bottle, premium DTC ad, 'réveille-toi vraiment' hook" \
      --image ./assets/bottle.jpg --image ./assets/logo.png \
      --count 1 --aspect-ratio 4:5 \
      --out ./creatives-v2/raw/A1.png

  # check the CLI is ready (no credits)
  python photoshoot_cli.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Official modes (from higgsfield-product-photoshoot SKILL.md, MIT).
MODES = [
    "product_shot", "lifestyle_scene", "closeup_product_with_person",
    "moodboard_pin", "hero_banner", "social_carousel", "ad_creative_pack",
    "virtual_model_tryout", "conceptual_product", "restyle",
]
ALLOWED_AR = {"1:1", "4:5", "5:4", "3:4", "4:3", "2:3", "3:2", "9:16", "16:9"}
URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+\.(?:jpg|jpeg|png|webp)", re.I)


def cli_path() -> str | None:
    return shutil.which("higgsfield")


def check(verbose: bool = True) -> bool:
    hf = cli_path()
    if not hf:
        if verbose:
            print("❌ CLI 'higgsfield' absente. Installe:\n"
                  "   curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh",
                  file=sys.stderr)
        return False
    try:
        r = subprocess.run([hf, "account", "status"], capture_output=True, text=True, timeout=30)
        out = (r.stdout + r.stderr).lower()
        if "not authenticated" in out or "session expired" in out:
            if verbose:
                print("❌ Non authentifié. Lance:  higgsfield auth login",
                      file=sys.stderr)
            return False
        if verbose:
            print("clé/CLI configurée ✅ (compte Higgsfield actif)")
        return True
    except Exception as e:  # noqa
        if verbose:
            print(f"⚠️  `higgsfield account status` a échoué: {e}", file=sys.stderr)
        return False


def generate(mode: str, intent: str, images: list[str], count: int,
             aspect_ratio: str | None, out_path: str, timeout: int = 600) -> dict:
    hf = cli_path()
    if not hf:
        raise RuntimeError("CLI higgsfield absente (voir --check).")
    if mode not in MODES:
        raise ValueError(f"mode invalide '{mode}'. Valides: {', '.join(MODES)}")

    cmd = [hf, "product-photoshoot", "create", "--mode", mode, "--prompt", intent,
           "--count", str(count)]
    for img in images:
        cmd += ["--image", img]
    if aspect_ratio:
        if aspect_ratio not in ALLOWED_AR:
            raise ValueError(f"aspect_ratio '{aspect_ratio}' non supporté. {sorted(ALLOWED_AR)}")
        cmd += ["--aspect_ratio", aspect_ratio]

    print(f"→ higgsfield product-photoshoot create --mode {mode} "
          f"--count {count} {'--aspect_ratio '+aspect_ratio if aspect_ratio else ''} "
          f"(images={len(images)})")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    stdout = r.stdout or ""
    if r.returncode != 0:
        raise RuntimeError(f"CLI exit {r.returncode}: {(r.stderr or stdout)[:300]}")

    urls = URL_RE.findall(stdout)
    if not urls:
        raise RuntimeError(f"Aucune URL image dans la sortie CLI: {stdout[:300]}")

    outs = []
    base = Path(out_path)
    for i, url in enumerate(urls):
        p = base if (count == 1 and len(urls) == 1) else base.with_name(f"{base.stem}-{i+1}{base.suffix}")
        _download(url, str(p))
        outs.append(str(p))
        print(f"✅ {p}")
    return {"engine": "cli", "mode": mode, "urls": urls, "outs": outs, "count": count}


def _download(url: str, out_path: str) -> None:
    import urllib.request
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, out_path)


def main() -> None:
    ap = argparse.ArgumentParser(description="Higgsfield product-photoshoot CLI wrapper")
    ap.add_argument("--check", action="store_true", help="vérifie CLI + auth (no credits)")
    ap.add_argument("--mode", default="ad_creative_pack", choices=MODES)
    ap.add_argument("--intent", default=None, help="prompt COURT d'intention (l'enhancer serveur l'étend)")
    ap.add_argument("--image", action="append", default=[], help="référence (chemin/UUID). Répétable.")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--aspect-ratio", default=None)
    ap.add_argument("--out", default="out.png")
    args = ap.parse_args()

    if args.check:
        sys.exit(0 if check() else 1)
    if not args.intent:
        print("❌ --intent requis", file=sys.stderr)
        sys.exit(1)
    if not check(verbose=True):
        sys.exit(1)
    meta = generate(args.mode, args.intent, args.image, args.count,
                    args.aspect_ratio, args.out)
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
