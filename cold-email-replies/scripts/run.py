#!/usr/bin/env python3
"""Agent de réponses au cold email.

  python3 scripts/run.py --dry-run                 rejoue examples/replies.sample.json, sans clé ni réseau
  python3 scripts/run.py --once                    une sonde réelle (REPLY_AGENT_ENABLED=1 et clés dans l'environnement)
  python3 scripts/run.py --loop                    une sonde toutes les poll_interval_seconds
  python3 scripts/run.py --status                  où en est chaque réponse, et ce qui attend un humain
  python3 scripts/run.py --booked prospect@x.com   un prospect a réservé : le livrable est-il déjà parti ?
  python3 scripts/run.py --check-leads leads.csv   contrôle d'une liste de contacts avant lancement
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reply_agent.agent import ReplyAgent  # noqa: E402
from reply_agent.classify import build_classifier  # noqa: E402
from reply_agent.config import ConfigError, env_settings, load_config  # noqa: E402
from reply_agent.deliverable import build_deliverables  # noqa: E402
from reply_agent.dryrun import format_report, run_dry_run  # noqa: E402
from reply_agent.notify import CrmWebhook, SlackWebhook  # noqa: E402
from reply_agent.preflight import check_leads, format_check  # noqa: E402
from reply_agent.smartlead import SmartleadClient  # noqa: E402
from reply_agent.store import Store  # noqa: E402

EXAMPLE_CONFIG = ROOT / "examples" / "config.example.json"
EXAMPLE_REPLIES = ROOT / "examples" / "replies.sample.json"


def resolve_config(path):
    if path:
        return path
    env_path = os.environ.get("REPLY_AGENT_CONFIG")
    if env_path:
        return env_path
    if Path("config.json").exists():
        return "config.json"
    return str(EXAMPLE_CONFIG)


def build_agent(cfg, env, store):
    missing = [name for name, ok in (
        ("REPLY_AGENT_ENABLED=1", env["enabled"]),
        ("SMARTLEAD_API_KEY", env["smartlead_api_key"]),
        ("SMARTLEAD_CAMPAIGN_IDS", env["campaign_ids"]),
    ) if not ok]
    if missing:
        raise SystemExit("Agent coupé, rien n'est fait. Manque : %s" % ", ".join(missing))
    if cfg["classifier"]["mode"] == "claude":
        try:
            import anthropic  # noqa: F401
        except ImportError:
            raise SystemExit("classifier.mode=claude : installez le SDK (`pip install anthropic`, Python 3.10+)")
    booking_url = env["booking_url"] or cfg["booking_url"]
    if not booking_url:
        print("avertissement : aucun lien de réservation (booking_url), la phrase qui le propose sera retirée du mail", file=sys.stderr)
    s = cfg["smartlead"]
    return ReplyAgent(
        cfg=cfg,
        store=store,
        smartlead=SmartleadClient(env["smartlead_api_key"], page_size=s["page_size"], max_pages=s["max_pages"]),
        classifier=build_classifier(cfg),
        deliverables=build_deliverables(cfg, env),
        slack=SlackWebhook(env["slack_webhook_url"]),
        crm=CrmWebhook(env["crm_webhook_url"], env["crm_webhook_secret"]),
        campaign_ids=env["campaign_ids"],
        booking_url=booking_url,
    )


def print_status(store):
    counts = store.status_counts()
    if not counts:
        print("Aucune réponse enregistrée.")
        return
    print("Réponses par statut :")
    for status, n in sorted(counts.items()):
        print("  %-20s %d" % (status, n))
    human = store.db.execute(
        "SELECT lead_email, status, intent, received_at FROM replies WHERE status IN ('review','send_failed','send_uncertain','deliverable_failed') ORDER BY received_at DESC LIMIT 20"
    ).fetchall()
    if human:
        print("\nÀ traiter à la main :")
        for r in human:
            print("  %s  %-18s %-16s %s" % (r["received_at"][:16], r["status"], r["intent"] or "-", r["lead_email"]))
    pending = len(store.pending_alerts())
    if pending:
        print("\n%d alerte(s) pas encore remise(s) à Slack." % pending)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Agent de réponses au cold email")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="simulation sur des réponses fictives, sans clé ni réseau")
    mode.add_argument("--once", action="store_true", help="une sonde réelle")
    mode.add_argument("--loop", action="store_true", help="sonde en continu")
    mode.add_argument("--status", action="store_true", help="état des réponses enregistrées")
    mode.add_argument("--booked", metavar="EMAIL", help="un prospect a réservé : dit si le livrable est déjà parti")
    mode.add_argument("--check-leads", metavar="CSV", help="contrôle d'une liste de contacts avant lancement")
    parser.add_argument("--config", help="fichier de configuration JSON (défaut : REPLY_AGENT_CONFIG, ./config.json, puis l'exemple)")
    parser.add_argument("--replies", default=str(EXAMPLE_REPLIES), help="réponses fictives pour --dry-run")
    parser.add_argument("--polls", type=int, default=3, help="nombre de sondes simulées (--dry-run)")
    parser.add_argument("--json", action="store_true", help="sortie JSON (--dry-run, --booked)")
    parser.add_argument("--db", help="base SQLite (défaut : REPLY_AGENT_DB ou ./reply-agent.sqlite3)")
    args = parser.parse_args(argv)

    try:
        cfg = load_config(resolve_config(args.config))
    except (ConfigError, OSError, ValueError) as exc:
        print("configuration invalide : %s" % exc, file=sys.stderr)
        return 2

    if args.dry_run:
        summary = run_dry_run(cfg, args.replies, polls=args.polls)
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            source = os.path.relpath(args.replies) if not os.path.isabs(args.replies) else Path(args.replies).name
            print(format_report(cfg, summary, source, args.polls, 20))
        return 0

    if args.check_leads:
        print(format_check(check_leads(args.check_leads, cfg["consumer_mailboxes"])))
        return 0

    env = env_settings()
    store = Store(args.db or env["db_path"])

    if args.status:
        print_status(store)
        return 0

    if args.booked:
        # Pas besoin de l'outil d'envoi ici : on lit la base et on prévient le CRM.
        agent = ReplyAgent(cfg=cfg, store=store, smartlead=None, classifier=None, deliverables=None,
                           slack=SlackWebhook(env["slack_webhook_url"]), crm=CrmWebhook(env["crm_webhook_url"], env["crm_webhook_secret"]),
                           campaign_ids=[], booking_url=env["booking_url"])
        result = agent.record_booking(args.booked)
        print(json.dumps(result, ensure_ascii=False) if args.json else
              ("Livrable déjà envoyé le %s : %s. Ne pas le renvoyer." % (result["answered_at"], result["deliverable_url"])
               if result["already_sent"] else "Aucun livrable envoyé à ce contact par l'agent."))
        return 0

    agent = build_agent(cfg, env, store)
    if args.once:
        result = agent.poll_once()
        print(json.dumps(result._asdict(), ensure_ascii=False))
        return 0

    interval = max(30, int(cfg["poll_interval_seconds"]))
    while True:
        try:
            result = agent.poll_once()
            if result.recorded or result.answered:
                print(json.dumps(result._asdict(), ensure_ascii=False), flush=True)
        except Exception as exc:  # une sonde ratée ne tue pas la boucle
            print("sonde en échec : %s" % type(exc).__name__, file=sys.stderr, flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main())
