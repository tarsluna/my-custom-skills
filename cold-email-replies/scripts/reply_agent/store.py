"""État de l'agent dans SQLite. Une ligne par réponse reçue, clé = identifiant du message :
une réponse relue ou un redémarrage ne peuvent ni la retraiter ni y répondre deux fois."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

STATUSES = (
    "received", "recorded", "review", "queued", "waiting", "sending", "answered",
    "send_failed", "send_uncertain", "deliverable_failed", "cancelled", "unsubscribe_pending", "unsubscribed",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS replies (
  message_id TEXT PRIMARY KEY,
  campaign_id TEXT NOT NULL,
  lead_id TEXT NOT NULL,
  lead_email TEXT NOT NULL,
  first_name TEXT, last_name TEXT, company_name TEXT, website TEXT,
  lead_unsubscribed INTEGER NOT NULL DEFAULT 0,
  tool_category INTEGER,
  email_stats_id TEXT,
  rfc_message_id TEXT,
  received_at TEXT NOT NULL,
  reply_text TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'received' CHECK (status IN (%s)),
  intent TEXT,
  confidence REAL,
  classify_attempts INTEGER NOT NULL DEFAULT 0,
  deliverable_key TEXT,
  deliverable_id TEXT,
  deliverable_requested_at TEXT,
  answer_claimed_at TEXT,
  answered_at TEXT,
  unsubscribed_at TEXT,
  blocklisted_at TEXT,
  unsubscribe_attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS replies_status ON replies (status, received_at);
CREATE INDEX IF NOT EXISTS replies_email ON replies (lower(lead_email));
-- Un prospect qui écrit deux fois « ok » ne reçoit qu'une réponse : la base le garantit au moment de réserver l'envoi.
CREATE UNIQUE INDEX IF NOT EXISTS replies_one_answer ON replies (campaign_id, lead_id) WHERE answer_claimed_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS deliverables (
  id TEXT PRIMARY KEY,
  key TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('requesting','queued','ready','failed')),
  external_id TEXT,
  url TEXT,
  company_name TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS deliverables_key ON deliverables (key, created_at);

-- Une alerte par événement, dans une file : une alerte que Slack refuse reste due, et une nouvelle n'écrase jamais l'ancienne.
CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id TEXT,
  kind TEXT NOT NULL,
  text TEXT NOT NULL,
  created_at TEXT NOT NULL,
  sent_at TEXT
);
CREATE TABLE IF NOT EXISTS crm_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  idempotency_key TEXT NOT NULL UNIQUE,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL,
  sent_at TEXT
);
""" % ",".join("'%s'" % s for s in STATUSES)

REPLY_FIELDS = {
    "status", "intent", "confidence", "classify_attempts", "deliverable_key", "deliverable_id", "deliverable_requested_at",
    "answer_claimed_at", "answered_at", "unsubscribed_at", "blocklisted_at", "unsubscribe_attempts", "last_error",
}
DELIVERABLE_FIELDS = {"status", "external_id", "url", "company_name", "last_error"}

ISO = "%Y-%m-%dT%H:%M:%S.%fZ"


def iso(dt: datetime) -> str:
    """Même format partout, en UTC, longueur fixe : la comparaison de chaînes suit l'ordre du temps."""
    return dt.astimezone(timezone.utc).strftime(ISO)


def parse_iso(value: str) -> datetime:
    return datetime.strptime(value, ISO).replace(tzinfo=timezone.utc)


