# -*- coding: utf-8 -*-
"""Contrôles hors ligne du générateur : python3 -m unittest discover -s tests"""
import copy
import json
import os
import sys
import unittest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "scripts"))
import build  # noqa: E402

GABARIT = os.path.join(RACINE, "template")
with open(os.path.join(GABARIT, "proposition.exemple.json"), encoding="utf-8") as _f:
    EXEMPLE = json.load(_f)

FINE, INS = chr(0x202F), chr(0xA0)


def construire(data):
    return build.construire(data, build.THEME_DEFAUT, GABARIT, GABARIT, GABARIT)


class Cadre(unittest.TestCase):
    def test_exemple_complet(self):
        page, avert = construire(copy.deepcopy(EXEMPLE))
        self.assertEqual(page.count("<section "), 14)
        self.assertEqual(avert, [])
        ordre = [l.split("· ")[1].split(" ")[0] for l in page.splitlines() if l.startswith("<!-- ")]
        self.assertEqual(ordre, build.ORDRE_DEFAUT)

    def test_preuve_avant_offre_et_garantie_apres(self):
        o = build.ORDRE_DEFAUT
        self.assertLess(o.index("temoignages"), o.index("offre"))
        self.assertLess(o.index("presentation"), o.index("situation"))
        self.assertLess(o.index("offre"), o.index("garantie"))
        self.assertLess(o.index("garantie"), o.index("devis"))

    def test_renvoi_de_page(self):
        page, _ = construire(copy.deepcopy(EXEMPLE))
        self.assertIn("Il est en page 12.", page)
        self.assertNotIn("{page:", page)

    def test_typographie(self):
        # Les attendus sont construits avec chr() : une première version du test comparait
        # deux chaînes identiques, parce que le même nettoyage avait aussi vidé l'attendu.
        self.assertEqual(build.typo("3 000 € en 3 mois : oui"),
                         "3" + FINE + "000" + INS + "€ en 3" + INS + "mois" + INS + ": oui")
        self.assertEqual(build.t("l'offre **garantie**"), 'l’offre <em class="b">garantie</em>')
        page, _ = construire(copy.deepcopy(EXEMPLE))
        self.assertIn("3" + INS + "mois", page)
        self.assertIn("3" + FINE + "000" + INS + "€", page)

    def test_typographie_change_vraiment_le_texte(self):
        """Garde-fou contre le piège du nettoyage : si les insécables disparaissent du
        générateur, typo() rend son entrée telle quelle et ce test casse."""
        self.assertNotEqual(build.typo("3 mois"), "3 mois")
        self.assertNotEqual(build.typo("3 000"), "3 000")
        self.assertEqual(ord(build.NBSP), 0xA0)
        self.assertEqual(ord(build.FINE), 0x202F)

    def test_montants_et_expressions(self):
        self.assertTrue(build.contient("Total 3 000,00 € HT", "3 000 €"))
        self.assertTrue(build.contient("3" + FINE + "000" + INS + "€", "3 000 €"))
        self.assertFalse(build.contient("Total 13 000 €", "3 000 €"))
        self.assertFalse(build.contient("11 000 €", "1 000 €"))
        self.assertFalse(build.contient("plus de 10 000 €", "1 000 €"))
        self.assertTrue(build.contient(["Essai, mois 1", "1 000 €"], "1 000 €"))
        self.assertTrue(build.contient("offre Sans  engagement", "sans engagement"))
        self.assertFalse(build.contient("dans un rayon de 20 km", "20 demandes"))
        self.assertTrue(build.contient("20 demandes garanties", "20 demandes"))

    def test_l_exemple_contient_le_piege_du_rayon(self):
        """L'exemple interdit « 20 demandes » dans le PDF et parle d'un rayon de 20 km :
        il doit se construire sans erreur."""
        self.assertIn("20 demandes", EXEMPLE["controles"]["interdits_dans_le_pdf"])
        self.assertTrue(any("20 km" in s for s in build.textes(EXEMPLE["presentation"])))
        construire(copy.deepcopy(EXEMPLE))

    def test_police_du_systeme(self):
        theme = build.fusion(build.THEME_DEFAUT, {"polices": {"texte": {"famille": "system-ui", "secours": "sans-serif"}}})
        feuille = build.css(theme, GABARIT, GABARIT)
        self.assertIn("--texte:system-ui,sans-serif", feuille)


