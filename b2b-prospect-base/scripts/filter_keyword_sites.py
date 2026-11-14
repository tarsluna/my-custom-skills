#!/usr/bin/env python3
"""Filtre le crawl brut et ecrit sources/<name>.csv.

Les sites identifies par les seuls mots du metier (`mots_cles`) sont les plus risques :
boutiques, annuaires, ecoles, medias ou fournisseurs y passent facilement. Le filtre lit
ce que le site dit de lui-meme (titre, h1, description, signaux de evidence.jsonl).

Les sites identifies par SIREN ou nom + lieu gardent leur identite. Ils ne sont retires
que si le site n'evoque jamais le metier.

Usage : python3 -I scripts/filter_keyword_sites.py --project DOSSIER --name NOM [--dry-run]
"""
import argparse
import collections
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prospect_core import SCHEMA, GuardrailError, load_config, normalize, raw_dir, read_csv  # noqa: E402

GENERIC_LABEL = re.compile(
    r"^(accueil|home|bienvenue|welcome|index|contact|page d.?accueil|site officiel|monsite|mon site|"
    r"wp|wordpress|wix|jimdo|site|site web|sans titre|untitled)$"
)
SPLIT = re.compile(r"\s[|\-–—:•]\s")
LEVEL_ORDER = {"siren": 0, "nom+lieu": 1, "fiche_ouverte": 2, "mots_cles": 3}


class Filter:
    def __init__(self, config):
        qf = config.get("quality_filter", {})
        self.hard = {name: re.compile(rx) for name, rx in qf.get("hard", {}).items()}
        self.soft = {name: re.compile(rx) for name, rx in qf.get("soft", {}).items()}
        self.explicit = re.compile(qf.get("explicit_regex") or "|".join(s["title_regex"] for s in config["segments"]))
        self.domain_trade = re.compile(qf["domain_trade_regex"]) if qf.get("domain_trade_regex") else None
        self.thresholds = qf.get("signal_thresholds", {})
        self.segments = [(s["name"], re.compile(s["title_regex"])) for s in config["segments"]]
        self.signal_names = set(config.get("site_signals", {}))

    @staticmethod
    def blob(item):
        return normalize(" | ".join([item.get("title", ""), item.get("h1", ""), item.get("desc", "")]))

    def keyword_reason(self, item):
        """Motif de retrait d'un site `mots_cles`, ou chaine vide."""
        blob = self.blob(item)
        home = normalize(item.get("home", ""))
        signals = item.get("signals", {})
        for name, pattern in self.hard.items():
            if pattern.search(blob):
                return name
        foreign = self.thresholds.get("hors_france")
        if foreign and signals.get("hors_france", 0) >= foreign:
            return "etranger"
        if not self.explicit.search(blob):
            for name, pattern in self.soft.items():
                if pattern.search(blob):
                    return name
            for name, threshold in self.thresholds.items():
                if name != "hors_france" and signals.get(name, 0) >= threshold:
                    return name
        if self.explicit.search(blob) or self.explicit.search(home):
            return ""
        label = item.get("domain", "").rsplit(".", 1)[0]
        strong_domain = self.domain_trade and self.domain_trade.search(label)
        strong_body = sum(signals.get(name, 0) for name in self.signal_names if name.startswith("metier"))
        if strong_domain and strong_body >= 2:
            return ""
        return "metier_non_affiche"

    def identity_reason(self, item):
        """Un site identifie qui n'evoque jamais le metier sort de la base."""
        if not any(name.startswith("metier") for name in self.signal_names):
            return ""
        signals = item.get("signals", {})
        if not any(value for name, value in signals.items() if name.startswith("metier")):
            return "hors_metier"
        return ""

    def segment_for(self, item, current):
        blob = self.blob(item)
        for name, pattern in self.segments:
            if pattern.search(blob):
                return name
        return current

    @staticmethod
    def clean_company(item, current):
        """Evite 'Accueil' ou un titre de referencement : prend la partie du titre qui rappelle le domaine."""
        label_tokens = {t for t in re.split(r"[^a-z0-9]+", item.get("domain", "").rsplit(".", 1)[0]) if len(t) >= 4}
        parts = [p.strip() for p in SPLIT.split(item.get("title", "")) if p.strip()]
        useful = [p for p in parts if not GENERIC_LABEL.match(normalize(p))]
        for part in useful:
            if any(token in normalize(part).replace(" ", "") for token in label_tokens):
                return part[:80]
        if GENERIC_LABEL.match(normalize(current)) or len(current) > 80:
            return useful[0][:80] if useful else item.get("domain", "")
        return current


def domain_of(row):
    return re.sub(r"^https?://", "", row.get("site", ""))


def run(project, config, name):
    folder = raw_dir(project, name)
    source = folder / "brut.csv"
    evidence_path = folder / "evidence.jsonl"
    if not source.exists() or not evidence_path.exists():
        raise GuardrailError(f"{source} ou evidence.jsonl absent : lance crawl_sites.py d'abord.")
    evidence = {}
    with evidence_path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                item = json.loads(line)
                evidence[item["domain"]] = item
    rows = read_csv(source)
    rows.sort(key=lambda r: (LEVEL_ORDER.get(evidence.get(domain_of(r), {}).get("level"), 9), not r.get("siren")))

    filter_ = Filter(config)
    kept, removed, seen, reasons = [], [], set(), collections.Counter()
    for row in rows:
        domain = domain_of(row)
        item = evidence.get(domain)
        if item is None:
            motif = "sans_trace"
        elif item["level"] == "mots_cles":
            motif = filter_.keyword_reason(item)
        else:
            motif = filter_.identity_reason(item)
        if motif:
            reasons[motif] += 1
            removed.append({"domaine": domain, "motif": motif})
            continue
        if item["level"] == "mots_cles":
            row["segment"] = filter_.segment_for(item, row["segment"])
            row["entreprise"] = filter_.clean_company(item, row["entreprise"])
        if row["email"] in seen:
            reasons["doublon_mail"] += 1
            continue
        seen.add(row["email"])
        kept.append(row)

    sources_dir = Path(project) / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    with (sources_dir / f"{name}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCHEMA)
        writer.writeheader()
        writer.writerows({k: r.get(k, "") for k in SCHEMA} for r in kept)
    with (folder / "retires.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["domaine", "motif"])
        writer.writeheader()
        writer.writerows(removed)
    print("lignes brutes:", len(rows), "gardees:", len(kept), "retraits:", reasons.most_common(), flush=True)
    return kept, reasons


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", default=".")
    parser.add_argument("--config")
    parser.add_argument("--name", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config = load_config(args.project, args.config)
        if args.dry_run:
            print(f"A blanc : filtrerait data/raw/{args.name}/brut.csv vers sources/{args.name}.csv, sans reseau.")
            return 0
        run(args.project, config, args.name)
        return 0
    except GuardrailError as exc:
        print(f"GARDE-FOU : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
