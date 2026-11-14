#!/usr/bin/env python3
"""Tests hors ligne : aucune clé, aucun réseau. `python3 -m unittest discover -s tests -v`"""
import json
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from reply_agent.classify import RuleClassifier, read_verdict  # noqa: E402
from reply_agent.config import ConfigError, load_config, parse_campaign_ids  # noqa: E402
from reply_agent.dryrun import DryRun, run_dry_run  # noqa: E402
from reply_agent.smartlead import SmartleadClient, interpret_send_response, parse_thread  # noqa: E402
from reply_agent.store import iso  # noqa: E402
from reply_agent.text import company_domain, pick_company_name, redact_contacts, render_reply, reply_text  # noqa: E402

CONFIG = str(ROOT / "examples" / "config.example.json")
SAMPLE = str(ROOT / "examples" / "replies.sample.json")


def cfg(**overrides):
    c = load_config(CONFIG)
    for path, value in overrides.items():
        node = c
        keys = path.split("__")
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value
    return c


def lead(email, text, **extra):
    item = {"email": email, "first_name": "Alex", "company_name": "Jardins Test", "website": email.split("@")[1], "text": text}
    item.update(extra)
    return item


def simulate(replies, config=None, polls=3, **fixture_extra):
    fixture = {"campaign_id": "101", "replies": replies, **fixture_extra}
    return DryRun(config or cfg(), fixture, polls=polls).run()


def by_email(run):
    out = {}
    for row in run.store.all_replies():
        out.setdefault(row["lead_email"], []).append(row)
    return out


class SampleScenario(unittest.TestCase):
    """Le fichier d'exemple couvre chaque règle de la mission ; on vérifie le statut final de chacune."""

    @classmethod
    def setUpClass(cls):
        cls.summary = run_dry_run(load_config(CONFIG), SAMPLE)
        cls.rows = cls.summary["replies"]

    def status(self, email, index=0):
        return [r for r in self.rows if r["email"] == email][index]["status"]

    def test_yes_gets_deliverable_and_booking_link_once(self):
        self.assertEqual(self.status("camille.martin@jardins-martin.example"), "answered")
        sent_to = [s["to"] for s in self.summary["sent"]]
        self.assertEqual(sent_to.count("camille.martin@jardins-martin.example"), 1)
        body = self.summary["sent"][0]["body"]
        self.assertIn("https://audit.example.com/r/jardins-martin", body)
        self.assertIn("https://cal.example.com/canopee/audit-offert-30-min", body)

    def test_meeting_request_counts_as_yes(self):
        self.assertEqual(self.status("paul@paysages-dubois.example"), "answered")

    def test_question_is_left_to_a_human(self):
        self.assertEqual(self.status("contact@vert-tendre.example"), "review")
        self.assertEqual(self.status("luc@les-allees.example"), "review")

    def test_no_unsubscribes_and_blocks_even_if_tool_says_interested(self):
        for email in ("direction@terrasses-sud.example", "bureau@haies-et-bosquets.example"):
            self.assertEqual(self.status(email), "unsubscribed")
            self.assertIn(email, self.summary["blocked"])
        self.assertFalse({"direction@terrasses-sud.example", "bureau@haies-et-bosquets.example"} & {s["to"] for s in self.summary["sent"]})

    def test_absence_and_later_do_nothing(self):
        self.assertEqual(self.status("agence@gazon-royal.example"), "recorded")
        self.assertEqual(self.status("eric@bois-joli.example"), "recorded")

    def test_tool_category_confirms_a_hesitant_yes(self):
        self.assertEqual(self.status("julie@clos-fleuri.example"), "answered")

    def test_consumer_mailbox_without_website_goes_to_a_human(self):
        self.assertEqual(self.status("durand.paysage@gmail.example"), "review")

    def test_200_with_success_false_is_not_a_success(self):
        self.assertEqual(self.status("anne@verdure-conseil.example"), "send_failed")
        self.assertNotIn("anne@verdure-conseil.example", [e["email"] for e in self.summary["crm"]])

    def test_no_after_yes_cancels_the_send(self):
        self.assertEqual(self.status("tom@jardin-zen.example", 0), "cancelled")
        self.assertNotIn("tom@jardin-zen.example", [s["to"] for s in self.summary["sent"]])

    def test_slack_announces_new_lead_then_sent(self):
        titles = [m.split("\n")[0] for m in self.summary["slack"]]
        self.assertLess(titles.index("NOUVEAU LEAD"), titles.index("audit envoyé"))
        self.assertEqual(titles.count("audit envoyé"), 3)

    def test_crm_receives_each_sent_deliverable(self):
        stages = [(e["email"], e["stage"]) for e in self.summary["crm"]]
        self.assertIn(("camille.martin@jardins-martin.example", "Audit envoyé"), stages)
        self.assertEqual(len(stages), 3)


