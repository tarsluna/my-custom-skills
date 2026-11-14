#!/usr/bin/env python3
"""Fusionne sources/*.csv en livrable/base_prospects.csv et livrable/stats.md.

Dedoublonnage sur le mail en minuscules. On garde la ligne la plus complete, on remplit
ses champs vides avec les autres lignes du meme mail, on cumule les source_url et on
garde la date de collecte la plus ancienne, qui fait courir le delai d'information.

Rejets : format invalide, adresses parasites, ligne sans preuve d'origine, liste de
suppression (suppression.csv), domaines sans MX. Le MX passe uniquement par `dig`,
jamais par SMTP. Les boites personnelles sont exclues par defaut.

Le prenom manquant est complete depuis le registre, sauf si le nom publie ou la boite
nominative designent quelqu'un d'autre que le dirigeant.

Usage : python3 -I scripts/merge.py --project DOSSIER [--dry-run]
"""
import argparse
import calendar
import csv
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prospect_core import FREEMAIL_DOMAINS, SCHEMA, GuardrailError, host_of, is_under, load_config, raw_dir  # noqa: E402

OUTPUT_COLUMNS = SCHEMA + ["prenom_source", "pret_campagne", "nb_sources", "a_arbitrer", "jugement_metier"]
URL_SEPARATOR = " | "
MX_WORKERS = 8
QC_MIN_LINES = 50
QC_MIN_SHARE = 0.8

EMAIL_RE = re.compile(r"^[a-z0-9._%+'-]+@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,24}$")
EDGE_JUNK = " \t\r\n<>()[]\"'.,;:​‎﻿ "
MOBILE_LOCAL = re.compile(r"^(\+?33|0033|0)[67]\d{8}$")
FILE_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "svg", "webp", "avif", "bmp", "ico", "tif", "tiff", "css", "js", "map",
    "json", "woff", "woff2", "ttf", "eot", "mp4", "webm", "pdf", "html", "htm", "php",
}
EXAMPLE_DOMAINS = {
    "example.com", "example.org", "example.net", "exemple.com", "exemple.fr", "domaine.com", "domaine.fr",
    "votredomaine.com", "votredomaine.fr", "mondomaine.com", "mondomaine.fr", "monsite.com", "monsite.fr",
}
PLACEHOLDER_LOCALS = {
    "votre", "votreemail", "votre.email", "votre-email", "votremail", "votre.mail", "votre-mail", "youremail",
    "your.email", "your-email", "prenom", "nom", "prenom.nom", "nom.prenom", "john.doe", "jane.doe", "johndoe",
    "janedoe", "xxx", "xxxx", "exemple", "example", "test",
}
SHARED_HOSTS = FREEMAIL_DOMAINS | {
    "wixsite.com", "wix.com", "business.site", "jimdofree.com", "jimdo.com", "webnode.fr", "webnode.com",
    "over-blog.com", "wordpress.com", "blogspot.com", "google.com", "linktr.ee", "facebook.com", "instagram.com",
    "linkedin.com", "pagesperso-orange.fr", "e-monsite.com",
}
NOT_A_FIRST_NAME = {
    "contact", "agence", "atelier", "studio", "bureau", "bonjour", "madame", "monsieur", "mme", "mr", "mlle",
    "info", "accueil", "secretariat", "direction", "equipe",
}
LEGAL_FORMS = {"sarl", "sas", "sasu", "eurl", "selarl", "selas", "selafa", "scp", "snc", "sa", "sci", "ei"}


