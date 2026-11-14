#!/usr/bin/env python3
"""Sources open data : jeux publics, OpenStreetMap, puis une seule table `sources/open-data.csv`.

Sous-commandes :
  search    liste les jeux de data.gouv.fr susceptibles de citer le metier
  overpass  fiches OpenStreetMap du metier, zone par zone (licence ODbL : citer la source)
  dataset   telecharge les jeux declares dans la configuration
  build     ecrit sources/open-data.csv et data/raw/open-data/sites_todo.csv

Aucun telephone n'est conserve, pas meme dans les fichiers bruts. Chaque jeu de donnees
doit avoir sa licence lue dans reviews/open-data.json avant le premier appel.

Usage : python3 -I scripts/open_data.py {search,overpass,dataset,build} --project DOSSIER [--dry-run]
"""
import argparse
import collections
import csv
import datetime as dt
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawl_sites import Crawl  # noqa: E402
from prospect_core import (  # noqa: E402
    SCHEMA, Blocked, Client, Disallowed, GuardrailError, Unreachable, host_of, is_under, load_config, normalize, raw_dir,
    read_csv, record_blocked,
)

SOURCE = "open-data"
SEARCH_API = "https://www.data.gouv.fr/api/1/datasets/?page_size=20&q="
OVERPASS_DEFAULT = "https://overpass.openstreetmap.fr/api/interpreter"
SOCIAL_HOSTS = ("facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com", "tiktok.com", "youtube.com",
                "pinterest.com", "google.com")