class Safety(unittest.TestCase):
    def test_replaying_the_same_replies_never_sends_twice(self):
        run = simulate([lead("a@jardins-a.example", "Ok")], polls=6)
        self.assertEqual(len(run.smartlead.sent), 1)

    def test_deliverable_waits_until_ready(self):
        run = simulate([lead("a@jardins-a.example", "Ok")], polls=1)
        self.assertEqual(run.store.all_replies()[0]["status"], "waiting")
        self.assertEqual(run.smartlead.sent, [])

    def test_interrupted_send_is_never_resent(self):
        run = simulate([lead("a@jardins-a.example", "Ok")], polls=1)
        mid = run.store.all_replies()[0]["message_id"]
        run.store.claim_send(mid, iso(run.clock))  # arrêt du processus juste après la réservation de l'envoi
        run.clock += timedelta(hours=1)
        run.agent.poll_once()
        self.assertEqual(run.store.reply(mid)["status"], "send_uncertain")
        self.assertEqual(run.smartlead.sent, [])

    def test_daily_cap_holds_then_resumes_next_day(self):
        replies = [lead("p%d@jardins-%d.example" % (i, i), "Ok") for i in range(3)]
        run = simulate(replies, config=cfg(deliverable__max_per_day=2), polls=3)
        statuses = sorted(r["status"] for r in run.store.all_replies())
        self.assertEqual(statuses, ["answered", "answered", "queued"])
        cap_alerts = [m for m in run.slack.messages if m.startswith("Plafond")]
        self.assertEqual(len(cap_alerts), 1)
        run.clock += timedelta(days=1)
        run.agent.poll_once()
        run.clock += timedelta(minutes=20)
        run.agent.poll_once()
        self.assertEqual(len(run.smartlead.sent), 3)

    def test_rate_limit_retries_later(self):
        run = simulate([lead("a@jardins-a.example", "Ok", simulate_send="rate_limited")], polls=3)
        self.assertEqual(len(run.smartlead.sent), 1)
        self.assertEqual(run.store.all_replies()[0]["status"], "answered")

    def test_uncertain_send_is_not_retried(self):
        run = simulate([lead("a@jardins-a.example", "Ok", simulate_send="uncertain")], polls=4)
        self.assertEqual(run.store.all_replies()[0]["status"], "send_uncertain")

    def test_failed_deliverable_sends_nothing(self):
        run = simulate([lead("a@jardins-a.example", "Ok")], failing_deliverables=["jardins-a.example"])
        self.assertEqual(run.store.all_replies()[0]["status"], "deliverable_failed")
        self.assertEqual(run.smartlead.sent, [])

    def test_missing_thread_id_does_not_order_the_deliverable(self):
        run = simulate([lead("a@jardins-a.example", "Ok", no_thread_id=True)])
        self.assertEqual(run.store.all_replies()[0]["status"], "review")
        self.assertEqual(run.store.deliverables_created_since("2000-01-01T00:00:00.000000Z"), 0)

    def test_low_confidence_no_still_unsubscribes_and_warns(self):
        run = simulate([lead("a@jardins-a.example", "x", simulate_verdict={"intent": "no", "confidence": 0.4})])
        self.assertEqual(run.store.all_replies()[0]["status"], "unsubscribed")
        self.assertTrue(any(m.startswith("Désinscription à vérifier") for m in run.slack.messages))

    def test_tool_category_never_turns_later_into_yes(self):
        run = simulate([lead("a@jardins-a.example", "Pas maintenant", tool_category="Interested")])
        self.assertEqual(run.store.all_replies()[0]["status"], "recorded")

    def test_question_can_be_upgraded_only_when_configured(self):
        text = "Intéressant, vous êtes où ?"
        kept = simulate([lead("a@jardins-a.example", text, tool_category="Interested")])
        self.assertEqual(kept.store.all_replies()[0]["status"], "review")
        upgraded = simulate([lead("a@jardins-a.example", text, tool_category="Interested")], config=cfg(tool_categories__upgrade_questions=True))
        self.assertEqual(upgraded.store.all_replies()[0]["status"], "answered")

    def test_slack_outage_keeps_alerts_due(self):
        run = DryRun(cfg(), {"campaign_id": "101", "replies": [lead("a@jardins-a.example", "Ok")]}, polls=1)
        run.slack.fail_times = 1
        run.agent.slack = run.slack
        run.run()
        self.assertEqual(run.slack.messages, [])
        run.clock += timedelta(minutes=20)
        run.agent.poll_once()
        titles = [m.split("\n")[0] for m in run.slack.messages]
        self.assertEqual(titles, ["NOUVEAU LEAD", "audit envoyé"])

    def test_booking_after_delivery_is_flagged(self):
        run = simulate([lead("a@jardins-a.example", "Ok")])
        result = run.agent.record_booking("A@jardins-a.example")
        self.assertTrue(result["already_sent"])
        self.assertTrue(result["deliverable_url"].startswith("https://"))
        self.assertFalse(run.agent.record_booking("b@ailleurs.example")["already_sent"])
        self.assertIn("Appel booké", [e["stage"] for e in run.crm.events])


