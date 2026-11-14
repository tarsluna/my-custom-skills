"""Passage vers un formulaire instantane, sans cle ni reseau : python3 -m unittest discover -s tests"""
import contextlib
import copy
import io
import json
import os
import pathlib
import socket
import subprocess
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import lead_form  # noqa: E402

EXAMPLES = ROOT / "examples" / "paysagistes" / "formulaire"
FORM = "000000000900"
TOKEN_ENV = ("META_ACCESS_TOKEN", "META_AD_ACCOUNT", "META_PAGE_ID", "META_PIXEL_ID")


def load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def old_ads():
    return load("pubs-ancienne-campagne.json")["data"]


class Payload(unittest.TestCase):
    def test_simple_video_points_to_form_and_keeps_everything_else(self):
        source = load("pub-video.json")["creative"]
        before = copy.deepcopy(source)
        payload = lead_form.form_creative(source, FORM)
        video = payload["object_story_spec"]["video_data"]
        self.assertEqual(video["call_to_action"], {"type": "LEARN_MORE", "value": {"lead_gen_form_id": FORM, "link": "http://fb.me/"}})
        self.assertEqual(video["video_id"], source["object_story_spec"]["video_data"]["video_id"])
        self.assertEqual(video["image_hash"], source["object_story_spec"]["video_data"]["image_hash"])
        self.assertEqual(payload["asset_feed_spec"], source["asset_feed_spec"])
        self.assertEqual(len(payload["asset_feed_spec"]["bodies"]), 5)
        self.assertEqual(len(payload["asset_feed_spec"]["titles"]), 5)
        self.assertEqual(payload["url_tags"], source["url_tags"])
        self.assertEqual(payload["degrees_of_freedom_spec"], source["degrees_of_freedom_spec"])
        self.assertNotIn("pepiniere-exemple.test", json.dumps(payload))
        self.assertEqual(source, before)

    def test_placement_video_uses_labels_by_name_and_call_to_actions(self):
        source = old_ads()[1]["creative"]
        before = copy.deepcopy(source)
        feed = lead_form.form_creative(source, FORM)["asset_feed_spec"]
        self.assertTrue(all(label.keys() == {"name"} for v in feed["videos"] for label in v["adlabels"]))
        self.assertTrue(all(rule["video_label"].keys() == {"name"} for rule in feed["asset_customization_rules"]))
        self.assertNotIn("call_to_action_types", feed)
        self.assertEqual(feed["call_to_actions"], [{"type": "LEARN_MORE", "value": {"lead_gen_form_id": FORM}}])
        self.assertEqual(feed["link_urls"], [{"website_url": "http://fb.me/"}])
        for key in lead_form.READ_ONLY_FEED_KEYS:
            self.assertNotIn(key, feed)
        self.assertEqual(source, before)

    def test_image_ad_is_refused(self):
        with self.assertRaises(ValueError):
            lead_form.form_creative({"object_story_spec": {"page_id": "1", "link_data": {"image_hash": "x"}}}, FORM)


class CreativeDiff(unittest.TestCase):
    def setUp(self):
        self.old = load("pub-video.json")["creative"]
        self.new = lead_form.form_creative(self.old, FORM)

    def levels(self, found):
        return [level for level, _ in found]

    def test_faithful_copy_has_no_gap(self):
        self.assertEqual(lead_form.creative_diff(self.old, self.new, FORM), [])

    def test_other_video_id_is_only_a_warning(self):
        self.new["object_story_spec"]["video_data"]["video_id"] = "000000000299"
        self.assertEqual(self.levels(lead_form.creative_diff(self.old, self.new, FORM)), ["A VERIFIER"])

    def test_empty_creative_from_ads_manager_duplicate_is_caught(self):
        empty = {"object_story_spec": {"page_id": "000000000001"}}
        found = lead_form.creative_diff(self.old, empty, FORM)
        self.assertIn("ECART", self.levels(found))
        self.assertTrue(any("vide" in message for _, message in found))

    def test_missing_title_and_wrong_form_are_gaps(self):
        self.new["asset_feed_spec"]["titles"].pop()
        self.new["object_story_spec"]["video_data"]["call_to_action"]["value"]["lead_gen_form_id"] = "autre"
        messages = [m for level, m in lead_form.creative_diff(self.old, self.new, FORM) if level == "ECART"]
        self.assertTrue(any(m.startswith("titres") for m in messages), messages)
        self.assertTrue(any(m.startswith("formulaire") for m in messages), messages)

    def test_site_creative_is_not_a_form(self):
        found = lead_form.creative_diff(self.old, self.old, FORM)
        self.assertIn(("ECART", "la nouvelle creative ne pointe vers aucun formulaire"), found)


