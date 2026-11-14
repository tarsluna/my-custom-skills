#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline checks for the template: it builds, it refuses bad decks, and it rebrands cleanly."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / 'template'
sys.path.insert(0, str(TEMPLATE))
from vsl import VISUALS  # noqa: E402


class Deck:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / 'deck'
        shutil.copytree(TEMPLATE, self.dir, ignore=shutil.ignore_patterns('node_modules', 'dist', '__pycache__'))

    def build(self, *args):
        return subprocess.run([sys.executable, 'build.py', *args], cwd=self.dir, capture_output=True, text=True)

    def append(self, code):
        with open(self.dir / 'content.py', 'a', encoding='utf8') as f:
            f.write('\n' + code + '\n')

    def brand(self, **changes):
        path = self.dir / 'brand.json'
        data = json.loads(path.read_text(encoding='utf8'))
        data.update(changes)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf8')
        return data

    def close(self):
        self.tmp.cleanup()


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.deck = Deck()
        self.addCleanup(self.deck.close)

    def refused(self, needle, *args):
        r = self.deck.build(*args)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(needle, r.stderr)

    def test_starter_builds_every_output(self):
        r = self.deck.build()
        self.assertEqual(r.returncode, 0, r.stderr)
        dist = self.deck.dir / 'dist'
        for name in ['votre-marque-vsl.html', 'script.html', 'script.md', 'script.txt', 'deck.json', 'verification/content-report.json']:
            self.assertTrue((dist / name).exists(), name)
        html = (dist / 'votre-marque-vsl.html').read_text(encoding='utf8')
        self.assertNotRegex(html.split('id="deck-data"')[0], r'__[A-Z_]+__')
        self.assertNotIn('http://', html.split('id="deck-data"')[0].replace('http://www.w3.org', ''))

    def test_starter_shows_every_visual_without_warning(self):
        r = self.deck.build()
        report = json.loads(r.stdout)
        self.assertEqual(sorted(report['visuals_used']), sorted(VISUALS))
        self.assertEqual(report['warnings'], [])

    def test_catalogues_match(self):
        player = (TEMPLATE / 'player.html').read_text(encoding='utf8')
        block = player[player.index('const VIS={'):player.index('function visual(v)')]
        drawn = set(re.findall(r'^ (\w+):\(', block, re.M))
        self.assertEqual(drawn, set(VISUALS))

    def test_player_has_no_brand_color(self):
        player = (TEMPLATE / 'player.html').read_text(encoding='utf8')
        without_print = re.sub(r'@media print\{.*?\}\}', '', player, flags=re.S)
        self.assertEqual(re.findall(r'#[0-9a-fA-F]{6}\b', without_print), [])

    def test_palettes_pass_and_recolor(self):
        palettes = json.loads((TEMPLATE / 'palettes.json').read_text(encoding='utf8'))
        for name, colors in palettes.items():
            self.deck.brand(colors=colors)
            r = self.deck.build()
            self.assertEqual(r.returncode, 0, name + r.stderr)
            html = (self.deck.dir / 'dist/votre-marque-vsl.html').read_text(encoding='utf8')
            self.assertIn('--accent:' + colors['accent'], html)

    def test_english_interface(self):
        self.deck.brand(lang='en')
        r = self.deck.build()
        self.assertEqual(r.returncode, 0, r.stderr)
        deck = json.loads((self.deck.dir / 'dist/deck.json').read_text(encoding='utf8'))
        self.assertEqual(deck['parts'][1], '2. Old way vs new way')
        self.assertEqual(deck['ui']['presenter'], 'Presenter')

    def test_low_contrast_refused(self):
        colors = json.loads((TEMPLATE / 'brand.json').read_text(encoding='utf8'))['colors']
        colors['accent'] = '#1a1a1a'
        self.deck.brand(colors=colors)
        self.refused('contrast too low')

    def test_missing_part_block_refused(self):
        self.deck.append("INTRO = [x for x in INTRO if x['role'] != 'picture']")
        self.refused('missing block "picture"')

    def test_mechanism_must_end_part_two(self):
        self.deck.append("OLD_NEW = OLD_NEW[::-1]")
        self.refused('must be "new"')

    def test_faq_stage_required(self):
        self.deck.append("FAQ[0]['stages'][1] = []")
        self.refused('all four stages')

    def test_offer_price_guarantee_required(self):
        self.deck.append("FAQ[3]['kind'] = ''")
        self.refused('kind="price"')

    def test_cta_question_required(self):
        self.deck.brand(cta=dict(button='X', question='une autre question ?', reminder='Réservez'))
        self.refused('word for word')

    def test_argument_after_cta_refused(self):
        self.deck.append("PROOF[0]['slides'].insert(0, s('Un dernier argument.', 'Argument.'))")
        self.refused('only proof after the CTA')

    def test_uninventoried_figure_refused_then_allowed_in_draft(self):
        self.deck.append("PROOF[0]['slides'][0]['stats'] = [('999', 'clients')]")
        self.refused('not in proof_inventory')
        self.assertEqual(self.deck.build('--draft').returncode, 0)

    def test_figure_needs_context(self):
        self.deck.append("PROOF[0]['slides'][0]['context'] = ''")
        self.refused('missing context')

    def test_placeholder_refused_then_allowed_in_draft(self):
        self.deck.append("FAQ[0]['stages'][3] = [s('[PROOF NEEDED: un résultat réel]', 'À venir.')]")
        self.refused('placeholder left')
        r = self.deck.build('--draft')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads(r.stdout)['draft'])

    def test_long_slide_refused(self):
        self.deck.append("INTRO[0]['slides'][0]['text'] = ' '.join(['mot'] * 28)")
        self.refused('one idea per slide')

    def test_banned_word_refused(self):
        self.deck.brand(banned=['salle'])
        self.refused('banned expression')

    def test_label_too_long_refused(self):
        self.deck.append("OLD_NEW[0]['slides'][1]['v']['items'][0] = 'Un libellé bien trop long'")
        self.refused('the drawing holds')

    def test_too_many_words_refused(self):
        self.deck.append("FAQ[2]['stages'][2] += [s(' '.join(['mot'] * 20), 'Mot.') for _ in range(6)]")
        self.refused('at most')

    def test_short_script_warns_instead_of_forcing_padding(self):
        self.deck.brand(format='long')
        self.deck.append("FAQ.append(dict(FAQ[0], kind='extra'))")
        r = self.deck.build()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(any('Do not pad' in w for w in json.loads(r.stdout)['warnings']))

    def test_phone_label_must_fit_its_circle(self):
        self.deck.append("OLD_NEW[3]['slides'][4]['v']['big'] = 'Monday'")
        self.refused('the drawing holds')

    def test_unknown_visual_refused(self):
        self.deck.append("OLD_NEW[0]['slides'][1]['v'] = v('hologram')")
        self.refused('unknown visual')


if __name__ == '__main__':
    unittest.main()
