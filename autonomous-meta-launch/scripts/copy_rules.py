"""Textes correles par adset : assemblage et controle avant tout envoi.

Pour chaque pub : texte 1 propre a la video, textes 2 a 5 communs a l'adset.
Les 5 titres sont communs a l'adset. L'offre et l'appel a l'action terminent
chaque texte.
"""
from __future__ import annotations

import pathlib
import re

COUNT = 5


def adset_of(cfg, ad):
    for adset in cfg["adsets"]:
        if adset["name"] == ad["adset"]:
            return adset
    return None


def resolve_ad(cfg, ad):
    """Renvoie les 5 textes, les 5 titres, la description et la page d'arrivee d'une pub."""
    copy, adset = cfg["copy"], adset_of(cfg, ad)
    ending = [copy["offer"], copy["cta"]]
    stack = ad.get("stack", adset.get("stack", ""))
    first = "\n\n".join(p for p in [ad["body"], stack] + ending if p)
    bodies = [first] + ["\n\n".join([variant] + ending) for variant in adset["variants"]]
    return {"bodies": bodies, "titles": list(adset["titles"]), "description": ad["description"], "link": adset["link"]}


def _check_ad(cfg, ad, adset):
    rules = cfg["copy"].get("rules", {})
    resolved = resolve_ad(cfg, ad)
    bodies, titles, description = resolved["bodies"], resolved["titles"], resolved["description"]
    tag, problems = ad["id"], []
    if len(bodies) != COUNT or len(titles) != COUNT:
        problems.append("%s : %d textes et %d titres, il en faut %d de chaque" % (tag, len(bodies), len(titles), COUNT))
    limit = rules.get("first_line_max", 125)
    for text in bodies:
        if len(text.split("\n")[0]) > limit:
            problems.append("%s : premiere ligne de plus de %d caracteres : %s" % (tag, limit, text[:50]))
        for needed in (cfg["copy"]["offer"], cfg["copy"]["cta"]):
            if needed.rstrip(".") not in text:
                problems.append("%s : offre ou appel a l'action absent : %s" % (tag, text[:50]))
    needed_title = adset.get("title_must_contain", "")
    for title in titles:
        if needed_title and needed_title.lower() not in title.lower():
            problems.append("%s : titre sans %r : %s" % (tag, needed_title, title))
    everything = "\n".join(bodies + titles + [description])
    for pattern in rules.get("banned", []):
        if re.search(pattern, everything, re.I):
            problems.append("%s : mot interdit %r" % (tag, pattern))
    for pattern in adset.get("audience_forbidden", []):
        if re.search(pattern, everything, re.I):
            problems.append("%s : mauvaise audience pour %s : %r" % (tag, adset["name"], pattern))
    hook = ad.get("hook") or {}
    if hook:
        if "allowed_hook_targets" in adset and hook.get("target", "") not in adset["allowed_hook_targets"]:
            problems.append("%s : cible d'accroche hors liste : %r" % (tag, hook.get("target")))
        if "allowed_hook_offers" in adset and hook.get("offer", "") not in adset["allowed_hook_offers"]:
            problems.append("%s : offre d'accroche hors liste : %r" % (tag, hook.get("offer")))
    return problems


def check(cfg):
    """Renvoie la liste des problemes. Vide : les textes peuvent partir."""
    problems = []
    names = [adset["name"] for adset in cfg["adsets"]]
    ids = [ad["id"] for ad in cfg["ads"]]
    for label, values in (("adset", names), ("pub", ids)):
        doubles = sorted({v for v in values if values.count(v) > 1})
        if doubles:
            problems.append("%s en double : %s" % (label, doubles))
    needle = cfg["conversion"]["url_contains"].lower()
    thanks = cfg["conversion"].get("thank_you_url", "")
    if thanks and needle not in thanks.lower():
        problems.append("la page merci %s ne contient pas %r : aucune conversion ne serait comptee" % (thanks, needle))
    for adset in cfg["adsets"]:
        if needle in adset["link"].lower():
            problems.append("la page d'arrivee %s contient %r : chaque visite compterait comme une conversion" % (adset["link"], needle))
    for ad in cfg["ads"]:
        adset = adset_of(cfg, ad)
        if adset is None:
            problems.append("%s : adset inconnu %r" % (ad["id"], ad["adset"]))
            continue
        problems += _check_ad(cfg, ad, adset)
    return problems


def write_review(cfg, path):
    """Ecrit un fichier a relire par un humain, classe par adset."""
    lines = []
    for adset in cfg["adsets"]:
        ads = [ad for ad in cfg["ads"] if ad["adset"] == adset["name"]]
        lines += ["#" * 60, "ADSET : %s" % adset["name"], "Page d'arrivee : %s" % adset["link"], "", "LES 5 TITRES (communs a cet adset)"]
        lines += ["%d. %s" % (i + 1, t) for i, t in enumerate(adset["titles"])]
        lines += ["", "TEXTES 2 A 5 (communs a cet adset)"]
        lines += ["--- Texte %d ---\n%s\n" % (i + 2, v) for i, v in enumerate(adset["variants"])]
        for ad in ads:
            resolved = resolve_ad(cfg, ad)
            hook = ad.get("hook") or {}
            lines += ["=" * 60, "%s - %s" % (ad["id"], ad["slug"])]
            if hook:
                lines.append("Accroche horizontale : %s / %s" % (hook.get("target") or "(sans cible)", hook.get("offer", "")))
            lines += ["", "DESCRIPTION", resolved["description"], "", "TEXTE PRINCIPAL 1", resolved["bodies"][0], ""]
    pathlib.Path(path).write_text("\n".join(lines), encoding="utf-8")
