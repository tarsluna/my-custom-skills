#!/usr/bin/env python3
"""Lance une campagne Meta depuis des videos deja montees jusqu'aux pubs actives.

Tout est cree en pause. Seule la commande go active, apres controle, et elle
exige le budget ecrit par un humain. --dry-run simule tout sans reseau.

    meta_launch.py --config campagne.json [--dry-run] COMMANDE
    COMMANDE : copy | check | structure | ads | rendezvous | relink | go | status | cleanup | run
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import copy_rules  # noqa: E402
from launch_state import State, StateError  # noqa: E402
from meta_api import DEFAULT_VERSION, DryRunClient, GraphClient, SimulatedCrash  # noqa: E402

FORMATS = (("V", "Vertical"), ("H", "Horizontal"))
NEEDED_PERMISSIONS = ("ads_management", "ads_read", "business_management", "pages_read_engagement", "pages_show_list")
LIVE_STATES = {"ACTIVE", "PENDING_REVIEW", "IN_PROCESS", "PREAPPROVED"}
BROKEN_STATES = {"DISAPPROVED", "WITH_ISSUES"}
SIM_IDS = {"account": "act_000000000000", "page": "000000000001", "pixel": "000000000002"}


def fingerprint(path):
    stat = path.stat()
    return "%d-%d" % (stat.st_size, int(stat.st_mtime))


def page_status(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except OSError:
        return 0


class Launch:
    def __init__(self, cfg, client, state, ids, base_dir):
        self.cfg = cfg
        self.client = client
        self.state = state
        self.account, self.page, self.pixel = ids["account"], ids["page"], ids["pixel"]
        self.base_dir = pathlib.Path(base_dir)

    # Outils communs

    @staticmethod
    def need(result, what):
        if "error" in result:
            e = result["error"]
            sys.exit("ECHEC %s: %s | %s | %s | code %s/%s" % (what, e.get("message"), e.get("error_user_title"), e.get("error_user_msg"), e.get("code"), e.get("error_subcode")))
        return result

    def edge(self, name):
        return "%s/%s" % (self.account, name)

    def keys(self):
        return ["%s-%s" % (ad["id"], code) for ad in self.cfg["ads"] for code, _ in FORMATS]

    def selected(self, only=None, adset=None):
        ads = self.cfg["ads"]
        known = {ad["id"] for ad in ads}
        unknown = set(only or []) - known
        if unknown:
            sys.exit("ARRET : pubs inconnues %s" % sorted(unknown))
        if only:
            ads = [ad for ad in ads if ad["id"] in only]
        if adset:
            ads = [ad for ad in ads if ad["adset"] == adset]
        return ads

    def video_path(self, ad, label):
        pattern = self.cfg.get("video_pattern", "{id}-{slug}-{format}.mp4")
        folder = self.base_dir / self.cfg.get("video_dir", ".")
        return folder / pattern.format(id=ad["id"], slug=ad["slug"], format=label)

    def _find(self, edge, name):
        if edge.endswith("customconversions"):
            found = self.client.get(edge, fields="id,name", limit=200)
        else:
            found = self.client.get(edge, fields="id,name", limit=50, filtering=[{"field": "name", "operator": "CONTAIN", "value": name}])
        self.need(found, "recherche %s" % name)
        for item in found.get("data", []):
            if item.get("name") == name:
                return item["id"]
        return None

    def ensure(self, bucket, key, edge, name, params):
        """Cree un objet une seule fois, meme si le script a ete coupe juste apres l'ecriture."""
        known = self.state.get(bucket) if key is None else self.state[bucket].get(key)
        if known:
            return known
        for _ in range(4):
            found = self._find(edge, name)
            if found:
                self.state.set(bucket, key, found)
                print("repris", name, flush=True)
                return found
            result = self.client.post(edge, dict(params, name=name), retry_network=False)
            if result.get("error", {}).get("network"):
                self.client.sleep(10)
                continue
            self.need(result, "%s %s" % (bucket, name))
            self.state.set(bucket, key, result["id"])
            print(bucket, name, result["id"], flush=True)
            return result["id"]
        sys.exit("ECHEC %s: reseau coupe a repetition, relance la meme commande" % name)

    # copy et check

    def copy(self):
        problems = copy_rules.check(self.cfg)
        out = self.base_dir / "textes-a-relire.txt"
        copy_rules.write_review(self.cfg, out)
        for problem in problems:
            print("PROBLEME", problem)
        print("textes : %d problemes, fichier %s" % (len(problems), out.name))
        if problems:
            sys.exit("ARRET : textes a corriger avant tout envoi")

    def _links(self):
        urls = sorted({a["link"] for a in self.cfg["adsets"]} | {self.cfg["conversion"].get("thank_you_url", "")} - {""})
        return [] if self.client.dry_run else [(u, page_status(u)) for u in urls]

    def check(self):
        problems = list(copy_rules.check(self.cfg))
        perms = self.client.get("me/permissions")
        if "error" in perms:
            print("avertissement : permissions illisibles :", perms["error"].get("message"))
        else:
            granted = {p.get("permission") for p in perms.get("data", []) if p.get("status") == "granted"}
            missing = [p for p in NEEDED_PERMISSIONS if p not in granted]
            if missing:
                problems.append("permissions manquantes sur le token : %s" % ", ".join(missing))
        account = self.client.get(self.account, fields="name,account_status,disable_reason,currency,funding_source")
        if "error" in account:
            problems.append("compte publicitaire illisible : %s" % account["error"].get("message"))
        else:
            if account.get("account_status") != 1:
                problems.append("compte publicitaire inactif (account_status=%s)" % account.get("account_status"))
            if not account.get("funding_source"):
                problems.append("aucun moyen de paiement sur le compte : les pubs seraient refusees")
            if account.get("currency") != self.cfg["campaign"]["currency"]:
                problems.append("devise du compte %s, la configuration annonce %s" % (account.get("currency"), self.cfg["campaign"]["currency"]))
        if "error" in self.client.get(self.page, fields="name"):
            problems.append("le token ne voit pas la Page : attribue-la a l'utilisateur systeme")
        if "error" in self.client.get(self.pixel, fields="name"):
            problems.append("le token ne voit pas le pixel : attribue-le a l'utilisateur systeme")
        for url, code in self._links():
            if code != 200:
                problems.append("page %s : reponse %s" % (url, code))
        if not self.client.dry_run:
            for tool in ("curl", "ffmpeg"):
                if not shutil.which(tool):
                    problems.append("outil absent : %s" % tool)
            absent = [str(self.video_path(ad, label).name) for ad in self.cfg["ads"] for _, label in FORMATS if not self.video_path(ad, label).exists()]
            if absent:
                print("videos pas encore la (le rendez-vous les attendra) :", ", ".join(absent))
        for problem in problems:
            print("PROBLEME", problem)
        if problems:
            sys.exit("ARRET : %d problemes avant lancement" % len(problems))
        print("controle initial : tout est bon")

    # Structure

    def structure(self, sync=False):
        campaign, conversion = self.cfg["campaign"], self.cfg["conversion"]
        campaign_id = self.ensure("campaign", None, self.edge("campaigns"), campaign["name"], {
            "objective": campaign.get("objective", "OUTCOME_LEADS"), "status": "PAUSED",
            "special_ad_categories": campaign.get("special_ad_categories", []),
            "daily_budget": campaign["daily_budget_minor"],
            "bid_strategy": campaign.get("bid_strategy", "LOWEST_COST_WITHOUT_CAP"),
        })
        rule = {"and": [{"event": {"eq": conversion.get("event", "PageView")}}, {"url": {"i_contains": conversion["url_contains"]}}]}
        conversion_id = self.ensure("conversion", None, self.edge("customconversions"), conversion["name"], {
            "event_source_id": self.pixel, "rule": rule, "custom_event_type": conversion.get("custom_event_type", "LEAD"),
        })
        base = self.cfg.get("targeting_base", {})
        dsa = self.cfg.get("dsa", {})
        for adset in self.cfg["adsets"]:
            params = {
                "campaign_id": campaign_id, "status": "PAUSED", "billing_event": "IMPRESSIONS",
                "optimization_goal": "OFFSITE_CONVERSIONS", "destination_type": "WEBSITE",
                "promoted_object": {"custom_conversion_id": conversion_id},
                "targeting": dict(base, **adset.get("targeting", {})),
            }
            if dsa:
                params["dsa_beneficiary"], params["dsa_payor"] = dsa["beneficiary"], dsa["payor"]
            adset_id = self.ensure("adsets", adset["name"], self.edge("adsets"), adset["name"], params)
            if sync:
                self.need(self.client.post(adset_id, {"targeting": params["targeting"]}), "ciblage %s" % adset["name"])
        if sync:
            self.need(self.client.post(campaign_id, {"daily_budget": campaign["daily_budget_minor"]}), "budget")
            print("budget et ciblage alignes sur la configuration", flush=True)

    # Videos, creatives, pubs

    def wait_ready(self, video_id):
        for _ in range(80):
            status = self.client.get(video_id, fields="status").get("status", {}).get("video_status")
            if status == "ready":
                return True
            if status == "error":
                return False
            self.client.sleep(self.client.poll_seconds)
        return False

    def thumbnail(self, path, key):
        known = self.state["images"].get(key)
        if known:
            return known
        with tempfile.TemporaryDirectory() as tmp:
            image = pathlib.Path(tmp) / ("%s.jpg" % key)
            if self.client.dry_run:
                image.write_bytes(b"")
            else:
                at = str(self.cfg.get("thumbnail_at_seconds", 1.2))
                subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", at, "-i", str(path), "-frames:v", "1", "-q:v", "2", str(image)], check=True)
            result = self.need(self.client.upload_image(self.account, image), "image %s" % key)
        digest = list(result["images"].values())[0]["hash"]
        self.state.set("images", key, digest)
        return digest

    def new_creative(self, ad, key, path, suffix=""):
        # 5 textes et 5 titres : le lien et le bouton vont dans video_data, les variantes dans asset_feed_spec
        copy = copy_rules.resolve_ad(self.cfg, ad)
        story = {"page_id": self.page, "video_data": {
            "video_id": self.state["videos"][key], "image_hash": self.thumbnail(path, key),
            "call_to_action": {"type": self.cfg["copy"].get("cta_type", "LEARN_MORE"), "value": {"link": copy["link"]}},
        }}
        feed = {
            "bodies": [{"text": t} for t in copy["bodies"]], "titles": [{"text": t} for t in copy["titles"]],
            "descriptions": [{"text": copy["description"]}], "optimization_type": "DEGREES_OF_FREEDOM",
        }
        tags = self.cfg.get("url_tags", "utm_source=meta&utm_medium=paid&utm_content={key}").format(key=key)
        name = "%s %s%s" % (self.cfg["campaign"]["name"], key, suffix)
        return self.need(self.client.post(self.edge("adcreatives"), {"name": name, "object_story_spec": story, "asset_feed_spec": feed, "url_tags": tags}), "creative %s" % key)["id"]

    def stale(self, key, path):
        known = self.state["video_files"].get(key)
        return bool(known) and not self.client.dry_run and path.exists() and fingerprint(path) != known

    def build(self, ad, code, label):
        key = "%s-%s" % (ad["id"], code)
        path = self.video_path(ad, label)
        if self.stale(key, path):
            sys.exit("ARRET : %s a change depuis son import. Lance cleanup --yes --only %s, puis ads." % (path.name, ad["id"]))
        if key in self.state["ads"]:
            return
        if not self.client.dry_run and not path.exists():
            print("en attente de la video", path.name, flush=True)
            return
        if key not in self.state["videos"]:
            result = self.need(self.client.upload_video(self.account, path), "video %s" % key)
            self.state.set("videos", key, result["id"])
            self.state.set("video_files", key, "simulation" if self.client.dry_run else fingerprint(path))
            print("video", key, result["id"], flush=True)
        if not self.wait_ready(self.state["videos"][key]):
            print("VIDEO PAS PRETE", key, flush=True)
            return
        if key not in self.state["creatives"]:
            self.state.set("creatives", key, self.new_creative(ad, key, path))
        self.ensure("ads", key, self.edge("ads"), "%s %s %s" % (ad["id"], ad["slug"], label), {
            "adset_id": self.state["adsets"][ad["adset"]],
            "creative": {"creative_id": self.state["creatives"][key]}, "status": "PAUSED",
        })

    def ads(self, only=None):
        if not self.state.get("campaign") or len(self.state["adsets"]) != len(self.cfg["adsets"]):
            sys.exit("ARRET : lance structure d'abord")
        for ad in self.selected(only):
            for code, label in FORMATS:
                self.build(ad, code, label)
        print("pubs en place : %d sur %d" % (len(self.state["ads"]), len(self.keys())), flush=True)

    def relink(self, only=None, adset=None):
        """Remplace la creative des pubs deja creees : nouveau texte ou nouvelle page d'arrivee."""
        for ad in self.selected(only, adset):
            for code, label in FORMATS:
                key = "%s-%s" % (ad["id"], code)
                if key not in self.state["ads"]:
                    print("absente", key, flush=True)
                    continue
                revision = self.state["revisions"].get(key, 1) + 1
                creative_id = self.new_creative(ad, key, self.video_path(ad, label), " v%d" % revision)
                self.need(self.client.post(self.state["ads"][key], {"creative": {"creative_id": creative_id}}), "maj pub %s" % key)
                self.state["retired_creatives"].append(self.state["creatives"][key])
                self.state["creatives"][key] = creative_id
                self.state["revisions"][key] = revision
                self.state.save()
                print("maj", key, flush=True)

    # Rendez-vous vertical / horizontal

    def _stage(self, key, ad, label):
        if key in self.state["ads"]:
            return "pret"
        if key in self.state["creatives"]:
            return "creative sans pub"
        if key in self.state["videos"]:
            return "video importee"
        return "fichier present" if not self.client.dry_run and self.video_path(ad, label).exists() else "ATTEND la video"

    def pairs_missing(self):
        return [key for key in self.keys() if key not in self.state["ads"]]

    def rendezvous(self):
        print("Rendez-vous vertical / horizontal")
        for ad in self.cfg["ads"]:
            cells = ["%s: %s" % (code, self._stage("%s-%s" % (ad["id"], code), ad, label)) for code, label in FORMATS]
            print("  %-6s %s" % (ad["id"], " | ".join(cells)))
        missing = self.pairs_missing()
        print("  %d pubs sur %d" % (len(self.keys()) - len(missing), len(self.keys())))
        return missing

    # Controle, activation, relecture

    def controls(self, confirmed_budget):
        """Rien n'est active si un seul controle echoue. Tout est relu chez Meta."""
        missing = self.pairs_missing()
        if missing:
            sys.exit("ARRET : %d pubs sur %d. Manquent : %s" % (len(self.keys()) - len(missing), len(self.keys()), ", ".join(missing)))
        expected = str(self.cfg["campaign"]["daily_budget_minor"])
        if str(confirmed_budget) != expected:
            sys.exit("ARRET : budget confirme %s, la configuration annonce %s" % (confirmed_budget, expected))
        campaign = self.need(self.client.get(self.state.get("campaign"), fields="daily_budget"), "campagne")
        if str(campaign.get("daily_budget")) != expected:
            sys.exit("ARRET : budget de la campagne chez Meta : %s" % campaign.get("daily_budget"))
        stale = [key for ad in self.cfg["ads"] for code, label in FORMATS for key in ["%s-%s" % (ad["id"], code)] if self.stale(key, self.video_path(ad, label))]
        if stale:
            sys.exit("ARRET : videos modifiees depuis leur import : %s" % ", ".join(stale))
        for url, code in self._links():
            if code != 200:
                sys.exit("ARRET : page %s : reponse %s" % (url, code))
        bad = []
        for key in self.keys():
            ad = self.need(self.client.get(self.state["ads"][key], fields="effective_status,issues_info,creative{asset_feed_spec{bodies,titles}}"), "pub %s" % key)
            feed = ad.get("creative", {}).get("asset_feed_spec", {})
            if ad.get("issues_info") or len(feed.get("bodies", [])) != copy_rules.COUNT or len(feed.get("titles", [])) != copy_rules.COUNT:
                bad.append((key, ad.get("effective_status"), ad.get("issues_info"), len(feed.get("bodies", []))))
        if bad:
            sys.exit("ARRET : pubs a probleme %s" % bad[:6])
        print("controle avant activation : %d pubs conformes" % len(self.keys()), flush=True)

    def _activate(self, object_id, what):
        result = self.client.post(object_id, {"status": "ACTIVE"})
        if "error" in result:
            e = result["error"]
            sys.exit("ARRET activation %s: %s" % (what, e.get("error_user_msg") or e.get("message")))

    def go(self, confirmed_budget):
        self.controls(confirmed_budget)
        for key in self.keys():
            self._activate(self.state["ads"][key], key)
        for name, adset_id in self.state["adsets"].items():
            self._activate(adset_id, name)
        self._activate(self.state.get("campaign"), "campagne")  # en dernier : une coupure avant ce point ne depense rien
        return self.readback(expect_live=True)

    def readback(self, expect_live=False):
        """Relit ce que Meta dit vraiment, pas ce qu'on a demande."""
        campaign = self.need(self.client.get(self.state.get("campaign"), fields="name,status,effective_status,daily_budget"), "campagne")
        print("campagne :", campaign.get("status"), campaign.get("effective_status"), "budget", campaign.get("daily_budget"))
        problems = []
        if expect_live and campaign.get("effective_status") not in LIVE_STATES:
            problems.append("campagne %s" % campaign.get("effective_status"))
        for name, adset_id in self.state["adsets"].items():
            adset = self.need(self.client.get(adset_id, fields="status,effective_status"), "adset")
            print("adset :", name, adset.get("effective_status"))
            if expect_live and adset.get("effective_status") not in LIVE_STATES:
                problems.append("adset %s %s" % (name, adset.get("effective_status")))
        counter = collections.Counter()
        for key, ad_id in self.state["ads"].items():
            ad = self.need(self.client.get(ad_id, fields="effective_status,issues_info"), "pub %s" % key)
            status = ad.get("effective_status")
            counter[status] += 1
            if status in BROKEN_STATES or ad.get("issues_info") or (expect_live and status not in LIVE_STATES):
                problems.append("pub %s %s %s" % (key, status, ad.get("issues_info") or ""))
        print("pubs :", dict(counter))
        for problem in problems:
            print("A REGARDER", problem)
        if problems:
            sys.exit("ARRET : %d objets ne sont pas dans l'etat attendu" % len(problems))
        print("etat relu chez Meta : conforme")
        return 0

    # Nettoyage

    def _purge(self, label, ids):
        done = 0
        for object_id in ids:
            result = self.client.delete(object_id)
            if "error" in result:
                print("  echec", label, object_id, result["error"].get("message"))
                self.state["cleanup_failed"].append(object_id)
            else:
                done += 1
        print("%s : %d/%d supprimes" % (label, done, len(ids)), flush=True)

    def cleanup(self, only=None, include_structure=False):
        """Ne supprime que les identifiants inscrits dans state.json."""
        campaign_id = self.state.get("campaign")
        if campaign_id:
            live = self.need(self.client.get(campaign_id, fields="effective_status"), "campagne").get("effective_status")
            if live in LIVE_STATES:
                sys.exit("ARRET : la campagne diffuse (%s). Mets-la en pause avant de nettoyer." % live)
        self.selected(only)

        def owned(key):
            return not only or key.rsplit("-", 1)[0] in only

        def take(bucket):
            return [self.state[bucket][k] for k in list(self.state[bucket]) if owned(k)]

        self._purge("pubs", take("ads"))
        retired = [] if only else list(self.state["retired_creatives"])
        self._purge("creatives", take("creatives") + retired)
        self._purge("videos", take("videos"))
        for bucket in ("ads", "creatives", "videos", "video_files", "images", "revisions"):
            self.state.data[bucket] = {k: v for k, v in self.state[bucket].items() if not owned(k)}
        if not only:
            self.state.data["retired_creatives"] = []
        if include_structure:
            self._purge("adsets", list(self.state["adsets"].values()))
            self._purge("campagne", [campaign_id] if campaign_id else [])
            self.state.data["adsets"] = {}
            self.state.data.pop("campaign", None)
        self.state.replace()


