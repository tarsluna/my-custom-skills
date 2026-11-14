"""Contrôle d'une liste de contacts avant lancement : part des messageries grand public, et « oui » qu'on ne pourra pas servir."""
from __future__ import annotations

import csv
from collections import Counter
from typing import Any, Dict, Iterable

from .text import company_domain, domain_from_email

PROVIDER_GROUPS = {
    "gmail": "Gmail", "googlemail": "Gmail",
    "hotmail": "Microsoft", "outlook": "Microsoft", "live": "Microsoft", "msn": "Microsoft",
    "yahoo": "Yahoo", "ymail": "Yahoo",
    "icloud": "Apple", "me": "Apple",
}
WARN_SHARE = 0.15


def check_leads(path: str, consumer_mailboxes: Iterable[str]) -> Dict[str, Any]:
    consumer = set(consumer_mailboxes)
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = {c.strip().lower(): c for c in (reader.fieldnames or [])}
        email_col = next((columns[c] for c in ("email", "e-mail", "mail", "email address") if c in columns), None)
        site_col = next((columns[c] for c in ("website", "site", "site web", "url") if c in columns), None)
        if not email_col:
            raise ValueError("colonne email introuvable dans %s" % path)
        total, providers, unservable = 0, Counter(), 0
        for row in reader:
            email = (row.get(email_col) or "").strip().lower()
            domain = domain_from_email(email)
            if not domain:
                continue
            total += 1
            labels = domain.split(".")[:-1]
            hit = next((label for label in labels if label in consumer), None)
            if hit:
                providers[PROVIDER_GROUPS.get(hit, "autres grand public")] += 1
            if not company_domain(row.get(site_col) if site_col else None, email, consumer):
                unservable += 1
    share = sum(providers.values()) / total if total else 0.0
    return {"total": total, "consumer": dict(providers), "consumer_share": share, "no_domain": unservable}


def format_check(result: Dict[str, Any]) -> str:
    total = result["total"] or 1
    lines = ["%d adresses lues." % result["total"]]
    for name, count in sorted(result["consumer"].items(), key=lambda kv: -kv[1]):
        lines.append("  %s : %d (%.0f %%)" % (name, count, 100 * count / total))
    lines.append("Messageries grand public : %.0f %% de la liste." % (100 * result["consumer_share"]))
    if result["consumer_share"] > WARN_SHARE:
        lines.append(
            "Attention : Gmail et Microsoft refusent souvent les boîtes d'envoi récentes ou d'un autre domaine que la marque. "
            "Envoyez d'abord une petite vague vers ces adresses et regardez les rebonds, ou sortez-les de la campagne."
        )
    if result["no_domain"]:
        lines.append(
            "%d contact(s) sans site ni adresse professionnelle : un « oui » de leur part partira en alerte, sans livrable automatique."
            % result["no_domain"]
        )
    return "\n".join(lines)
