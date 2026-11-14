#!/usr/bin/env python3
"""Visite les sites officiels et recopie les mails qu'ils publient.

Entree : un CSV avec une colonne `domain`. Avec des colonnes du registre (siren,
entreprise, ville...), le site doit prouver qu'il est bien cette entreprise. Avec
`domain` seul, l'entreprise vient du SIREN lu sur le site, sinon du titre et des mots
du metier (niveau `mots_cles`, a filtrer ensuite). Une colonne `level_hint` valant
`fiche_ouverte` signale une fiche open data qui donne deja le site de l'entreprise.

Ordre par site : robots.txt, puis page legale, puis extraction. Si la page legale
interdit la collecte, rien n'est extrait et le site part dans BLOCKED.md, avec la phrase.
Seuls mailto et texte visible comptent. Aucun mail n'est devine ni desobfusque.

Sorties : data/raw/<name>/brut.csv, evidence.jsonl, statuses.tsv, BLOCKED.md.
sources/<name>.csv est ecrit par filter_keyword_sites.py.

Usage : python3 -I scripts/crawl_sites.py --project DOSSIER --input X.csv --name NOM
        [--workers 30] [--limit N] [--sample N] [--shard i/n] [--retry-unreachable] [--dry-run]
"""
import argparse
import collections
import concurrent.futures as cf
import csv
import datetime as dt
import html
import json
import random
import re
import socket
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prospect_core import (  # noqa: E402
    DEFAULT_CONNECTIONS, FREEMAIL_DOMAINS, H1, SCHEMA, ASSET, TAG, TITLE, DESCRIPTION, Blocked, Client, Disallowed,
    ForbiddenHost, GuardrailError, Unreachable, check_workers, first_match, host_of, load_config, mask_contacts,
    normalize, published_emails, raw_dir, read_csv, registrable, terms_forbid, tokens,
)

MAX_PAGES = 5
MAX_EMAILS = 3
MIN_TEXT = 200
LEGAL_PATHS = ("/mentions-legales", "/cgu")
HREF = re.compile(r"""<a\b[^>]*href=["']([^"'#]+)["'][^>]*>(.*?)</a>""", re.I | re.S)
OG_NAME = re.compile(r"""property=["']og:site_name["'][^>]*content=["']([^"']+)""", re.I)
SIREN_IN_TEXT = re.compile(r"(?<!\d)\d{3}[ . ]?\d{3}[ . ]?\d{3}(?!\d)")
LINK = re.compile(r"contact|mention|legal|l[eé]gal|cgu|conditions|a-propos|about|equipe|[eé]quipe|qui-sommes", re.I)
LEGAL_LINK = re.compile(r"mention|legal|l[eé]gal|cgu|conditions", re.I)
SKIP_LOCAL = re.compile(r"^(recrutement|rh|jobs?|emploi|stage|compta|comptabilite|facturation|presse)\b", re.I)
GENERIC_LOCALS = (
    "contact|info|infos|hello|bonjour|agence|atelier|studio|accueil|secretariat|mail|email|"
    "admin|administratif|commercial|direction|projets?|devis|rdv|communication|marketing"
)