def parser():
    p = argparse.ArgumentParser(description="Lancement de campagne Meta, reprise et controle inclus.")
    p.add_argument("--config", required=True, help="fichier de campagne (JSON)")
    p.add_argument("--dry-run", action="store_true", help="simule tout, sans reseau ni token")
    p.add_argument("--state", help="chemin de state.json (defaut : a cote de la configuration)")
    p.add_argument("--fresh", action="store_true", help="simulation seulement : repart de zero")
    p.add_argument("--simulate-crash-after", type=int, help="simulation seulement : coupe apres N ecritures")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("copy", "check", "rendezvous", "status"):
        sub.add_parser(name)
    structure = sub.add_parser("structure")
    structure.add_argument("--sync", action="store_true", help="repousse le budget et le ciblage de la configuration")
    ads = sub.add_parser("ads")
    ads.add_argument("--only", nargs="+")
    relink = sub.add_parser("relink")
    relink.add_argument("--only", nargs="+")
    relink.add_argument("--adset")
    go = sub.add_parser("go")
    go.add_argument("--confirm-budget", required=True, help="budget journalier en centimes, tape par un humain")
    cleanup = sub.add_parser("cleanup")
    cleanup.add_argument("--yes", action="store_true")
    cleanup.add_argument("--only", nargs="+")
    cleanup.add_argument("--include-structure", action="store_true")
    run = sub.add_parser("run", help="enchaine tout jusqu'au rendez-vous ; en simulation, active si --confirm-budget est donne")
    run.add_argument("--confirm-budget")
    return p


