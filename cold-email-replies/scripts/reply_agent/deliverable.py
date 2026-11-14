"""Le livrable offert : un audit fabriqué pour chaque prospect (webhook vers votre générateur) ou un même lien pour tous (static)."""
from __future__ import annotations

import re
from typing import Any, Dict, NamedTuple, Optional

from .net import Http, NetworkError, parse_json, send_json, urllib_http


class DeliverableState(NamedTuple):
    status: str  # queued | ready | failed
    external_id: Optional[str] = None
    url: Optional[str] = None
    company_name: Optional[str] = None


class DeliverableError(RuntimeError):
    pass


def is_public_link(url: Optional[str]) -> bool:
    return isinstance(url, str) and re.match(r"^https?://[^\s/]+\.[^\s]+$", url) is not None


def _state(data: Any) -> DeliverableState:
    if not isinstance(data, dict) or data.get("status") not in ("queued", "ready", "failed"):
        raise DeliverableError("réponse du générateur illisible")
    return DeliverableState(
        status=data["status"],
        external_id=str(data["id"]) if data.get("id") is not None else None,
        url=data.get("url") if isinstance(data.get("url"), str) else None,
        company_name=data.get("company_name") if isinstance(data.get("company_name"), str) else None,
    )


class StaticDeliverable:
    """Un guide, une vidéo, une page commune : prêt tout de suite, le même lien pour tout le monde."""

    def __init__(self, url: str):
        self.url = url

    def request(self, local_id: str, key: str, lead: Dict[str, Any]) -> DeliverableState:
        return DeliverableState("ready", external_id=local_id, url=self.url)

    def check(self, external_id: str) -> DeliverableState:
        return DeliverableState("ready", external_id=external_id, url=self.url)


class WebhookDeliverable:
    """Contrat attendu de votre générateur (voir references/05-integrations.md) :
    POST {url} -> {"id", "status": "queued|ready|failed", "url"?, "company_name"?} ; GET {url}/{id} -> même forme."""

    def __init__(self, api_url: str, api_key: Optional[str] = None, http: Http = urllib_http):
        self.api_url = api_url.rstrip("/")
        self.headers = {"x-api-key": api_key} if api_key else {}
        self.http = http

    def request(self, local_id: str, key: str, lead: Dict[str, Any]) -> DeliverableState:
        payload = {"key": key, "source": "cold_email_reply", **lead}
        try:
            status, body = send_json(self.http, "POST", self.api_url, payload, headers={**self.headers, "idempotency-key": local_id}, timeout=60)
        except NetworkError as exc:
            raise DeliverableError("générateur injoignable (%s)" % exc) from None
        if not 200 <= status < 300:
            raise DeliverableError("générateur : réponse %d" % status)
        return _state(parse_json(body))

    def check(self, external_id: str) -> DeliverableState:
        try:
            status, body = send_json(self.http, "GET", "%s/%s" % (self.api_url, external_id), headers=self.headers, timeout=30)
        except NetworkError as exc:
            raise DeliverableError("générateur injoignable (%s)" % exc) from None
        if status != 200:
            raise DeliverableError("générateur : réponse %d" % status)
        return _state(parse_json(body))


def build_deliverables(cfg: Dict[str, Any], env: Dict[str, Any]):
    d = cfg["deliverable"]
    if d["mode"] == "static":
        return StaticDeliverable(d["static_url"])
    if not env.get("deliverable_api_url"):
        raise DeliverableError("deliverable.mode=webhook demande DELIVERABLE_API_URL")
    return WebhookDeliverable(env["deliverable_api_url"], env.get("deliverable_api_key"))