class Crawl:
    """Regles du metier compilees a partir de la configuration."""

    def __init__(self, config):
        self.config = config
        self.segments = [(s["name"], re.compile(s["title_regex"])) for s in config["segments"]]
        self.trade = re.compile("|".join(s["title_regex"] for s in config["segments"]))
        extra = [re.escape(word) for word in config.get("generic_mail_locals", [])]
        self.generic = re.compile(r"^(%s)\b" % "|".join([GENERIC_LOCALS] + extra), re.I)
        self.trade_words = set(config.get("domains", {}).get("trade_words", []))
        self.signals = {name: re.compile(rx) for name, rx in config.get("site_signals", {}).items()}
        self.registry_nafs = set(config.get("registry", {}).get("naf", {}))

    def email_type(self, email):
        local, domain = email.rsplit("@", 1)
        if domain in FREEMAIL_DOMAINS:
            return "domaine_perso"
        return "generique" if self.generic.match(local) else "nominatif"

    def rank(self, email, row):
        kind = self.email_type(email)
        local = normalize(email.rsplit("@", 1)[0])
        names = tokens(row.get("prenom", "")) + tokens(row.get("nom", ""))
        if kind == "nominatif" and any(n in local for n in names if len(n) >= 3):
            return 0
        return {"nominatif": 1, "generique": 2, "domaine_perso": 3}[kind]

    def segment_of(self, row, norm):
        """Le titre vient du site. Le registre ne sert que si le site reste muet."""
        for name, pattern in self.segments:
            if pattern.search(norm):
                return name
        trusted = row.get("naf") in self.registry_nafs or row.get("level_hint") == "fiche_ouverte"
        return row.get("segment", "") if trusted else ""

    def verify(self, row, text):
        digits = re.sub(r"[\s.\- ]", "", text)
        siren = row.get("siren", "")
        if siren and siren in digits:
            return "siren"
        norm = normalize(text)
        significant = [t for t in tokens(row.get("entreprise", "")) if len(t) >= 4 and t not in self.trade_words]
        place = (row.get("code_postal") and row["code_postal"] in text) or (
            row.get("ville") and normalize(row["ville"]) in norm
        )
        if significant and all(t in norm for t in significant) and place and self.trade.search(norm):
            return "nom+lieu"
        return ""

    def identify(self, row, pages, registry_index, home_html):
        joined = " ".join(p.text for p in pages)
        if row.get("level_hint") == "fiche_ouverte":
            return row, "fiche_ouverte"
        if row.get("siren") or row.get("entreprise"):
            level = self.verify(row, joined)
            return (row, level) if level else (None, "")
        for match in SIREN_IN_TEXT.findall(joined):
            known = registry_index.get(re.sub(r"\D", "", match))
            if known:
                return ({**known, "domain": row["domain"]}, "siren")
        norm = normalize(joined)
        if not self.trade.search(norm):
            return None, ""
        name = OG_NAME.search(home_html) or TITLE.search(home_html)
        label = html.unescape(TAG.sub(" ", name.group(1))).strip() if name else ""
        label = re.split(r"\s[|\-–—:]\s", label)[0].strip()
        return ({**row, "entreprise": label}, "mots_cles") if label else (None, "")

    def emails_of(self, page, site):
        kept = set()
        for email in published_emails(page.html, page.text):
            local, domain = email.rsplit("@", 1)
            if SKIP_LOCAL.match(local):
                continue
            if domain in FREEMAIL_DOMAINS or registrable(domain) == registrable(site):
                kept.add(email)
        return kept

    def rows_for(self, row, domain, pages, registry_index):
        known, level = self.identify(row, pages, registry_index, pages[0].html)
        if not known:
            return None
        norm = normalize(" ".join(p.text for p in pages))
        segment = self.segment_of(known, norm)
        if not segment:
            return None
        sources = {}
        for page in pages:
            for email in self.emails_of(page, domain):
                sources.setdefault(email, page.url)
        picked = sorted(sources, key=lambda e: (self.rank(e, known), e))[:MAX_EMAILS]
        today = dt.date.today().isoformat()
        rows = [
            {
                "prenom": "", "nom": "", "email": email,
                "entreprise": known.get("entreprise", ""), "segment": segment,
                "ville": known.get("ville", ""), "code_postal": known.get("code_postal", ""),
                "site": "https://" + domain, "siren": known.get("siren", ""),
                "email_type": self.email_type(email), "source_url": sources[email], "collected_at": today,
            }
            for email in picked
        ]
        return rows, level, known

    def evidence_of(self, domain, level, known, pages, registry_index):
        """Trace sans coordonnees, pour le filtre et le controle qualite."""
        home = pages[0]
        joined = " ".join(p.text for p in pages)
        norm = normalize(joined)
        seen = {re.sub(r"\D", "", m) for m in SIREN_IN_TEXT.findall(joined)}
        return {
            "domain": domain, "level": level,
            "siren": known.get("siren", ""), "entreprise": known.get("entreprise", ""),
            "title": first_match(TITLE, home.html), "h1": first_match(H1, home.html),
            "desc": first_match(DESCRIPTION, home.html),
            "sirens_hors_base": len([x for x in seen if x not in registry_index]),
            "signals": {name: len(rx.findall(norm)) for name, rx in self.signals.items()},
            "home": re.sub(r"\d", "#", mask_contacts(home.text))[:600],
        }