def real_ids():
    names = {"account": "META_AD_ACCOUNT", "page": "META_PAGE_ID", "pixel": "META_PIXEL_ID"}
    absent = [v for v in list(names.values()) + ["META_ACCESS_TOKEN"] if not os.environ.get(v)]
    if absent:
        sys.exit("Variables d'environnement absentes : %s" % ", ".join(absent))
    ids = {k: os.environ[v] for k, v in names.items()}
    if not ids["account"].startswith("act_"):
        ids["account"] = "act_" + ids["account"]
    return ids


def execute(args, launch):
    command = args.command
    if command == "copy":
        launch.copy()
    elif command == "check":
        launch.check()
    elif command == "structure":
        launch.structure(args.sync)
    elif command == "ads":
        launch.ads(args.only)
    elif command == "rendezvous":
        launch.rendezvous()
    elif command == "relink":
        launch.relink(args.only, args.adset)
    elif command == "go":
        launch.go(args.confirm_budget)
    elif command == "status":
        launch.readback()
    elif command == "cleanup":
        if not args.yes:
            sys.exit("ARRET : cleanup supprime chez Meta, ajoute --yes apres accord humain")
        launch.cleanup(args.only, args.include_structure)
    elif command == "run":
        launch.copy()
        launch.check()
        launch.structure()
        launch.ads()
        launch.rendezvous()
        if not launch.client.dry_run:
            print("Arret volontaire avant l'activation : lance go --confirm-budget apres accord humain.")
        elif args.confirm_budget:
            launch.go(args.confirm_budget)