class RealClientsWithFakeHttp(unittest.TestCase):
    """Le vrai client Smartlead, le vrai webhook de livrable, Slack et CRM, branchés sur un faux réseau."""

    def test_full_path(self):
        from reply_agent.agent import ReplyAgent
        from reply_agent.classify import RuleClassifier
        from reply_agent.deliverable import WebhookDeliverable
        from reply_agent.notify import CrmWebhook, SlackWebhook
        from reply_agent.store import Store

        calls = []

        def http(method, url, headers, body, timeout):
            payload = json.loads(body.decode()) if body else None
            calls.append((method, url, headers, payload))
            if "/campaigns/101/leads?" in url:
                return 200, json.dumps({"data": [{"lead_category_id": 1, "lead": {
                    "id": 7, "email": "Alex@Jardins-X.example", "first_name": "Alex", "company_name": "Jardins X", "website": "jardins-x.example"}}]}).encode()
            if url.split("?")[0].endswith("/campaigns/101/leads/7/message-history"):
                return 200, json.dumps({"history": [
                    {"type": "SENT", "time": "2026-03-10T08:00:00Z", "email_body": "Bonjour, audit offert ?"},
                    {"type": "REPLY", "time": "2026-03-10T09:00:00Z", "email_body": "Ok <!channel>", "message_id": "<r1@x>", "stats_id": "st7"},
                ]}).encode()
            if url.split("?")[0].endswith("/reply-email-thread"):
                return 200, b'{"ok": true}'
            if url == "https://gen.example/api" and method == "POST":
                return 200, b'{"id": "g1", "status": "queued"}'
            if url == "https://gen.example/api/g1":
                return 200, b'{"id": "g1", "status": "ready", "url": "https://gen.example/r/g1"}'
            if url in ("https://hooks.example/slack", "https://crm.example/hook"):
                return 200, b"ok"
            return 404, b""

        clock = [datetime(2026, 3, 10, 9, 5, tzinfo=timezone.utc)]
        store = Store(":memory:")
        store.set_setting("watermark", "2026-03-10T00:00:00.000000Z", "2026-03-10T00:00:00.000000Z")
        c = cfg()
        agent = ReplyAgent(
            cfg=c, store=store, smartlead=SmartleadClient("k-test", http=http), classifier=RuleClassifier(c["classifier"]["keywords"]),
            deliverables=WebhookDeliverable("https://gen.example/api", "gen-key", http=http),
            slack=SlackWebhook("https://hooks.example/slack", http=http), crm=CrmWebhook("https://crm.example/hook", "s3", http=http),
            campaign_ids=["101"], now=lambda: clock[0], sleep=lambda s: None, pace_seconds=0, quiet=True,
        )
        agent.poll_once()
        clock[0] += timedelta(minutes=20)
        agent.poll_once()

        sends = [p for m, u, h, p in calls if u.split("?")[0].endswith("/reply-email-thread")]
        self.assertEqual(len(sends), 1)
        self.assertEqual(sends[0]["email_stats_id"], "st7")
        self.assertEqual(sends[0]["reply_message_id"], "<r1@x>")
        self.assertIn("https://gen.example/r/g1", sends[0]["email_body"])
        self.assertIn(c["booking_url"], sends[0]["email_body"])
        slack = [p["text"] for m, u, h, p in calls if u == "https://hooks.example/slack"]
        self.assertEqual([t.split("\n")[0] for t in slack], ["NOUVEAU LEAD", "audit envoyé"])
        self.assertTrue(all("<!channel>" not in t for t in slack))
        crm = [(h, p) for m, u, h, p in calls if u == "https://crm.example/hook"]
        self.assertEqual(crm[0][1]["stage"], "Audit envoyé")
        self.assertEqual(crm[0][0]["x-webhook-secret"], "s3")
        self.assertIn("idempotency-key", crm[0][0])
        for m, u, h, p in calls:
            if "smartlead" in u:
                self.assertIn("api_key=k-test", u)
            else:
                self.assertNotIn("k-test", u)


