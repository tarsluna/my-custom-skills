#!/usr/bin/env python3
"""Tests hors ligne : aucun modèle, aucune clé, aucune vidéo. numpy, opencv et whisper ne sont pas requis."""
import contextlib
import importlib
import io
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
import wave

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import caps  # noqa: E402
import common  # noqa: E402
import cut  # noqa: E402
import extract_audio  # noqa: E402
import finish  # noqa: E402
import gen  # noqa: E402
import init_project  # noqa: E402
import rerender  # noqa: E402
import topup  # noqa: E402

SCRIPTS = ["caps", "common", "cut", "extract_audio", "faces", "finish", "gen", "init_project", "rerender", "seams", "show", "text_pass", "topup", "track", "transcribe"]


def quiet(fn, *a):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        fn(*a)
    return out.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name) / "projet"
        quiet(init_project.main, [str(self.root)])
        common.write_json(self.root / "work/takes.json", {"T01": {"file": "a.mov", "w": 3840, "h": 2160, "dur": 40.0}})
        common.write_json(self.root / "work/faces.json", {"T01": {"cx": .5, "cy": .4, "h": .3, "n": 8}})
        self.P = common.Project(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def make_ad(self, plan=None, ad="A01"):
        A = self.root / "ads" / ad
        (A / "build").mkdir(parents=True)
        common.write_json(A / "edit.json", {"id": ad, "segments": [{"take": "T01", "s": 1.0, "e": 11.0}, {"take": "T01", "s": 12.0, "e": 26.0}]})
        common.write_json(A / "build/timeline.json", {"duration": 24.0, "frames": 720, "seams": [10.0], "segments": []})
        for n in ("voice.wav", "vert.mp4", "horiz.mp4", "bg.mp4"):
            (A / "build" / n).write_bytes(b"x")
        common.write_json(A / "captions.json", [{"t0": t, "t1": t + 1.5, "text": f"groupe {i}"} for i, t in enumerate(range(0, 24, 2))])
        common.write_json(A / "plan.json", plan or {"id": ad, "h_target": "Salle de sport", "h_goal": "14 jours d'essai offerts", "hook_d": 3,
                                                     "keywords": [{"t": 8.0, "d": 1.5, "text": "14 JOURS <OFFERTS>"}]})
        return A


class Imports(unittest.TestCase):
    def test_every_script_imports(self):
        for name in SCRIPTS:
            importlib.import_module(name)


class Crops(Base):
    def test_4k_matches_the_values_used_in_production(self):
        v, h, b = self.P.crops("T01")
        self.assertEqual((v[0], v[1]), (1012, 1800))
        self.assertEqual((h[0], h[1]), (3000, 1688))
        self.assertEqual((b[0], b[1]), (1214, 2160))

    def test_every_crop_stays_inside_the_frame(self):
        for w, h in ((3840, 2160), (1920, 1080), (1080, 1920), (1280, 720)):
            for cx, cy in ((0, 0), (1, 1), (.5, .4)):
                self.P._takes = {"T01": {"file": "a.mov", "w": w, "h": h, "dur": 1}}
                self.P._faces = {"T01": {"cx": cx, "cy": cy}}
                for cw, ch, x, y in self.P.crops("T01"):
                    self.assertTrue(0 <= x and x + cw <= w and 0 <= y and y + ch <= h, (w, h, cx, cy, cw, ch, x, y))
                    self.assertEqual((cw % 2, ch % 2), (0, 0))

    def test_missing_face_falls_back_to_center(self):
        self.P._faces = {}
        self.assertEqual(len(self.P.crops("T01")), 3)


class Takes(Base):
    def test_screen_recordings_are_excluded(self):
        rushes = self.root / "rushes"
        for n in ("prise1/camera.mov", "prise1/ecran.mov", "prise2/camera.mov", "_Programme.mp4", "notes.txt"):
            (rushes / n).parent.mkdir(parents=True, exist_ok=True)
            (rushes / n).write_bytes(b"x")
        found = [p.relative_to(rushes).as_posix() for p in extract_audio.discover(rushes, self.P.config["takes"]["include"], self.P.config["takes"]["exclude"])]
        self.assertEqual(found, ["prise1/camera.mov", "prise2/camera.mov"])


class Captions(unittest.TestCase):
    def words(self, text):
        return [{"text": w, "start": i * .3, "end": i * .3 + .25} for i, w in enumerate(text.split())]

    def test_limits(self):
        groups = caps.group_words(self.words("un deux trois quatre cinq six sept extraordinairement huit neuf"), 10)
        for g in groups:
            self.assertLessEqual(len(g["text"].split()), 4)

    def test_chars_and_punctuation(self):
        groups = caps.group_words(self.words("vraiment extraordinaire aujourd'hui, non ? oui."), 10, max_chars=22)
        self.assertTrue(all(len(g["text"]) <= 22 for g in groups))
        self.assertFalse(any(g["text"].endswith((",", ".")) for g in groups))
        self.assertTrue(any(g["text"].endswith("?") for g in groups))

    def test_elision_tokens_are_merged(self):
        words = caps.merge_tokens([(" l", 0, .1), ("'essai", .1, .4), (" gratuit", .4, .8)])
        self.assertEqual([w["text"] for w in words], ["l'essai", "gratuit"])


class Compose(Base):
    def build(self):
        quiet(gen.main, [str(self.root), "A01"])
        A = self.root / "ads/A01"
        return (A / "hf-v/index.html").read_text(encoding="utf-8"), (A / "hf-h/index.html").read_text(encoding="utf-8")

    def test_defaults(self):
        self.make_ad()
        v, h = self.build()
        self.assertIn("Bricolage Grotesque", v)
        self.assertIn("font:800 72px/1.08", v)
        self.assertIn('data-duration="1.500"', v)
        self.assertNotIn('class="hh"', v)
        self.assertNotIn('class="clip hv"', v)
        self.assertIn('class="hh"', h)
        self.assertIn("Salle de sport", h)
        self.assertNotIn('id="sfx', v)

    def test_text_is_escaped(self):
        self.make_ad()
        v, _ = self.build()
        self.assertIn("&lt;OFFERTS&gt;", v)
        self.assertNotIn("<OFFERTS>", v)

    def test_style_file_drives_the_look(self):
        self.make_ad()
        s = common.read_json(self.root / "style.json")
        s["colors"]["caption"] = "#ABCDEF"
        s["captions"]["size"] = 64
        s["font"]["tracking_em"] = -0.01
        common.write_json(self.root / "style.json", s)
        self.P = common.Project(self.root)
        v, _ = self.build()
        self.assertIn("color:#ABCDEF", v)
        self.assertIn("800 64px", v)
        self.assertIn("letter-spacing:-0.01em", v)

    def test_vertical_hook_is_opt_in(self):
        self.make_ad()
        s = common.read_json(self.root / "style.json")
        s["hook"]["on_vertical"] = True
        common.write_json(self.root / "style.json", s)
        v, _ = self.build()
        self.assertIn('class="clip hv"', v)

    def test_goal_only_and_plain_hook(self):
        self.make_ad({"id": "A01", "hook": "Un hook simple", "keywords": []})
        _, h = self.build()
        self.assertIn("Un hook simple", h)

    def test_zooms_land_on_seams_and_never_leave_long_shots(self):
        self.make_ad()
        c = gen.Composer(common.Project(self.root), "A01")
        beats = c.beats()
        self.assertIn(10.0, beats)
        gaps = [b - a for a, b in zip(beats, beats[1:] + [c.D])]
        self.assertLessEqual(max(gaps), 6.2)

    def test_captions_never_overlap_keywords(self):
        self.make_ad()
        c = gen.Composer(common.Project(self.root), "A01")
        for a, b, _ in c.kept_captions():
            self.assertTrue(b <= 8.0 or a >= 9.5)

    def test_long_keyword_breaks_into_lines(self):
        self.assertEqual(gen.kw_lines("SANS\nENGAGEMENT"), ["SANS", "ENGAGEMENT"])
        self.assertGreater(len(gen.kw_lines("PREMIER COURS OFFERT")), 1)
        self.assertEqual(gen.kw_lines("OFFERT"), ["OFFERT"])

    def test_warnings_flag_long_captions(self):
        self.make_ad()
        common.write_json(self.root / "ads/A01/captions.json", [{"t0": 0, "t1": 1, "text": "un deux trois quatre cinq"}])
        self.assertTrue(gen.Composer(common.Project(self.root), "A01").warnings())

    @unittest.skipUnless(shutil.which("ffprobe"), "ffprobe absent")
    def test_user_sounds_are_wired_when_present(self):
        self.make_ad()
        with wave.open(str(self.root / "sounds/thump.mp3"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(8000)
            w.writeframes(b"\0\0" * 2400)
        v, _ = self.build()
        self.assertIn('src="assets/sfx/thump.mp3"', v)
        self.assertNotIn("whoosh.mp3", v)
        self.assertTrue((self.root / "ads/A01/hf-v/assets/sfx/thump.mp3").exists())


class Topup(unittest.TestCase):
    def test_rules(self):
        plan = {"hook_d": 3, "keywords": [{"t": 10.0, "d": 1.5, "text": "DÉJÀ"}]}
        caps_ = [{"t0": 1.0, "t1": 2, "text": "tout au début"}, {"t0": 10.5, "t1": 11, "text": "trop proche"}, {"t0": 20.0, "t1": 21, "text": "essai gratuit"}]
        added, refused = topup.add_keywords(plan, caps_, [[1.0, "début", "A"], [10.5, "proche", "B"], [20.2, "essai", "ESSAI GRATUIT"], [40, "absent", "C"]])
        self.assertEqual([k["text"] for k in added], ["ESSAI GRATUIT"])
        self.assertEqual(sorted(r[1].split(" ")[0] for r in refused), ["introuvable", "pendant", "trop"])
        self.assertEqual([k["text"] for k in plan["keywords"]], ["DÉJÀ", "ESSAI GRATUIT"])


class DryRun(Base):
    def test_cut_plans_without_writing(self):
        A = self.make_ad()
        shutil.rmtree(A / "build")
        out = quiet(cut.main, [str(self.root), "A01", "--dry-run"])
        self.assertIn("2 segments", out)
        self.assertFalse((A / "build").exists())

    def test_filtergraph_handles_mirror_flag(self):
        self.make_ad()
        res = cut.resolve([{"take": "T01", "s": 1, "e": 2}])
        self.assertNotIn("hflip", ";".join(cut.graph(self.P, res, None)[1]))
        self.P.config["mirror"] = True
        res = cut.resolve([{"take": "T01", "s": 1, "e": 2}])
        self.assertIn("hflip", ";".join(cut.graph(self.P, res, None)[1]))

    def test_inverted_segment_is_refused(self):
        with self.assertRaises(SystemExit):
            cut.resolve([{"take": "T01", "s": 5, "e": 2}])

    def test_every_tool_runs_dry(self):
        self.make_ad()
        p = str(self.root)
        modules = {name: importlib.import_module(name) for name in ("extract_audio", "transcribe", "text_pass", "faces", "cut", "seams", "caps", "gen", "track", "finish", "rerender")}
        quiet(modules["extract_audio"].main, [p, "--dry-run"])
        quiet(modules["transcribe"].main, [p, "--dry-run"])
        quiet(modules["text_pass"].main, [p, "--dry-run"])
        quiet(modules["text_pass"].main, [p, "--ad", "A01", "--dry-run"])
        quiet(modules["faces"].main, [p, "--dry-run"])
        for tool in ("cut", "seams", "caps", "gen", "track"):
            quiet(modules[tool].main, [p, "A01", "--dry-run"])
        quiet(modules["finish"].main, [p, "A01", "demo", "--dry-run"])

    def test_topup_dry_run_leaves_the_plan_alone(self):
        A = self.make_ad()
        before = (A / "plan.json").read_text(encoding="utf-8")
        additions = self.root / "ajouts.json"
        common.write_json(additions, {"A01": [[14.0, "groupe 7", "ESSAI GRATUIT"]]})
        out = quiet(topup.main, [str(self.root), str(additions), "--dry-run"])
        self.assertIn("ESSAI GRATUIT", out)
        self.assertEqual((A / "plan.json").read_text(encoding="utf-8"), before)

    def test_render_command_is_pinned(self):
        cmd = [str(c) for c in finish.render_cmd(self.P, "hf", "o.mp4")]
        self.assertIn("hyperframes@0.9.23", cmd)
        self.assertNotIn("--skill=hyperframes", cmd)

    def test_rerender_dry_lists_ads(self):
        self.make_ad()
        out = quiet(rerender.main, [str(self.root), "--dry-run"])
        self.assertIn("1 pubs", out)

    def test_project_required(self):
        with self.assertRaises(SystemExit):
            common.Project(self.root / "absent")

    def test_partial_style_keeps_defaults(self):
        (self.root / "style.json").write_text(json.dumps({"colors": {"caption": "#111111"}}), encoding="utf-8")
        s = common.Project(self.root).style
        self.assertEqual(s["colors"]["caption"], "#111111")
        self.assertEqual(s["captions"]["size"], 72)


if __name__ == "__main__":
    unittest.main()
