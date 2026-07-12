#!/usr/bin/env python3
"""
engine_fal.py — fal.ai engine for the V2 static-creative pipeline.

Replaces the Higgsfield CLI/SDK as the generation backend. One provider, two
quality-first models (price is secondary by design):
  - GENERATION : OpenAI GPT Image 2   -> model "openai/gpt-image-2"   (best text-in-image)
  - EDIT       : Google Nano Banana Pro (Gemini 3 Pro Image, instruction edit)
                 -> model "fal-ai/nano-banana-pro/edit"

Uses fal's SYNCHRONOUS endpoint (https://fal.run/{model}) — submit + wait, one
image per call. Stdlib only (urllib), a browser-ish UA to avoid WAF blocks.

CREDENTIALS (never printed): FAL_KEY (or FAL_API_KEY) env, else a `FAL_KEY` line
in secrets/api-keys.md at the skills root. The key is funded later — calls fail
LOUDLY but cleanly (401/402) when it's missing/unfunded.

`generate()` mirrors gpt_image2_generate.generate() so build_variations.py can
call it the same way (engine "fal").

USAGE
  python engine_fal.py --prompt "..." --aspect-ratio 4:5 --out raw/A1.png
  python engine_fal.py --edit raw/A1.png --instruction "remplace 'X' par 'Y'" --out edited/A1.png
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

FAL_BASE = os.environ.get("FAL_BASE", "https://fal.run")
GEN_MODEL = "openai/gpt-image-2"
EDIT_MODEL = "fal-ai/nano-banana-pro/edit"
UA = "creative-statics-v2/1.0"

# GPT Image 2 supports 1024x1024 / portrait / landscape; map ad ratios onto them.
SIZE = {
    "1:1": "1024x1024", "feed-1x1": "1024x1024",
    "4:5": "1024x1536", "feed-4x5": "1024x1536",
    "9:16": "1024x1536", "story-9x16": "1024x1536",
    "16:9": "1536x1024", "1.91:1": "1536x1024",
}


# --- credentials ---------------------------------------------------------------
def resolve_key() -> str | None:
    """Return the fal key or None. NEVER print the value."""
    for var in ("FAL_KEY", "FAL_API_KEY"):
        v = os.environ.get(var)
        if v:
            return v.strip()
    for root in (Path.cwd(), *Path.cwd().parents):
        f = root / "secrets" / "api-keys.md"
        if f.exists():
            for line in f.read_text(errors="ignore").splitlines():
                if "FAL_KEY" in line or "FAL_API_KEY" in line:
                    for part in line.replace("`", " ").replace("=", " ").split():
                        if len(part) > 12 and ":" not in part[:4]:
                            return part.strip()
            break
    return None


def have_key_or_die() -> str:
    k = resolve_key()
    if not k:
        print("❌ Aucune clé fal trouvée (FAL_KEY). Ajoute-la dans l'env ou "
              "secrets/api-keys.md. (Tu l'alimenteras plus tard.)", file=sys.stderr)
        sys.exit(2)
    print("clé fal configurée ✅")
    return k


# --- HTTP ----------------------------------------------------------------------
def _post(model: str, payload: dict, timeout: int = 180) -> dict:
    key = have_key_or_die()
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{FAL_BASE}/{model}",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Key {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": UA,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")[:300]
        hint = {401: "clé fal invalide", 403: "clé fal invalide",
                402: "crédits fal insuffisants (alimente la clé)"}.get(
                    e.code, f"erreur fal {e.code}")
        raise RuntimeError(f"{hint} — {body}") from None


def _extract_url(result: dict) -> str | None:
    imgs = result.get("images") or result.get("output") or []
    if isinstance(imgs, list) and imgs:
        first = imgs[0]
        return first.get("url") if isinstance(first, dict) else first
    img = result.get("image")
    if isinstance(img, dict):
        return img.get("url")
    return result.get("url") or result.get("image_url")


def _download(url: str, out_path: str) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r, open(out_path, "wb") as f:
        f.write(r.read())


# --- public API (mirrors gpt_image2_generate.generate signature) ---------------
def default_model(explicit: str | None) -> str:
    return explicit or GEN_MODEL


def generate(model: str, prompt: str, resolution: str, aspect_ratio: str,
             refs: list[str], negative: str | None, out_path: str,
             quality: str = "high") -> dict:
    """Generate one ad creative with GPT Image 2 via fal. `resolution`/`negative`
    kept for signature parity (GPT Image 2 caps at 1536; refs as URLs only)."""
    model = model or GEN_MODEL
    args: dict = {
        "prompt": prompt,
        "image_size": SIZE.get(aspect_ratio, "1024x1024"),
        "quality": quality,
        "num_images": 1,
    }
    url_refs = [r for r in (refs or []) if str(r).startswith("http")]
    if url_refs:
        args["image_urls"] = url_refs  # reference conditioning (URL refs only)
    print(f"→ fal {model} | size={args['image_size']} q={quality} refs={len(url_refs)}")
    t0 = time.time()
    result = _post(model, args)
    url = _extract_url(result)
    if not url:
        raise RuntimeError(f"Pas d'URL image: {json.dumps(result)[:300]}")
    _download(url, out_path)
    dt = round(time.time() - t0, 1)
    print(f"✅ {out_path}  ({dt}s)")
    return {"model": model, "url": url, "out": out_path, "seconds": dt,
            "arguments": {k: v for k, v in args.items() if k != "prompt"}}


def edit(image_url_or_path: str, instruction: str, out_path: str,
         model: str = EDIT_MODEL) -> dict:
    """Edit an existing creative's text with Nano Banana Pro (instruction-based)."""
    if not str(image_url_or_path).startswith("http"):
        raise RuntimeError("L'édition fal exige une URL d'image publique "
                           "(héberge l'image, puis passe son URL).")
    t0 = time.time()
    result = _post(model, {"prompt": instruction, "image_urls": [image_url_or_path]})
    url = _extract_url(result)
    if not url:
        raise RuntimeError(f"Pas d'URL image: {json.dumps(result)[:300]}")
    _download(url, out_path)
    dt = round(time.time() - t0, 1)
    print(f"✅ {out_path}  ({dt}s)")
    return {"model": model, "url": url, "out": out_path, "seconds": dt}


