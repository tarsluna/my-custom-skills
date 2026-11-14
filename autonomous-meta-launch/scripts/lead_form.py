#!/usr/bin/env python3
"""Passe une campagne video vers un formulaire instantane, pubs a l'identique.

Cas reel : une campagne vers un site depense deja. On recopie ses pubs dans une
nouvelle campagne dont la destination est un formulaire instantane, sans
toucher l'ancienne. Rien n'est jamais ecrit sur l'ancienne campagne. Tout ce
qui est cree l'est en pause.

--dry-run n'ecrit rien chez Meta. Avec --file ou --files, aucun reseau ni token.

    lead_form.py check-form   (--file F | --form-id ID) [--locale fr_FR]
    lead_form.py copy-adset   --adset ID --name NOM [--campaign ID]
    lead_form.py diff-adsets  (--files ANCIEN NOUVEAU | --adsets ANCIEN NOUVEAU)
    lead_form.py copy-ad      (--file F | --ad ID [ID ...] | --from-adset ID) --form-id ID --adset ID
    lead_form.py diff         (--files ANCIENNE NOUVELLE | --ads ANCIENNE NOUVELLE)
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from meta_api import DEFAULT_VERSION, GraphClient  # noqa: E402

FORM_LINK = "http://fb.me/"  # lien factice que Meta attend a cote d'un formulaire
DEFAULT_CTA = "LEARN_MORE"
READ_ONLY_FEED_KEYS = ("additional_data", "reasons_to_shop", "shops_bundle")
CREATIVE_FIELDS = "id,name,object_story_spec,asset_feed_spec,degrees_of_freedom_spec,url_tags"
AD_FIELDS = "id,name,status,effective_status,adset_id,creative{%s}" % CREATIVE_FIELDS
ADSET_FIELDS = "id,name,campaign_id,status,targeting,optimization_goal,destination_type,billing_event"
FORM_FIELDS = "id,name,status,locale,questions"
SKIPPED_STATES = {"DISAPPROVED"}
ALLOWED_PLATFORMS = ("facebook", "instagram")


# Charge utile de la creative vers le formulaire

def _instagram(story):
    return story.get("instagram_user_id") or story.get("instagram_actor_id")


def form_creative(creative, form_id):
    """Renvoie les parametres d'une nouvelle creative, identique a `creative`, qui ouvre le formulaire.

    `creative` est la creative d'origine telle que Meta la renvoie en lecture.
    La source n'est jamais modifiee.
    """
    story = creative.get("object_story_spec") or {}
    feed = copy.deepcopy(creative.get("asset_feed_spec") or {})
    params = {key: copy.deepcopy(creative[key]) for key in ("degrees_of_freedom_spec", "url_tags") if creative.get(key)}
    new_story = {"page_id": story.get("page_id")}
    if _instagram(story):
        new_story["instagram_user_id"] = _instagram(story)
    video = story.get("video_data")
    if video:
        # Video simple : le formulaire va dans le bouton, les 5 textes et 5 titres restent dans asset_feed_spec
        cta_type = (video.get("call_to_action") or {}).get("type") or DEFAULT_CTA
        data = {"video_id": video["video_id"]}
        if video.get("image_hash"):
            data["image_hash"] = video["image_hash"]
        elif video.get("image_url"):
            data["image_url"] = video["image_url"]
        else:
            raise ValueError("vignette absente : ni image_hash ni image_url dans video_data")
        data["call_to_action"] = {"type": cta_type, "value": {"lead_gen_form_id": str(form_id), "link": FORM_LINK}}
        new_story["video_data"] = data
    elif feed.get("videos"):
        # Video par emplacement : les libelles se citent par nom, le formulaire va dans call_to_actions
        for item in feed["videos"]:
            if item.get("adlabels"):
                item["adlabels"] = [{"name": label["name"]} for label in item["adlabels"]]
        for rule in feed.get("asset_customization_rules", []):
            if rule.get("video_label"):
                rule["video_label"] = {"name": rule["video_label"]["name"]}
        types = feed.pop("call_to_action_types", None) or [c.get("type") for c in feed.get("call_to_actions", [])] or [DEFAULT_CTA]
        feed["call_to_actions"] = [{"type": t, "value": {"lead_gen_form_id": str(form_id)}} for t in types]
        feed["link_urls"] = [{"website_url": FORM_LINK}]
        for key in READ_ONLY_FEED_KEYS:
            feed.pop(key, None)
    else:
        raise ValueError("ni video_data ni videos dans asset_feed_spec : seules les pubs video sont couvertes")
    params["object_story_spec"] = new_story
    if feed:
        params["asset_feed_spec"] = feed
    return params


# Controle champ par champ apres copie

def form_ids(creative):
    story = creative.get("object_story_spec") or {}
    found = [(((story.get("video_data") or {}).get("call_to_action") or {}).get("value") or {}).get("lead_gen_form_id")]
    found += [(c.get("value") or {}).get("lead_gen_form_id") for c in (creative.get("asset_feed_spec") or {}).get("call_to_actions", [])]
    return sorted({str(f) for f in found if f})


def signature(creative):
    """Ce qui doit rester identique entre l'ancienne et la nouvelle creative."""
    story = creative.get("object_story_spec") or {}
    video = story.get("video_data") or {}
    feed = creative.get("asset_feed_spec") or {}

    def texts(key):
        return sorted(item.get("text", "") for item in feed.get(key, []))

    if video:
        videos = [video.get("video_id")]
        thumbnails = [video.get("image_hash")]
        buttons = [(video.get("call_to_action") or {}).get("type")]
    else:
        videos = sorted(str(item["video_id"]) for item in feed.get("videos", []) if item.get("video_id"))
        thumbnails = []  # relues en URL temporaire : pas comparables
        buttons = sorted(feed.get("call_to_action_types") or [c.get("type") for c in feed.get("call_to_actions", [])])
    placements = sorted(json.dumps(rule.get("customization_spec", {}), sort_keys=True) for rule in feed.get("asset_customization_rules", []))
    return {
        "page": story.get("page_id"),
        "instagram": _instagram(story),
        "videos": [v for v in videos if v],
        "vignettes": [t for t in thumbnails if t],
        "textes": texts("bodies"),
        "titres": texts("titles"),
        "descriptions": texts("descriptions"),
        "bouton": [b for b in buttons if b],
        "emplacements": placements,
        "url_tags": creative.get("url_tags"),
    }


