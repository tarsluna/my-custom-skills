"""Client de l'API Smartlead (https://server.smartlead.ai/api/v1). La clé part dans l'URL, comme l'exige l'API :
aucun message d'erreur ne contient donc l'URL.

La documentation se contredit sur la forme de certaines réponses. Les lecteurs ci-dessous n'acceptent que des noms de
champs qui y figurent ; un message qu'ils ne savent pas lire est compté, jamais deviné, et ne déclenche aucune réponse."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, NamedTuple, Optional, Tuple
from urllib.parse import urlencode

from .net import Http, NetworkError, parse_json, send_json, urllib_http

BASE = "https://server.smartlead.ai/api/v1"


class Lead(NamedTuple):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    company_name: Optional[str]
    website: Optional[str]
    is_unsubscribed: bool
    category: Optional[int]  # classification native de l'outil (Interested, Meeting Request…), absente tant qu'elle n'a pas tourné


class Reply(NamedTuple):
    message_id: str
    rfc_message_id: Optional[str]
    stats_id: Optional[str]
    received_at: datetime
    body: str


class SendOutcome(NamedTuple):
    outcome: str  # sent | rate_limited | rejected | uncertain
    detail: str = ""


class SmartleadError(RuntimeError):
    pass


def _text(value: Any) -> Optional[str]:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    s = str(value).strip()
    return s or None


def _date(value: Any) -> Optional[datetime]:
    s = _text(value)
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _category(value: Any) -> Optional[int]:
    s = _text(value)
    return int(s) if s and s.isdigit() else None


def parse_lead(row: Dict[str, Any]) -> Optional[Lead]:
    # GET /campaigns/{id}/leads : `data[].lead` sur une page de la doc, `leads[]` à plat sur une autre.
    lead = row.get("lead") if isinstance(row, dict) and isinstance(row.get("lead"), dict) else row
    if not isinstance(lead, dict):
        return None
    lead_id, email = _text(lead.get("id")), _text(lead.get("email"))
    if not lead_id or not lead_id.isdigit() or not email:
        return None
    return Lead(
        id=lead_id,
        email=email.lower(),
        first_name=_text(lead.get("first_name")),
        last_name=_text(lead.get("last_name")),
        company_name=_text(lead.get("company_name")),
        website=_text(lead.get("website")),
        is_unsubscribed=lead.get("is_unsubscribed") is True,
        category=_category(row.get("lead_category_id", lead.get("lead_category_id"))),
    )


def parse_thread(body: Any) -> Tuple[List[Reply], int]:
    """Réponses reçues dans le fil d'un contact. Formes acceptées, toutes tirées de la documentation :
    `messages[]` avec `direction`, `id`, `received_at`, `body` ; `history[]` avec `type`, `time`, `email_body` ;
    `message_id` et `stats_id`. Un message sortant n'est jamais retenu."""
    rows = None
    if isinstance(body, dict):
        rows = body.get("messages") if isinstance(body.get("messages"), list) else body.get("history")
    if not isinstance(rows, list):
        raise SmartleadError("historique illisible")
    replies: List[Reply] = []
    unreadable = 0
    for row in rows:
        if not isinstance(row, dict) or (row.get("direction") != "inbound" and row.get("type") != "REPLY"):
            continue
        rfc = _text(row.get("message_id"))
        message_id = rfc or _text(row.get("id"))
        received_at = _date(row.get("received_at")) or _date(row.get("time"))
        content = row.get("email_body") if isinstance(row.get("email_body"), str) else row.get("body")
        if not message_id or not received_at or not isinstance(content, str):
            unreadable += 1
            continue
        replies.append(Reply(message_id, rfc, _text(row.get("stats_id")), received_at, content))
    return replies, unreadable


