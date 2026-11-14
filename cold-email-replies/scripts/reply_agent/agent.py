"""La sonde : lire les réponses, les classer, désinscrire les « non », commander le livrable des « oui », répondre dans le fil,
prévenir l'équipe et nourrir le CRM. Chaque étape reprend là où la précédente s'est arrêtée, sans jamais répondre deux fois."""
from __future__ import annotations

import json
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, NamedTuple, Optional

from .config import INTENT_LABELS
from .deliverable import is_public_link
from .store import Store, iso, parse_iso
from .text import clean_first_name, company_domain, pick_company_name, redact_contacts, render_reply, reply_text

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore[assignment]

# La relecture chevauche la précédente : l'idempotence par message rend le recouvrement sans effet.
CURSOR_OVERLAP = timedelta(hours=1)
# Une ligne restée « sending » plus longtemps vient d'un arrêt en plein envoi : le mail est peut-être parti.
SEND_STALE = timedelta(minutes=10)
LOCK_TTL = timedelta(minutes=15)


class PollResult(NamedTuple):
    skipped: bool
    recorded: int = 0
    answered: int = 0


def short_error(exc: BaseException) -> str:
    return ("%s: %s" % (type(exc).__name__, exc))[:240]


class ReplyAgent:
    def __init__(
        self,
        *,
        cfg: Dict[str, Any],
        store: Store,
        smartlead: Any,
        classifier: Any,
        deliverables: Any,
        slack: Any,
        crm: Any,
        campaign_ids: List[str],
        booking_url: Optional[str] = None,
        now: Optional[Callable[[], datetime]] = None,
        sleep: Optional[Callable[[float], None]] = None,
        pace_seconds: Optional[float] = None,
        quiet: bool = False,
    ):
        self.cfg = cfg
        self.store = store
        self.smartlead = smartlead
        self.classifier = classifier
        self.deliverables = deliverables
        self.slack = slack
        self.crm = crm
        self.campaign_ids = list(campaign_ids)
        self.booking_url = booking_url or cfg["booking_url"]
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.sleep = sleep or time.sleep
        self.pace = cfg["smartlead"]["pace_seconds"] if pace_seconds is None else pace_seconds
        self.quiet = quiet
        self.positive_ids = {int(k): v for k, v in cfg["tool_categories"]["positive"].items()}
        try:
            self.tz = ZoneInfo(cfg["timezone"]) if ZoneInfo else timezone.utc
        except Exception:
            self.tz = timezone.utc
        self.journal: List[Dict[str, str]] = []

    # Outils ------------------------------------------------------------------------------------------------

    def _now(self) -> str:
        return iso(self.now())

    def _log(self, message_id: Optional[str], action: str, detail: str = "") -> None:
        self.journal.append({"message_id": message_id or "", "action": action, "detail": detail})

    def _warn(self, text: str) -> None:
        self._log(None, "warning", text)
        if not self.quiet:
            print("avertissement : " + text, file=sys.stderr)

    def _set(self, message_id: str, **fields: Any) -> None:
        self.store.update_reply(message_id, self._now(), **fields)

    def _today(self) -> str:
        return self.now().astimezone(self.tz).date().isoformat()

    def _today_start(self) -> str:
        local = self.now().astimezone(self.tz)
        return iso(local.replace(hour=0, minute=0, second=0, microsecond=0))

    def _describe(self, row: Any) -> str:
        who = " ".join(x for x in (row["first_name"], row["last_name"], row["company_name"]) if x)
        tool = ""
        if row["tool_category"] is not None:
            tool = ", outil : %s" % self.positive_ids.get(row["tool_category"], "catégorie %s" % row["tool_category"])
        intent = INTENT_LABELS.get(row["intent"], "pas encore classée") if row["intent"] else "pas encore classée"
        confidence = "" if row["confidence"] is None else " (confiance %.2f)" % row["confidence"]
        target = ", livrable pour %s" % row["deliverable_key"] if row["deliverable_key"] else ""
        return "\n".join([
            "De : %s%s" % (row["lead_email"], " (%s)" % who if who else ""),
            "Classement : %s%s%s" % (intent, confidence, tool),
            "Campagne %s, contact %s%s" % (row["campaign_id"], row["lead_id"], target),
            "Message :",
            row["reply_text"][:2000] or "(vide)",
        ])

    def _alert(self, message_id: str, kind: str, headline: str, detail: str) -> None:
        row = self.store.reply(message_id)
        self.store.add_alert(message_id, kind, "%s\n%s\n%s" % (headline, detail, self._describe(row)), self._now())
        self._log(message_id, "alert", headline)

    def _alert_daily(self, topic: str, text: str) -> None:
        """Une alerte par jour et par sujet pour les problèmes qui se répètent à chaque sonde."""
        key = "daily_alert_" + topic
        today = self._today()
        if self.store.get_setting(key) == today:
            return
        self.store.set_setting(key, today, self._now())
        self.store.add_alert(None, topic, text, self._now())
        self._log(None, "alert", text.split("\n")[0])

    def _crm(self, row: Any, event: str, stage: Optional[str], **extra: Any) -> None:
        if not stage:
            return
        key = row["deliverable_key"]
        payload = {
            "event": event,
            "stage": stage,
            "email": row["lead_email"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "company_name": row["company_name"],
            "website": row["website"],
            "domain": key if key and "@" not in key else None,
            "campaign_id": row["campaign_id"],
            "lead_id": row["lead_id"],
            "reply_excerpt": row["reply_text"][:500],
            "occurred_at": self._now(),
            **extra,
        }
        self.store.add_crm_event("%s:%s" % (row["message_id"], event), payload, self._now())
        self._log(row["message_id"], "crm", stage)

    # 1. Arrêts en plein envoi ---------------------------------------------------------------------------------

    def _sweep_interrupted(self) -> None:
        """Arrêt du service en plein envoi : on ne sait pas si le mail est parti, donc on ne le renvoie jamais."""
        for row in self.store.interrupted_sends(iso(self.now() - SEND_STALE)):
            self._set(row["message_id"], status="send_uncertain", last_error="envoi interrompu")
            self._alert(row["message_id"], "failure", "Envoi interrompu, résultat inconnu",
                        "Vérifier le fil dans l'outil d'envoi avant de répondre à la main. L'agent ne renverra rien à ce contact.")

    # 2. Lecture des réponses ------------------------------------------------------------------------------------

    def _ingest(self, campaign_id: str, watermark: datetime) -> List[int]:
        """Le curseur n'avance que si tout a été lu ; sinon la prochaine sonde relit la même fenêtre."""
        started = self.now()
        cursor = self.store.get_setting("cursor_" + campaign_id)
        since = parse_iso(cursor) if cursor else watermark
        leads, unreadable = self.smartlead.list_replied_leads(campaign_id, since)
        recorded, complete = 0, True
        for lead in leads:
            if self.pace:
                self.sleep(self.pace)
            try:
                replies, bad = self.smartlead.fetch_replies(campaign_id, lead.id)
            except Exception as exc:
                complete = False
                self._warn("historique du contact %s non lu (%s)" % (lead.id, short_error(exc)))
                continue
            unreadable += bad
            for reply in replies:
                if reply.received_at < watermark:
                    continue  # antérieure au premier démarrage : ni livrable ni mail
                inserted = self.store.insert_reply({
                    "message_id": reply.message_id,
                    "campaign_id": campaign_id,
                    "lead_id": lead.id,
                    "lead_email": lead.email,
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "company_name": lead.company_name,
                    "website": lead.website,
                    "lead_unsubscribed": 1 if lead.is_unsubscribed else 0,
                    "tool_category": lead.category,
                    "email_stats_id": reply.stats_id,
                    "rfc_message_id": reply.rfc_message_id,
                    "received_at": iso(reply.received_at),
                    "reply_text": reply_text(reply.body),
                }, self._now())
                if inserted:
                    recorded += 1
                    self._log(reply.message_id, "recorded", lead.email)
        if complete and not unreadable:
            self.store.set_setting("cursor_" + campaign_id, iso(max(watermark, started - CURSOR_OVERLAP)), self._now())
        return [recorded, unreadable]

    # 3. Classement --------------------------------------------------------------------------------------------

    def _classify_pending(self) -> None:
        max_attempts = int(self.cfg["classifier"]["max_attempts"])
        for row in self.store.replies_with_status("received", 200):
            try:
                verdict = self.classifier.classify(redact_contacts(row["reply_text"]))
            except Exception as exc:
                attempts = row["classify_attempts"] + 1
                give_up = attempts >= max_attempts
                self._set(row["message_id"], classify_attempts=attempts, last_error=short_error(exc), **({"status": "review"} if give_up else {}))
                self._warn("classement en échec (%d/%d) : %s" % (attempts, max_attempts, short_error(exc)))
                if give_up:
                    self._alert(row["message_id"], "failure", "Classement impossible",
                                "Après %d essais : aucune réponse automatique, à traiter à la main." % attempts)
                continue
            self._log(row["message_id"], "classified", "%s %.2f" % (verdict.intent, verdict.confidence))
            self._apply_verdict(row, verdict)

    def _apply_verdict(self, row: Any, verdict: Any) -> None:
        mid = row["message_id"]
        sure = verdict.confidence >= float(self.cfg["classifier"]["min_confidence"])
        base = {"intent": verdict.intent, "confidence": verdict.confidence}

        # Un « non » est honoré à toute confiance : jamais de réponse, désinscription et blocage sans attendre un humain.
        if verdict.intent == "no":
            self._set(mid, status="unsubscribe_pending", **base)
            if not sure:
                self._alert(mid, "check", "Désinscription à vérifier", "Exécutée malgré une confiance faible. Si c'était un oui, reprenez contact à la main.")
            return

        # La catégorie de l'outil confirme un oui quand l'agent hésite. Elle ne retourne jamais un non, un « plus tard » ou une absence.
        tool_yes = row["tool_category"] in self.positive_ids
        agent_yes = verdict.intent in ("yes", "meeting_request")
        upgradable = agent_yes or verdict.intent == "other" or (verdict.intent == "question" and self.cfg["tool_categories"]["upgrade_questions"])
        positive = (agent_yes and sure) or (tool_yes and upgradable)

        if not positive:
            if not sure:
                self._set(mid, status="review", **base)
                self._alert(mid, "review", "Réponse à lire", "Confiance insuffisante : aucune réponse automatique.")
            elif verdict.intent in ("later", "out_of_office"):
                self._set(mid, status="recorded", **base)
            elif verdict.intent == "question":
                self._set(mid, status="review", **base)
                self._alert(mid, "question", "Question d'un prospect", "Aucune réponse automatique : à répondre à la main.")
            else:
                self._set(mid, status="review", **base)
                self._alert(mid, "review", "Réponse non classée", "Aucune réponse automatique : à lire.")
            return

        title = self.cfg["alerts"]["new_lead_title"]
        manual = title + " · à traiter à la main"
        if row["lead_unsubscribed"]:
            self._set(mid, status="review", **base)
            self._alert(mid, "new_lead", manual, "Réponse positive d'un contact déjà désinscrit : aucune réponse automatique.")
            return
        domain = company_domain(row["website"], row["lead_email"], self.cfg["consumer_mailboxes"])
        key = domain or (None if self.cfg["deliverable"]["requires_domain"] else row["lead_email"].lower())
        if not key:
            self._set(mid, status="review", **base)
            self._alert(mid, "new_lead", manual, "Ni site renseigné ni adresse professionnelle : impossible de fabriquer le livrable.")
            return
        if not row["email_stats_id"]:
            # Sans identifiant de fil, la réponse ne pourrait pas partir : on ne paie pas le livrable.
            self._set(mid, status="review", deliverable_key=key, **base)
            self._alert(mid, "new_lead", manual, "Identifiant de fil absent : la réponse ne pourrait pas partir dans le fil. Livrable non commandé.")
            return
        self._set(mid, status="queued", deliverable_key=key, **base)
        in_progress = any(o["status"] in ("queued", "waiting", "sending", "answered") for o in self.store.other_replies_from(row["lead_email"], mid))
        if in_progress:
            self._log(mid, "duplicate", "ce contact a déjà une réponse positive en cours")
            return  # deux « ok » du même contact : une seule alerte, et la base garantit une seule réponse
        name = self.cfg["deliverable"]["name"]
        self._alert(mid, "new_lead", title, "Réponse positive : %s en préparation, il partira tout seul dans le fil avec le lien de réservation." % name)
        self._crm(self.store.reply(mid), "new_lead", self.cfg["crm"]["stages"].get("new_lead"))

    # 4. Désinscriptions ------------------------------------------------------------------------------------------

    def _process_unsubscribes(self) -> None:
        for row in self.store.replies_with_status("unsubscribe_pending"):
            mid = row["message_id"]
            try:
                if not row["unsubscribed_at"]:
                    self.smartlead.unsubscribe_lead(row["lead_id"])
                    self._set(mid, unsubscribed_at=self._now())
                    self._log(mid, "unsubscribed")
                if not row["blocklisted_at"]:
                    self.smartlead.add_to_block_list(row["lead_email"])
                    self._set(mid, blocklisted_at=self._now())
                    self._log(mid, "blocklisted")
                self._set(mid, status="unsubscribed", last_error=None)
            except Exception as exc:
                attempts = row["unsubscribe_attempts"] + 1
                self._set(mid, unsubscribe_attempts=attempts, last_error=short_error(exc))
                if attempts == 1:
                    self._alert(mid, "failure", "Désinscription en échec", "Nouvel essai à chaque sonde. À vérifier dans l'outil d'envoi.")

    # 5. Commande des livrables ----------------------------------------------------------------------------------

    def _follow_up(self, row: Any) -> str:
        """Un « non » (à toute date) ou un « plus tard » plus récent annule l'envoi. Une réponse plus récente pas encore classée le retient."""
        state = "clear"
        for other in self.store.other_replies_from(row["lead_email"], row["message_id"]):
            newer = other["received_at"] > row["received_at"]
            if other["intent"] == "no" or (other["intent"] == "later" and newer):
                return "cancel"
            if other["status"] == "received" and newer:
                state = "hold"
        return state

    def _cancel(self, row: Any) -> None:
        self._set(row["message_id"], status="cancelled")
        self._alert(row["message_id"], "review", "Envoi annulé", "Le contact a refusé ou reporté depuis sa réponse positive : rien ne part.")

    def _drain_queue(self) -> None:
        capped = []
        for row in self.store.replies_with_status("queued"):
            state = self._follow_up(row)
            if state == "hold":
                self._log(row["message_id"], "held", "réponse plus récente à classer")
                continue
            if state == "cancel":
                self._cancel(row)
                continue
            if self._request_deliverable(row) == "capped":
                capped.append(row)
        if capped:
            cap = self.cfg["deliverable"]["max_per_day"]
            self._alert_daily("cap", "Plafond de %d livrables par jour atteint\n%d réponse(s) positive(s) en attente, reprise automatique demain. Première en file : %s"
                              % (cap, len(capped), capped[0]["lead_email"]))

    def _request_deliverable(self, row: Any) -> str:
        """Compte et réserve dans la même transaction : le plafond tient même si deux sondes se recouvrent."""
        mid, key = row["message_id"], row["deliverable_key"]
        now = self.now()
        now_s = iso(now)
        with self.store.tx():
            reusable = self.store.reusable_deliverable(key, iso(now - timedelta(days=self.cfg["deliverable"]["reuse_days"])))
            if reusable:
                self._set(mid, status="waiting", deliverable_id=reusable["id"], deliverable_requested_at=now_s)
                self._log(mid, "deliverable_reused", key)
                return "reused"
            if self.store.deliverables_created_since(self._today_start()) >= self.cfg["deliverable"]["max_per_day"]:
                self._log(mid, "capped", key)
                return "capped"
            deliverable_id = uuid.uuid4().hex
            self.store.create_deliverable(deliverable_id, key, now_s)
            self._set(mid, status="waiting", deliverable_id=deliverable_id, deliverable_requested_at=now_s)
        lead = {
            "domain": key if "@" not in key else None,
            "email": row["lead_email"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "company_name": row["company_name"],
        }
        try:
            state = self.deliverables.request(deliverable_id, key, lead)
        except Exception as exc:
            self.store.update_deliverable(deliverable_id, self._now(), status="failed", last_error=short_error(exc))
            self._set(mid, status="deliverable_failed", last_error=short_error(exc))
            self._alert(mid, "failure", "Livrable non commandé", "%s. Aucune réponse envoyée : à traiter à la main." % short_error(exc))
            return "failed"
        self.store.update_deliverable(deliverable_id, self._now(), status=state.status, external_id=state.external_id, url=state.url, company_name=state.company_name)
        self._log(mid, "deliverable_requested", key)
        return "requested"

    # 6. Envoi des réponses ----------------------------------------------------------------------------------------

    def _refresh(self, deliverable_id: Optional[str]) -> Any:
        d = self.store.deliverable(deliverable_id)
        if d is not None and d["status"] in ("requesting", "queued") and d["external_id"]:
            try:
                state = self.deliverables.check(d["external_id"])
                self.store.update_deliverable(d["id"], self._now(), status=state.status, url=state.url or d["url"], company_name=state.company_name or d["company_name"])
            except Exception as exc:
                self._warn("état du livrable %s non lu (%s)" % (d["id"], short_error(exc)))
            d = self.store.deliverable(deliverable_id)
        return d

    def _send_ready(self) -> int:
        answered = 0
        stuck_after = timedelta(hours=self.cfg["deliverable"]["stuck_hours"])
        for row in self.store.replies_with_status("waiting"):
            mid = row["message_id"]
            d = self._refresh(row["deliverable_id"])
            if d is None or d["status"] == "failed" or (d["status"] == "ready" and not is_public_link(d["url"])):
                self._set(mid, status="deliverable_failed")
                self._alert(mid, "failure", "Livrable en échec", "Aucune réponse envoyée : à traiter à la main.")
                continue
            if d["status"] != "ready":
                if self.now() - parse_iso(row["deliverable_requested_at"]) > stuck_after:
                    self._set(mid, status="deliverable_failed", last_error="livrable jamais prêt")
                    self._alert(mid, "failure", "Livrable toujours pas prêt après %d h" % self.cfg["deliverable"]["stuck_hours"],
                                "Aucune réponse envoyée : à traiter à la main.")
                continue
            state = self._follow_up(row)
            if state == "hold":
                continue
            if state == "cancel":
                self._cancel(row)
                continue
            result = self._send(row, d)
            if result == "sent":
                answered += 1
            elif result == "rate_limited":
                break  # inutile d'insister pendant cette sonde
        return answered

    def _send(self, row: Any, d: Any) -> str:
        mid = row["message_id"]
        claim = self.store.claim_send(mid, self._now())
        if claim == "already_answered":
            self._set(mid, status="recorded", last_error="contact déjà servi par une autre réponse")
            self._log(mid, "skipped", "contact déjà servi")
            return "skipped"
        if claim != "claimed":
            return "skipped"
        link = d["url"]
        body = render_reply(
            self.cfg,
            first_name=clean_first_name(row["first_name"]),
            company=pick_company_name(d["company_name"], row["company_name"]),
            link=link,
            booking_url=self.booking_url,
        )
        try:
            outcome = self.smartlead.reply_in_thread(row["campaign_id"], row["email_stats_id"], body, row["rfc_message_id"], parse_iso(row["received_at"]))
        except Exception as exc:
            from .smartlead import SendOutcome
            outcome = SendOutcome("uncertain", short_error(exc))
        if outcome.outcome == "sent":
            self._set(mid, status="answered", answered_at=self._now())
            self._log(mid, "sent", body)
            self._alert(mid, "sent", self.cfg["alerts"]["sent_title"], "Lien : %s%s" % (link, "\nRéservation proposée : %s" % self.booking_url if self.booking_url else ""))
            self._crm(self.store.reply(mid), "deliverable_sent", self.cfg["crm"]["stages"].get("sent"), deliverable_url=link, booking_url=self.booking_url)
            return "sent"
        if outcome.outcome == "rate_limited":
            self._set(mid, status="waiting", answer_claimed_at=None)
            self._log(mid, "rate_limited")
            return "rate_limited"
        name = self.cfg["deliverable"]["name"]
        if outcome.outcome == "rejected":
            self._set(mid, status="send_failed", last_error=outcome.detail)
            self._log(mid, "send_failed", outcome.detail)
            self._alert(mid, "failure", "Envoi refusé par l'outil d'envoi",
                        "%s prêt (%s) mais aucune réponse n'est partie (%s) : à répondre à la main." % (name, link, outcome.detail))
            return "failed"
        self._set(mid, status="send_uncertain", last_error=outcome.detail)
        self._log(mid, "send_uncertain", outcome.detail)
        self._alert(mid, "failure", "Envoi au résultat inconnu",
                    "Vérifier le fil dans l'outil d'envoi avant de répondre à la main (%s). L'agent ne renverra rien à ce contact." % outcome.detail)
        return "failed"

    # 7. Sorties vers l'équipe ---------------------------------------------------------------------------------------

    def _flush_alerts(self) -> None:
        for alert in self.store.pending_alerts():
            try:
                self.slack.send(alert["text"])
            except Exception as exc:
                self._warn("alerte non envoyée, nouvel essai à la prochaine sonde (%s)" % short_error(exc))
                return
            self.store.mark_alert_sent(alert["id"], self._now())

    def _flush_crm(self) -> None:
        for event in self.store.pending_crm_events():
            try:
                self.crm.push(event["idempotency_key"], json.loads(event["payload"]))
            except Exception as exc:
                self._warn("événement CRM non envoyé, nouvel essai à la prochaine sonde (%s)" % short_error(exc))
                return
            self.store.mark_crm_sent(event["id"], self._now())

    # Entrées publiques ----------------------------------------------------------------------------------------------

    def poll_once(self) -> PollResult:
        """Une sonde à la fois, même si deux processus se recouvrent."""
        now = self.now()
        if not self.store.try_lock("poll", iso(now), iso(now + LOCK_TTL)):
            return PollResult(skipped=True)
        try:
            return self._run()
        finally:
            self.store.release_lock("poll")

    def _run(self) -> PollResult:
        # Posé une seule fois : les réponses antérieures au premier démarrage ne déclenchent ni livrable ni mail.
        watermark = parse_iso(self.store.set_setting_if_absent("watermark", self._now(), self._now()))
        self._sweep_interrupted()
        recorded = unreadable = 0
        for campaign_id in self.campaign_ids:
            try:
                r, u = self._ingest(campaign_id, watermark)
            except Exception as exc:
                self._warn("campagne %s non lue (%s)" % (campaign_id, short_error(exc)))
                continue
            recorded += r
            unreadable += u
        if unreadable:
            self._alert_daily("unreadable", "Réponses illisibles dans l'API de l'outil d'envoi\n%d réponse(s) que l'agent ne sait pas lire : aucune réponse automatique pour elles, à traiter dans la boîte de l'outil." % unreadable)
        self._classify_pending()
        self._process_unsubscribes()
        self._drain_queue()
        answered = self._send_ready()
        self._flush_alerts()
        self._flush_crm()
        return PollResult(False, recorded, answered)

    def record_booking(self, email: str) -> Dict[str, Any]:
        """À appeler quand un prospect réserve : dit si le livrable est déjà parti, pour que l'outil de réservation ne le renvoie pas."""
        email = email.strip().lower()
        domain = company_domain(None, email, self.cfg["consumer_mailboxes"])
        row = self.store.delivered_to(email, domain)
        stage = self.cfg["crm"]["stages"].get("booked")
        if stage:
            payload = {"event": "booked", "stage": stage, "email": email, "domain": domain, "already_sent": row is not None,
                       "deliverable_url": row["deliverable_url"] if row else None, "occurred_at": self._now()}
            self.store.add_crm_event("booked:%s:%s" % (email, self._today()), payload, self._now())
            self._flush_crm()
        return {
            "already_sent": row is not None,
            "deliverable_url": row["deliverable_url"] if row else None,
            "answered_at": row["answered_at"] if row else None,
        }
