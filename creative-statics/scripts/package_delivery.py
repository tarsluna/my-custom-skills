#!/usr/bin/env python3
"""
Package ALL Acme creatives into one pro deliverable.

Collects PNGs from:
 - creatives/angle-1-BookNow/ angle-2-anti-360/ angle-3-transparence/ (v1)
 - creatives/v2/
 - creatives/v3/v1-* v2-* v3-* v4-* v5-*
 - creatives/v4/A1-* A2-* A3-* B1-* B2-* B3-*
 - iterations/iter-*

Output :
 - ~/Desktop/Acme-Ads-Pack-YYYYMMDD.zip  (all PNGs + README + strategy docs)
 - macOS notification
 - Tries email via /usr/bin/mail or osascript Mail.app if configured
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path("~/skills/projects/client-slug/05-meta-ads")
CRE = ROOT / "creatives"
ITER = ROOT / "iterations"
DESKTOP = Path("~/Desktop")

TARGET_EMAIL = "you@example.com"


def collect_all():
    """Return (display_name, absolute_path) tuples for every PNG to include."""
    items = []

    # v1 (three old angles)
    for sub in ("angle-1-BookNow", "angle-2-anti-360", "angle-3-transparence"):
        for p in sorted((CRE / sub).glob("*.png")):
            items.append((f"v1_{sub}/{p.name}", p))

    # v2
    for p in sorted((CRE / "v2").glob("*.png")):
        items.append((f"v2/{p.name}", p))

    # v3
    for sub in sorted((CRE / "v3").glob("v*")):
        if sub.is_dir():
            for p in sorted(sub.glob("*.png")):
                items.append((f"v3_{sub.name}/{p.name}", p))

    # v4
    for sub in sorted((CRE / "v4").glob("[AB]*")):
        if sub.is_dir():
            for p in sorted(sub.glob("*.png")):
                items.append((f"v4_{sub.name}/{p.name}", p))

    # iterations
    for it in sorted(ITER.glob("iter-*")):
        if it.is_dir():
            for p in sorted(it.glob("*.png")):
                items.append((f"iterations_{it.name}/{p.name}", p))

    return items


def build_readme(items, zip_path):
    lines = [
        "# Acme Agency — Meta Ads Creative Pack",
        "",
        f"**Date de livraison** : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Total créatives** : {len(items)}",
        f"**Livrable** : `{zip_path.name}`",
        "",
        "---",
        "",
        "## Organisation du pack",
        "",
        "- **v1** — 3 angles de base (BookNow / Anti-360 / Transparence) × 3 formats (Feed 1:1, Feed 4:5, Story 9:16)",
        "- **v2** — 3 réalisations photo-réalistes via fal.ai FLUX, Instrument Serif hero",
        "- **v3** — 5 variations attaquant les white spaces concurrentiels (Due Diligence, Excel kills, Prix-en-hero, UGC Alex, Anti-retainer 72 k€)",
        "- **v4** — 6 angles avec value props retravaillées sur MVP + Outil sur mesure (timeline, diptych, comparison chart, stat hero, manifeste carrousel)",
        "- **iterations** — batchs générés automatiquement toutes les 2 h avec angles frais tirés du pool de rotation",
        "",
        "## Recommandation d'utilisation",
        "",
        "1. Commence par **v4** (value props les plus affûtées) pour lancer tes premières campagnes",
        "2. Utilise **v3** comme variantes A/B pour tester les angles alternatifs",
        "3. **v2** et **v1** en backup / retargeting",
        "4. **iterations** = réserve de variations fraîches — à filtrer via Council avant production",
        "",
        "## Fonts",
        "",
        "- Instrument Serif (hero display éditorial)",
        "- Space Grotesk (body, CTA)",
        "- Sources : Google Fonts (OFL)",
        "",
        "## Palette brand Acme",
        "",
        "- Navy deep : `#0A1628`",
        "- Off-white : `#F5F0E6`",
        "- Orange CTA : `#FF5A1F`",
        "- Lime accent : `#D8FF3C`",
        "- Green trust : `#22AC80`",
        "",
        "---",
        "",
        "## Contenu du ZIP",
        "",
    ]

    current_group = None
    for display, _ in items:
        group = display.split("/")[0]
        if group != current_group:
            lines.append(f"\n### {group}\n")
            current_group = group
        lines.append(f"- `{display}`")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("Livré automatiquement par le pipeline · Acme Agency.")

    return "\n".join(lines)


def build_zip(items, dest: Path, readme_text: str):
    if dest.exists():
        dest.unlink()
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for display, path in items:
            zf.write(path, arcname=f"Acme-Ads-Pack/{display}")
        # add README
        zf.writestr("Acme-Ads-Pack/README.md", readme_text)
        # add strategy docs (unique names)
        for doc, alias in [
            (CRE / "v3" / "_strategy.md", "v3-strategy.md"),
            (CRE / "v4" / "_strategy.md", "v4-strategy.md"),
            (ROOT / "ads-multi-variantes.md", "copy-ads-multi-variantes.md"),
        ]:
            if doc.exists():
                zf.write(doc, arcname=f"Acme-Ads-Pack/docs/{alias}")
    print(f"ZIP built: {dest}  ({dest.stat().st_size // 1024} KB)")


def notify_macos(title, msg):
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification "{msg}" with title "{title}" sound name "Glass"'],
                       check=False, timeout=5)
    except Exception as e:
        print(f"Notification failed: {e}")


def try_email(zip_path: Path):
    """
    Try to email the zip via macOS Mail.app (osascript).
    Returns True if dispatch succeeded (doesn't guarantee delivery).
    """
    script = f'''
    tell application "Mail"
        set newMessage to make new outgoing message with properties {{subject:"Acme Ads Pack · {datetime.now().strftime('%Y-%m-%d')}", content:"ZIP créatives Acme Agency en pièce jointe.\\n\\nLivré automatiquement par le pipeline.", visible:false}}
        tell newMessage
            make new to recipient at end of to recipients with properties {{address:"{TARGET_EMAIL}"}}
            make new attachment with properties {{file name:POSIX file "{zip_path}"}} at after the last paragraph
        end tell
        send newMessage
    end tell
    '''
    try:
        r = subprocess.run(["osascript", "-e", script],
                           capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            print("Email dispatched via Mail.app")
            return True
        print(f"Mail.app error: {r.stderr}")
    except Exception as e:
        print(f"osascript failed: {e}")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", action="store_true", help="Attempt email via Mail.app")
    parser.add_argument("--notify", action="store_true", default=True)
    args = parser.parse_args()

    items = collect_all()
    print(f"Found {len(items)} creatives")

    ts = datetime.now().strftime("%Y%m%d-%H%M")
    zip_path = DESKTOP / f"Acme-Ads-Pack-{ts}.zip"

    readme = build_readme(items, zip_path)
    build_zip(items, zip_path, readme)

    if args.email:
        sent = try_email(zip_path)
        if not sent:
            print(f"Email not sent — ZIP available at {zip_path}")

    if args.notify:
        notify_macos("Acme Ads Pack livré",
                     f"{len(items)} créatives dans {zip_path.name}")

    print(f"\n✓ Delivery complete: {zip_path}")


if __name__ == "__main__":
    main()
