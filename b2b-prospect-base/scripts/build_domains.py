#!/usr/bin/env python3
"""Croise la liste ouverte Afnic du .fr avec le registre, pour ne visiter que de vrais domaines.

Deux entrees pour crawl_sites.py :
  a) input_a.csv : domaines existants qui correspondent exactement au nom d'une entreprise
     du registre (une ligne par couple entreprise/domaine) ;
  b) input_b.csv : autres domaines dont le nom contient un mot du metier (colonne `domain`).

Seuls les domaines actifs, en .fr direct et non IDN sont gardes. Aucune requete reseau.
La licence de la liste doit avoir ete lue : reviews/afnic-domaines.json.

Usage : python3 -I scripts/build_domains.py --project DOSSIER --afnic FICHIER.csv [--dry-run]
"""
import argparse
import collections
import csv
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prospect_core import GuardrailError, load_config, raw_dir, read_csv, require_terms_review, tokens  # noqa: E402

SOURCE = "afnic-domaines"


def active_domains(path):
    kept = set()
    with Path(path).open(encoding="utf-8", newline="", errors="replace") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            if row.get("Date de retrait du WHOIS") or row.get("Sous domaine") != "fr" or row.get("Domaine IDN") != "0":
                continue
            kept.add(row["Nom de domaine"].strip().lower())
    return kept


def candidates(row, domains_config):
    """Noms de domaine plausibles d'une entreprise, a confronter a la liste. Jamais testes en DNS."""
    trade_words = set(domains_config.get("trade_words", []))
    suffixes = domains_config.get("stem_suffixes", [])
    words = tokens(row.get("entreprise", ""))
    core = [word for word in words if word not in trade_words]
    stems = []
    for parts in (words, core):
        if parts:
            stems += ["".join(parts), "-".join(parts)]
    if core:
        stems += ["".join(core) + suffix for suffix in suffixes]
    first, last = tokens(row.get("prenom", "")), tokens(row.get("nom", ""))
    if first and last:
        person = first[0], "".join(last)
        stems += ["".join(person), "-".join(person)]
    out = []
    for stem in dict.fromkeys(stems):
        if 5 <= len(stem) <= 50:
            out.append(stem + ".fr")
    return out


def build(project, config, afnic_path, seed=42):
    domains_config = config["domains"]
    keyword = re.compile(domains_config["keywords"])
    false_friend = re.compile(domains_config["false_friends"]) if domains_config.get("false_friends") else None
    strong = re.compile(domains_config.get("strong_keywords") or domains_config["keywords"])

    active = active_domains(afnic_path)
    registry = read_csv(Path(project) / "data" / "registre.csv")
    matches = collections.defaultdict(list)
    for row in registry:
        for domain in candidates(row, domains_config):
            if domain in active:
                matches[domain].append(row)

    rand = random.Random(seed)
    from_company = {
        domain for domain, rows in matches.items()
        if any(domain in candidates({**row, "prenom": "", "nom": ""}, domains_config) for row in rows)
    }
    ordered = sorted(matches)
    rand.shuffle(ordered)
    ordered.sort(key=lambda domain: domain not in from_company)  # d'abord les noms d'entreprise

    out_dir = raw_dir(project, SOURCE)
    fields = list(registry[0].keys()) + ["domain"] if registry else ["domain"]
    with (out_dir / "input_a.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for domain in ordered:
            for row in matches[domain]:
                writer.writerow({**row, "domain": domain})

    by_keyword = []
    for domain in active:
        label = domain[:-3]
        if domain in matches or not keyword.search(label) or (false_friend and false_friend.search(label)):
            continue
        by_keyword.append(domain)
    by_keyword.sort()
    rand.shuffle(by_keyword)
    by_keyword.sort(key=lambda domain: not strong.search(domain[:-3]))  # d'abord les mots les plus specifiques
    with (out_dir / "input_b.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["domain"])
        writer.writeheader()
        writer.writerows({"domain": domain} for domain in by_keyword)

    summary = {"domaines_actifs": len(active), "a_noms": len(ordered), "b_mots": len(by_keyword)}
    print(summary, flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", default=".")
    parser.add_argument("--config")
    parser.add_argument("--afnic", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config = load_config(args.project, args.config)
        if args.dry_run:
            print(f"A blanc : lirait {args.afnic} et data/registre.csv, sans aucune requete reseau.")
            return 0
        require_terms_review(args.project, SOURCE)
        build(args.project, config, args.afnic)
        return 0
    except GuardrailError as exc:
        print(f"GARDE-FOU : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