def _short(value):
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= 120 else text[:117] + "..."


def creative_diff(old, new, form_id=None):
    """Liste de (niveau, message). ECART bloque. A VERIFIER peut etre un faux positif."""
    before, after = signature(old), signature(new)
    found = []
    if not after["videos"] or not after["textes"]:
        found.append(("ECART", "creative vide : %d video(s), %d texte(s). Ne pas dupliquer dans le Gestionnaire, recreer par l'API" % (len(after["videos"]), len(after["textes"]))))
    forms = form_ids(new)
    if not forms and (new.get("object_story_spec") or {}).get("video_data"):
        found.append(("ECART", "la nouvelle creative ne pointe vers aucun formulaire"))
    elif not forms:
        found.append(("A VERIFIER", "formulaire absent de la relecture : verifie la destination dans le Gestionnaire"))
    elif form_id and forms != [str(form_id)]:
        found.append(("ECART", "formulaire %s, attendu %s" % (", ".join(forms), form_id)))
    for field in before:
        if before[field] == after[field]:
            continue
        if field == "videos":
            found.append(("A VERIFIER", "videos : %s -> %s. Une meme video reimportee change d'identifiant : compare les vignettes" % (_short(before[field]), _short(after[field]))))
        else:
            found.append(("ECART", "%s : %s -> %s" % (field, _short(before[field]), _short(after[field]))))
    return found