# --- CLI -----------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="fal.ai engine — GPT Image 2 / Nano Banana Pro")
    ap.add_argument("--prompt", default=None)
    ap.add_argument("--prompt-file", default=None)
    ap.add_argument("--aspect-ratio", default="4:5")
    ap.add_argument("--resolution", default="2k")
    ap.add_argument("--quality", default="high", choices=["low", "medium", "high"])
    ap.add_argument("--ref", action="append", default=[], help="URL de référence (répétable)")
    ap.add_argument("--model", default=None, help=f"slug fal (défaut: {GEN_MODEL})")
    ap.add_argument("--edit", default=None, help="URL d'image à éditer (Nano Banana Pro)")
    ap.add_argument("--instruction", default=None, help="(avec --edit) consigne d'édition")
    ap.add_argument("--out", default="out.png")
    a = ap.parse_args()

    if a.edit:
        if not a.instruction:
            print("❌ --instruction requis avec --edit", file=sys.stderr); sys.exit(1)
        print(json.dumps(edit(a.edit, a.instruction, a.out), ensure_ascii=False)); return

    prompt = a.prompt or (Path(a.prompt_file).read_text() if a.prompt_file else None)
    if not prompt:
        print("❌ --prompt ou --prompt-file requis", file=sys.stderr); sys.exit(1)
    meta = generate(default_model(a.model), prompt, a.resolution, a.aspect_ratio,
                    a.ref, None, a.out, quality=a.quality)
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
