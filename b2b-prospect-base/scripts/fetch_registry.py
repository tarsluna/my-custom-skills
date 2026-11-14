#!/usr/bin/env python3
"""Socle : entreprises actives du metier, depuis l'API publique recherche-entreprises.

Sortie : data/registre.csv, une entreprise par SIREN, sans aucun mail. Ce socle sert a
verifier les sites et a completer les prenoms.

Minimisation : ni date de naissance ni adresse postale (le siege d'un entrepreneur
individuel est souvent son domicile), seulement le code postal et la commune. Les
entites en diffusion partielle (opposition au registre) sont ecartees.

Usage : python3 -I scripts/fetch_registry.py --project DOSSIER [--dry-run]
Reprise automatique. Un 403 ou un 429 arrete tout : relancer plus tard, sans contourner.
"""
import argparse
import csv
import re
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prospect_core import (  # noqa: E402
    Blocked, Client, Disallowed, GuardrailError, Unreachable, load_config, raw_dir, record_blocked,
)

API = "https://recherche-entreprises.api.gouv.fr/search"
SOURCE = "registre"
CAP = 10000  # plafond de pagination de l'API
PER_PAGE = 25
DEPARTMENTS = [f"{i:02d}" for i in range(1, 96) if i != 20] + ["2A", "2B", "971", "972", "973", "974", "976"]
PARIS_POSTCODES = [f"750{i:02d}" for i in range(1, 21)] + ["75116"]
FIELDS = ["siren", "entreprise", "segment", "naf", "prenom", "nom", "qualite", "code_postal", "ville", "departement"]


def first_name(raw):
    token = (raw or "").strip().split(" ")[0]
    return token.title() if token else ""


def is_partial(item):
    siege = item.get("siege") or {}
    return "P" in (item.get("statut_diffusion"), siege.get("statut_diffusion_etablissement"))


def to_row(item, naf, segment, department):
    siege = item.get("siege") or {}
    person = next((d for d in item.get("dirigeants") or [] if d.get("type_dirigeant") == "personne physique"), {})
    return {
        "siren": item.get("siren", ""),
        "entreprise": item.get("nom_raison_sociale") or item.get("nom_complet") or "",
        "segment": segment,
        "naf": naf,
        "prenom": first_name(person.get("prenoms")),
        "nom": (person.get("nom") or "").title(),
        "qualite": person.get("qualite", ""),
        "code_postal": siege.get("code_postal", ""),
        "ville": siege.get("libelle_commune", ""),
        "departement": department,
    }


class Run:
    def __init__(self, project, config, client, retry_wait=5):
        self.project = Path(project)
        self.config = config["registry"]
        self.client = client
        self.retry_wait = retry_wait
        self.stats = {"gardees": 0, "diffusion_partielle": 0, "filtrees": 0, "plafonnees": 0, "erreurs": 0}
        self.out_path = self.project / "data" / "registre.csv"
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self.done_path = raw_dir(self.project, SOURCE) / "done.txt"
        self.done = set(self.done_path.read_text(encoding="utf-8").split("\n")) if self.done_path.exists() else set()
        self.seen = set()
        if self.out_path.exists():
            with self.out_path.open(encoding="utf-8", newline="") as handle:
                self.seen = {row["siren"] for row in csv.DictReader(handle)}
        fresh = not self.out_path.exists() or self.out_path.stat().st_size == 0
        self.handle = self.out_path.open("a", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.handle, fieldnames=FIELDS)
        if fresh:
            self.writer.writeheader()

    def get(self, params):
        url = API + "?" + urllib.parse.urlencode(params)
        for attempt in range(3):
            try:
                return self.client.get_json(url)
            except Unreachable:
                time.sleep(self.retry_wait * (attempt + 1))
        raise Unreachable(url)

    def keep(self, results, naf, segment, department):
        name_filter = self.config.get("name_filter", {}).get(naf)
        for item in results:
            if item.get("siren") in self.seen:
                continue
            self.seen.add(item.get("siren"))
            if is_partial(item):
                self.stats["diffusion_partielle"] += 1
                continue
            if name_filter and not re.search(name_filter, item.get("nom_complet") or "", re.I):
                self.stats["filtrees"] += 1
                continue
            self.writer.writerow(to_row(item, naf, segment, department))
            self.stats["gardees"] += 1
        self.handle.flush()

    def mark_done(self, key):
        with self.done_path.open("a", encoding="utf-8") as handle:
            handle.write(key + "\n")
        self.done.add(key)

    def walk(self, naf, segment, department, postcode=None):
        key = f"{naf}|{department}|{postcode or ''}"
        if key in self.done:
            return
        params = {"activite_principale": naf, "etat_administratif": "A", "per_page": PER_PAGE}
        params.update({"code_postal": postcode} if postcode else {"departement": department})
        try:
            first = self.get({**params, "page": 1})
        except Unreachable as exc:
            self.stats["erreurs"] += 1
            print(f"ERREUR {key}: {exc}", file=sys.stderr)
            return
        total = first.get("total_results", 0)
        if total >= CAP and not postcode:
            if department == "75":
                for code in PARIS_POSTCODES:
                    self.walk(naf, segment, department, code)
                self.mark_done(key)
                return
            self.stats["plafonnees"] += 1
            print(f"PLAFOND {key}: {total} resultats, la fin ne sera pas vue", file=sys.stderr)
        self.keep(first.get("results", []), naf, segment, department)
        failed = False
        for page in range(2, first.get("total_pages", 1) + 1):
            try:
                data = self.get({**params, "page": page})
            except Unreachable as exc:
                self.stats["erreurs"] += 1
                failed = True
                print(f"ERREUR {key} p{page}: {exc}", file=sys.stderr)
                continue
            self.keep(data.get("results", []), naf, segment, department)
        if not failed:
            self.mark_done(key)

    def close(self):
        self.handle.close()


def run(project, config, client, retry_wait=5):
    registry = config.get("registry", {})
    departments = registry.get("departments") or DEPARTMENTS
    job = Run(project, config, client, retry_wait)
    try:
        for naf, segment in registry["naf"].items():
            for department in departments:
                job.walk(naf, segment, department)
    except Blocked as exc:
        print(f"ARRET : {exc}. Voir BLOCKED.md. Relancer plus tard, ne pas contourner.", file=sys.stderr)
        return 2, job.stats
    except Disallowed as exc:
        record_blocked(project, SOURCE, "recherche-entreprises.api.gouv.fr", "robots", f"robots.txt interdit {exc}")
        print(f"ARRET : robots.txt interdit {exc}.", file=sys.stderr)
        return 2, job.stats
    finally:
        job.close()
    print("FINI", job.stats, flush=True)
    return 0, job.stats


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", default=".")
    parser.add_argument("--config")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config = load_config(args.project, args.config)
        registry = config.get("registry") or {}
        if not registry.get("naf"):
            print("GARDE-FOU : renseigne registry.naf dans la configuration.", file=sys.stderr)
            return 2
        if args.dry_run:
            departments = registry.get("departments") or DEPARTMENTS
            print(f"A blanc : {len(registry['naf'])} code(s) NAF x {len(departments)} departement(s), API publique, "
                  "1 requete par seconde, aucun mail collecte.")
            return 0
        client = Client(args.project, SOURCE, config)
        return run(args.project, config, client)[0]
    except GuardrailError as exc:
        print(f"GARDE-FOU : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