# Relecture du formulaire, avant d'y diriger les pubs

ENGLISH = re.compile(r"\b(what|your|how|which|please|company|annual|yearly|monthly|select|choose|size|full|name|number|phone|first|last|less|than|more|between|over|under|per|year|month)\b", re.I)
NUMBER = re.compile(r"(\d+(?:[ .]\d{3})*(?:,\d+)?)\s*([km])?(?![a-z])")  # apres _plain : espaces insecables deja normalises
BELOW = re.compile(r"moins de|inferieur|less than|under|<")
UP_TO = re.compile(r"jusqu|up to")
ABOVE = re.compile(r"plus de|superieur|au-dela|more than|over|>|\+")
FROM = re.compile(r"a partir de|from")


def _plain(text):
    text = unicodedata.normalize("NFKD", text.replace("\u2019", "'")).encode("ascii", "ignore").decode()
    return text.lower()


def parse_range(text):
    """(bas, haut, bas inclus, haut inclus) d'une tranche en clair, ou None."""
    plain = _plain(text)
    numbers = []
    for match in NUMBER.finditer(plain):
        value = float(re.sub(r"[ .]", "", match.group(1)).replace(",", "."))
        numbers.append(value * {"k": 1e3, "m": 1e6}.get((match.group(2) or "").lower(), 1))
    if not numbers:
        return None
    if len(numbers) >= 2:
        return (numbers[0], numbers[1], True, not BELOW.search(plain))
    if BELOW.search(plain):
        return (0.0, numbers[0], True, False)
    if UP_TO.search(plain):
        return (0.0, numbers[0], True, True)
    if ABOVE.search(plain):
        return (numbers[0], float("inf"), False, True)
    if FROM.search(plain):
        return (numbers[0], float("inf"), True, True)
    return (numbers[0], numbers[0], True, True)


def overlapping(values):
    """Paires de tranches ou une meme valeur tombe dans les deux."""
    ranges = [(parse_range(v), v) for v in values]
    ranges = sorted(((r, v) for r, v in ranges if r), key=lambda item: (item[0][0], item[0][1]))
    if len(ranges) < 2 or all(r[0] == r[1] for r, _ in ranges):
        return []
    found = []
    for i, (a, label_a) in enumerate(ranges):
        for b, label_b in ranges[i + 1:]:
            if b[0] < a[1] or (b[0] == a[1] and a[3] and b[2]):
                found.append("%r et %r se chevauchent" % (label_a, label_b))
    return found


def form_problems(form, locale=None):
    problems = []
    if locale and form.get("locale") and form["locale"] != locale:
        problems.append("langue du formulaire %s, attendue %s : les champs preremplis s'afficheront dans cette langue" % (form["locale"], locale))
    for question in form.get("questions", []):
        label = question.get("label") or ""
        options = [option.get("value", "") for option in question.get("options", [])]
        for text in [label] + options:
            if ENGLISH.search(_plain(text)):
                problems.append("libelle en anglais ? %r" % text)
        for message in overlapping(options):
            problems.append("%s : %s" % (label or question.get("key"), message))
    return problems


# Comparaison des adsets : l'heritage d'un adset cree a la main

def _interests(targeting):
    names = []
    specs = list(targeting.get("flexible_spec") or []) + [{k: v for k, v in targeting.items() if k in ("interests", "behaviors")}]
    for spec in specs:
        for values in spec.values():
            names += [str(item.get("name") or item.get("id")) for item in values if isinstance(item, dict)]
    return sorted(names)


def targeting_view(adset):
    targeting = adset.get("targeting") or {}
    geo = targeting.get("geo_locations") or {}
    return {
        "pays": sorted(geo.get("countries", [])),
        "regions et villes": sorted(json.dumps(item, sort_keys=True) for key in ("regions", "cities", "zips") for item in geo.get(key, [])),
        "age_min": targeting.get("age_min"),
        "age_max": targeting.get("age_max"),
        "langues": sorted(targeting.get("locales", [])),
        "genres": sorted(targeting.get("genders", [])),
        "plateformes": sorted(targeting.get("publisher_platforms", [])) or "automatiques",
        "interets": _interests(targeting),
        "advantage_audience": (targeting.get("targeting_automation") or {}).get("advantage_audience"),
    }


