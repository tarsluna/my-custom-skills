#!/usr/bin/env python3
"""Controle qualite : tire 50 lignes par source et relit chaque mail sur sa page.

  sample  tire les lignes, rouvre source_url et prepare data/raw/<name>/qc_packet.json
  report  compte les verdicts apres relecture et ecrit qc_report.json

Le paquet ne recopie pas le mail : il dit s'il a ete retrouve, avec un contexte masque.
Le relecteur remplit `verdict` (`ok` ou `mauvais`) et `motif` pour chaque entree.
Un filtre ne se juge jamais sur le tirage qui a servi a le regler : changer --seed.

Usage : python3 -I scripts/qc_sample.py sample --project DOSSIER --name NOM [--n 50] [--seed 1]
        python3 -I scripts/qc_sample.py report --project DOSSIER --name NOM
"""
import argparse
import datetime as dt
import html
import json
import random
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prospect_core import (  # noqa: E402
    H1, TITLE, Blocked, Client, Disallowed, ForbiddenHost, GuardrailError, Unreachable, first_match, host_of,
    load_config, mask_contacts, raw_dir, read_csv, visible_text,
)

NOT_VERIFIABLE = {"bloque", "robots", "injoignable", "exclu"}


def fetch(client, url):
    """(statut, corps). Les refus restent des refus : aucun nouvel essai."""
    try:
        response = client.get(url)
        return response.status, response.text()
    except Blocked:
        return "bloque", ""
    except Disallowed:
        return "robots", ""
    except Unreachable:
        return "injoignable", ""
    except ForbiddenHost:
        return "exclu", ""


def found_in(email, body):
    lowered = email.lower()
    plain = html.unescape(urllib.parse.unquote(body or "")).lower()
    return lowered in (body or "").lower() or lowered in plain


def load_osm(project):
    tags = {}
    for path in sorted((raw_dir(project, "open-data") / "osm").glob("*.json")):
        for element in json.loads(path.read_text(encoding="utf-8")).get("elements", []):
            tags[f"{element['type']}/{element['id']}"] = element.get("tags", {})
    return tags


def build_item(client, row, evidence, osm_tags, trade_regex):
    url = row["source_url"].split(" | ")[0]
    email = row["email"].lower()
    if "openstreetmap.org/" in url:
        tags = osm_tags.get(url.split("openstreetmap.org/")[1], {})
        code = "fichier_osm"
        retrouve = email in (tags.get("email", "") + ";" + tags.get("contact:email", "")).lower()
    else:
        code, body = fetch(client, url)
        retrouve = found_in(email, body)
    parts = urllib.parse.urlsplit(url)
    home_code, home = (None, "")
    if parts.scheme in ("http", "https") and "openstreetmap.org" not in parts.netloc:
        home_code, home = fetch(client, f"{parts.scheme}://{parts.netloc}/")
    text = re.sub(r"\s+", " ", visible_text(home))
    context = []
    for match in re.finditer(trade_regex, text.lower()):
        context.append(mask_contacts(text[max(0, match.start() - 50): match.end() + 50]))
        if len(context) >= 6:
            break
    return {
        "domain": host_of(url), "niveau": evidence.get("level", ""), "a_un_siren": bool(row.get("siren")),
        "entreprise": row.get("entreprise", ""), "segment": row.get("segment", ""),
        "email_type": row.get("email_type", ""), "source_url": url,
        "code_page": code, "email_retrouve": retrouve, "code_accueil": home_code,
        "title": first_match(TITLE, home), "h1": first_match(H1, home),
        "signals": {k: v for k, v in evidence.get("signals", {}).items() if v},
        "contexte": context, "verdict": "", "motif": "",
    }


def sample(project, config, client, name, n=50, seed=1, share_weak=0.7):
    rows = read_csv(Path(project) / "sources" / f"{name}.csv")
    folder = raw_dir(project, name)
    evidence = {}
    evidence_path = folder / "evidence.jsonl"
    if evidence_path.exists():
        for line in evidence_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                evidence[item["domain"]] = item
    by_domain = {}
    for row in rows:
        by_domain.setdefault(host_of(row["site"]) or host_of(row["source_url"]), []).append(row)
    rand = random.Random(seed)
    weak = sorted(d for d, r in by_domain.items() if not r[0].get("siren"))
    strong = sorted(d for d, r in by_domain.items() if r[0].get("siren"))
    weak_count = min(len(weak), round(n * share_weak))
    strong_count = min(len(strong), n - weak_count)
    weak_count = min(len(weak), n - strong_count)
    picked = rand.sample(weak, weak_count) + rand.sample(strong, strong_count)
    trade_regex = "|".join(s["title_regex"] for s in config["segments"])
    osm_tags = load_osm(project)
    items = [build_item(client, rand.choice(by_domain[d]), evidence.get(d, {}), osm_tags, trade_regex) for d in picked]
    payload = {"source": name, "seed": seed, "lignes_source": len(rows), "items": items}
    (folder / "qc_packet.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    found = sum(1 for item in items if item["email_retrouve"])
    print(f"{len(items)} lignes tirees, {found} mails retrouves -> {folder / 'qc_packet.json'}", flush=True)
    return items


def report(project, name):
    folder = raw_dir(project, name)
    path = folder / "qc_packet.json"
    if not path.exists():
        raise GuardrailError(f"{path} absent : lance d'abord `sample`.")
    packet = json.loads(path.read_text(encoding="utf-8"))
    items = packet["items"]
    pending = [item["domain"] for item in items if item.get("verdict") not in ("ok", "mauvais")]
    if pending:
        raise GuardrailError(f"Relecture incomplete, {len(pending)} ligne(s) sans verdict : {pending[:5]}")
    unverifiable = [item for item in items if not item["email_retrouve"] and item["code_page"] in NOT_VERIFIABLE]
    checked = [item for item in items if item not in unverifiable]
    bad = sum(1 for item in checked if item["verdict"] == "mauvais" or not item["email_retrouve"])
    summary = {
        "source": name, "seed": packet.get("seed"), "lignes_source": packet.get("lignes_source"),
        "relues": len(checked), "non_verifiables": len(unverifiable), "mauvaises": bad,
        "taux_mauvaises": round(bad / len(checked), 3) if checked else None, "date": dt.date.today().isoformat(),
    }
    (folder / "qc_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(summary, flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["sample", "report"])
    parser.add_argument("--project", default=".")
    parser.add_argument("--config")
    parser.add_argument("--name", required=True)
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config = load_config(args.project, args.config)
        if args.dry_run:
            print(f"A blanc : `{args.command}` sur sources/{args.name}.csv, tirage de {args.n} lignes.")
            return 0
        if args.command == "report":
            report(args.project, args.name)
            return 0
        client = Client(args.project, args.name, config)
        sample(args.project, config, client, args.name, args.n, args.seed)
        return 0
    except GuardrailError as exc:
        print(f"GARDE-FOU : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