class FormCheck(unittest.TestCase):
    def test_example_form_is_caught(self):
        problems = lead_form.form_problems(load("formulaire-a-corriger.json"), "fr_FR")
        self.assertTrue(any("en_US" in p for p in problems))
        self.assertTrue(any("Full name" in p for p in problems))
        self.assertTrue(any("se chevauchent" in p and "250 000" in p for p in problems))
        self.assertEqual(len(problems), 4, problems)

    def test_corrected_form_passes(self):
        form = load("formulaire-a-corriger.json")
        form["locale"] = "fr_FR"
        labels = {"full_name": "Nom et prénom", "email": "E-mail", "phone_number": "Numéro de téléphone"}
        for question in form["questions"]:
            question["label"] = labels.get(question["key"], question["label"])
        form["questions"][3]["options"][2]["value"] = "300 001 € à 500 000 €"
        self.assertEqual(lead_form.form_problems(form, "fr_FR"), [])

    def test_ranges(self):
        self.assertEqual(lead_form.overlapping(["Moins de 50 000 €", "50 000 € à 100 000 €", "Plus de 100 000 €"]), [])
        self.assertEqual(len(lead_form.overlapping(["0 - 50 000 €", "50 000 - 100 000 €"])), 1)
        self.assertEqual(len(lead_form.overlapping(["50k-100k", "80k-150k"])), 1)
        self.assertEqual(lead_form.overlapping(["Oui", "Non"]), [])


class AdsetDiff(unittest.TestCase):
    def test_hand_made_adset_is_flagged(self):
        found = lead_form.adset_diff(load("adset-site.json"), load("adset-formulaire.json"))
        gaps = [m for level, m in found if level == "ECART"]
        signals = [m for level, m in found if level == "A SIGNALER"]
        self.assertTrue(any("Audience Network" in m for m in gaps))
        self.assertTrue(any(m.startswith("pays") for m in signals))
        self.assertTrue(any(m.startswith("age_min") for m in signals))

    def test_interests_break_broad_targeting(self):
        new = load("adset-site.json")
        new["targeting"]["flexible_spec"] = [{"interests": [{"id": "1", "name": "Jardinage"}]}]
        self.assertTrue(any("interets" in m for level, m in lead_form.adset_diff(load("adset-site.json"), new) if level == "ECART"))

    def test_aligned_adsets_only_show_expected_changes(self):
        new = load("adset-site.json")
        new.update({"optimization_goal": "LEAD_GENERATION", "destination_type": "ON_AD"})
        self.assertEqual({level for level, _ in lead_form.adset_diff(load("adset-site.json"), new)}, {"INFO"})


class FakeClient:
    """Imite Meta en memoire, pour suivre le chemin reel sans reseau."""

    def __init__(self, objects=None, listings=None):
        self.objects = objects or {}
        self.listings = listings or {}
        self.posts = []
        self.next = 1

    def _id(self):
        self.next += 1
        return "new%03d" % self.next

    def get(self, path, **params):
        if path in self.listings:
            return {"data": self.listings[path]}
        return self.objects.get(path, {"error": {"message": "inconnu", "code": 100}})

    def post(self, path, params, retry_network=True):
        self.posts.append((path, params))
        if path.endswith("/copies"):
            return {"copied_adset_id": self._id()}
        if path.endswith("/adcreatives"):
            oid = self._id()
            self.objects[oid] = dict(params, id=oid)
            return {"id": oid}
        if path.endswith("/ads"):
            oid = self._id()
            self.objects[oid] = {"id": oid, "name": params["name"], "status": params["status"], "creative": self.objects[params["creative"]["creative_id"]]}
            return {"id": oid}
        return {"success": True}