def legal_links(page, base_url, host):
    """Liens internes vers une page legale ou de contact. Legales d'abord."""
    found = []
    for href, label in HREF.findall(page.html):
        url = urllib.parse.urljoin(base_url, html.unescape(href.strip()))
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in ("http", "https") or host_of(url) != host or ASSET.search(parts.path):
            continue
        blob = parts.path + " " + TAG.sub(" ", label)
        if LINK.search(blob):
            found.append((0 if LEGAL_LINK.search(blob) else 1, url.split("#")[0]))
    return [url for _, url in sorted(set(found))]


def safe_page(client, url):
    """Une page, ou None. Les refus remontent : ils arretent le site."""
    try:
        return client.page(url)
    except (Disallowed, Unreachable):
        return None


def read_legal_first(client, base, host):
    """Lit la page legale avant toute extraction. Renvoie (pages legales, accueil ou None)."""
    legal, seen_urls = [], set()
    for path in LEGAL_PATHS:
        page = safe_page(client, base + path)
        if page and len(page.text.strip()) >= MIN_TEXT:
            legal.append(page)
            seen_urls.add(page.url)
            break
    home = None
    if not legal:  # l'accueil ne sert ici qu'a trouver le lien : rien n'en est extrait avant la lecture
        home = safe_page(client, base + "/")
        if home:
            for url in legal_links(home, home.url, host):
                if LEGAL_LINK.search(url) and url not in seen_urls:
                    page = safe_page(client, url)
                    if page:
                        legal.append(page)
                        seen_urls.add(page.url)
                        break
    for page in legal:
        quote = terms_forbid(page.text)
        if quote:
            client.block(page.url, "conditions_du_site", quote)
    return legal, home


def crawl_domain(client, domain, crawl):
    """Pages lisibles d'un site, ou une chaine de statut. Les refus levent Blocked."""
    base = legal = home = None
    for scheme in ("https", "http"):
        candidate = f"{scheme}://{domain}"
        try:
            parser, _ = client.robots_for(candidate + "/")
        except Unreachable:
            continue
        if not parser.can_fetch(client.agent, candidate + "/"):
            client.block(candidate + "/", "robots", "robots.txt interdit la page d'accueil")
        legal, home = read_legal_first(client, candidate, domain)
        if home is None:
            home = safe_page(client, candidate + "/")
        if home or legal:
            base = candidate
            break
    if base is None:
        return "injoignable"
    if home is None or len(home.text.strip()) < MIN_TEXT:
        return "vide"

    host = host_of(home.url)
    pages = [home] + [p for p in legal if p.url != home.url]
    seen = {p.url for p in pages}
    links = [url for url in legal_links(home, home.url, host) if url not in seen] or [
        urllib.parse.urljoin(base + "/", "/contact")
    ]
    # Accueil sans mot du metier : une seule page de plus, pour moins solliciter les sites hors sujet.
    extra = MAX_PAGES - len(pages) if crawl.trade.search(normalize(home.text)) else 1
    for url in links[:max(0, extra)]:
        page = safe_page(client, url)
        if page and page.url not in seen:
            seen.add(page.url)
            pages.append(page)
    return pages


def process(group, registry_index, client, crawl, resolve):
    """Un domaine, une visite. Renvoie (lignes, statut, trace)."""
    domain = group[0]["domain"].strip().lower()
    if not resolve(domain):
        return [], "sans_dns", None
    try:
        pages = crawl_domain(client, domain, crawl)
    except Blocked as exc:
        return [], f"bloque:{exc.reason}:{domain}", None
    except ForbiddenHost:
        return [], "exclu", None
    if isinstance(pages, str):
        return [], pages, None
    found = []
    for row in group:
        known, level = crawl.identify(row, pages, registry_index, pages[0].html)
        if known:
            found.append((known, level, row))
    if not found:
        return [], "non_verifie", None
    found.sort(key=lambda item: item[1] != "siren")
    known, level, row = found[0]
    if level != "siren" and len({item[0].get("siren", "") for item in found}) > 1:
        row = {**row, "siren": ""}  # homonymes au meme endroit : on ne choisit pas au hasard
        known = {**known, "siren": ""}
    site = host_of(pages[0].url) or domain  # apres redirection, le site est celui qui publie les mails
    result = crawl.rows_for(row, site, pages, registry_index)
    if not result:
        return [], "non_verifie", None
    lines, level, known = result
    return lines, "verifie", crawl.evidence_of(site, level, known, pages, registry_index)