class Store:
    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path, isolation_level=None, timeout=30)
        self.db.row_factory = sqlite3.Row
        if path != ":memory:":
            self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)

    def close(self) -> None:
        self.db.close()

    @contextmanager
    def tx(self) -> Iterator[None]:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        self.db.execute("COMMIT")

    # Réglages, filigrane, curseurs, verrou ---------------------------------------------------------------

    def get_setting(self, key: str) -> Optional[str]:
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    def set_setting(self, key: str, value: str, now: str) -> None:
        self.db.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, value, now),
        )

    def set_setting_if_absent(self, key: str, value: str, now: str) -> str:
        self.db.execute("INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES (?,?,?)", (key, value, now))
        return self.get_setting(key)  # type: ignore[return-value]

    def try_lock(self, name: str, now: str, until: str) -> bool:
        """Une sonde à la fois, même si deux processus se recouvrent. Un verrou expiré se reprend."""
        with self.tx():
            held = self.get_setting("lock_" + name)
            if held and held > now:
                return False
            self.set_setting("lock_" + name, until, now)
        return True

    def release_lock(self, name: str) -> None:
        self.db.execute("DELETE FROM settings WHERE key=?", ("lock_" + name,))

    # Réponses ----------------------------------------------------------------------------------------------

    def insert_reply(self, row: Dict[str, Any], now: str) -> bool:
        cols = list(row) + ["created_at", "updated_at"]
        cur = self.db.execute(
            "INSERT OR IGNORE INTO replies (%s) VALUES (%s)" % (",".join(cols), ",".join("?" * len(cols))),
            [row[c] for c in row] + [now, now],
        )
        return cur.rowcount == 1

    def update_reply(self, message_id: str, now: str, **fields: Any) -> None:
        unknown = set(fields) - REPLY_FIELDS
        if unknown:
            raise ValueError("champs inconnus : %s" % sorted(unknown))
        sets = ", ".join("%s=?" % name for name in fields)
        self.db.execute("UPDATE replies SET %s, updated_at=? WHERE message_id=?" % sets, [*fields.values(), now, message_id])

    def reply(self, message_id: str) -> Optional[sqlite3.Row]:
        return self.db.execute("SELECT * FROM replies WHERE message_id=?", (message_id,)).fetchone()

    def replies_with_status(self, status: str, limit: int = 500) -> List[sqlite3.Row]:
        return self.db.execute("SELECT * FROM replies WHERE status=? ORDER BY received_at LIMIT ?", (status, limit)).fetchall()

    def all_replies(self) -> List[sqlite3.Row]:
        return self.db.execute("SELECT * FROM replies ORDER BY received_at, message_id").fetchall()

    def other_replies_from(self, email: str, message_id: str) -> List[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM replies WHERE lower(lead_email)=lower(?) AND message_id<>?", (email, message_id)
        ).fetchall()

    def claim_send(self, message_id: str, now: str) -> str:
        """Réserve l'envoi avant d'appeler l'outil : un arrêt après ce point peut coûter un mail, jamais en ajouter un."""
        try:
            with self.tx():
                cur = self.db.execute(
                    "UPDATE replies SET status='sending', answer_claimed_at=?, updated_at=? WHERE message_id=? AND status='waiting'",
                    (now, now, message_id),
                )
            return "claimed" if cur.rowcount == 1 else "taken"
        except sqlite3.IntegrityError:
            return "already_answered"

    def interrupted_sends(self, before: str) -> List[sqlite3.Row]:
        return self.db.execute("SELECT * FROM replies WHERE status='sending' AND answer_claimed_at < ?", (before,)).fetchall()

    def delivered_to(self, email: str, domain: Optional[str]) -> Optional[sqlite3.Row]:
        """Le livrable est-il déjà parti vers ce contact, ou vers son entreprise ? Sert à ne pas l'envoyer deux fois."""
        return self.db.execute(
            """SELECT r.*, d.url AS deliverable_url FROM replies r LEFT JOIN deliverables d ON d.id=r.deliverable_id
               WHERE r.status='answered' AND (lower(r.lead_email)=lower(?) OR (? IS NOT NULL AND r.deliverable_key=?))
               ORDER BY r.answered_at DESC LIMIT 1""",
            (email, domain, domain),
        ).fetchone()

    def status_counts(self) -> Dict[str, int]:
        return {r["status"]: r["n"] for r in self.db.execute("SELECT status, count(*) AS n FROM replies GROUP BY status")}

    # Livrables --------------------------------------------------------------------------------------------

    def create_deliverable(self, deliverable_id: str, key: str, now: str) -> None:
        self.db.execute(
            "INSERT INTO deliverables (id, key, status, created_at, updated_at) VALUES (?,?,'requesting',?,?)",
            (deliverable_id, key, now, now),
        )

    def update_deliverable(self, deliverable_id: str, now: str, **fields: Any) -> None:
        unknown = set(fields) - DELIVERABLE_FIELDS
        if unknown:
            raise ValueError("champs inconnus : %s" % sorted(unknown))
        sets = ", ".join("%s=?" % name for name in fields)
        self.db.execute("UPDATE deliverables SET %s, updated_at=? WHERE id=?" % sets, [*fields.values(), now, deliverable_id])

    def deliverable(self, deliverable_id: Optional[str]) -> Optional[sqlite3.Row]:
        if not deliverable_id:
            return None
        return self.db.execute("SELECT * FROM deliverables WHERE id=?", (deliverable_id,)).fetchone()

    def reusable_deliverable(self, key: str, since: str) -> Optional[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM deliverables WHERE key=? AND status<>'failed' AND created_at>=? ORDER BY created_at DESC LIMIT 1",
            (key, since),
        ).fetchone()

    def deliverables_created_since(self, since: str) -> int:
        return self.db.execute("SELECT count(*) AS n FROM deliverables WHERE created_at>=?", (since,)).fetchone()["n"]

    # Alertes et CRM -----------------------------------------------------------------------------------------

    def add_alert(self, message_id: Optional[str], kind: str, text: str, now: str) -> None:
        self.db.execute("INSERT INTO alerts (message_id, kind, text, created_at) VALUES (?,?,?,?)", (message_id, kind, text, now))

    def pending_alerts(self) -> List[sqlite3.Row]:
        return self.db.execute("SELECT * FROM alerts WHERE sent_at IS NULL ORDER BY id").fetchall()

    def mark_alert_sent(self, alert_id: int, now: str) -> None:
        self.db.execute("UPDATE alerts SET sent_at=? WHERE id=?", (now, alert_id))

    def add_crm_event(self, idempotency_key: str, payload: Dict[str, Any], now: str) -> None:
        self.db.execute(
            "INSERT OR IGNORE INTO crm_events (idempotency_key, payload, created_at) VALUES (?,?,?)",
            (idempotency_key, json.dumps(payload, ensure_ascii=False), now),
        )

    def pending_crm_events(self) -> List[sqlite3.Row]:
        return self.db.execute("SELECT * FROM crm_events WHERE sent_at IS NULL ORDER BY id").fetchall()

    def mark_crm_sent(self, event_id: int, now: str) -> None:
        self.db.execute("UPDATE crm_events SET sent_at=? WHERE id=?", (now, event_id))