class Cli(unittest.TestCase):
    def setUp(self):
        env = {k: v for k, v in os.environ.items() if k not in TOKEN_ENV}
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        for target, name in ((socket.socket, "connect"), (subprocess, "run")):
            guard = mock.patch.object(target, name, side_effect=AssertionError("appel reseau a blanc"))
            guard.start()
            self.addCleanup(guard.stop)

    def cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = lead_form.main(list(args))
        self.output = out.getvalue()
        return code

    def test_dry_run_prints_payload_without_token(self):
        self.assertEqual(self.cli("--dry-run", "copy-ad", "--file", str(EXAMPLES / "pub-video.json"), "--form-id", FORM, "--adset", "000000000402"), 0)
        self.assertIn('"lead_gen_form_id": "%s"' % FORM, self.output)
        self.assertIn("status=PAUSED", self.output)
        self.assertIn("controle 0 ecart", self.output)

    def test_dry_run_skips_refused_ads(self):
        self.cli("--dry-run", "copy-ad", "--file", str(EXAMPLES / "pubs-ancienne-campagne.json"), "--form-id", FORM, "--adset", "000000000402")
        self.assertIn("2 a copier, 0 deja la, 1 refusee(s)", self.output)

    def test_real_mode_needs_token(self):
        with self.assertRaises(SystemExit) as stop:
            self.cli("copy-ad", "--file", str(EXAMPLES / "pub-video.json"), "--form-id", FORM, "--adset", "2")
        self.assertIn("META_ACCESS_TOKEN", str(stop.exception))

    def test_real_path_creates_paused_ads_once(self):
        ads = old_ads()
        target = "000000000402"
        fake = FakeClient(objects={a["id"]: a for a in ads}, listings={"OLD/ads": ads, "%s/ads" % target: []})
        os.environ["META_AD_ACCOUNT"] = "000000000000"
        with mock.patch.object(lead_form, "make_client", return_value=fake):
            self.assertEqual(self.cli("copy-ad", "--from-adset", "OLD", "--form-id", FORM, "--adset", target), 0)
            created = [p for path, p in fake.posts if path.endswith("/ads")]
            self.assertEqual([p["status"] for p in created], ["PAUSED", "PAUSED"])
            self.assertTrue(all(path.startswith("act_000000000000/") for path, _ in fake.posts))
            self.assertIn("1 refusee(s)", self.output)
            fake.listings["%s/ads" % target] = [{"id": "x", "name": p["name"]} for p in created]
            self.cli("copy-ad", "--from-adset", "OLD", "--form-id", FORM, "--adset", target)
        self.assertEqual(len([p for path, p in fake.posts if path.endswith("/ads")]), 2)
        self.assertIn("2 deja la", self.output)

    def test_copy_adset_without_ads_paused_then_renamed(self):
        fake = FakeClient(objects={"SRC": {"id": "SRC", "name": "Fait main", "campaign_id": "CAMP"}}, listings={"CAMP/adsets": []})
        with mock.patch.object(lead_form, "make_client", return_value=fake):
            self.cli("copy-adset", "--adset", "SRC", "--name", "Copie renommee")
        (copy_path, copy_params), (rename_path, rename_params) = fake.posts
        self.assertEqual(copy_path, "SRC/copies")
        self.assertEqual(copy_params, {"deep_copy": False, "status_option": "PAUSED"})
        self.assertEqual(rename_params, {"name": "Copie renommee"})

    def test_check_form_stops_on_problems(self):
        with self.assertRaises(SystemExit) as stop:
            self.cli("check-form", "--file", str(EXAMPLES / "formulaire-a-corriger.json"))
        self.assertIn("ne se modifie plus", str(stop.exception))


if __name__ == "__main__":
    unittest.main()