def fold(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def clean_text(value):
    value = re.sub(r"\s+", " ", (value or "").strip())
    # Une cellule venue du web ne doit pas s'executer comme formule dans un tableur.
    return re.sub(r"^[=+\-@]+\s*", "", value)


def clean_first_name(value):
    value = value.strip(" .,;:")
    if len(value) < 2 or re.search(r"[\d@/]", value) or fold(value) in NOT_A_FIRST_NAME:
        return ""
    return value.title() if value.isupper() or value.islower() else value


def clean_siren(value):
    digits = re.sub(r"\D", "", value or "")
    return digits[:9] if len(digits) in (9, 14) else ""


def normalize_email(raw):
    email = unquote((raw or "").strip())
    email = re.sub(r"^mailto:", "", email, flags=re.I).split("?")[0]
    return email.strip(EDGE_JUNK).lower()


def ascii_domain(domain):
    try:
        return domain.encode("idna").decode("ascii")
    except UnicodeError:
        return ""


def has_valid_format(email):
    if email.count("@") != 1 or len(email) > 254:
        return False
    local, domain = email.split("@")
    if not local or len(local) > 64 or local[0] == "." or local[-1] == "." or ".." in local:
        return False
    return bool(EMAIL_RE.match(f"{local}@{ascii_domain(domain)}"))


def rejection_before_dns(email, public_regex):
    """Motif de rejet qui ne demande aucune requete DNS, ou None."""
    if not email:
        return "mail_absent"
    local, _, domain = email.partition("@")
    if domain.rsplit(".", 1)[-1] in FILE_EXTENSIONS:  # x@2x.png ressemble a une adresse valide
        return "parasite:fichier"
    if not has_valid_format(email):
        return "format_invalide"
    if is_under(domain, EXAMPLE_DOMAINS) or local in PLACEHOLDER_LOCALS:
        return "parasite:exemple"
    tokens = set(re.split(r"[._+-]+", local))
    compact = re.sub(r"[._+-]+", "", local)
    if compact.startswith(("noreply", "donotreply", "nepasrepondre", "nereponspas")):
        return "parasite:noreply"
    if "webmaster" in compact:
        return "parasite:webmaster"
    if tokens & {"dpo", "dpd"}:
        return "parasite:dpo"
    if tokens & {"rgpd", "gdpr", "privacy"} or re.search(r"rgpd|gdpr|donneespersonnelles|protectiond(es)?donnees", compact):
        return "parasite:rgpd"
    if "sentry" in tokens or "sentry" in domain or re.fullmatch(r"[0-9a-f]{24,}", local):
        return "parasite:sentry"
    if MOBILE_LOCAL.match(re.sub(r"[ ._-]", "", local)):
        return "portable_dans_le_mail"
    if public_regex and re.search(public_regex, domain, re.I):
        return "organisme_public"
    return None


def load_suppression(path, warnings):
    """Une valeur sans partie locale, comme @domaine.fr, bloque tout le domaine."""
    emails, domains = set(), set()
    if not path.exists():
        return emails, domains
    with path.open(encoding="utf-8-sig", newline="", errors="replace") as handle:
        rows = [row for row in csv.reader(handle) if any(cell.strip() for cell in row)]
    column = 0
    if rows:
        header = [cell.strip().lower() for cell in rows[0]]
        named = [i for i, cell in enumerate(header) if cell in ("email", "mail", "e-mail", "adresse")]
        if named:
            column, rows = named[0], rows[1:]
    unknown = 0
    for row in rows:
        value = normalize_email(row[column] if column < len(row) else "")
        if has_valid_format(value):
            emails.add(value)
        elif has_valid_format("x@" + value.lstrip("@")):
            domains.add(value.lstrip("@"))
        else:
            unknown += 1
    if unknown:
        warnings.append(f"suppression.csv : {unknown} entree(s) non reconnue(s), donc non appliquee(s).")
    return emails, domains


def dig_mx(domain):
    """'ok', 'none' ou 'indetermine', par DNS uniquement."""
    name = ascii_domain(domain)
    try:
        short = subprocess.run(["dig", "+short", "+time=3", "+tries=2", "MX", name],
                               capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return "indetermine"
    output = short.stdout.strip()
    if short.returncode != 0 or ";;" in output:
        return "indetermine"
    if output:
        fields = [line.split() for line in output.splitlines()]
        hosts = [f[1] for f in fields if len(f) == 2 and f[0].isdigit()]
        return "ok" if any(host != "." for host in hosts) else "none"  # "0 ." : MX nul, RFC 7505
    # +short n'affiche rien, ni pour NXDOMAIN ni pour SERVFAIL : on lit le statut.
    try:
        full = subprocess.run(["dig", "+noall", "+comments", "+time=3", "+tries=2", "MX", name],
                              capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return "indetermine"
    status = re.search(r"status: (\w+)", full.stdout)
    return "none" if status and status.group(1) in ("NOERROR", "NXDOMAIN") else "indetermine"


def resolve_domains(domains, cache_path, mx_lookup):
    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except ValueError:
            cache = {}
    pending = sorted(d for d in domains if d not in cache)
    with ThreadPoolExecutor(MX_WORKERS) as pool:
        fresh = dict(zip(pending, pool.map(mx_lookup, pending)))
    cache.update({d: status for d, status in fresh.items() if status != "indetermine"})
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=0, sort_keys=True), encoding="utf-8")
    return {d: fresh.get(d, cache.get(d)) for d in domains}


def read_sources(folder, warnings):
    rows, lines_read = [], Counter()
    csv.field_size_limit(10_000_000)
    for path in sorted(folder.glob("*.csv")):
        with path.open(encoding="utf-8-sig", newline="", errors="replace") as handle:
            reader = csv.DictReader(handle)
            missing = [c for c in SCHEMA if c not in (reader.fieldnames or [])]
            if "email" in missing:
                warnings.append(f"{path.name} : pas de colonne email, fichier ignore.")
                continue
            if missing:
                warnings.append(f"{path.name} : colonnes manquantes : {', '.join(missing)}.")
            for number, raw in enumerate(reader, start=2):
                row = {c: clean_text(raw.get(c)) for c in SCHEMA}
                row["email"] = normalize_email(raw.get("email"))
                row["_source"], row["_line"] = path.stem, number
                lines_read[path.stem] += 1
                rows.append(row)
    return rows, lines_read


def merge_group(group):
    filled = lambda row: sum(1 for column in SCHEMA if row.get(column))  # noqa: E731
    group = sorted(group, key=lambda r: (-filled(r), not r["prenom"], r["_source"], r["_line"]))
    merged = {column: group[0].get(column, "") for column in SCHEMA}
    for other in group[1:]:
        for column in SCHEMA:
            if not merged[column] and other.get(column):
                merged[column] = other[column]
    urls = list(dict.fromkeys(r["source_url"] for r in group if r["source_url"]))
    dates = [r["collected_at"] for r in group if r["collected_at"]]
    merged["source_url"] = URL_SEPARATOR.join(urls)
    merged["collected_at"] = min(dates) if dates else ""
    merged["nb_sources"] = len(urls)
    merged["_sources"] = sorted({r["_source"] for r in group})
    return merged


def compact_name(text):
    name = "".join(word for word in fold(text).split() if word not in LEGAL_FORMS)
    return name if len(name) >= 5 else ""


def load_registry(path, warnings):
    by_siren, by_name = {}, defaultdict(set)
    if not path.exists():
        warnings.append("data/registre.csv absent : aucun prenom complete.")
        return by_siren, by_name
    with path.open(encoding="utf-8-sig", newline="", errors="replace") as handle:
        for raw in csv.DictReader(handle):
            siren = clean_siren(raw.get("siren"))
            if not siren:
                continue
            entry = {"prenom": clean_first_name(clean_text(raw.get("prenom"))), "nom": clean_text(raw.get("nom"))}
            if siren not in by_siren or (entry["prenom"] and not by_siren[siren]["prenom"]):
                by_siren[siren] = entry
            key = compact_name(raw.get("entreprise"))
            if key:
                by_name[key].add(siren)
    return by_siren, by_name


def contact_domain(row):
    """Domaine propre a l'entreprise, ou "" s'il est partage (messagerie, hebergeur)."""
    domain = host_of(row["site"])
    if not domain and row["email"].split("@")[1] not in FREEMAIL_DOMAINS:
        domain = row["email"].split("@")[1]
    return "" if not domain or is_under(domain, SHARED_HOSTS) else domain


def find_siren(row, by_siren, by_name, domain_sirens, domain_companies):
    siren = clean_siren(row["siren"])
    if siren in by_siren:
        return siren
    domain = contact_domain(row)
    if not domain or len(domain_companies[domain]) > 1 or len(domain_sirens[domain]) > 1:
        return ""
    if domain_sirens[domain]:
        known = next(iter(domain_sirens[domain]))
        return known if known in by_siren else ""
    candidates = by_name.get(compact_name(domain.split(".")[0].replace("-", " ")), set())
    return next(iter(candidates)) if len(candidates) == 1 else ""


def same_person(row, entry):
    published, registered = set(fold(row["nom"]).split()), set(fold(entry["nom"]).split())
    if published and registered and not published & registered:
        return False
    if row["email_type"] == "nominatif":
        local = re.sub(r"[^a-z0-9]", "", row["email"].split("@")[0])
        parts = [fold(entry["prenom"]).replace(" ", ""), fold(entry["nom"]).replace(" ", "")]
        return any(len(part) >= 3 and part in local for part in parts)
    return True


def complete_first_names(contacts, by_siren, by_name):
    domain_sirens, domain_companies = defaultdict(set), defaultdict(set)
    for row in contacts:
        domain = contact_domain(row)
        if not domain:
            continue
        if clean_siren(row["siren"]):
            domain_sirens[domain].add(clean_siren(row["siren"]))
        if row["entreprise"]:
            domain_companies[domain].add(fold(row["entreprise"]))
    discarded = 0
    for row in contacts:
        row["siren"] = clean_siren(row["siren"]) or row["siren"]
        row["prenom"] = clean_first_name(row["prenom"])
        row["prenom_source"] = "publie" if row["prenom"] else ""
        if row["prenom"]:
            continue
        siren = find_siren(row, by_siren, by_name, domain_sirens, domain_companies)
        entry = by_siren.get(siren)
        if not entry or not entry["prenom"]:
            continue
        if not same_person(row, entry):
            discarded += 1
            continue
        row["prenom"], row["prenom_source"] = entry["prenom"], "dirigeant_registre"
        row["siren"] = row["siren"] or siren
    return discarded


def one_month_after(day):
    year, month = day.year + day.month // 12, day.month % 12 + 1
    return day.replace(year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1]))


