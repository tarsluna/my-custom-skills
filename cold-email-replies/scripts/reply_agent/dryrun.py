"""Simulation sans clé ni réseau : rejoue des réponses fictives d'un fichier JSON et montre ce que l'agent ferait."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .agent import ReplyAgent
from .classify import RuleClassifier, Verdict, read_verdict
from .config import INTENT_LABELS
from .deliverable import DeliverableState, StaticDeliverable
from .notify import Recorder
from .smartlead import Lead, Reply, SendOutcome, interpret_send_response
from .store import Store, iso
from .text import redact_contacts, reply_text

STATUS_LABELS = {
    "received": "à classer",
    "recorded": "enregistrée, rien à envoyer",
    "review": "à traiter à la main",
    "queued": "en file pour le livrable",
    "waiting": "livrable en préparation",
    "sending": "envoi en cours",
    "answered": "répondue avec le livrable",
    "send_failed": "envoi refusé, à répondre à la main",
    "send_uncertain": "envoi incertain, vérifier le fil",
    "deliverable_failed": "livrable en échec, aucune réponse",
    "cancelled": "annulée par un refus ultérieur",
    "unsubscribe_pending": "désinscription en cours",
    "unsubscribed": "désinscrite et bloquée",
}

ACTION_LABELS = {
    "unsubscribed": "Désinscription de toutes les campagnes",
    "blocklisted": "Adresse ajoutée à la liste de blocage",
    "deliverable_requested": "Livrable commandé pour %s",
    "deliverable_reused": "Livrable déjà commandé pour %s, réutilisé",
    "sent": "Réponse envoyée dans le fil (lien du livrable + lien de réservation)",
    "send_failed": "Envoi refusé par l'outil : %s",
    "send_uncertain": "Envoi incertain : %s",
    "rate_limited": "Limite de débit de l'outil : nouvel essai à la sonde suivante",
    "capped": "Plafond du jour atteint pour %s : en attente",
    "held": "Retenue : %s",
    "skipped": "Pas de deuxième réponse : %s",
    "duplicate": "Pas de deuxième alerte : %s",
    "crm": "CRM : étape « %s »",
    "alert": "Slack : %s",
}

TOOL_NAMES = {"interested": 1, "meeting request": 2}


def _parse_time(value: Optional[str], fallback: datetime) -> datetime:
    if not value:
        return fallback
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class FakeSmartlead:
    """Rejoue le fichier : un contact par adresse, ses réponses dans son fil. Les envois sont gardés en mémoire."""

    def __init__(self, fixture: Dict[str, Any], positive_ids: Dict[int, str]):
        self.campaign_id = str(fixture.get("campaign_id", "101"))
        self.leads: Dict[str, Lead] = {}
        self.threads: Dict[str, List[Reply]] = {}
        self.behaviour: Dict[str, str] = {}
        self.verdicts: Dict[str, Verdict] = {}
        self.notes: Dict[str, str] = {}
        self.sent: List[Dict[str, str]] = []
        self.unsubscribed: List[str] = []
        self.blocked: List[str] = []
        self._rate_limited_once: set = set()
        names = {v.lower(): k for k, v in positive_ids.items()}
        names.update({k: v for k, v in TOOL_NAMES.items() if k not in names})
        clock = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
        for n, item in enumerate(fixture["replies"], start=1):
            email = item["email"].strip().lower()
            if email not in self.leads:
                lead_id = str(5000 + len(self.leads) + 1)
                category = item.get("tool_category")
                if isinstance(category, str):
                    category = names.get(category.lower())
                self.leads[email] = Lead(lead_id, email, item.get("first_name"), item.get("last_name"), item.get("company_name"),
                                         item.get("website"), bool(item.get("already_unsubscribed")), category)
                self.threads[lead_id] = []
            lead = self.leads[email]
            clock = _parse_time(item.get("received_at"), clock + timedelta(minutes=7))
            message_id = "<dry-run-%d@example.invalid>" % n
            body = item.get("html") or item.get("text") or ""
            stats_id = None if item.get("no_thread_id") else "stats-%s" % lead.id
            self.threads[lead.id].append(Reply(message_id, message_id, stats_id, clock, body))
            if item.get("simulate_send"):
                self.behaviour[lead.id] = item["simulate_send"]
            if item.get("simulate_verdict"):
                self.verdicts[redact_contacts(reply_text(body))] = read_verdict(item["simulate_verdict"])
            if item.get("note"):
                self.notes[message_id] = item["note"]
        self.last_received = clock

    def list_replied_leads(self, campaign_id: str, since: datetime) -> Tuple[List[Lead], int]:
        return list(self.leads.values()), 0

    def fetch_replies(self, campaign_id: str, lead_id: str) -> Tuple[List[Reply], int]:
        return list(self.threads[lead_id]), 0

    def reply_in_thread(self, campaign_id, email_stats_id, body, reply_message_id, reply_time) -> SendOutcome:
        lead_id = email_stats_id.split("-", 1)[1]
        mode = self.behaviour.get(lead_id, "sent")
        if mode == "rate_limited" and lead_id not in self._rate_limited_once:
            self._rate_limited_once.add(lead_id)
            return interpret_send_response(429, b"")
        responses = {
            "sent": (200, b'{"ok": true}'),
            "rate_limited": (200, b'{"ok": true}'),
            "false_success": (200, b'{"success": false, "message": "mailbox disconnected"}'),
            "rejected": (400, b'{"error": "bad request"}'),
            "uncertain": (502, b""),
        }
        outcome = interpret_send_response(*responses[mode])
        if outcome.outcome == "sent":
            email = next(e for e, lead in self.leads.items() if lead.id == lead_id)
            self.sent.append({"to": email, "body": body, "in_reply_to": reply_message_id or ""})
        return outcome

    def unsubscribe_lead(self, lead_id: str) -> None:
        self.unsubscribed.append(lead_id)

    def add_to_block_list(self, email: str) -> None:
        self.blocked.append(email)


class FakeDeliverables:
    """Un générateur qui met du temps, comme un vrai audit : prêt `minutes` après la commande, donc à une sonde suivante."""

    def __init__(self, now: Callable[[], datetime], minutes: int = 15, base_url: str = "https://audit.example.com/r/", failing_keys: Optional[set] = None):
        self.now = now
        self.delay = timedelta(minutes=minutes)
        self.base_url = base_url
        self.failing = failing_keys or set()
        self.requested: Dict[str, Tuple[str, datetime]] = {}

    def request(self, local_id: str, key: str, lead: Dict[str, Any]) -> DeliverableState:
        self.requested[local_id] = (key, self.now())
        return DeliverableState("queued", external_id=local_id)

    def check(self, external_id: str) -> DeliverableState:
        key, at = self.requested[external_id]
        if key in self.failing:
            return DeliverableState("failed", external_id=external_id)
        if self.now() - at < self.delay:
            return DeliverableState("queued", external_id=external_id)
        slug = key.split("@")[-1].split(".")[0]
        return DeliverableState("ready", external_id=external_id, url=self.base_url + slug)


class FixtureClassifier:
    """Classement par mots-clés, sauf quand le fichier impose un verdict (pour simuler la sortie d'un modèle)."""

    def __init__(self, rules: RuleClassifier, overrides: Dict[str, Verdict]):
        self.rules = rules
        self.overrides = overrides

    def classify(self, text: str) -> Verdict:
        return self.overrides.get(text) or self.rules.classify(text)


class DryRun:
    def __init__(self, cfg: Dict[str, Any], fixture: Dict[str, Any], polls: int = 3, step_minutes: int = 20):
        self.cfg = cfg
        self.store = Store(":memory:")
        positive = {int(k): v for k, v in cfg["tool_categories"]["positive"].items()}
        self.smartlead = FakeSmartlead(fixture, positive)
        self.clock = self.smartlead.last_received + timedelta(minutes=2)
        failing = {str(k).lower() for k in fixture.get("failing_deliverables", [])}
        if cfg["deliverable"]["mode"] == "static":
            self.deliverables: Any = StaticDeliverable(cfg["deliverable"]["static_url"])
        else:
            self.deliverables = FakeDeliverables(lambda: self.clock, minutes=max(1, step_minutes - 5), failing_keys=failing)
        self.slack = Recorder()
        self.crm = Recorder()
        self.step = timedelta(minutes=step_minutes)
        self.polls = polls
        # Le filigrane est posé avant les réponses du fichier : elles sont toutes traitées, comme si l'agent tournait déjà.
        self.store.set_setting("watermark", iso(datetime(2000, 1, 1, tzinfo=timezone.utc)), iso(self.clock))
        self.agent = ReplyAgent(
            cfg=cfg,
            store=self.store,
            smartlead=self.smartlead,
            classifier=FixtureClassifier(RuleClassifier(cfg["classifier"]["keywords"]), self.smartlead.verdicts),
            deliverables=self.deliverables,
            slack=self.slack,
            crm=self.crm,
            campaign_ids=[self.smartlead.campaign_id],
            now=lambda: self.clock,
            sleep=lambda _s: None,
            pace_seconds=0,
            quiet=True,
        )

    def run(self) -> "DryRun":
        for n in range(self.polls):
            if n:
                self.clock += self.step
            self.agent.poll_once()
        return self

    def summary(self) -> Dict[str, Any]:
        rows = []
        for row in self.store.all_replies():
            actions = [j for j in self.agent.journal if j["message_id"] == row["message_id"] and j["action"] not in ("recorded", "classified")]
            rows.append({
                "email": row["lead_email"],
                "text": row["reply_text"],
                "intent": row["intent"],
                "confidence": row["confidence"],
                "tool_category": row["tool_category"],
                "status": row["status"],
                "note": self.smartlead.notes.get(row["message_id"]),
                "actions": [{"action": a["action"], "detail": a["detail"]} for a in actions],
            })
        return {
            "replies": rows,
            "sent": self.smartlead.sent,
            "unsubscribed": self.smartlead.unsubscribed,
            "blocked": self.smartlead.blocked,
            "slack": self.slack.messages,
            "crm": self.crm.events,
            "status_counts": self.store.status_counts(),
        }


def _action_line(action: Dict[str, str]) -> Optional[str]:
    label = ACTION_LABELS.get(action["action"])
    if not label:
        return None
    if action["action"] == "sent":
        return label
    return label % action["detail"] if "%s" in label else label


def format_report(cfg: Dict[str, Any], summary: Dict[str, Any], source: str, polls: int, step_minutes: int) -> str:
    positive = {int(k): v for k, v in cfg["tool_categories"]["positive"].items()}
    out = [
        "Agent de réponses au cold email · simulation",
        "Aucun appel réseau, aucune clé. Source : %s · %d réponses · %d sondes, %d min entre deux sondes."
        % (source, len(summary["replies"]), polls, step_minutes),
        "",
    ]
    for n, r in enumerate(summary["replies"], start=1):
        excerpt = " ".join(r["text"].split())
        excerpt = excerpt if len(excerpt) <= 90 else excerpt[:87] + "..."
        out.append("%d. %s : « %s »" % (n, r["email"], excerpt))
        if r["note"]:
            out.append("   Cas : %s" % r["note"])
        tool = ""
        if r["tool_category"] is not None:
            tool = " · outil : %s" % positive.get(r["tool_category"], "catégorie %s" % r["tool_category"])
        intent = INTENT_LABELS.get(r["intent"] or "", "non classée")
        confidence = "" if r["confidence"] is None else " (%.2f)" % r["confidence"]
        out.append("   Classement : %s%s%s" % (intent, confidence, tool))
        for action in r["actions"]:
            line = _action_line(action)
            if line:
                out.append("   - " + line)
        out.append("   Résultat : %s" % STATUS_LABELS.get(r["status"], r["status"]))
        out.append("")
    if summary["sent"]:
        first = summary["sent"][0]
        out.append("Premier mail envoyé (à %s) :" % first["to"])
        out.extend("  | " + line for line in first["body"].split("\n"))
        out.append("")
    counts = summary["status_counts"]
    out.append("Bilan : %d réponse(s) envoyée(s), %d désinscription(s), %d alerte(s) Slack, %d événement(s) CRM."
               % (len(summary["sent"]), len(summary["unsubscribed"]), len(summary["slack"]), len(summary["crm"])))
    out.append("Par statut : " + ", ".join("%s %d" % (STATUS_LABELS.get(k, k), v) for k, v in sorted(counts.items())))
    return "\n".join(out)


def run_dry_run(cfg: Dict[str, Any], fixture_path: str, polls: int = 3, step_minutes: int = 20) -> Dict[str, Any]:
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    return DryRun(cfg, fixture, polls=polls, step_minutes=step_minutes).run().summary()
