"""Acces a la Graph API de Meta, reel ou simule.

Le token vient uniquement de la variable d'environnement META_ACCESS_TOKEN.
Il n'est jamais affiche, jamais ecrit sur le disque, et n'apparait pas dans la
ligne de commande de curl : il passe par l'entree standard.
"""
from __future__ import annotations

import http.client
import json
import pathlib
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_VERSION = "v23.0"
GRAPH = "https://graph.facebook.com"
GRAPH_VIDEO = "https://graph-video.facebook.com"
RATE_LIMIT_CODES = {4, 17, 32, 613, 80004}
RATE_LIMIT_SUBCODES = {4841018}
THROTTLE_SECONDS = 40  # delai qui a suffi apres une cinquantaine d'ecritures d'affilee
NETWORK_ERRORS = (OSError, http.client.HTTPException)


class SimulatedCrash(RuntimeError):
    """Coupure volontaire du mode --dry-run : l'ecriture est faite, la reponse est perdue."""


def encode(params):
    return {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in params.items()}


class GraphClient:
    dry_run = False
    poll_seconds = 15

    def __init__(self, token, version=None, base=GRAPH, video_base=GRAPH_VIDEO, sleep=time.sleep):
        self.token = token
        self.version = version or DEFAULT_VERSION
        self.base = base
        self.video_base = video_base
        self.sleep = sleep

    def _clean(self, text):
        return text.replace(self.token, "***")

    def _url(self, root, path):
        return "%s/%s/%s" % (root, self.version, path)

    def _http_error(self, exc):
        body = self._clean(exc.read().decode("utf-8", "replace"))
        try:
            return json.loads(body).get("error") or {"message": body[:300]}
        except ValueError:
            return {"message": body[:300], "code": exc.code}

    @staticmethod
    def _throttled(err):
        return err.get("code") in RATE_LIMIT_CODES or err.get("error_subcode") in RATE_LIMIT_SUBCODES

    def _call(self, make_request, attempts, retry_network):
        for _ in range(attempts):
            try:
                with urllib.request.urlopen(make_request(), timeout=120) as response:
                    return json.loads(self._clean(response.read().decode("utf-8", "replace")))
            except urllib.error.HTTPError as exc:
                err = self._http_error(exc)
                if self._throttled(err):
                    self.sleep(THROTTLE_SECONDS)
                    continue
                return {"error": err}
            except NETWORK_ERRORS:
                if not retry_network:
                    return {"error": {"message": "reponse perdue, l'ecriture a peut-etre ete appliquee", "network": True}}
                self.sleep(10)
        return {"error": {"message": "limite de debit Meta ou reseau indisponible"}}

    def get(self, path, **params):
        query = urllib.parse.urlencode(encode(dict(params, access_token=self.token)))
        url = self._url(self.base, path) + "?" + query
        return self._call(lambda: urllib.request.Request(url), 6, True)

    def post(self, path, params, retry_network=True):
        """retry_network=False pour une creation : voir Launch.ensure, qui verifie avant de recommencer."""
        data = urllib.parse.urlencode(encode(dict(params, access_token=self.token))).encode()
        url = self._url(self.base, path)
        return self._call(lambda: urllib.request.Request(url, data=data), 10, retry_network)

    def delete(self, path):
        query = urllib.parse.urlencode({"access_token": self.token})
        url = self._url(self.base, path) + "?" + query
        return self._call(lambda: urllib.request.Request(url, method="DELETE"), 8, True)

    def _form(self, url, fields, file_field, file_path, timeout):
        config = 'form-string = "access_token=%s"\n' % self.token
        quoted = str(file_path).replace("\\", "\\\\").replace('"', '\\"')
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "reponse.json"
            cmd = ["curl", "-sS", "-m", str(timeout), "-o", str(out), "--config", "-"]
            for key, value in fields.items():
                cmd += ["--form-string", "%s=%s" % (key, value)]
            cmd += ["-F", '%s=@"%s"' % (file_field, quoted), url]
            try:
                subprocess.run(cmd, input=config, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except subprocess.CalledProcessError as exc:
                return {"error": {"message": self._clean(exc.stderr or "envoi interrompu")[:300]}}
            try:
                return json.loads(self._clean(out.read_text(encoding="utf-8")))
            except ValueError:
                return {"error": {"message": "reponse illisible apres l'envoi"}}

    def upload_video(self, account, path):
        path = pathlib.Path(path)
        return self._form(self._url(self.video_base, "%s/advideos" % account), {"title": path.stem}, "source", path, 900)

    def upload_image(self, account, path):
        return self._form(self._url(self.base, "%s/adimages" % account), {}, "filename", path, 120)


REQUIRED = {
    "campaigns": ("name", "objective", "status", "special_ad_categories"),
    "customconversions": ("name", "event_source_id", "rule", "custom_event_type"),
    "adsets": ("name", "campaign_id", "status", "billing_event", "optimization_goal", "destination_type", "promoted_object", "targeting"),
    "adcreatives": ("name", "object_story_spec", "asset_feed_spec"),
    "ads": ("name", "adset_id", "creative", "status"),
}
KIND = {"campaigns": "campaign", "customconversions": "conversion", "adsets": "adset", "adcreatives": "creative", "ads": "ad"}
SIM_PERMISSIONS = ("ads_management", "ads_read", "business_management", "pages_read_engagement", "pages_show_list")


class DryRunClient:
    """Imite Meta dans un fichier local. Aucun appel reseau, aucun token, aucun fichier video requis."""

    dry_run = True
    poll_seconds = 0

    def __init__(self, world_path, page, pixel, currency="EUR", crash_after=None, log=print):
        self.path = pathlib.Path(world_path)
        self.world = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {"next": 1, "objects": {}}
        self.world["objects"].setdefault(page, {"kind": "page", "name": "Page simulee"})
        self.world["objects"].setdefault(pixel, {"kind": "pixel", "name": "Pixel simule"})
        self.currency = currency
        self.crash_after = crash_after
        self.writes = 0
        self.log = log

    @staticmethod
    def sleep(_seconds):
        return None

    @property
    def objects(self):
        return self.world["objects"]

    def _persist(self):
        self.path.write_text(json.dumps(self.world, ensure_ascii=False, indent=1), encoding="utf-8")

    def _new_id(self):
        number = self.world["next"]
        self.world["next"] = number + 1
        return "sim%06d" % number

    def _written(self):
        self._persist()
        self.writes += 1
        if self.crash_after is not None and self.writes >= self.crash_after:
            raise SimulatedCrash("coupure simulee apres l'ecriture %d" % self.writes)

    def _of_kind(self, kind):
        return {oid: obj for oid, obj in self.objects.items() if obj["kind"] == kind}

    def _effective(self, oid):
        obj = self.objects[oid]
        if obj["kind"] == "campaign":
            return obj["status"]
        if obj["kind"] == "adset":
            return "CAMPAIGN_PAUSED" if self.objects[obj["campaign_id"]]["status"] == "PAUSED" else obj["status"]
        adset = self.objects[obj["adset_id"]]
        if self.objects[adset["campaign_id"]]["status"] == "PAUSED":
            return "CAMPAIGN_PAUSED"
        if adset["status"] == "PAUSED":
            return "ADSET_PAUSED"
        return "PAUSED" if obj["status"] == "PAUSED" else "PENDING_REVIEW"

    def _view(self, oid):
        view = dict(self.objects[oid], id=oid)
        kind = view["kind"]
        if kind == "video":
            view["status"] = {"video_status": "ready"}
        if kind in ("campaign", "adset", "ad"):
            view["effective_status"] = self._effective(oid)
            view["issues_info"] = []
        if kind == "ad":
            view["creative"] = dict(self.objects[view["creative"]["creative_id"]], id=view["creative"]["creative_id"])
        return view

    def get(self, path, **params):
        if path == "me/permissions":
            return {"data": [{"permission": name, "status": "granted"} for name in SIM_PERMISSIONS]}
        if path.startswith("act_") and "/" not in path:
            return {"id": path, "name": "Compte simule", "account_status": 1, "currency": self.currency, "funding_source": "simule"}
        if "/" in path:
            kind = KIND.get(path.split("/", 1)[1])
            items = self._of_kind(kind)
            wanted = None
            for rule in params.get("filtering") or []:
                if rule.get("field") == "name":
                    wanted = rule.get("value")
            return {"data": [{"id": oid, "name": obj["name"]} for oid, obj in items.items() if wanted is None or wanted in obj["name"]]}
        if path not in self.objects:
            return {"error": {"message": "objet inconnu : %s" % path, "code": 100}}
        return self._view(path)

    def _invalid(self, edge, params):
        missing = [field for field in REQUIRED[edge] if field not in params]
        if missing:
            return "champs manquants : %s" % ", ".join(missing)
        refs = []
        if edge == "adsets":
            refs = [params["campaign_id"], params["promoted_object"].get("custom_conversion_id")]
        if edge == "adcreatives":
            data = params["object_story_spec"].get("video_data", {})
            refs = [params["object_story_spec"].get("page_id"), data.get("video_id")]
            if data.get("image_hash") not in {o.get("hash") for o in self.objects.values()}:
                return "image_hash inconnu"
        if edge == "ads":
            refs = [params["adset_id"], params["creative"].get("creative_id")]
        unknown = [ref for ref in refs if ref not in self.objects]
        return "identifiant inconnu : %s" % unknown if unknown else ""

    def post(self, path, params, retry_network=True):
        label = params.get("name") or params.get("status") or "maj"
        self.log("[simulation] POST %s  %s" % (path, label))
        if "/" in path:
            edge = path.split("/", 1)[1]
            problem = self._invalid(edge, params)
            if problem:
                return {"error": {"message": problem, "code": 100}}
            oid = self._new_id()
            obj = json.loads(json.dumps(params, ensure_ascii=False))
            obj["kind"] = KIND[edge]
            if "daily_budget" in obj:
                obj["daily_budget"] = str(obj["daily_budget"])
            self.objects[oid] = obj
            self._written()
            return {"id": oid}
        if path not in self.objects:
            return {"error": {"message": "objet inconnu : %s" % path, "code": 100}}
        self.objects[path].update(json.loads(json.dumps(params, ensure_ascii=False)))
        self._written()
        return {"success": True}

    def delete(self, path):
        self.log("[simulation] DELETE %s" % path)
        if path not in self.objects:
            return {"error": {"message": "objet inconnu : %s" % path, "code": 100}}
        del self.objects[path]
        self._written()
        return {"success": True}

    def upload_video(self, account, path):
        self.log("[simulation] envoi video %s" % pathlib.Path(path).name)
        oid = self._new_id()
        self.objects[oid] = {"kind": "video", "name": pathlib.Path(path).stem}
        self._written()
        return {"id": oid}

    def upload_image(self, account, path):
        name = pathlib.Path(path).name
        digest = "simhash%06d" % self.world["next"]
        self.objects[self._new_id()] = {"kind": "image", "name": name, "hash": digest}
        self._written()
        return {"images": {name: {"hash": digest}}}