def adset_diff(old, new, allowed_platforms=ALLOWED_PLATFORMS):
    """Liste de (niveau, message). A SIGNALER : a faire valider par un humain avant le lancement."""
    before, after = targeting_view(old), targeting_view(new)
    found = []
    platforms = after["plateformes"]
    if platforms == "automatiques" or any(p not in allowed_platforms for p in platforms):
        found.append(("ECART", "plateformes %s : seules %s sont voulues, sans Audience Network" % (_short(platforms), ", ".join(allowed_platforms))))
    if after["interets"]:
        found.append(("ECART", "interets presents, le ciblage n'est pas large : %s" % _short(after["interets"])))
    for field in before:
        if before[field] != after[field]:
            found.append(("A SIGNALER", "%s : ancien %s, nouveau %s" % (field, _short(before[field]), _short(after[field]))))
    for field in ("optimization_goal", "destination_type"):
        if old.get(field) != new.get(field):
            found.append(("INFO", "%s : %s -> %s (attendu en passant au formulaire)" % (field, old.get(field), new.get(field))))
    return found


# Ligne de commande

def need(result, what):
    if "error" in result:
        e = result["error"]
        sys.exit("ECHEC %s: %s | %s | code %s/%s" % (what, e.get("message"), e.get("error_user_msg"), e.get("code"), e.get("error_subcode")))
    return result