class Refus(unittest.TestCase):
    def refuse(self, data, mot):
        with self.assertRaises(build.Erreur) as c:
            construire(data)
        self.assertIn(mot, str(c.exception))

    def test_offre_personnelle_dans_le_pdf(self):
        d = copy.deepcopy(EXEMPLE)
        d["offre"]["prix"]["note"] = "Premier mois à 1 000 €."
        self.refuse(d, "ne doit pas apparaître")

    def test_garantie_de_l_offre_personnelle_dans_le_pdf(self):
        d = copy.deepcopy(EXEMPLE)
        d["suite"]["pied_gauche"] = "20 demandes garanties dès le premier mois"
        self.refuse(d, "ne doit pas apparaître")

    def test_prix_plein_absent(self):
        d = copy.deepcopy(EXEMPLE)
        d["devis"]["total"]["montant"] = "2 900,00 € HT"
        self.refuse(d, "prix plein")

    def test_texte_a_trou(self):
        d = copy.deepcopy(EXEMPLE)
        d["garantie"]["definition"] = "Une demande qualifiée est [à définir]."
        self.refuse(d, "texte à trou")

    def test_diapo_manquante(self):
        d = copy.deepcopy(EXEMPLE)
        del d["objectifs"]
        self.refuse(d, "absente du contenu")

    def test_photo_introuvable(self):
        d = copy.deepcopy(EXEMPLE)
        d["presentation"]["photos"][0]["fichier"] = "photos/absente.jpg"
        self.refuse(d, "photo introuvable")


class Variantes(unittest.TestCase):
    def test_devis_seul(self):
        with open(os.path.join(GABARIT, "devis-offre-personnelle.exemple.json"), encoding="utf-8") as f:
            d = json.load(f)
        page, avert = construire(d)
        self.assertEqual(page.count("<section "), 1)
        self.assertIn("1 / 1", page)
        self.assertEqual(avert, [])
        self.assertNotEqual(d["meta"]["sortie"], EXEMPLE["meta"]["sortie"])

    def test_reste_de_l_exemple_signale(self):
        d = copy.deepcopy(EXEMPLE)
        d["meta"]["prospect"] = "Autre Société"
        _, avert = construire(d)
        self.assertTrue(any("identique à l’exemple" in a for a in avert))

    def test_cinq_briques_signalees(self):
        d = copy.deepcopy(EXEMPLE)
        d["offre"]["lignes"].append(dict(d["offre"]["lignes"][0], nom="Cinquième brique"))
        _, avert = construire(d)
        self.assertTrue(any("offre" in a and "4 au plus" in a for a in avert))

    def test_devis_sans_tva_ni_reglement(self):
        d = copy.deepcopy(EXEMPLE)
        del d["devis"]["apres_total"]
        d["devis"]["mentions"] = [{"label": "Conditions", "texte": "engagement de 3 mois."}]
        _, avert = construire(d)
        self.assertTrue(any("TVA" in a for a in avert))
        self.assertTrue(any("paiement" in a for a in avert))

    def test_devis_incomplet_averti(self):
        d = copy.deepcopy(EXEMPLE)
        d["devis"]["emetteur"] = ["Votre Agence"]
        _, avert = construire(d)
        self.assertTrue(any("identité" in a for a in avert))

    def test_garantie_sans_guillemets(self):
        d = copy.deepcopy(EXEMPLE)
        d["garantie"]["citation"] = "« " + d["garantie"]["citation"] + " »"
        _, avert = construire(d)
        self.assertTrue(any("guillemets" in a for a in avert))


class LigneDeCommande(unittest.TestCase):
    def test_build_ecrit_le_html(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            dossier = os.path.join(tmp, "prospect")
            shutil.copytree(GABARIT, dossier)
            code = build.main([os.path.join(dossier, "proposition.exemple.json")])
            self.assertEqual(code, 0)
            sortie = os.path.join(dossier, EXEMPLE["meta"]["sortie"] + ".html")
            with open(sortie, encoding="utf-8") as f:
                self.assertEqual(f.read().count('class="slide'), 14)


if __name__ == "__main__":
    unittest.main()