def qc_status(project, source, lines, max_bad_rate):
    """Lit qc_report.json : `` si la source a passe le tirage, sinon le drapeau a poser."""
    path = raw_dir(project, source) / "qc_report.json"
    if not path.exists():
        return "qc_absent"
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("relues", 0) < QC_MIN_SHARE * min(QC_MIN_LINES, lines):
        return "qc_insuffisant"
    rate = report.get("taux_mauvaises")
    if rate is None or rate > max_bad_rate:
        return "qc_trop_de_mauvaises"
    return ""


def load_verdicts(path):
    verdicts = {}
    if path.exists():
        with path.open(encoding="utf-8", newline="") as handle:
            for raw in csv.DictReader(handle):
                if raw.get("statut") == "ok":
                    verdicts[host_of(raw["domain"])] = (raw["choice"], float(raw["confidence"]))
    return verdicts


def to_arbitrate(row, rules, qc_flags):
    urls = [url for url in row["source_url"].split(URL_SEPARATOR) if url]
    flags = []
    if row["email"].split("@")[1] in FREEMAIL_DOMAINS or row["email_type"] == "domaine_perso":
        flags.append("boite_perso")
    for rule in rules:
        if urls and all(rule["url_contains"] in url for url in urls):
            flags.append(rule["flag"])
    sources_qc = {qc_flags.get(source, "qc_absent") for source in row["_sources"]}
    flags += sorted(flag for flag in sources_qc if flag)
    return ";".join(flags)


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return lines