def load(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def make_client():
    if not os.environ.get("META_ACCESS_TOKEN"):
        sys.exit("Variable d'environnement absente : META_ACCESS_TOKEN (ou travaille sur des fichiers avec --dry-run)")
    return GraphClient(os.environ["META_ACCESS_TOKEN"], os.environ.get("META_GRAPH_VERSION") or DEFAULT_VERSION)


def account_id(dry_run):
    account = os.environ.get("META_AD_ACCOUNT")
    if not account:
        if dry_run:
            return "act_COMPTE"
        sys.exit("Variable d'environnement absente : META_AD_ACCOUNT")
    return account if account.startswith("act_") else "act_" + account


def report(found, stop_on=("ECART",)):
    for level, message in found:
        print("  %s %s" % (level, message))
    return sum(1 for level, _ in found if level in stop_on)


def cmd_check_form(args, client):
    form = load(args.file) if args.file else need(client.get(args.form_id, fields=FORM_FIELDS), "formulaire")
    problems = form_problems(form, args.locale)
    print("formulaire %r : %d question(s), langue %s" % (form.get("name"), len(form.get("questions", [])), form.get("locale")))
    for problem in problems:
        print("PROBLEME", problem)
    if problems:
        sys.exit("ARRET : %d probleme(s). Un formulaire publie ne se modifie plus : duplique-le dans le Gestionnaire, corrige la copie, relis-la, et dirige les pubs vers la copie." % len(problems))
    print("formulaire relu : rien a corriger")


def cmd_copy_adset(args, client):
    params = {"deep_copy": False, "status_option": "PAUSED"}
    if args.campaign:
        params["campaign_id"] = args.campaign
    if args.dry_run:
        print("[a blanc] POST %s/copies %s" % (args.adset, json.dumps(params)))
        print("[a blanc] POST <copie> name=%r" % args.name)
        return
    source = need(client.get(args.adset, fields="id,name,campaign_id"), "adset source")
    campaign = args.campaign or source["campaign_id"]
    existing = need(client.get("%s/adsets" % campaign, fields="id,name", limit=200), "adsets de la campagne")
    for item in existing.get("data", []):
        if item.get("name") == args.name:
            print("existe deja :", args.name, item["id"])
            return
    result = need(client.post("%s/copies" % args.adset, params, retry_network=False), "copie de l'adset")
    copied = result.get("copied_adset_id") or result.get("id")
    need(client.post(copied, {"name": args.name}), "renommage")
    print("adset copie, sans les pubs, en pause :", args.name, copied)


def cmd_diff_adsets(args, client):
    if args.files:
        old, new = load(args.files[0]), load(args.files[1])
    else:
        old, new = [need(client.get(i, fields=ADSET_FIELDS), "adset %s" % i) for i in args.adsets]
    print("ancien %r / nouveau %r" % (old.get("name"), new.get("name")))
    found = adset_diff(old, new, tuple(args.platforms.split(",")))
    report(found)
    blocking = sum(1 for level, _ in found if level in ("ECART", "A SIGNALER"))
    if blocking:
        sys.exit("ARRET : %d point(s) a faire valider par un humain avant le lancement" % blocking)
    print("adsets alignes")


def _sources(args, client):
    if args.file:
        data = load(args.file)
        return data if isinstance(data, list) else data.get("data", [data])
    if args.ad:
        return [need(client.get(ad_id, fields=AD_FIELDS), "pub %s" % ad_id) for ad_id in args.ad]
    listed = need(client.get("%s/ads" % args.from_adset, fields=AD_FIELDS, limit=200), "pubs de l'adset")
    if (listed.get("paging") or {}).get("next"):
        print("avertissement : plus de 200 pubs, seules les 200 premieres sont traitees")
    return listed.get("data", [])


def _describe(payload):
    story, feed = payload["object_story_spec"], payload.get("asset_feed_spec", {})
    kind = "video simple" if "video_data" in story else "video par emplacement (%d videos)" % len(feed.get("videos", []))
    return "%s, %d textes, %d titres" % (kind, len(feed.get("bodies", [])), len(feed.get("titles", [])))


def cmd_copy_ad(args, client):
    sources = _sources(args, client)
    existing = {}
    if client is not None:
        listed = need(client.get("%s/ads" % args.adset, fields="id,name", limit=200), "pubs de l'adset cible")
        existing = {item["name"]: item["id"] for item in listed.get("data", [])}
    account = account_id(args.dry_run)
    copied = skipped = already = problems = 0
    for source in sources:
        name = source["name"]
        if source.get("effective_status") in SKIPPED_STATES:
            print("ignoree, refusee par Meta dans l'ancienne campagne :", name)
            skipped += 1
            continue
        if name in existing:
            print("deja copiee :", name, existing[name])
            already += 1
            continue
        payload = form_creative(source["creative"], args.form_id)
        if args.dry_run:
            check = creative_diff(source["creative"], payload, args.form_id)
            gaps = sum(1 for level, _ in check if level == "ECART")
            print("[a blanc] %s : %s, statut source %s, controle %d ecart(s)" % (name, _describe(payload), source.get("status"), gaps))
            report(check)
            if len(sources) == 1:
                print("POST %s/adcreatives" % account)
                print(json.dumps(dict(payload, name="%s | formulaire" % name), ensure_ascii=False, indent=1))
                print("POST %s/ads name=%r adset_id=%s status=PAUSED" % (account, name, args.adset))
            copied += 1
            continue
        creative = need(client.post("%s/adcreatives" % account, dict(payload, name="%s | formulaire" % name), retry_network=False), "creative %s" % name)
        ad = need(client.post("%s/ads" % account, {"name": name, "adset_id": args.adset, "creative": {"creative_id": creative["id"]}, "status": "PAUSED"}, retry_network=False), "pub %s" % name)
        reread = need(client.get(ad["id"], fields=AD_FIELDS), "relecture %s" % name)
        print("copiee en pause : %s %s (statut source %s)" % (name, ad["id"], source.get("status")))
        problems += report(creative_diff(source["creative"], reread.get("creative", {}), args.form_id))
        copied += 1
    verb = "a copier" if args.dry_run else "copiees"
    print("%d %s, %d deja la, %d refusee(s) non recopiee(s)" % (copied, verb, already, skipped))
    if problems:
        sys.exit("ARRET : %d ecart(s) entre l'ancienne et la nouvelle creative" % problems)


def cmd_diff(args, client):
    if args.files:
        old, new = load(args.files[0]), load(args.files[1])
    else:
        old, new = [need(client.get(i, fields=AD_FIELDS), "pub %s" % i) for i in args.ads]
    old, new = old.get("creative", old), new.get("creative", new)
    found = creative_diff(old, new, args.form_id)
    blocking = report(found)
    if blocking:
        sys.exit("ARRET : %d ecart(s)" % blocking)
    print("creatives identiques, hors destination" + (" (videos a verifier)" if found else ""))


def parser():
    p = argparse.ArgumentParser(description="Passe une campagne video vers un formulaire instantane, pubs a l'identique.")
    p.add_argument("--dry-run", action="store_true", help="n'ecrit rien chez Meta ; avec --file ou --files, ni reseau ni token")
    sub = p.add_subparsers(dest="command", required=True)

    form = sub.add_parser("check-form", help="relit le formulaire avant d'y diriger les pubs")
    group = form.add_mutually_exclusive_group(required=True)
    group.add_argument("--file")
    group.add_argument("--form-id")
    form.add_argument("--locale", default="fr_FR", help="langue attendue, par defaut fr_FR")

    adset = sub.add_parser("copy-adset", help="copie un adset sans ses pubs, en pause, puis le renomme")
    adset.add_argument("--adset", required=True)
    adset.add_argument("--name", required=True)
    adset.add_argument("--campaign", help="campagne cible, par defaut celle de l'adset copie")

    adsets = sub.add_parser("diff-adsets", help="compare le ciblage de l'ancien et du nouvel adset")
    group = adsets.add_mutually_exclusive_group(required=True)
    group.add_argument("--files", nargs=2, metavar=("ANCIEN", "NOUVEAU"))
    group.add_argument("--adsets", nargs=2, metavar=("ANCIEN", "NOUVEAU"))
    adsets.add_argument("--platforms", default=",".join(ALLOWED_PLATFORMS))

    ad = sub.add_parser("copy-ad", help="recree des pubs vers le formulaire, en pause")
    group = ad.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="pub ou liste de pubs, telles que Meta les renvoie")
    group.add_argument("--ad", nargs="+")
    group.add_argument("--from-adset")
    ad.add_argument("--form-id", required=True)
    ad.add_argument("--adset", required=True, help="adset cible, dans la nouvelle campagne")

    diff = sub.add_parser("diff", help="compare champ par champ l'ancienne et la nouvelle creative")
    group = diff.add_mutually_exclusive_group(required=True)
    group.add_argument("--files", nargs=2, metavar=("ANCIENNE", "NOUVELLE"))
    group.add_argument("--ads", nargs=2, metavar=("ANCIENNE", "NOUVELLE"))
    diff.add_argument("--form-id")
    return p


COMMANDS = {"check-form": cmd_check_form, "copy-adset": cmd_copy_adset, "diff-adsets": cmd_diff_adsets, "copy-ad": cmd_copy_ad, "diff": cmd_diff}


def offline(args):
    """Vrai si la commande peut tourner sans reseau ni token."""
    if args.command == "copy-adset":
        return args.dry_run
    from_files = getattr(args, "file", None) or getattr(args, "files", None)
    return bool(from_files) and (args.command != "copy-ad" or args.dry_run)


def main(argv=None):
    args = parser().parse_args(argv)
    if args.dry_run:
        print("A BLANC : rien n'est ecrit chez Meta.")
    client = None if offline(args) else make_client()
    try:
        COMMANDS[args.command](args, client)
    except ValueError as exc:
        sys.exit("ARRET : %s" % exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
