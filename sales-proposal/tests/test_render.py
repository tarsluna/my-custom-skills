# -*- coding: utf-8 -*-
"""Rendu PDF de l'exemple dans un vrai navigateur.

Se saute proprement si Node ou Playwright manquent. Pour le lancer :
    npm i playwright && npx playwright install chromium        (hors du dépôt de préférence)
ou PLAYWRIGHT_MODULE=/chemin/node_modules/playwright [CHROME_PATH=/chemin/vers/chrome]
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "scripts"))
import build  # noqa: E402

RENDER = os.path.join(RACINE, "scripts", "render.cjs")
GABARIT = os.path.join(RACINE, "template")


def playwright_disponible():
    node = shutil.which("node")
    if not node:
        return None, "node absent"
    pistes = [os.environ.get("PLAYWRIGHT_MODULE"), "playwright", "playwright-core"]
    for p in [x for x in pistes if x]:
        r = subprocess.run([node, "-e", "require(%r)" % p], cwd=os.path.dirname(RENDER),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0:
            return node, ""
    return None, "Playwright introuvable (voir PLAYWRIGHT_MODULE dans le README)"


NODE, RAISON = playwright_disponible()


@unittest.skipUnless(NODE, "rendu PDF sauté : %s" % RAISON)
class Rendu(unittest.TestCase):
    def rendre(self, nom_contenu):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        dossier = os.path.join(tmp, "prospect")
        shutil.copytree(GABARIT, dossier)
        self.assertEqual(build.main([os.path.join(dossier, nom_contenu)]), 0)
        with open(os.path.join(dossier, nom_contenu), encoding="utf-8") as f:
            html = json.load(f)["meta"]["sortie"] + ".html"
        r = subprocess.run([NODE, RENDER, os.path.join(dossier, html)], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, universal_newlines=True, timeout=180)
        if r.returncode == 3:  # Playwright ou navigateur absent : render.cjs l'explique
            self.skipTest("rendu PDF sauté : " + (r.stderr.strip().splitlines() or [""])[0])
        self.assertEqual(r.returncode, 0, r.stderr)
        return dossier, html[:-5]

    def test_exemple_14_pages_sans_debordement(self):
        dossier, nom = self.rendre("proposition.exemple.json")
        self.assertTrue(os.path.exists(os.path.join(dossier, nom + ".pdf")))
        self.assertEqual(len([f for f in os.listdir(os.path.join(dossier, "pages")) if f.endswith(".png")]), 14)

    def test_devis_offre_personnelle_une_page(self):
        dossier, nom = self.rendre("devis-offre-personnelle.exemple.json")
        self.assertTrue(os.path.exists(os.path.join(dossier, nom + ".pdf")))
        self.assertEqual(len(os.listdir(os.path.join(dossier, "pages"))), 1)


if __name__ == "__main__":
    unittest.main()
