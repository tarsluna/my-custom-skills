#!/usr/bin/env python3
"""
gpt_image2_generate.py — GPT Image 2 generation via Higgsfield Cloud.

Single-image client for the V2 static-creative pipeline. Resolves the GPT Image 2
model slug from the live catalog, submits a text-to-image (optionally
reference-conditioned) job, polls, and downloads the result.

CREDENTIALS (never printed): resolved in this order ->
  HF_KEY ("key_id:key_secret")  |  HF_CREDENTIALS  |  XFIELD_KEY
  |  HF_API_KEY + HF_API_SECRET  |  XFIELD_API_KEY + XFIELD_API_SECRET
Falls back to reading secrets/api-keys.md in the skills root if present.

IMPORTANT — model slug:
  The exact Higgsfield Cloud application slug for GPT Image 2 must be confirmed
  from the live catalog before any billed batch. The official CLI exposes
  `gpt_image_2`; the Cloud SDK uses paths like `bytedance/seedream/v4/text-to-image`.
  Run `--list-models` to discover the real slug, then pass `--model-slug`.

USAGE
  # 1) discover the slug (no credits)
  python gpt_image2_generate.py --list-models | grep -i gpt

  # 2) one image
  python gpt_image2_generate.py \
      --model-slug "openai/gpt-image-2/text-to-image" \
      --prompt-file prompt.txt \
      --resolution 2k --aspect-ratio 4:5 \
      --ref ./assets/logo.png --ref ./assets/product.jpg \
      --out ./creatives-v2/raw/A1.png

Primary path uses the official `higgsfield-client` Python SDK (`pip install
higgsfield-client`). A thin HTTP fallback is provided but MUST be verified against
the live API before relying on it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# --- candidate slugs --------------------------------------------------------
# CONFIRMED (deep-research, May 2026): the official Higgsfield CLI model id is
# `gpt_image_2` (1 credit/image, ~$0.07). The official `higgsfield-product-photoshoot`
# skill uses gpt_image_2 as its generation backend — so this is the right model for
# ad creatives. The Cloud SDK V2 subscribe() may expose it under a path-style slug;
# ALWAYS confirm the exact application path via --list-models before a billed batch.
# Other confirmed image model ids on the catalog: text2image_soul_v2 (Soul V2,
# 0.12 cr ~ $0.009, cheap photoreal — no text), nano_banana_2 (best text-in-image, 2 cr),
# flux_2, seedream_v4_5, marketing_studio_image.
GPT_IMAGE2_SLUG_CANDIDATES = [
    "gpt_image_2",                       # confirmed CLI id
    "openai/gpt-image-2/text-to-image",  # possible Cloud V2 path
    "openai/gpt-image-2",
    "gpt-image-2",
]
# Cheap photoreal alternative (swap per-cell for no-text lifestyle/product cells):
SOUL_V2_SLUG_CANDIDATES = ["text2image_soul_v2", "higgsfield/soul/v2/text-to-image"]

PLATFORM_BASE = os.environ.get("HF_PLATFORM_BASE", "https://platform.higgsfield.ai")


# --- credentials ---------------------------------------------------------------
def resolve_credentials() -> str | None:
    """Return 'key_id:key_secret' or None. NEVER print the value."""
    for var in ("HF_KEY", "HF_CREDENTIALS", "XFIELD_KEY"):
        v = os.environ.get(var)
        if v:
            return v.strip()
    key = os.environ.get("HF_API_KEY") or os.environ.get("XFIELD_API_KEY")
    sec = os.environ.get("HF_API_SECRET") or os.environ.get("XFIELD_API_SECRET")
    if key and sec:
        return f"{key.strip()}:{sec.strip()}"
    # last resort: secrets file in skills root
    for root in (Path.cwd(), *Path.cwd().parents):
        f = root / "secrets" / "api-keys.md"
        if f.exists():
            txt = f.read_text(errors="ignore")
            for token in ("HF_KEY", "HIGGSFIELD", "XFIELD_KEY"):
                for line in txt.splitlines():
                    if token in line and ":" in line:
                        # extract a key:secret-looking token, do not log it
                        for part in line.replace("`", " ").split():
                            if part.count(":") == 1 and len(part) > 12:
                                return part.strip()
            break
    return None


def have_creds_or_die() -> str:
    creds = resolve_credentials()
    if not creds:
        print("❌ Aucune credential Higgsfield trouvée (HF_KEY / HF_API_KEY+SECRET).",
              file=sys.stderr)
        sys.exit(2)
    # export for the SDK without echoing the value
    os.environ.setdefault("HF_KEY", creds)
    print("clé configurée ✅")
    return creds


# --- SDK path ------------------------------------------------------------------
def _try_import_sdk():
    try:
        import higgsfield_client  # type: ignore
        return higgsfield_client
    except Exception:
        return None


def list_models() -> list[dict]:
    """List available models. Tries SDK, then HTTP. Read-only, no credits."""
    have_creds_or_die()
    sdk = _try_import_sdk()
    if sdk is not None:
        for fn in ("list_models", "models", "list_applications"):
            f = getattr(sdk, fn, None)
            if callable(f):
                try:
                    return list(f())
                except Exception as e:  # noqa
                    print(f"[sdk.{fn}] {e}", file=sys.stderr)
    # HTTP fallback (verify endpoint against live API)
    return _http_list_models()


def _http_list_models() -> list[dict]:
    import urllib.request
    creds = resolve_credentials() or ""
    out: list[dict] = []
    for path in ("/v1/models", "/v1/applications", "/v1/motions"):
        try:
            req = urllib.request.Request(
                PLATFORM_BASE + path,
                headers={"Authorization": f"Key {creds}", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
                items = data if isinstance(data, list) else data.get("data") or data.get("items") or []
                for it in items:
                    out.append(it if isinstance(it, dict) else {"id": it})
                if out:
                    return out
        except Exception as e:  # noqa
            print(f"[http {path}] {e}", file=sys.stderr)
    return out


def resolve_gpt_image2_slug(explicit: str | None) -> str:
    if explicit:
        return explicit
    models = list_models()
    ids = []
    for m in models:
        mid = (m.get("id") or m.get("slug") or m.get("name") or "").lower()
        if mid:
            ids.append(mid)
    for cand in GPT_IMAGE2_SLUG_CANDIDATES:
        if cand.lower() in ids:
            return cand
    # fuzzy: anything containing gpt + image
    for mid in ids:
        if "gpt" in mid and "image" in mid:
            return mid
    print("⚠️  Slug GPT Image 2 non confirmé dans le catalogue. "
          "Passe --model-slug explicitement. Candidats par défaut: "
          + ", ".join(GPT_IMAGE2_SLUG_CANDIDATES), file=sys.stderr)
    return GPT_IMAGE2_SLUG_CANDIDATES[0]


# --- aspect ratio mapping ------------------------------------------------------
ASPECT = {"4:5": "4:5", "9:16": "9:16", "1:1": "1:1", "feed-4x5": "4:5",
          "story-9x16": "9:16", "feed-1x1": "1:1"}


def build_arguments(prompt: str, resolution: str, aspect_ratio: str,
                    refs: list[str], negative: str | None) -> dict:
    args: dict = {
        "prompt": prompt,
        "resolution": resolution.upper() if resolution.lower() in ("1k", "2k", "4k") else resolution,
        "aspect_ratio": ASPECT.get(aspect_ratio, aspect_ratio),
    }
    if negative:
        args["negative_prompt"] = negative
    if refs:
        # arg name varies by model. We pass the common ones; the SDK ignores unknowns
        # for some models. Confirm per-model schema if a 422 is returned.
        urls = [r for r in refs if r.startswith("http")]
        local = [r for r in refs if not r.startswith("http")]
        if urls:
            args["image_urls"] = urls
            args["input_images"] = urls
        if local:
            args["input_files"] = local  # SDK auto-uploads local files for some models
    return args


def generate(model_slug: str, prompt: str, resolution: str, aspect_ratio: str,
             refs: list[str], negative: str | None, out_path: str,
             poll_timeout: int = 300) -> dict:
    have_creds_or_die()
    args = build_arguments(prompt, resolution, aspect_ratio, refs, negative)
    sdk = _try_import_sdk()
    if sdk is None:
        print("❌ SDK higgsfield-client absent. `pip install higgsfield-client` "
              "(le fallback HTTP n'est pas garanti).", file=sys.stderr)
        sys.exit(3)

    print(f"→ submit {model_slug} | res={args['resolution']} ar={args['aspect_ratio']} "
          f"refs={len(refs)}")
    t0 = time.time()
    try:
        result = sdk.subscribe(model_slug, arguments=args)  # submit + wait
    except Exception as e:  # noqa
        # retry once without refs if the model rejects them (422 on unknown field)
        if refs:
            print(f"[retry sans refs] {e}", file=sys.stderr)
            result = sdk.subscribe(model_slug, arguments=build_arguments(
                prompt, resolution, aspect_ratio, [], negative))
        else:
            raise
    url = _extract_url(result)
    if not url:
        raise RuntimeError(f"Pas d'URL image dans la réponse: {json.dumps(result)[:300]}")
    _download(url, out_path)
    dt = round(time.time() - t0, 1)
    print(f"✅ {out_path}  ({dt}s)")
    return {"model": model_slug, "url": url, "out": out_path, "seconds": dt,
            "arguments": {k: v for k, v in args.items() if k != "prompt"}}


def _extract_url(result: dict) -> str | None:
    if not isinstance(result, dict):
        return None
    imgs = result.get("images") or result.get("output") or []
    if isinstance(imgs, list) and imgs:
        first = imgs[0]
        return first.get("url") if isinstance(first, dict) else first
    return result.get("url") or result.get("image_url")


def _download(url: str, out_path: str) -> None:
    import urllib.request
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, out_path)


# --- CLI -----------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="GPT Image 2 via Higgsfield Cloud")
    ap.add_argument("--list-models", action="store_true",
                    help="Lister les modèles (read-only, no credits) et sortir")
    ap.add_argument("--model-slug", default=None,
                    help="Slug exact (sinon résolu via catalogue)")
    ap.add_argument("--prompt", default=None)
    ap.add_argument("--prompt-file", default=None)
    ap.add_argument("--resolution", default="2k", choices=["1k", "2k", "4k"])
    ap.add_argument("--aspect-ratio", default="4:5")
    ap.add_argument("--ref", action="append", default=[],
                    help="Image de référence (URL ou chemin local). Répétable.")
    ap.add_argument("--negative", default=(
        "no watermark, no extra gibberish text, no distorted hands, "
        "no fake logos, no lorem ipsum, no duplicated UI chrome"))
    ap.add_argument("--out", default="out.png")
    args = ap.parse_args()

    if args.list_models:
        for m in list_models():
            mid = m.get("id") or m.get("slug") or m.get("name") or m
            cat = m.get("category", "") if isinstance(m, dict) else ""
            print(f"{mid}\t{cat}")
        return

    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text()
    if not prompt:
        print("❌ --prompt ou --prompt-file requis", file=sys.stderr)
        sys.exit(1)

    slug = resolve_gpt_image2_slug(args.model_slug)
    meta = generate(slug, prompt, args.resolution, args.aspect_ratio,
                    args.ref, args.negative, args.out)
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
