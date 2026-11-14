"""Tests sans cle ni reseau externe : python3 -m unittest discover -s tests"""
import contextlib
import copy
import http.server
import io
import json
import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import copy_rules  # noqa: E402
import meta_api  # noqa: E402
import meta_launch  # noqa: E402

EXAMPLE = ROOT / "examples" / "paysagistes" / "campagne.json"
TOKEN_ENV = ("META_ACCESS_TOKEN", "META_AD_ACCOUNT", "META_PAGE_ID", "META_PIXEL_ID")


class DryRunBase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = pathlib.Path(tmp.name)
        self.config = self.dir / "campagne.json"
        self.config.write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        self.state = self.dir / "state.json"
        self.world = pathlib.Path(str(self.state) + ".world.json")
        env = {k: v for k, v in os.environ.items() if k not in TOKEN_ENV}
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        for target, name in ((socket.socket, "connect"), (subprocess, "run")):
            guard = mock.patch.object(target, name, side_effect=AssertionError("appel reseau en simulation"))
            guard.start()
            self.addCleanup(guard.stop)

    def cli(self, *args, crash=None):
        argv = ["--config", str(self.config), "--dry-run", "--state", str(self.state)]
        if crash is not None:
            argv += ["--simulate-crash-after", str(crash)]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = meta_launch.main(argv + list(args))
        self.output = out.getvalue()
        return code

    def objects(self, kind):
        world = json.loads(self.world.read_text(encoding="utf-8"))
        return [o for o in world["objects"].values() if o["kind"] == kind]

    def saved(self):
        return json.loads(self.state.read_text(encoding="utf-8"))


class FullRun(DryRunBase):
    def test_whole_launch_without_network_or_token(self):
        self.assertEqual(self.cli("run", "--confirm-budget", "3000"), 0)
        self.assertEqual(len(self.objects("ad")), 12)
        self.assertEqual(len(self.objects("adset")), 2)
        self.assertEqual(len(self.objects("conversion")), 1)
        self.assertIn("PENDING_REVIEW", self.output)
        self.assertIn("conforme", self.output)
        for creative in self.objects("creative"):
            self.assertEqual(len(creative["asset_feed_spec"]["bodies"]), 5)
            self.assertEqual(len(creative["asset_feed_spec"]["titles"]), 5)

    def test_everything_paused_before_go(self):
        self.cli("structure")
        self.cli("ads")
        self.assertEqual({o["status"] for o in self.objects("campaign") + self.objects("adset") + self.objects("ad")}, {"PAUSED"})

    def test_titles_shared_within_adset_and_first_text_unique(self):
        self.cli("structure")
        self.cli("ads")
        creatives = self.objects("creative")
        firsts = {c["asset_feed_spec"]["bodies"][0]["text"] for c in creatives}
        titles = {json.dumps(c["asset_feed_spec"]["titles"]) for c in creatives}
        self.assertEqual(len(firsts), 6)
        self.assertEqual(len(titles), 2)


class Resume(DryRunBase):
    def test_crash_after_write_creates_no_duplicates(self):
        self.cli("structure")
        for crash in (4, 8, 13):  # 4 et 8 tombent juste apres la creation d'une pub
            code = self.cli("ads", crash=crash)
            self.assertEqual(code, 3)
        self.assertEqual(self.cli("ads"), 0)
        self.assertEqual(len(self.objects("ad")), 12)
        self.assertEqual(len(self.saved()["ads"]), 12)

    def test_crash_during_structure_is_reconciled(self):
        self.assertEqual(self.cli("structure", crash=1), 3)
        self.assertNotIn("campaign", self.saved() if self.state.exists() else {})
        self.assertEqual(self.cli("structure"), 0)
        self.assertEqual(len(self.objects("campaign")), 1)

    def test_second_run_does_nothing(self):
        self.cli("structure")
        self.cli("ads")
        before = json.loads(self.world.read_text(encoding="utf-8"))["next"]
        self.cli("ads")
        self.assertEqual(json.loads(self.world.read_text(encoding="utf-8"))["next"], before)


