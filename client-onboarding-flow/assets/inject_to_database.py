#!/usr/bin/env python3
"""
inject_to_database.py — upload les livrables d'un client vers Supabase Storage
+ indexe dans la table `ai_deliverables`.

Pipeline :
1. Résout l'UUID du client dans Supabase (par `company` puis `full_name`)
2. Scanne récursivement le dossier client local
3. Upload chaque fichier vers le bucket privé `ai-deliverables` sous le path
   `{client_id}/{relative_path_from_client_folder}`
4. Upsert chaque fichier dans la table `ai_deliverables` (idempotent),
   avec `relative_path` = path Storage (PAS le path filesystem local)

Usage :
    python3 inject_to_database.py \\
        --client-folder "$PROJECT_DIR/acme-fermetures" \\
        --client-name "Acme Fermetures" \\
        [--dry-run]

Variables d'environnement requises :
    SUPABASE_URL                — ex: https://<your-project-ref>.supabase.co
    SUPABASE_SERVICE_ROLE_KEY   — service_role key (PAS l'anon key)
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


VALID_TYPES = {
    "onboarding_form",
    "deep_search_market_awareness",
    "deep_search_competitor_research",
    "deep_search_psychographic",
    "competitor_ads_brief",
    "competitor_ads_data",
    "competitor_ads_analysis",
    "competitor_ads_creative",
    "campaign_proposal",
    "vsl_script",
    "vsl_strategy",
    "vsl_docx",
    "meta_ads_copy",
    "meta_ads_docx",
    "readme_index",
    "other",
}

BUCKET = "ai-deliverables"


def infer_deliverable_type(rel_from_client: str) -> str:
    p = rel_from_client.lower().replace("\\", "/")
    if "00-onboarding" in p:
        return "onboarding_form"
    if "01-deep-search" in p:
        if "market" in p:
            return "deep_search_market_awareness"
        if "competitor" in p:
            return "deep_search_competitor_research"
        if "psycho" in p:
            return "deep_search_psychographic"
        return "deep_search_market_awareness"
    if "02-competitor-ads" in p:
        if "creatives/" in p:
            return "competitor_ads_creative"
        if p.endswith(".csv"):
            return "competitor_ads_data"
        if p.endswith(".docx"):
            return "competitor_ads_brief"
        if p.endswith(".md"):
            return "competitor_ads_analysis"
        return "competitor_ads_brief"
    if "03-campaign-proposal" in p:
        return "campaign_proposal"
    if "04-vsl" in p:
        if p.endswith(".docx"):
            return "vsl_docx"
        if "strategy" in p:
            return "vsl_strategy"
        return "vsl_script"
    if "05-meta-ads" in p:
        if p.endswith(".docx"):
            return "meta_ads_docx"
        return "meta_ads_copy"
    if p.endswith("readme.md"):
        return "readme_index"
    return "other"


IGNORED_DIRS = {"node_modules", ".git", ".DS_Store"}


def scan_client_folder(client_folder: Path) -> list[dict]:
    results = []
    for path in client_folder.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") or part in IGNORED_DIRS for part in path.parts):
            continue

        rel_from_client = path.relative_to(client_folder).as_posix()
        ext = path.suffix.lstrip(".").lower()
        stat = path.stat()

        results.append(
            {
                "_abs_path": str(path),
                "_rel_from_client": rel_from_client,
                "deliverable_type": infer_deliverable_type(rel_from_client),
                "deliverable_name": path.name,
                "file_size_bytes": stat.st_size,
                "file_extension": ext,
                "status": "available",
                "generated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    results.sort(key=lambda r: r["_rel_from_client"])
    return results


# =====================================================================
# Supabase REST helpers
# =====================================================================


class SupabaseError(Exception):
    pass


def supabase_request(
    method: str,
    path: str,
    body: Optional[bytes | dict | list] = None,
    prefer: str = "",
    extra_headers: Optional[dict] = None,
    base: str = "rest/v1",
) -> tuple[int, str]:
    url = f"{SUPABASE_URL}/{base}{path}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    if prefer:
        headers["Prefer"] = prefer
    if extra_headers:
        headers.update(extra_headers)

    data: Optional[bytes] = None
    if body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        else:
            data = body

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="replace")
        raise SupabaseError(f"HTTP {e.code} on {method} {path}: {body_err}") from e
    except urllib.error.URLError as e:
        raise SupabaseError(f"Network error on {method} {path}: {e}") from e


def find_client_uuid(client_name: str) -> Optional[str]:
    encoded = urllib.parse.quote(client_name)
    status, body = supabase_request(
        "GET", f"/profiles?company=ilike.{encoded}&select=id&limit=1"
    )
    rows = json.loads(body)
    if rows:
        return rows[0]["id"]
    status, body = supabase_request(
        "GET", f"/profiles?full_name=ilike.{encoded}&select=id&limit=1"
    )
    rows = json.loads(body)
    if rows:
        return rows[0]["id"]
    return None


def upload_to_storage(storage_path: str, file_bytes: bytes, content_type: str) -> None:
    """Upload (upsert) un fichier dans le bucket Storage."""
    encoded_path = urllib.parse.quote(storage_path)
    supabase_request(
        "POST",
        f"/{BUCKET}/{encoded_path}",
        body=file_bytes,
        extra_headers={
            "Content-Type": content_type,
            "x-upsert": "true",
            "Cache-Control": "3600",
        },
        base="storage/v1/object",
    )


def upsert_deliverables(client_id: str, deliverables: list[dict]) -> int:
    payload = [
        {
            "client_id": client_id,
            "skill_name": "client-onboarding-flow",
            "deliverable_type": d["deliverable_type"],
            "deliverable_name": d["deliverable_name"],
            "relative_path": d["storage_path"],  # path Storage, pas filesystem
            "file_size_bytes": d["file_size_bytes"],
            "file_extension": d["file_extension"],
            "status": "available",
            "generated_at": d["generated_at"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        for d in deliverables
    ]
    supabase_request(
        "POST",
        "/ai_deliverables?on_conflict=client_id,relative_path",
        body=payload,
        prefer="resolution=merge-duplicates,return=minimal",
    )
    return len(payload)


# =====================================================================
# Main
# =====================================================================


def main() -> int:
    global SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--client-folder", required=True)
    parser.add_argument("--client-name", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("ERROR: SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY requis (voir .env.example ; étape optionnelle).", file=sys.stderr)
        return 1

    client_folder = Path(args.client_folder).resolve()
    if not client_folder.is_dir():
        print(f"ERROR: dossier introuvable : {client_folder}", file=sys.stderr)
        return 1

    print(f"📂 Scan {client_folder}")
    files = scan_client_folder(client_folder)
    print(f"   → {len(files)} fichier(s) détecté(s)")

    if not files:
        print("Aucun fichier à injecter.")
        return 0

    if args.dry_run:
        print("\n--- DRY RUN — preview ---")
        for f in files:
            print(f"  [{f['deliverable_type']:32}] {f['deliverable_name']} ({f['file_size_bytes']} B)")
        return 0

    print(f"\n🔎 Recherche UUID Supabase pour client : {args.client_name}")
    try:
        client_id = find_client_uuid(args.client_name)
    except SupabaseError as e:
        print(f"ERROR Supabase : {e}", file=sys.stderr)
        return 1

    if not client_id:
        print(f"ERROR: client '{args.client_name}' introuvable dans profiles.", file=sys.stderr)
        return 1

    print(f"   ✓ client_id = {client_id}")

    print(f"\n☁️  Upload vers Supabase Storage (bucket: {BUCKET})...")
    for f in files:
        storage_path = f"{client_id}/{f['_rel_from_client']}"
        f["storage_path"] = storage_path
        with open(f["_abs_path"], "rb") as fh:
            file_bytes = fh.read()
        mime, _ = mimetypes.guess_type(f["deliverable_name"])
        content_type = mime or "application/octet-stream"
        try:
            upload_to_storage(storage_path, file_bytes, content_type)
            print(f"   ✓ {storage_path}")
        except SupabaseError as e:
            print(f"   ✗ {storage_path} — {e}", file=sys.stderr)
            return 1

    print(f"\n📤 Upsert de {len(files)} ligne(s) dans ai_deliverables...")
    try:
        n = upsert_deliverables(client_id, files)
    except SupabaseError as e:
        print(f"ERROR upsert : {e}", file=sys.stderr)
        return 1

    print(f"   ✓ {n} livrable(s) indexé(s)")
    print(f"\n✅ Terminé. Ouvre la page client {client_id} dans ton app (ex. /admin/clients/{client_id}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