def main(argv=None):
    args = parser().parse_args(argv)
    if not args.dry_run and (args.fresh or args.simulate_crash_after is not None):
        sys.exit("--fresh et --simulate-crash-after n'existent qu'avec --dry-run")
    config_path = pathlib.Path(args.config).resolve()
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    default_name = "state.dry-run.json" if args.dry_run else "state.json"
    state_path = pathlib.Path(args.state).resolve() if args.state else config_path.parent / default_name
    if args.dry_run:
        ids = dict(SIM_IDS)
        world = pathlib.Path(str(state_path) + ".world.json")
        if args.fresh:
            for leftover in (state_path, world):
                if leftover.exists():
                    leftover.unlink()
        print("SIMULATION : aucun appel reseau, aucun token.")
        client = DryRunClient(world, ids["page"], ids["pixel"], cfg["campaign"]["currency"], args.simulate_crash_after)
    else:
        ids = real_ids()
        client = GraphClient(os.environ["META_ACCESS_TOKEN"], os.environ.get("META_GRAPH_VERSION") or DEFAULT_VERSION)
    try:
        state = State(state_path, "simulation" if args.dry_run else "reel")
    except StateError as exc:
        sys.exit("ARRET : %s" % exc)
    try:
        execute(args, Launch(cfg, client, state, ids, config_path.parent))
    except SimulatedCrash as exc:
        print("INTERRUPTION :", exc, "- relance la meme commande pour reprendre.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