class Gate(DryRunBase):
    def prepared(self, *only):
        self.cli("structure")
        self.cli("ads", *(["--only"] + list(only) if only else []))

    def test_missing_pair_blocks_launch(self):
        self.prepared("P01")
        with self.assertRaises(SystemExit) as stop:
            self.cli("go", "--confirm-budget", "3000")
        self.assertIn("2 pubs sur 12", str(stop.exception))
        self.assertEqual({o["status"] for o in self.objects("campaign")}, {"PAUSED"})

    def test_wrong_confirmed_budget_blocks_launch(self):
        self.prepared()
        with self.assertRaises(SystemExit) as stop:
            self.cli("go", "--confirm-budget", "30000")
        self.assertIn("budget", str(stop.exception))
        self.assertEqual({o["status"] for o in self.objects("ad")}, {"PAUSED"})

    def test_budget_changed_at_meta_blocks_launch(self):
        self.prepared()
        world = json.loads(self.world.read_text(encoding="utf-8"))
        for obj in world["objects"].values():
            if obj["kind"] == "campaign":
                obj["daily_budget"] = "9900"
        self.world.write_text(json.dumps(world), encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.cli("go", "--confirm-budget", "3000")

    def test_ad_with_four_texts_blocks_launch(self):
        self.prepared()
        world = json.loads(self.world.read_text(encoding="utf-8"))
        creative = next(o for o in world["objects"].values() if o["kind"] == "creative")
        creative["asset_feed_spec"]["bodies"].pop()
        self.world.write_text(json.dumps(world), encoding="utf-8")
        with self.assertRaises(SystemExit) as stop:
            self.cli("go", "--confirm-budget", "3000")
        self.assertIn("pubs a probleme", str(stop.exception))

    def test_cleanup_refuses_live_campaign_and_only_touches_state(self):
        self.cli("run", "--confirm-budget", "3000")
        with self.assertRaises(SystemExit):
            self.cli("cleanup", "--yes")

    def test_cleanup_of_one_ad(self):
        self.prepared()
        self.cli("cleanup", "--yes", "--only", "P01")
        self.assertEqual(len(self.objects("ad")), 10)
        self.assertNotIn("P01-V", self.saved()["ads"])
        self.assertIn("P02-V", self.saved()["ads"])

    def test_sync_pushes_budget_and_targeting(self):
        self.prepared()
        cfg = json.loads(self.config.read_text(encoding="utf-8"))
        cfg["campaign"]["daily_budget_minor"] = 4500
        cfg["targeting_base"]["age_min"] = 40
        self.config.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
        self.cli("structure", "--sync")
        self.assertEqual(self.objects("campaign")[0]["daily_budget"], 4500)
        self.assertEqual({a["targeting"]["age_min"] for a in self.objects("adset")}, {40})

    def test_relink_keeps_ad_and_retires_old_creative(self):
        self.prepared()
        old = self.saved()["creatives"]["P01-V"]
        self.cli("relink", "--only", "P01")
        self.assertNotEqual(self.saved()["creatives"]["P01-V"], old)
        self.assertIn(old, self.saved()["retired_creatives"])
        self.assertEqual(len(self.objects("ad")), 12)


class CopyRules(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_example_is_clean(self):
        self.assertEqual(copy_rules.check(self.cfg), [])

    def assert_flagged(self, fragment):
        problems = copy_rules.check(self.cfg)
        self.assertTrue(any(fragment in p for p in problems), problems)

    def test_four_titles(self):
        self.cfg["adsets"][0]["titles"].pop()
        self.assert_flagged("4 titres")

    def test_wrong_audience(self):
        self.cfg["ads"][0]["body"] += " Pour vos espaces verts."
        self.assert_flagged("mauvaise audience")

    def test_banned_word(self):
        self.cfg["ads"][0]["description"] = "Le meilleur prix."
        self.assert_flagged("mot interdit")

    def test_long_first_line(self):
        self.cfg["ads"][0]["body"] = "x" * 126
        self.assert_flagged("premiere ligne")

    def test_hook_outside_list(self):
        self.cfg["ads"][0]["hook"]["offer"] = "Autre promesse"
        self.assert_flagged("accroche")

    def test_landing_matching_conversion_rule(self):
        self.cfg["adsets"][0]["link"] = "https://pepiniere-exemple.test/merci-paysagistes"
        self.assert_flagged("chaque visite")

    def test_thank_you_page_not_matching_rule(self):
        self.cfg["conversion"]["thank_you_url"] = "https://pepiniere-exemple.test/fin"
        self.assert_flagged("aucune conversion")

    def test_ad_on_unknown_adset(self):
        broken = copy.deepcopy(self.cfg)
        broken["ads"][0]["adset"] = "Inconnu"
        self.assertTrue(any("adset inconnu" in p for p in copy_rules.check(broken)))


FAKE_TOKEN = "jeton-de-test-123"


class Handler(http.server.BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *args):
        return None

    def _reply(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        Handler.calls.append(self.path)
        if "throttle" in self.path and sum("throttle" in c for c in Handler.calls) == 1:
            return self._reply(400, {"error": {"code": 17, "message": "limite"}})
        if "fuite" in self.path:
            return self._reply(400, {"error": {"code": 100, "message": "mauvais jeton %s" % FAKE_TOKEN}})
        return self._reply(200, {"ok": True})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        Handler.calls.append(self.rfile.read(length))
        return self._reply(200, {"id": "42"})


class RealClientOnLocalServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        root = "http://127.0.0.1:%d" % cls.server.server_address[1]
        cls.client = meta_api.GraphClient(FAKE_TOKEN, base=root, video_base=root, sleep=lambda _s: None)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Handler.calls.clear()

    def test_throttled_call_is_retried(self):
        self.assertEqual(self.client.get("throttle"), {"ok": True})
        self.assertEqual(len(Handler.calls), 2)

    def test_token_masked_in_errors(self):
        self.assertNotIn(FAKE_TOKEN, json.dumps(self.client.get("fuite")))

    def test_upload_keeps_token_out_of_argv(self):
        real_run = subprocess.run
        seen = {}

        def spy(cmd, **kwargs):
            seen["cmd"] = cmd
            seen["input"] = kwargs.get("input")
            return real_run(cmd, **kwargs)

        with tempfile.NamedTemporaryFile(suffix=".mp4") as video, mock.patch.object(subprocess, "run", spy):
            video.write(b"fausse video")
            video.flush()
            result = self.client.upload_video("act_1", video.name)
        self.assertEqual(result, {"id": "42"})
        self.assertNotIn(FAKE_TOKEN, " ".join(seen["cmd"]))
        self.assertIn(FAKE_TOKEN, seen["input"])
        self.assertIn(FAKE_TOKEN.encode(), Handler.calls[0])
        self.assertIn(b"fausse video", Handler.calls[0])


class Safety(unittest.TestCase):
    def test_real_mode_needs_variables(self):
        env = {k: v for k, v in os.environ.items() if k not in TOKEN_ENV}
        with mock.patch.dict(os.environ, env, clear=True), self.assertRaises(SystemExit) as stop:
            meta_launch.main(["--config", str(EXAMPLE), "status"])
        self.assertIn("META_ACCESS_TOKEN", str(stop.exception))

    def test_simulation_flags_refused_in_real_mode(self):
        with self.assertRaises(SystemExit):
            meta_launch.main(["--config", str(EXAMPLE), "--fresh", "status"])


if __name__ == "__main__":
    unittest.main()