class TextAndParsing(unittest.TestCase):
    def test_strips_quoted_thread_text_and_html(self):
        self.assertEqual(reply_text("Ok go\n\nLe 10 mars 2026, X a écrit :\n> blabla"), "Ok go")
        html = '<div>Oui merci</div><div class="gmail_quote"><blockquote>offre</blockquote></div>'
        self.assertEqual(reply_text(html), "Oui merci")
        outlook = '<p>Ok</p><div id="divRplyFwdMsg">De : X</div><p>ancien message</p>'
        self.assertEqual(reply_text(outlook), "Ok")

    def test_redacts_emails_and_phones_but_keeps_small_numbers(self):
        text = redact_contacts("Appelez le 06 12 34 56 78 ou +44 20 7946 0958, mail a@b.example, 3 chantiers")
        self.assertNotIn("06 12", text)
        self.assertNotIn("7946", text)
        self.assertNotIn("@", text)
        self.assertIn("3 chantiers", text)

    def test_company_domain_ignores_consumer_mailboxes(self):
        consumer = load_config(CONFIG)["consumer_mailboxes"]
        self.assertEqual(company_domain(None, "x@jardins.example", consumer), "jardins.example")
        self.assertIsNone(company_domain(None, "x@gmail.com", consumer))
        self.assertIsNone(company_domain(None, "x@yahoo.de", consumer))
        self.assertEqual(company_domain("https://www.site.example/contact", "x@gmail.com", consumer), "site.example")

    def test_names(self):
        self.assertEqual(pick_company_name("JARDINS NORD", "Jardins Nord"), "Jardins Nord")
        self.assertIsNone(pick_company_name("JARDINS NORD", None))
        c = load_config(CONFIG)
        body = render_reply(c, first_name=None, company=None, link="https://x.example/r/1", booking_url=None)
        self.assertTrue(body.startswith("Bonjour,"))
        self.assertNotIn("réservez", body)

    def test_send_response_interpretation(self):
        self.assertEqual(interpret_send_response(200, b'{"ok": true}').outcome, "sent")
        self.assertEqual(interpret_send_response(200, b'{"success": false}').outcome, "rejected")
        self.assertEqual(interpret_send_response(200, b"<html>").outcome, "uncertain")
        self.assertEqual(interpret_send_response(429, b"").outcome, "rate_limited")
        self.assertEqual(interpret_send_response(503, b"").outcome, "uncertain")
        self.assertEqual(interpret_send_response(400, b"").outcome, "rejected")

    def test_thread_parser_keeps_inbound_only_and_counts_unreadable(self):
        replies, bad = parse_thread({"history": [
            {"type": "SENT", "time": "2026-03-10T08:00:00Z", "email_body": "offre"},
            {"type": "REPLY", "time": "2026-03-10T09:00:00Z", "email_body": "ok", "message_id": "<m1>", "stats_id": "s1"},
            {"type": "REPLY", "email_body": "sans date", "message_id": "<m2>"},
        ]})
        self.assertEqual([r.body for r in replies], ["ok"])
        self.assertEqual(bad, 1)

    def test_client_never_puts_the_key_in_errors(self):
        def http(method, url, headers, body, timeout):
            return 500, b""
        client = SmartleadClient("secret-value", http=http)
        with self.assertRaises(Exception) as ctx:
            client.fetch_replies("1", "2")
        self.assertNotIn("secret-value", str(ctx.exception))
        self.assertEqual(client.reply_in_thread("1", "s", "b", None, datetime.now(timezone.utc)).outcome, "uncertain")

    def test_rule_classifier(self):
        rules = RuleClassifier(load_config(CONFIG)["classifier"]["keywords"])
        self.assertEqual(rules.classify("Pas intéressé").intent, "no")
        self.assertEqual(rules.classify("Pas intéressé").confidence, 0.95)
        self.assertEqual(rules.classify("ok go").intent, "yes")
        self.assertEqual(rules.classify("On peut caler un rdv ?").intent, "meeting_request")
        self.assertEqual(rules.classify("").intent, "other")

    def test_claude_classifier_reads_schema_output_and_refusals(self):
        from types import SimpleNamespace
        from reply_agent.classify import ClaudeClassifier

        class FakeMessages:
            def __init__(self, response):
                self.response, self.kwargs = response, None

            def create(self, **kwargs):
                self.kwargs = kwargs
                return self.response

        def client(response):
            return SimpleNamespace(beta=SimpleNamespace(messages=FakeMessages(response)))

        ok = client(SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text='{"intent": "yes", "confidence": 0.93}')]))
        verdict = ClaudeClassifier("claude-opus-5-5", "Offer.", client=ok).classify("ok go")
        self.assertEqual((verdict.intent, verdict.confidence), ("yes", 0.93))
        sent = ok.beta.messages.kwargs
        self.assertEqual(sent["output_config"]["format"]["type"], "json_schema")
        self.assertIn("untrusted", sent["system"])
        refused = client(SimpleNamespace(stop_reason="refusal", content=[]))
        self.assertEqual(ClaudeClassifier("claude-opus-5-5", "Offer.", client=refused).classify("x").intent, "other")

    def test_verdict_outside_the_list_is_undecided(self):
        self.assertEqual(read_verdict({"intent": "maybe", "confidence": 0.9}).intent, "other")
        self.assertEqual(read_verdict({"intent": "yes", "confidence": 3}).intent, "other")
        self.assertEqual(read_verdict({"intent": "yes", "confidence": True}).intent, "other")


class Config(unittest.TestCase):
    def test_campaign_ids(self):
        self.assertEqual(parse_campaign_ids("101, 202 abc;303"), ["101", "202", "303"])

    def test_rejects_unknown_placeholder(self):
        path = ROOT / "tests" / "_tmp_config.json"
        try:
            path.write_text(json.dumps({"reply": {"lines": ["{link} {prenom}"]}}), encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(str(path))
        finally:
            path.unlink()


class Cli(unittest.TestCase):
    def test_dry_run_command(self):
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "run.py"), "--dry-run"], capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("NOUVEAU LEAD", out.stdout)
        self.assertIn("Bilan : 3 réponse(s) envoyée(s)", out.stdout)

    def test_real_mode_refuses_to_start_without_keys(self):
        env = {"PATH": "/usr/bin:/bin"}
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "run.py"), "--once", "--db", ":memory:"], capture_output=True, text=True, timeout=60, env=env)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("Agent coupé", out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
