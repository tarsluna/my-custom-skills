"""Sorties vers l'équipe : Slack (webhook entrant) et CRM (webhook JSON). Un échec lève une erreur pour que l'appelant retente ;
une sortie non configurée renvoie « skipped » et l'agent continue."""
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

from .net import Http, NetworkError, send_json, urllib_http
from .text import escape_slack


class NotifyError(RuntimeError):
    pass


class SlackWebhook:
    def __init__(self, webhook_url: Optional[str], http: Http = urllib_http):
        self.url = webhook_url
        self.http = http
        self._warned = False

    def send(self, text: str) -> str:
        if not self.url:
            if not self._warned:
                print("avertissement : SLACK_WEBHOOK_URL absent, alertes affichées ici seulement", file=sys.stderr)
                self._warned = True
            print("[alerte] " + text.replace("\n", " | ")[:500], file=sys.stderr)
            return "skipped"
        try:
            status, _ = send_json(self.http, "POST", self.url, {"text": escape_slack(text), "unfurl_links": False, "unfurl_media": False}, timeout=15)
        except NetworkError as exc:
            raise NotifyError("Slack : %s" % exc) from None
        if status != 200:
            raise NotifyError("Slack : réponse %d" % status)
        return "sent"


class CrmWebhook:
    """POST du prospect vers votre CRM. L'en-tête Idempotency-Key permet au CRM d'ignorer un événement reçu deux fois."""

    def __init__(self, webhook_url: Optional[str], secret: Optional[str] = None, http: Http = urllib_http):
        self.url = webhook_url
        self.secret = secret
        self.http = http

    def push(self, idempotency_key: str, payload: Dict[str, Any]) -> str:
        if not self.url:
            return "skipped"
        headers = {"idempotency-key": idempotency_key}
        if self.secret:
            headers["x-webhook-secret"] = self.secret
        try:
            status, _ = send_json(self.http, "POST", self.url, payload, headers=headers, timeout=15)
        except NetworkError as exc:
            raise NotifyError("CRM : %s" % exc) from None
        if not 200 <= status < 300:
            raise NotifyError("CRM : réponse %d" % status)
        return "sent"


class Recorder:
    """Slack et CRM pour la simulation et les tests : garde tout en mémoire, n'envoie rien."""

    def __init__(self, fail_times: int = 0):
        self.messages: List[str] = []
        self.events: List[Dict[str, Any]] = []
        self.fail_times = fail_times

    def _maybe_fail(self) -> None:
        if self.fail_times > 0:
            self.fail_times -= 1
            raise NotifyError("panne simulée")

    def send(self, text: str) -> str:
        self._maybe_fail()
        self.messages.append(text)
        return "sent"

    def push(self, idempotency_key: str, payload: Dict[str, Any]) -> str:
        self._maybe_fail()
        self.events.append(json.loads(json.dumps({"key": idempotency_key, **payload})))
        return "sent"