def write_stats(path, contacts, lines_read, rejected, rejected_emails, alerts):
    total = len(contacts)
    ready = sum(1 for row in contacts if row["pret_campagne"] == "oui")
    origin = Counter(row["prenom_source"] for row in contacts)
    lines = [
        "# Statistiques de fusion", "",
        f"- Contacts uniques : **{total}**",
        f"- Prets pour la campagne (prenom, mail, entreprise, rien a arbitrer) : **{ready}**",
        f"- Prenom publie : {origin['publie']} ; complete par le dirigeant : {origin['dirigeant_registre']} ; "
        f"sans prenom : {origin['']}",
        f"- Lignes lues : {sum(lines_read.values())} dans {len(lines_read)} fichier(s)",
        "", "## A arbitrer", "",
    ]
    counts = Counter(row["a_arbitrer"] or "(rien)" for row in contacts)
    lines += table(["a_arbitrer", "contacts"], counts.most_common())
    lines += ["", "## Rejets par motif", ""]
    lines += table(["motif", "lignes", "adresses distinctes"],
                   [(m, c, len(rejected_emails[m])) for m, c in rejected.most_common()])
    lines += ["", "## Alertes (signalees, non appliquees)", ""]
    lines += [f"- {alert}" for alert in alerts] or ["- Aucune."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_alerts(contacts, status, discarded, warnings, max_per_domain):
    alerts = []
    per_domain = Counter(row["email"].split("@")[1] for row in contacts if row["email"].split("@")[1] not in FREEMAIL_DOMAINS)
    over = [count for count in per_domain.values() if count > max_per_domain]
    if over:
        alerts.append(f"Domaines de plus de {max_per_domain} adresses : {len(over)}, maximum {max(over)} sur un meme domaine.")
    if discarded:
        alerts.append(f"Prenoms du dirigeant ecartes car le nom ou la boite designent une autre personne : {discarded}.")
    unknown = sum(1 for value in status.values() if value == "indetermine")
    if unknown:
        alerts.append(f"Domaines au MX indetermine (rejetes, a relancer) : {unknown}.")
    days = []
    for row in contacts:
        try:
            days.append(dt.date.fromisoformat(row["collected_at"][:10]))
        except ValueError:
            continue
    if days:
        oldest = min(days)
        alerts.append(f"Collecte la plus ancienne : {oldest.isoformat()}. Information des personnes (RGPD art. 14) due "
                      f"au plus tard le {one_month_after(oldest).isoformat()}, ou au premier contact s'il arrive avant.")
    return alerts + warnings


def run(project, config, mx_lookup=dig_mx):
    project = Path(project)
    settings = config.get("merge", {})
    mode = settings.get("personal_mailboxes", "exclude")
    if mode not in ("exclude", "flag"):
        raise GuardrailError("merge.personal_mailboxes doit valoir `exclude` ou `flag`.")
    judge = config.get("judge", {})
    public_regex = settings.get("public_mail_regex")
    warnings = []
    rows, lines_read = read_sources(project / "sources", warnings)
    suppressed_emails, suppressed_domains = load_suppression(project / "suppression.csv", warnings)
    by_siren, by_name = load_registry(project / "data" / "registre.csv", warnings)

    rejected, rejected_emails, candidates = Counter(), defaultdict(set), []

    def reject(row, motif):
        rejected[motif] += 1
        rejected_emails[motif].add(row["email"])

    for row in rows:
        motif = rejection_before_dns(row["email"], public_regex)
        domain = row["email"].split("@")[1] if "@" in row["email"] else ""
        if not motif and not row["source_url"].startswith("http"):
            motif = "sans_preuve_d_origine"
        if not motif and (row["email"] in suppressed_emails or is_under(domain, suppressed_domains)):
            motif = "liste_opposition"
        if not motif and (domain in FREEMAIL_DOMAINS or row["email_type"] == "domaine_perso") and mode == "exclude":
            motif = "boite_perso_exclue"
        if motif:
            reject(row, motif)
        else:
            candidates.append(row)

    status = resolve_domains({r["email"].split("@")[1] for r in candidates}, project / "data" / "mx_cache.json", mx_lookup)
    groups = defaultdict(list)
    for row in candidates:
        verdict = status[row["email"].split("@")[1]]
        if verdict == "ok":
            groups[row["email"]].append(row)
        else:
            reject(row, "domaine_sans_mx" if verdict == "none" else "mx_indetermine")

    verdicts = load_verdicts(raw_dir(project, "judge") / "verdicts.csv")
    reject_choice, min_confidence = judge.get("reject_choice", "hors_cible"), float(judge.get("min_confidence", 0.8))
    qc_flags = {source: qc_status(project, source, lines_read[source], float(settings.get("max_bad_rate", 0.1)))
                for source in lines_read}
    contacts = []
    for _, group in sorted(groups.items()):
        row = merge_group(group)
        choice, confidence = verdicts.get(host_of(row["site"]), ("", 0.0))
        row["jugement_metier"] = choice
        if choice == reject_choice and confidence >= min_confidence:
            reject(row, "jugement_hors_cible")
            continue
        contacts.append(row)

    discarded = complete_first_names(contacts, by_siren, by_name)
    rules = settings.get("arbitrate", [])
    for row in contacts:
        row["a_arbitrer"] = to_arbitrate(row, rules, qc_flags)
        complete = row["prenom"] and row["email"] and row["entreprise"]
        row["pret_campagne"] = "oui" if complete and not row["a_arbitrer"] else "non"

    output = project / "livrable"
    output.mkdir(parents=True, exist_ok=True)
    target = output / "base_prospects.csv"
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(contacts)
    os.chmod(target, 0o600)
    alerts = build_alerts(contacts, status, discarded, warnings, int(settings.get("max_per_domain", 3)))
    write_stats(output / "stats.md", contacts, lines_read, rejected, rejected_emails, alerts)
    ready = sum(1 for row in contacts if row["pret_campagne"] == "oui")
    print(f"{len(contacts)} contacts, {ready} prets, {sum(rejected.values())} lignes rejetees -> {output}", flush=True)
    return contacts, rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", default=".")
    parser.add_argument("--config")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config = load_config(args.project, args.config)
        if args.dry_run:
            print("A blanc : fusionnerait sources/*.csv, controle MX par dig uniquement, aucun envoi, aucune sonde SMTP.")
            return 0
        if not shutil.which("dig"):
            print("GARDE-FOU : dig introuvable, verification MX impossible.", file=sys.stderr)
            return 2
        run(args.project, config)
        return 0
    except GuardrailError as exc:
        print(f"GARDE-FOU : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