PHONE_TAG = re.compile(r"phone|mobile|fax|whatsapp", re.I)
VALID_EMAIL = re.compile(r"[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
LEGAL_FORM = re.compile(r"\b(sarl|sas|sasu|eurl|sa|scp|selarl|selas|sci|ste|societe|ei|snc)\b")


def namekey(value):
    return re.sub(r"\s+", " ", LEGAL_FORM.sub(" ", re.sub(r"[^a-z0-9 ]+", " ", normalize(value)))).strip()


def clean_site(site, excluded):
    host = host_of(site)
    return "" if not host or is_under(host, tuple(SOCIAL_HOSTS) + tuple(excluded)) else site


def stop(project, exc):
    if isinstance(exc, Disallowed):
        record_blocked(project, SOURCE, urllib.parse.urlsplit(str(exc)).netloc or "?", "robots", f"robots.txt interdit {exc}")
    print(f"ARRET : {exc}. Voir BLOCKED.md, ne pas contourner.", file=sys.stderr)
    return 2


def cmd_search(project, config, client):
    out = raw_dir(project, SOURCE) / "datagouv_candidats.tsv"
    seen = {}
    try:
        for query in config.get("open_data", {}).get("search_queries", []):
            data = client.get_json(SEARCH_API + urllib.parse.quote(query))
            for item in data.get("data", []):
                organization = (item.get("organization") or {}).get("name", "")
                seen[item["id"]] = (query, item.get("license"), organization, item.get("title"))
    except (Blocked, Disallowed) as exc:
        return stop(project, exc)
    with out.open("w", encoding="utf-8") as handle:
        handle.write("id\trequete\tlicence\torganisation\ttitre\n")
        for key, values in seen.items():
            handle.write(key + "\t" + "\t".join(str(v).replace("\t", " ").replace("\n", " ") for v in values) + "\n")
    print(len(seen), "jeux candidats ->", out)
    return 0


def overpass_query(area, filters):
    clauses = "\n".join(f'  nwr["{tag}"~"^({values})$"](area.a);' for tag, values in filters.items())
    return f'[out:json][timeout:300];\narea["ISO3166-2"="{area}"]->.a;\n(\n{clauses}\n);\nout center tags;'


def scrub_phones(document):
    for element in document.get("elements", []):
        tags = element.get("tags", {})
        for key in [k for k in tags if PHONE_TAG.search(k)]:
            del tags[key]
    return document


def cmd_overpass(project, config, client, retry_wait=30):
    settings = config.get("open_data", {}).get("overpass", {})
    endpoint = settings.get("endpoint", OVERPASS_DEFAULT)
    folder = raw_dir(project, SOURCE) / "osm"
    folder.mkdir(parents=True, exist_ok=True)
    for area in settings.get("areas", []):
        path = folder / f"{area}.json"
        if path.exists():
            continue
        query = overpass_query(area, settings.get("filters", {}))
        for attempt in range(3):
            try:
                document = client.post_form(endpoint, {"data": query})
            except (Blocked, Disallowed) as exc:
                return stop(project, exc)
            except (Unreachable, ValueError) as exc:
                print("nouvel essai", area, exc, flush=True)
                time.sleep(retry_wait * (attempt + 1))
                continue
            path.write_text(json.dumps(scrub_phones(document), ensure_ascii=False), encoding="utf-8")
            print("ok", area, len(document.get("elements", [])), flush=True)
            break
        else:
            print("ECHEC", area, flush=True)
    return 0


def cmd_dataset(project, config, client):
    folder = raw_dir(project, SOURCE)
    for spec in config.get("open_data", {}).get("datasets", []):
        fields = spec["fields"]
        path = folder / f"{spec['name']}.jsonl"
        url = spec["url"]
        count = 0
        try:
            with path.open("w", encoding="utf-8") as handle:
                while url:
                    page = client.get_json(url)
                    results = page.get(spec.get("results_key", "results"), [])
                    for item in results:  # seuls les champs du schema restent, le reste n'est pas ecrit
                        handle.write(json.dumps({k: item.get(v) for k, v in fields.items()}, ensure_ascii=False) + "\n")
                        count += 1
                    url = page.get(spec.get("next_key", "next")) if results else None
        except (Blocked, Disallowed) as exc:
            return stop(project, exc)
        print(spec["name"], count, "lignes", flush=True)
    return 0


def load_osm(project):
    out = {}
    for path in sorted((raw_dir(project, SOURCE) / "osm").glob("*.json")):
        for element in json.loads(path.read_text(encoding="utf-8")).get("elements", []):
            out[f"{element['type']}/{element['id']}"] = element
    return out


def classify_osm(element, settings):
    """(segment, nom, site, mail) ou None si la fiche est hors perimetre."""
    tags = element.get("tags", {})
    name = (tags.get("name") or tags.get("operator") or "").strip()
    if not name or tags.get("brand") or tags.get("brand:wikidata"):
        return None
    excluded = settings.get("exclude_name_regex")
    chains = settings.get("chains_regex")
    if (excluded and re.search(excluded, normalize(name))) or (chains and re.search(chains, normalize(name))):
        return None
    segment = next((seg for rule, seg in settings.get("tag_segments", {}).items()
                    if tags.get(rule.split("=")[0]) == rule.split("=")[1]), "")
    if not segment:
        return None
    site = (tags.get("website") or tags.get("contact:website") or tags.get("url") or "").strip().split(";")[0].strip()
    mail = (tags.get("email") or tags.get("contact:email") or "").strip()
    return segment, name, site, mail


def registry_index(project):
    by_cp, by_city = collections.defaultdict(set), collections.defaultdict(set)
    known = set()
    path = Path(project) / "data" / "registre.csv"
    if not path.exists():
        return by_cp, by_city, known
    for row in read_csv(path):
        siren = row["siren"].strip()
        known.add(siren)
        key = namekey(row.get("entreprise", ""))
        if key:
            if row.get("code_postal"):
                by_cp[(key, row["code_postal"].strip())].add(siren)
            if row.get("ville"):
                by_city[(key, normalize(row["ville"]))].add(siren)
    return by_cp, by_city, known


def match_siren(name, postcode, city, published, index):
    by_cp, by_city, known = index
    hits = set(published) & known
    if len(hits) == 1:
        return hits.pop()
    if hits:
        return ""  # plusieurs SIREN connus : ambigu
    key = namekey(name)
    if len(key) < 4:
        return ""
    if postcode:
        found = by_cp.get((key, postcode), set())
        if len(found) == 1:
            return next(iter(found))
        if found:
            return ""
    if city:
        found = by_city.get((key, normalize(city)), set())
        if len(found) == 1:
            return next(iter(found))
    return ""


def cmd_build(project, config):
    settings = config.get("open_data", {})
    excluded = config.get("excluded_hosts", [])
    crawl = Crawl(config)
    index = registry_index(project)
    today = dt.date.today().isoformat()
    candidates = []
    folder = raw_dir(project, SOURCE)

    for spec in settings.get("datasets", []):
        path = folder / f"{spec['name']}.jsonl"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            mail = (item.get("email") or "").strip()
            if not VALID_EMAIL.fullmatch(mail):
                continue
            siret = re.sub(r"\D", "", str(item.get("siret") or ""))
            name = (item.get("entreprise") or "").strip()
            candidates.append((0, {
                "email": mail, "entreprise": name, "segment": spec["segment"],
                "ville": (item.get("ville") or "").strip(), "code_postal": (item.get("code_postal") or "").strip(),
                "site": clean_site(item.get("site") or "", excluded),
                "siren": siret[:9] if len(siret) == 14 else match_siren(name, item.get("code_postal"), item.get("ville"), [], index),
                "source_url": spec["source_url_template"].format(**item),
            }))

    overpass = settings.get("overpass", {})
    osm_url = overpass.get("source_url_prefix", "https://www.openstreetmap.org/")
    todo = []
    for key, element in load_osm(project).items():
        result = classify_osm(element, overpass)
        if not result:
            continue
        segment, name, site, mail = result
        tags = element.get("tags", {})
        postcode = (tags.get("addr:postcode") or "").strip()
        city = (tags.get("addr:city") or "").strip()
        site = clean_site(site, excluded)
        if mail:
            for address in re.split(r"[;,\s]+", mail):
                if VALID_EMAIL.fullmatch(address):
                    candidates.append((1, {
                        "email": address, "entreprise": name, "segment": segment, "ville": city, "code_postal": postcode,
                        "site": site, "siren": match_siren(name, postcode, city, [], index), "source_url": osm_url + key,
                    }))
        elif site:
            todo.append({"domain": host_of(site), "entreprise": name, "segment": segment, "ville": city,
                         "code_postal": postcode, "level_hint": "fiche_ouverte"})

    best, sirens_of = {}, collections.defaultdict(set)
    for _, row in candidates:
        if row["siren"]:
            sirens_of[row["email"].lower()].add(row["siren"])
    for _, row in sorted(candidates, key=lambda item: item[0]):
        best.setdefault(row["email"].lower(), row)
    rows = []
    for key, row in best.items():
        sirens = sirens_of.get(key, set())
        row["siren"] = next(iter(sirens)) if len(sirens) == 1 else ""  # SIREN differents : rattachement ambigu
        row.update(prenom="", nom="", email=key, email_type=crawl.email_type(key), collected_at=today)
        rows.append(row)
    rows.sort(key=lambda r: r["email"])

    sources = Path(project) / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    with (sources / "open-data.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCHEMA)
        writer.writeheader()
        writer.writerows({k: r.get(k, "") for k in SCHEMA} for r in rows)
    with (folder / "sites_todo.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["domain", "entreprise", "segment", "ville", "code_postal", "level_hint"])
        writer.writeheader()
        writer.writerows({k: v for k, v in item.items()} for item in {t["domain"]: t for t in todo}.values())
    print(f"{len(rows)} lignes, {len(todo)} fiches a visiter", flush=True)
    return rows, todo


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["search", "overpass", "dataset", "build"])
    parser.add_argument("--project", default=".")
    parser.add_argument("--config")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config = load_config(args.project, args.config)
        if args.dry_run:
            print(f"A blanc : `{args.command}`, 1 requete par seconde et par hote, aucune requete envoyee.")
            return 0
        if args.command == "build":
            cmd_build(args.project, config)
            return 0
        client = Client(args.project, SOURCE, config)
        return {"search": cmd_search, "overpass": cmd_overpass, "dataset": cmd_dataset}[args.command](args.project, config, client)
    except GuardrailError as exc:
        print(f"GARDE-FOU : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
