#!/usr/bin/env python3
"""
soul_id.py — Train & reuse a Higgsfield Soul Character (identity-faithful face model).

For ad packs that need a RECURRING spokesperson/founder across many creatives
(design style S4), a one-shot face per image breaks credibility. Soul ID trains a
face-faithful identity once, then every Soul-powered generation reuses it.

Ported from github.com/higgsfield-ai/skills `higgsfield-soul-id` (MIT, © 2026
Higgsfield AI). See NOTICE.md. Drives the official CLI.

PREREQS
  - higgsfield CLI on PATH + `higgsfield auth login`
  - Soul training requires a paid plan (Basic+).
  - 5–20 face photos, varied angles & lighting (only user-approved photos!).

USAGE
  # train (one-time) -> prints a reference_id; store it in client-brand-profile.json
  python soul_id.py create --name founder --soul-2 \
      --image ./refs/1.jpg --image ./refs/2.jpg --image ./refs/3.jpg
  python soul_id.py list
  python soul_id.py get <id>

  # then generate with the trained identity (Soul model, not gpt_image_2):
  higgsfield generate create text2image_soul_v2 --prompt "..." --soul-id <id> --quality 2k --wait
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys

ID_RE = re.compile(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b", re.I)


def hf() -> str:
    p = shutil.which("higgsfield")
    if not p:
        print("❌ CLI 'higgsfield' absente. Installe:\n"
              "   curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh",
              file=sys.stderr)
        sys.exit(2)
    return p


def run(cmd: list[str], timeout: int = 1800) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        low = out.lower()
        if "minimum basic plan" in low:
            raise SystemExit("❌ Soul ID nécessite un plan payant (Basic+).")
        if "session expired" in low or "not authenticated" in low:
            raise SystemExit("❌ Non authentifié. Lance: higgsfield auth login")
        raise SystemExit(f"❌ CLI exit {r.returncode}: {out[:300]}")
    return out


def create(name: str, images: list[str], variant: str, wait: bool) -> None:
    if len(images) < 5:
        print(f"⚠️  {len(images)} photo(s) — recommandé 5–20, angles/lumières variés.", file=sys.stderr)
    cmd = [hf(), "soul-id", "create", "--name", name, variant]
    for img in images:
        cmd += ["--image", img]
    out = run(cmd)
    m = ID_RE.search(out)
    ref = m.group(1) if m else None
    print(f"Soul «{name}» soumis ✅" + (f" (ref={ref})" if ref else ""))
    if ref and wait:
        print("⏳ entraînement (silencieux, ~minutes)…")
        run([hf(), "soul-id", "wait", ref])
        print(f"Soul «{name}» prêt ✅ → ajoute-le dans client-brand-profile.json: render.soul_id = {ref}")
        print(f"   usage: higgsfield generate create text2image_soul_v2 --prompt \"...\" --soul-id {ref} --quality 2k --wait")


def main() -> None:
    ap = argparse.ArgumentParser(description="Higgsfield Soul ID (identity-faithful character)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create", help="entraîner un Soul (one-time)")
    c.add_argument("--name", required=True, help="référence courte (1 mot)")
    c.add_argument("--image", action="append", default=[], required=True, help="photo (répétable, 5–20)")
    grp = c.add_mutually_exclusive_group()
    grp.add_argument("--soul-2", dest="variant", action="store_const", const="--soul-2",
                     default="--soul-2", help="pour génération image (défaut)")
    grp.add_argument("--soul-cinematic", dest="variant", action="store_const",
                     const="--soul-cinematic", help="pour cinématique/vidéo")
    c.add_argument("--no-wait", action="store_true")

    sub.add_parser("list", help="lister les Souls existants")
    g = sub.add_parser("get", help="détail d'un Soul"); g.add_argument("id")

    args = ap.parse_args()
    if args.cmd == "create":
        create(args.name, args.image, args.variant, wait=not args.no_wait)
    elif args.cmd == "list":
        print(run([hf(), "soul-id", "list"]))
    elif args.cmd == "get":
        print(run([hf(), "soul-id", "get", args.id]))


if __name__ == "__main__":
    main()