def resolves(domain):
    try:
        socket.getaddrinfo(domain, 443, proto=socket.IPPROTO_TCP)
        return True
    except OSError:
        return False


def load_registry(project):
    path = Path(project) / "data" / "registre.csv"
    return {row["siren"]: row for row in read_csv(path)} if path.exists() else {}


def run(project, config, client, input_path, name, workers=DEFAULT_CONNECTIONS, limit=None, sample=None,
        shard=None, retry_unreachable=False, resolve=resolves):
    workers = check_workers(workers)
    crawl = Crawl(config)
    folder = raw_dir(project, name)
    done_path, out_path = folder / "done.txt", folder / "brut.csv"
    done = set(done_path.read_text(encoding="utf-8").split("\n")) if done_path.exists() else set()
    statuses_path = folder / "statuses.tsv"
    groups = {}
    for row in read_csv(input_path):
        groups.setdefault(row["domain"].strip().lower(), []).append(row)
    if retry_unreachable:
        last_status = {}
        if statuses_path.exists():
            for line in statuses_path.read_text(encoding="utf-8").splitlines():
                status, _, domain = line.partition("\t")
                last_status[domain] = status
        groups = {d: r for d, r in groups.items() if last_status.get(d) == "injoignable"}
    domains = list(groups)
    if shard:
        index, total = map(int, shard.split("/"))
        domains = domains[index::total]
    if sample:
        domains = random.Random(42).sample(domains, min(sample, len(domains)))
    if limit:
        domains = domains[:limit]
    domains = [d for d in domains if d not in done]
    print(f"a traiter: {len(domains)}", flush=True)

    registry_index = load_registry(project)
    stats = collections.Counter()
    fresh = not out_path.exists() or out_path.stat().st_size == 0
    with out_path.open("a", encoding="utf-8", newline="") as out, done_path.open("a", encoding="utf-8") as dlog, \
            statuses_path.open("a", encoding="utf-8") as slog, \
            (folder / "evidence.jsonl").open("a", encoding="utf-8") as elog:
        writer = csv.DictWriter(out, fieldnames=SCHEMA)
        if fresh:
            writer.writeheader()

        def work(domain):
            try:
                return domain, process(groups[domain], registry_index, client, crawl, resolve)
            except Exception as exc:  # un site pathologique ne doit pas arreter le lot
                return domain, ([], f"erreur:{type(exc).__name__}", None)

        with cf.ThreadPoolExecutor(max_workers=workers) as pool:
            for count, (domain, (lines, status, trace)) in enumerate(pool.map(work, domains), 1):
                head = status.split(":")[0]
                stats[head] += 1
                stats["mails"] += len(lines)
                writer.writerows(lines)
                out.flush()
                if head != "injoignable":
                    dlog.write(domain + "\n")
                    dlog.flush()
                slog.write(f"{head}\t{domain}\n")
                slog.flush()
                if trace:
                    elog.write(json.dumps(trace, ensure_ascii=False) + "\n")
                    elog.flush()
                if count % 200 == 0:
                    print(dict(stats), flush=True)
    print("FINI", dict(stats), flush=True)
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", default=".")
    parser.add_argument("--config")
    parser.add_argument("--input", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--workers", type=int, default=DEFAULT_CONNECTIONS)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--sample", type=int)
    parser.add_argument("--shard")
    parser.add_argument("--retry-unreachable", action="store_true",
                        help="Reprend les sites injoignables. A lancer avec --workers 8.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config = load_config(args.project, args.config)
        check_workers(args.workers)
        if args.dry_run:
            print(f"A blanc : {args.input} serait visite par {args.workers} connexions au plus, "
                  "robots.txt puis page legale avant extraction. Aucune requete envoyee.")
            return 0
        client = Client(args.project, args.name, config)
        run(args.project, config, client, args.input, args.name, args.workers, args.limit, args.sample, args.shard,
            args.retry_unreachable)
        return 0
    except GuardrailError as exc:
        print(f"GARDE-FOU : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