def interpret_send_response(status: int, body: bytes) -> SendOutcome:
    """Seul un 2xx dont le corps ne dit pas « échec » compte comme envoyé. Un 200 avec `success: false` est un refus,
    pas un succès ; un 200 illisible reste incertain. Seul un 429 prouve que rien n'est parti."""
    if status == 429:
        return SendOutcome("rate_limited")
    if status >= 500:
        return SendOutcome("uncertain", "réponse %d" % status)
    if not 200 <= status < 300:
        return SendOutcome("rejected", "réponse %d" % status)
    data = parse_json(body)
    if not isinstance(data, dict):
        return SendOutcome("uncertain", "réponse %d sans corps JSON lisible" % status)
    if data.get("success") is False or data.get("ok") is False or data.get("error"):
        return SendOutcome("rejected", "refus dans le corps de la réponse")
    return SendOutcome("sent")


class SmartleadClient:
    def __init__(self, api_key: str, http: Http = urllib_http, base: str = BASE, page_size: int = 100, max_pages: int = 50):
        if not api_key:
            raise SmartleadError("clé absente")
        self._key = api_key
        self._http = http
        self._base = base
        self.page_size = page_size
        self.max_pages = max_pages

    def _call(self, method: str, path: str, query: Optional[Dict[str, str]] = None, payload: Any = None, timeout: float = 30) -> Tuple[int, bytes]:
        url = "%s%s?%s" % (self._base, path, urlencode({**(query or {}), "api_key": self._key}))
        return send_json(self._http, method, url, payload, timeout=timeout)

    def list_replied_leads(self, campaign_id: str, since: datetime) -> Tuple[List[Lead], int]:
        """Contacts d'une campagne qui ont répondu, avec une activité postérieure à `since`."""
        leads: List[Lead] = []
        unreadable = 0
        for page in range(self.max_pages):
            status, body = self._call("GET", "/campaigns/%s/leads" % campaign_id, {
                "emailStatus": "is_replied",
                "event_time_gt": since.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                "limit": str(self.page_size),
                "offset": str(page * self.page_size),
            })
            if status != 200:
                raise SmartleadError("liste des contacts, réponse %d" % status)
            data = parse_json(body)
            rows = None
            if isinstance(data, dict):
                rows = data.get("data") if isinstance(data.get("data"), list) else data.get("leads")
            if not isinstance(rows, list):
                raise SmartleadError("liste des contacts illisible")
            for row in rows:
                lead = parse_lead(row) if isinstance(row, dict) else None
                if lead:
                    leads.append(lead)
                else:
                    unreadable += 1
            if len(rows) < self.page_size:
                break
        return leads, unreadable

    def fetch_replies(self, campaign_id: str, lead_id: str) -> Tuple[List[Reply], int]:
        status, body = self._call("GET", "/campaigns/%s/leads/%s/message-history" % (campaign_id, lead_id))
        if status != 200:
            raise SmartleadError("historique, réponse %d" % status)
        return parse_thread(parse_json(body))

    def reply_in_thread(self, campaign_id: str, email_stats_id: str, body: str, reply_message_id: Optional[str], reply_time: datetime) -> SendOutcome:
        """Envoi unique, sans aucune reprise : un délai dépassé ou un 5xx peuvent cacher un mail parti."""
        payload: Dict[str, Any] = {
            "email_stats_id": email_stats_id,
            "email_body": body,
            "add_signature": False,
            "reply_email_time": reply_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        if reply_message_id:
            payload["reply_message_id"] = reply_message_id
        try:
            status, raw = self._call("POST", "/campaigns/%s/reply-email-thread" % campaign_id, payload=payload)
        except NetworkError as exc:
            return SendOutcome("uncertain", str(exc))
        return interpret_send_response(status, raw)

    def unsubscribe_lead(self, lead_id: str) -> None:
        """Désinscription de toutes les campagnes. `{ok: false}` signifie « déjà à jour » dans la documentation."""
        status, _ = self._call("POST", "/leads/%s/unsubscribe" % lead_id)
        if not 200 <= status < 300:
            raise SmartleadError("désinscription, réponse %d" % status)

    def add_to_block_list(self, email: str) -> None:
        status, raw = self._call("POST", "/leads/add-domain-block-list", payload={"domain_block_list": [email]})
        if not 200 <= status < 300:
            raise SmartleadError("liste de blocage, réponse %d" % status)
        data = parse_json(raw)
        if isinstance(data, dict) and data.get("success") is False:
            raise SmartleadError("liste de blocage refusée")
