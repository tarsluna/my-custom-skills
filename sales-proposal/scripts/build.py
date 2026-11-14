#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construit la proposition commerciale (HTML, une page par diapo) à partir d'un
contenu JSON et d'un thème JSON. Aucune dépendance, Python 3.9+.

    python3 scripts/build.py chemin/proposition.json [--theme chemin/theme.json] [--out dossier]

Le script s'arrête avec la liste des problèmes si le contenu ne respecte pas le cadre
(diapo manquante, texte à trous, prix plein absent, offre personnelle dans le PDF...).
"""
import argparse
import html
import json
import os
import re
import sys

ORDRE_DEFAUT = [
    "couverture", "presentation", "situation", "objectifs",
    "preuve_chiffres", "preuve_cas", "preuve_autres", "temoignages",
    "deroule", "systeme", "offre", "garantie", "devis", "suite",
]
LABELS_DEFAUT = {
    "presentation": "Vous", "situation": "Votre situation", "objectifs": "Vos objectifs",
    "preuve_chiffres": "Nos résultats", "preuve_cas": "Nos résultats · études de cas",
    "preuve_autres": "Nos résultats · suite", "temoignages": "Nos résultats · ce que disent nos clients",
    "deroule": "Le déroulé", "systeme": "Le système", "offre": "L’offre",
    "garantie": "La garantie, par écrit", "suite": "La suite",
}
SANS_NUMERO = {"couverture", "devis"}
MAX_BRIQUES = 4  # lignes de l'offre ; le système en montre 3 + « continu », le devis 4 + la garantie
SOMBRES = {"couverture", "temoignages", "garantie", "suite"}
# Écrits avec chr() et jamais en caractère littéral : un nettoyage des sources (copier-coller,
# anonymisation, « remplacer les espaces bizarres ») les effaçait sans bruit, et les titres se
# coupaient entre le chiffre et l'unité (« 3 / mois »).
NBSP, FINE = chr(0xA0), chr(0x202F)  # insécable, fine insécable
UNITES = ("jours?|mois|heures?|h|minutes?|min|semaines?|ans?|avis|clients?|prospects?|contacts?|"
          "personnes?|chantiers?|rendez-vous|demandes?|pages?")
TROUS = re.compile(r"\[[^\]]{0,80}\]|\bTODO\b|\bXXX\b|lorem ipsum|à compléter", re.I)


class Erreur(Exception):
    pass


def typo(s):
    """Typographie française : apostrophes, espaces insécables, milliers."""
    s = s.replace("'", "’")
    s = re.sub(r"(\d) (\d{3})(?!\d)", r"\1" + FINE + r"\2", s)
    s = re.sub(r" ([:;!?»€%])", NBSP + r"\1", s)
    s = s.replace("« ", "«" + NBSP)
    s = re.sub(r"(\d) (%s)\b" % UNITES, r"\1" + NBSP + r"\2", s)
    return s


def t(s):
    """Texte du JSON vers HTML. **gras d'accent** et retours à la ligne acceptés."""
    if s is None:
        return ""
    s = typo(html.escape(str(s), quote=False))
    s = re.sub(r"\*\*(.+?)\*\*", r'<em class="b">\1</em>', s)
    return s.replace("\n", "<br>")


def textes(obj):
    """Toutes les chaînes d'un objet, pour les contrôles."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            for x in textes(v):
                yield x
    elif isinstance(obj, list):
        for v in obj:
            for x in textes(v):
                yield x


def remplacer(obj, fn):
    if isinstance(obj, str):
        return fn(obj)
    if isinstance(obj, dict):
        return dict((k, remplacer(v, fn)) for k, v in obj.items())
    if isinstance(obj, list):
        return [remplacer(v, fn) for v in obj]
    return obj


ESPACES = r"[ \t" + chr(0xA0) + chr(0x202F) + "]"
MONTANT = re.compile(r"^[\d\s.,€$£%" + chr(0xA0) + chr(0x202F) + r"]+(ht|ttc)?$", re.I)


def contient(chaines, cherche):
    """Vrai si « cherche » figure dans l'une des chaînes.
    Un montant (« 3 000 € ») se compare sur ses chiffres, quels que soient les espaces :
    il est reconnu dans « 3 000,00 € HT », pas dans « 13 000 € ».
    Une expression (« sans engagement », « 20 demandes ») se compare mot à mot :
    « 20 demandes » n'est pas reconnu dans « dans un rayon de 20 km ». Une première version
    cherchait chaque nombre seul et bloquait ainsi une proposition parfaitement propre."""
    if isinstance(chaines, str):
        chaines = [chaines]
    if MONTANT.match(cherche.strip()) and re.search(r"\d", cherche):
        chiffres = re.sub(r"\D", "", cherche)
        motif = re.compile(r"(?<!\d)(?<!\d%s)%s(?!%s?\d)" % (ESPACES, (ESPACES + "?").join(chiffres), ESPACES))
    else:
        mots = [re.escape(m) for m in re.split(r"\s+", cherche.strip().replace(chr(0xA0), " ").replace(chr(0x202F), " "))]
        motif = re.compile(r"(?<!\w)%s(?!\w)" % (ESPACES + "+").join(mots), re.I)
    return any(motif.search(c) for c in chaines)


# ---------------------------------------------------------------- thème

THEME_DEFAUT = {
    "couleurs": {"fond": "#F2F0EB", "carte": "#FAF9F6", "encre": "#141414",
                 "discret": "#6A6A66", "sombre": "#151515", "accent": "#C9A46A"},
    "polices": {
        "titres": {"famille": "Helvetica Neue", "secours": "Arial, sans-serif"},
        "texte": {"famille": "Helvetica Neue", "secours": "Arial, sans-serif"},
        "mono": {"famille": "Menlo", "secours": "Consolas, monospace"},
    },
    "titres": {"graisse": 400, "graisse_couverture": 300},
    "logo": {"texte": ""},
    "rayon": 14,
    "page": {"largeur": 1280, "hauteur": 720},
}


def fusion(base, extra):
    out = dict(base)
    for k, v in (extra or {}).items():
        out[k] = fusion(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def css(theme, theme_dir, out_dir):
    c, p = theme["couleurs"], theme["polices"]
    faces = []
    for cle in ("titres", "texte", "mono"):
        f = p[cle]
        if f.get("fichier"):
            chemin = os.path.join(theme_dir, f["fichier"])
            if not os.path.exists(chemin):
                raise Erreur("thème : police introuvable : %s" % chemin)
            rel = os.path.relpath(chemin, out_dir).replace(os.sep, "/")
            faces.append("@font-face{font-family:'%s';src:url('%s');font-weight:%s}" % (
                f["famille"], rel, f.get("graisses", "100 900")))
    generiques = ("system-ui", "sans-serif", "serif", "monospace", "ui-monospace", "ui-sans-serif", "ui-serif")

    def pile(cle):
        famille = p[cle]["famille"]
        nom = famille if famille in generiques else "'%s'" % famille
        return "%s,%s" % (nom, p[cle].get("secours", "sans-serif"))
    w, h = theme["page"]["largeur"], theme["page"]["hauteur"]
    return "\n".join(faces) + """
:root{--fond:%(fond)s;--carte:%(carte)s;--encre:%(encre)s;--discret:%(discret)s;--sombre:%(sombre)s;--accent:%(accent)s;
--trait:color-mix(in srgb,var(--encre) 20%%,transparent);--trait-s:color-mix(in srgb,var(--fond) 22%%,transparent);
--clair-s:color-mix(in srgb,var(--fond) 66%%,transparent);
--titres:%(titres)s;--texte:%(texte)s;--mono:%(mono)s;--rayon:%(rayon)spx}
@page{size:%(w)spx %(h)spx;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--fond);color:var(--encre);font-family:var(--texte);-webkit-print-color-adjust:exact;print-color-adjust:exact}
.slide{width:%(w)spx;height:%(h)spx;position:relative;overflow:hidden;padding:54px 72px 58px;page-break-after:always;break-after:page;background:var(--fond);display:flex;flex-direction:column}
.slide.dark{background:var(--sombre);color:var(--fond)}
.slide.papier{background:var(--carte)}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:34px}
.logo{height:15px;width:auto;display:block}.logo path{fill:currentColor}
.logo-texte{font-family:var(--titres);font-weight:300;font-size:19px;letter-spacing:.34em;text-transform:uppercase}
.mono{font-family:var(--mono);font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--discret)}
.dark .mono{color:var(--clair-s)}
.foot{position:absolute;left:72px;right:72px;bottom:26px;display:flex;justify-content:space-between}
h1{font-family:var(--titres);font-weight:%(g_couv)s;font-size:72px;line-height:1.03;letter-spacing:-.01em}
h2{font-family:var(--titres);font-weight:%(g_titre)s;font-size:42px;line-height:1.08;max-width:1040px}
h3{font-family:var(--titres);font-weight:500;font-size:21px;line-height:1.2}
p{font-size:16.5px;line-height:1.5}
em.b{font-style:normal;font-weight:600}
.dark em.b,.card.noir em.b,.bandeau em.b{color:var(--accent);font-weight:inherit}
.sous{font-size:23px;line-height:1.45;margin-top:26px;color:var(--discret);max-width:900px}.dark .sous{color:var(--clair-s)}
.petit{font-size:14.5px;line-height:1.45;color:var(--discret)}.dark .petit{color:var(--clair-s)}
.grow{flex:1}.centre{display:flex;flex-direction:column;justify-content:center}
.grid{display:grid;gap:18px}
.card{background:var(--carte);border:1px solid var(--trait);border-radius:var(--rayon);padding:22px 22px 20px}
.dark .card{background:color-mix(in srgb,var(--fond) 5%%,transparent);border-color:var(--trait-s)}
.card.noir{background:var(--encre);color:var(--fond);border-color:var(--encre)}
.card.noir .mono,.card.noir .petit{color:var(--clair-s)}
.card.noir li{border-color:var(--trait-s)}.card.noir li:before{background:var(--fond)}
ul{list-style:none}
li{font-size:16px;line-height:1.45;padding:9px 0 9px 20px;position:relative;border-top:1px solid var(--trait)}
li:first-child{border-top:0}
li:before{content:"";position:absolute;left:0;top:18px;width:8px;height:1px;background:var(--encre)}
.num{font-family:var(--titres);font-weight:300;font-size:58px;line-height:1;letter-spacing:-.02em}
.tag{display:inline-block;font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;border:1px solid currentColor;border-radius:999px;padding:7px 13px}
.pas{border-top:1px solid var(--encre);padding-top:14px}.dark .pas{border-color:var(--fond)}
.pas .mono{color:var(--encre)}.dark .pas .mono{color:var(--accent)}
.bandeau{background:var(--encre);color:var(--fond);border-radius:var(--rayon);padding:18px 24px;display:flex;justify-content:space-between;align-items:center;gap:30px}
.fleche{font-family:var(--titres);font-weight:300;font-size:30px;color:var(--discret);align-self:center;text-align:center}
figure img{display:block;width:100%%;height:236px;object-fit:cover;border-radius:calc(var(--rayon) - 2px)}
figcaption{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--discret);margin-top:8px}
.fait{border-top:1px solid var(--encre);padding-top:10px}
.fait b{font-family:var(--titres);font-weight:400;font-size:26px;display:block;line-height:1.1}
.fait span{font-size:13.5px;color:var(--discret)}
table{width:100%%;border-collapse:collapse}
td,th{text-align:left;vertical-align:top;padding:11px 12px 11px 0;border-top:1px solid var(--trait);font-size:14.5px;line-height:1.42}
th{font-family:var(--mono);font-weight:400;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--discret);border-top:0;padding-bottom:8px}
td.n{font-family:var(--mono);font-size:12px;color:var(--discret);width:44px;padding-top:14px}
td.nom{font-family:var(--titres);font-weight:500;font-size:18px;width:250px;line-height:1.2}
td.d,th.d{text-align:right;padding-right:0;white-space:nowrap}
tr.total td{border-top:1.5px solid var(--encre)}
.devis td{padding-top:8px;padding-bottom:8px}
.citation{font-family:var(--titres);font-weight:300;font-size:42px;line-height:1.14;max-width:1100px}
""" % dict(c, titres=pile("titres"), texte=pile("texte"), mono=pile("mono"), rayon=theme["rayon"],
           w=w, h=h, g_couv=theme["titres"]["graisse_couverture"], g_titre=theme["titres"]["graisse"])


def logo(theme, theme_dir, meta):
    l = theme.get("logo") or {}
    if l.get("svg"):
        chemin = os.path.join(theme_dir, l["svg"])
        if not os.path.exists(chemin):
            raise Erreur("thème : logo introuvable : %s" % chemin)
        with open(chemin, encoding="utf-8") as f:
            svg = f.read()
        svg = re.sub(r"<\?xml.*?\?>|<!DOCTYPE.*?>", "", svg, flags=re.S).strip()
        return re.sub(r"<svg\b", '<svg class="logo"', svg, count=1)
    return '<span class="logo-texte">%s</span>' % t(l.get("texte") or meta.get("agence", ""))


# ---------------------------------------------------------------- diapos

def grille(n, maxi=4):
    return "grid-template-columns:repeat(%d,1fr)" % max(1, min(n, maxi))


def taille_valeur(v, grand=86):
    n = len(str(v))
    return grand if n <= 4 else int(grand * 0.8) if n <= 6 else int(grand * 0.62)


def d_couverture(d, x):
    tags = "".join('<span class="tag">%s</span>' % t(v) for v in d.get("pastilles", []))
    return ('<div class="top">%s<span class="mono">%s</span></div>'
            '<div class="grow centre"><span class="mono" style="margin-bottom:22px">%s</span>'
            '<h1>%s</h1><p class="sous">%s</p>'
            '<div style="display:flex;gap:12px;margin-top:38px;flex-wrap:wrap">%s</div></div>'
            '<div class="foot"><span class="mono">%s</span><span class="mono">%s</span></div>') % (
        x["logo"], t(d.get("mention", "")), t(d["surtitre"]), t(d["titre"]), t(d["sous_titre"]), tags,
        t(d.get("pied_gauche", "")), t(x["meta"].get("site", "")))


def d_presentation(d, x):
    photos = d.get("photos", [])
    figs = "".join('<figure><img src="%s" alt=""><figcaption>%s</figcaption></figure>' % (
        html.escape(p["fichier"]), t(p.get("legende", ""))) for p in photos)
    faits = "".join('<div class="fait"><b>%s</b><span>%s</span></div>' % (t(f["valeur"]), t(f["texte"]))
                    for f in d.get("faits", []))
    out = x["top"] + (
        '<div style="display:flex;gap:48px;align-items:flex-end"><div style="flex:1">'
        '<span class="mono">%s</span><h2 style="font-size:46px;margin-top:10px">%s</h2></div>'
        '<p style="width:470px;font-size:16px;color:var(--discret)">%s</p></div>') % (
        t(d.get("surtitre", "")), t(d["slogan"]), t(d["phrase"]))
    if figs:
        out += '<div class="grid" style="gap:14px;margin-top:24px;%s">%s</div>' % (grille(len(photos)), figs)
    if faits:
        out += '<div class="grid" style="gap:14px;margin-top:22px;%s">%s</div>' % (grille(len(d["faits"])), faits)
    return out + x["foot"]


def d_situation(d, x):
    cols = ""
    for c in d["colonnes"]:
        items = "".join("<li>%s</li>" % t(i) for i in c["items"])
        cols += '<div class="card%s"><span class="mono">%s</span><ul style="margin-top:12px">%s</ul></div>' % (
            " noir" if c.get("sombre") else "", t(c["titre"]), items)
    return x["top"] + "<h2>%s</h2>" % t(d["titre"]) + (
        '<div class="grid" style="gap:22px;margin-top:34px;%s">%s</div>' % (grille(len(d["colonnes"]), 3), cols)) + x["foot"]


def d_objectifs(d, x):
    cartes = "".join(
        '<div class="card"><span class="mono">%02d</span><h3 style="margin:10px 0 8px">%s</h3><p class="petit">%s</p></div>' % (
            i + 1, t(o["titre"]), t(o.get("texte", ""))) for i, o in enumerate(d["items"]))
    return x["top"] + "<h2>%s</h2>" % t(d["titre"]) + (
        '<div class="grid" style="margin-top:34px;%s">%s</div>' % (grille(len(d["items"]), 3), cartes)) + x["foot"]


def d_preuve_chiffres(d, x):
    taille = min(taille_valeur(c["valeur"]) for c in d["chiffres"])  # une seule taille sur la ligne
    ch = "".join(
        '<div class="pas"><div class="num" style="font-size:%dpx">%s</div><p style="margin-top:14px">%s</p></div>' % (
            taille, t(c["valeur"]), t(c["texte"])) for c in d["chiffres"])
    out = x["top"] + "<h2>%s</h2>" % t(d["titre"]) + (
        '<div class="grid" style="gap:22px;margin-top:44px;%s">%s</div><div class="grow"></div>' % (grille(len(d["chiffres"])), ch))
    n = d.get("note")
    if n:
        out += ('<div class="card" style="margin-bottom:22px;display:flex;gap:26px;align-items:center">'
                '<span class="mono" style="width:190px">%s</span><p style="flex:1;font-size:15.5px">%s</p></div>') % (
            t(n.get("label", "")), t(n["texte"]))
    return out + x["foot"]


def d_preuve_cas(d, x):
    cas = "".join(
        '<div class="card"><span class="mono" style="display:block;min-height:2.9em">%s · %s</span><div class="num" style="margin-top:8px">%s</div>'
        '<p style="margin-top:6px;font-weight:600">%s</p>'
        '<hr style="height:1px;border:0;background:var(--trait);margin:14px 0"><p class="petit" style="font-size:13.5px">%s</p></div>' % (
            t(c["client"]), t(c["metier"]), t(c["valeur"]), t(c["resultat"]), t(c.get("detail", ""))) for c in d["cas"])
    out = x["top"] + '<h2 style="font-size:38px">%s</h2>' % t(d["titre"]) + (
        '<div class="grid" style="margin-top:26px;%s">%s</div><div class="grow"></div>' % (grille(len(d["cas"])), cas))
    b = d.get("bandeau")
    if b:
        out += ('<div class="bandeau" style="margin-bottom:22px"><p style="font-size:16px;opacity:.82">%s</p>'
                '<p style="font-size:16px"><em class="b">%s</em></p></div>') % (t(b.get("gauche", "")), t(b.get("droite", "")))
    return out + x["foot"]


def d_preuve_autres(d, x):
    res = "".join(
        '<div class="card"><div class="num">%s</div><p style="margin-top:8px">%s</p>'
        '<span class="mono" style="display:block;margin-top:12px">%s</span></div>' % (
            t(r["valeur"]), t(r["texte"]), t(r.get("client", ""))) for r in d["resultats"])
    out = x["top"] + '<h2 style="font-size:38px">%s</h2>' % t(d["titre"]) + (
        '<div class="grid" style="margin-top:28px;%s">%s</div>' % (grille(len(d["resultats"]), 3), res))
    if d.get("note"):
        out += '<p class="petit" style="margin-top:20px;max-width:1000px">%s</p>' % t(d["note"])
    return out + x["foot"]


def d_temoignages(d, x):
    cit = "".join(
        '<div class="card"><p>«%s%s%s»</p><span class="mono" style="display:block;margin-top:14px;color:var(--accent)">%s</span></div>' % (
            NBSP, t(c["texte"]), NBSP, t(c["auteur"])) for c in d["citations"])
    return x["top"] + '<h2 style="font-size:38px">%s</h2>' % t(d["titre"]) + (
        '<div class="grid" style="margin-top:26px;%s">%s</div>' % (grille(len(d["citations"]), 3), cit)) + x["foot"]


def d_deroule(d, x):
    et = "".join(
        '<div class="pas"><span class="mono">%s</span><h3 style="margin:10px 0 8px">%s</h3><p class="petit" style="font-size:13.5px">%s</p></div>' % (
            t(e["quand"]), t(e["titre"]), t(e["texte"])) for e in d["etapes"])
    out = x["top"] + "<h2>%s</h2>" % t(d["titre"]) + (
        '<div class="grid" style="gap:20px;margin-top:40px;%s">%s</div><div class="grow"></div>' % (grille(len(d["etapes"]), 6), et))
    enc = d.get("encadres") or []
    if enc:
        out += '<div class="grid" style="margin-bottom:22px;gap:22px;%s">%s</div>' % (grille(len(enc), 3), "".join(
            '<div class="card"><span class="mono">%s</span><p style="margin-top:8px;font-size:15.5px">%s</p></div>' % (
                t(e["label"]), t(e["texte"])) for e in enc))
    return out + x["foot"]


def d_systeme(d, x):
    blocs = []
    for i, b in enumerate(d["briques"]):
        blocs.append('<div class="card"><span class="mono">%s</span><h3 style="margin:10px 0 8px">%s</h3><p class="petit" style="font-size:13.5px">%s</p></div>' % (
            t(b.get("numero", "%02d" % (i + 1))), t(b["titre"]), t(b["texte"])))
    a = d.get("arrivee")
    if a:
        blocs.append('<div class="card noir"><span class="mono">%s</span><h3 style="margin:10px 0 8px">%s</h3><p class="petit" style="font-size:13.5px">%s</p></div>' % (
            t(a.get("label", "Vous")), t(a["titre"]), t(a["texte"])))
    colonnes = " 34px ".join(["1fr"] * len(blocs))
    flux = '<div class="fleche">→</div>'.join(blocs)
    out = x["top"] + "<h2>%s</h2>" % t(d["titre"]) + (
        '<div style="display:grid;grid-template-columns:%s;margin-top:34px">%s</div>' % (colonnes, flux))
    c = d.get("continu")
    if c:
        out += ('<div class="card" style="margin-top:22px;display:flex;gap:28px;align-items:center">'
                '<div style="width:250px"><span class="mono">%s</span><h3 style="margin-top:8px">%s</h3></div>'
                '<p class="petit" style="flex:1;font-size:15px">%s</p></div>') % (t(c.get("label", "")), t(c["titre"]), t(c["texte"]))
    return out + x["foot"]


def d_offre(d, x):
    col = d.get("colonnes", ["Ce que nous installons", "Ce que nous faisons", "Ce que vous y gagnez"])
    lignes = "".join(
        '<tr><td class="n">%s</td><td class="nom">%s</td><td>%s</td><td>%s</td></tr>' % (
            t(l.get("numero", "%02d" % (i + 1))), t(l["nom"]), t(l["fait"]), t(l["gain"])) for i, l in enumerate(d["lignes"]))
    inc = d.get("inclus")
    if inc:
        lignes += '<tr><td class="n">+</td><td class="nom">%s</td><td colspan="2">%s</td></tr>' % (t(inc["nom"]), t(inc["texte"]))
    p = d["prix"]
    return x["top"] + '<h2 style="font-size:38px">%s</h2>' % t(d["titre"]) + (
        '<table style="margin-top:20px"><tr><th></th><th>%s</th><th>%s</th><th>%s</th></tr>%s</table><div class="grow"></div>'
        '<div class="bandeau" style="margin-bottom:22px"><p style="font-size:15.5px;max-width:640px;opacity:.8">%s</p>'
        '<div style="text-align:right"><div class="num" style="font-size:46px;white-space:nowrap">%s <span style="font-size:22px">%s</span></div>'
        '<span class="mono" style="color:var(--accent)">%s</span></div></div>') % (
        t(col[0]), t(col[1]), t(col[2]), lignes, t(p.get("note", "")), t(p["montant"]), t(p.get("unite", "")), t(p.get("legende", ""))) + x["foot"]


def d_garantie(d, x):
    faits = "".join(
        '<div class="card"><div class="num">%s%s</div><p style="margin-top:10px">%s</p></div>' % (
            t(f["valeur"]), (' <span style="font-size:24px">%s</span>' % t(f["unite"])) if f.get("unite") else "", t(f["texte"]))
        for f in d.get("faits", []))
    out = x["top"] + '<p class="citation">%s</p>' % t(d["citation"])
    if faits:
        out += '<div class="grid" style="gap:22px;margin-top:34px;%s">%s</div>' % (grille(len(d["faits"]), 3), faits)
    if d.get("definition"):
        out += '<p class="petit" style="margin-top:22px;max-width:1040px">%s</p>' % t(d["definition"])
    return out + x["foot"]


def d_devis(d, x):
    def bloc(titre, lignes, droite=False):
        corps = "<br>".join(("<b>%s</b>" % t(l)) if i == 0 else t(l) for i, l in enumerate(lignes))
        return '<div%s><span class="mono">%s</span><p style="margin-top:6px;font-size:14.5px">%s</p></div>' % (
            ' style="text-align:right"' if droite else "", titre, corps)
    lignes = "".join('<tr><td style="font-weight:600;width:300px">%s</td><td>%s</td><td class="d">%s</td></tr>' % (
        t(l["nom"]), t(l.get("detail", "")), t(l.get("montant", "Inclus"))) for l in d["lignes"])
    tot = d["total"]
    lignes += ('<tr class="total"><td style="font-family:var(--titres);font-size:20px;font-weight:500">%s</td>'
               '<td style="padding-top:16px">%s</td><td class="d" style="font-family:var(--titres);font-size:24px;font-weight:500">%s</td></tr>') % (
        t(tot["nom"]), t(tot.get("detail", "")), t(tot["montant"]))
    apres = " · ".join("%s : %s" % (l["nom"], l["montant"]) for l in d.get("apres_total", []))
    apres = ('<p style="text-align:right;font-size:13.5px;margin-top:-2px">%s</p>' % t(apres)) if apres else ""
    mentions = "<br>".join('<b style="color:var(--encre)">%s%s:</b> %s' % (t(m["label"]), NBSP, t(m["texte"])) for m in d.get("mentions", []))
    entete = "Devis n° %s · émis le %s" % (d["numero"], d["emis_le"])
    if d.get("valable_jusqu_au"):
        entete += " · valable jusqu’au %s" % d["valable_jusqu_au"]
    return ('<div class="top" style="margin-bottom:22px">%s<span class="mono">%s</span></div>'
            '<div style="display:flex;justify-content:space-between;gap:40px">%s%s%s</div>'
            '<table class="devis" style="margin-top:14px"><tr><th>Désignation</th><th>Détail</th><th class="d">%s</th></tr>%s</table>%s'
            '<div style="display:flex;gap:28px;margin-top:10px"><p class="petit" style="flex:1;font-size:12.5px">%s</p>'
            '<div style="width:360px;border:1px solid var(--trait);border-radius:10px;padding:10px 14px;height:92px"><span class="mono">%s</span></div></div>') % (
        x["logo"], t(entete), bloc("Émetteur", d["emetteur"]), bloc("Client", d["client"]), bloc("Objet", d["objet"], True),
        t(d.get("colonne_montant", "Montant HT")), lignes, apres, mentions,
        t(d.get("signature", "Bon pour accord · date et signature"))) + x["foot"]


def d_suite(d, x):
    et = "".join(
        '<div class="pas"><span class="mono">%d</span><h3 style="margin:10px 0 8px">%s</h3><p class="petit" style="font-size:15px">%s</p></div>' % (
            i + 1, t(e["titre"]), t(e["texte"])) for i, e in enumerate(d["etapes"]))
    return ('<div class="top">%s<span class="mono">%s</span></div>'
            '<div class="grow centre"><h1 style="font-size:64px">%s</h1>'
            '<div class="grid" style="gap:22px;margin-top:44px;%s">%s</div></div>'
            '<div class="foot"><span class="mono">%s</span><span class="mono">%s</span></div>') % (
        x["logo"], x["label"], t(d["titre"]), grille(len(d["etapes"]), 3), et,
        t(d.get("pied_gauche", "")), t(x["meta"].get("site", "")))


RENDUS = {
    "couverture": d_couverture, "presentation": d_presentation, "situation": d_situation,
    "objectifs": d_objectifs, "preuve_chiffres": d_preuve_chiffres, "preuve_cas": d_preuve_cas,
    "preuve_autres": d_preuve_autres, "temoignages": d_temoignages, "deroule": d_deroule,
    "systeme": d_systeme, "offre": d_offre, "garantie": d_garantie, "devis": d_devis, "suite": d_suite,
}


# ---------------------------------------------------------------- contrôles

def controler(data, ordre, base_dir):
    err, avert = [], []
    for cle in ordre:
        if cle not in RENDUS:
            err.append("ordre : diapo inconnue « %s »" % cle)
        elif cle not in data:
            err.append("diapo « %s » : absente du contenu" % cle)
    for cle in ordre:
        for s in textes(data.get(cle, {})):
            m = TROUS.search(s)
            if m:
                err.append("diapo « %s » : texte à trou « %s »" % (cle, m.group(0)))
    ctl = data.get("controles", {})
    prix = ctl.get("prix_plein")
    if prix:
        for cle in ("couverture", "offre", "devis"):
            if cle in ordre and not contient(list(textes(data.get(cle, {}))), prix):
                err.append("diapo « %s » : le prix plein « %s » n’y figure pas" % (cle, prix))
    elif len(ordre) > 1:
        avert.append("controles.prix_plein absent : la cohérence du prix n’est pas vérifiée")
    for interdit in ctl.get("interdits_dans_le_pdf", []):
        for cle in ordre:
            if contient(list(textes(data.get(cle, {}))), interdit):
                err.append("diapo « %s » : « %s » ne doit pas apparaître dans le PDF (offre personnelle = mail)" % (cle, interdit))
    # Au format 1280 x 720, cinq briques débordent dès qu'un texte fait deux lignes : quatre au plus.
    briques = [("offre", "lignes", MAX_BRIQUES), ("systeme", "briques", MAX_BRIQUES - 1),
               ("devis", "lignes", MAX_BRIQUES + 1)]
    for cle, champ, maxi in briques:
        n = len(data.get(cle, {}).get(champ) or []) if cle in ordre else 0
        if n > maxi:
            avert.append("diapo « %s » : %d %s pour %d au plus ; au-delà, la page déborde dès qu’un texte passe sur deux lignes (regrouper des briques)" % (cle, n, champ, maxi))
    for p in (data.get("presentation", {}).get("photos") or []) if "presentation" in ordre else []:
        if not os.path.exists(os.path.join(base_dir, p["fichier"])):
            err.append("présentation : photo introuvable : %s" % p["fichier"])
    if "devis" in ordre:
        dv = data.get("devis", {})
        bas = " ".join(textes(dv.get("mentions", [])) ) + " " + " ".join(textes(dv.get("apres_total", [])))
        if len(dv.get("emetteur", [])) < 3:
            avert.append("devis : identité de l’émetteur incomplète (raison sociale, numéro d’immatriculation, adresse)")
        if len(dv.get("client", [])) < 2:
            avert.append("devis : adresse du client absente")
        if not re.search(r"TVA|TTC", bas):
            avert.append("devis : régime de TVA non indiqué (ligne « apres_total » ou mention)")
        if not re.search(r"règlement|paiement|payable", bas, re.I):
            avert.append("devis : modalités de paiement absentes")
    avert.extend(restes_de_l_exemple(data, ordre))
    if "garantie" in ordre and re.match(r"\s*[«\"“]", data.get("garantie", {}).get("citation", "")):
        avert.append("garantie : la phrase s’écrit sans guillemets")
    return err, avert


def restes_de_l_exemple(data, ordre):
    """Signale les phrases restées identiques à l'exemple fourni : un chiffre ou une promesse
    de l'exemple qui part chez un prospect est une erreur difficile à voir à la relecture."""
    chemin = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "template", "proposition.exemple.json")
    if not os.path.exists(chemin):
        return []
    with open(chemin, encoding="utf-8") as f:
        exemple = json.load(f)
    if data.get("meta", {}).get("prospect") == exemple.get("meta", {}).get("prospect"):
        return []
    connus = set(x for x in textes(exemple) if len(x) >= 30)
    out = []
    for cle in ordre:
        for x in textes(data.get(cle, {})):
            if x in connus:
                out.append("diapo « %s » : phrase identique à l’exemple, à vérifier : « %s »" % (cle, x[:70]))
    return out[:12]


def construire(data, theme, base_dir, theme_dir, out_dir):
    ordre = data.get("ordre") or ORDRE_DEFAUT
    err, avert = controler(data, ordre, base_dir)
    if err:
        raise Erreur("\n".join(err))
    meta = data.get("meta", {})
    pages = dict((cle, i + 1) for i, cle in enumerate(ordre))

    def renvoi(s):
        def rep(m):
            if m.group(1) not in pages:
                raise Erreur("renvoi {page:%s} : diapo absente de l’ordre" % m.group(1))
            return str(pages[m.group(1)])
        return re.sub(r"\{page:(\w+)\}", rep, s)
    data = dict(data)
    for cle in ordre:  # seules les diapos présentes sont lues : un devis seul ignore les autres
        data[cle] = remplacer(data[cle], renvoi)

    lg = logo(theme, theme_dir, meta)
    total, sections, n, precedent = len(ordre), [], 0, None
    for i, cle in enumerate(ordre):
        d = data[cle]
        label = d.get("label") or LABELS_DEFAUT.get(cle, "")
        if cle not in SANS_NUMERO:
            base = label.split(" · ")[0]
            if base != precedent:
                n += 1
                precedent = base
            label = "%02d · %s" % (n, t(label))
        droite = t(d.get("mention") or meta.get("entete", ""))
        x = {
            "meta": meta, "logo": lg, "label": label,
            "top": '<div class="top"><span class="mono">%s</span><span class="mono">%s</span></div>' % (label, droite),
            "foot": '<div class="foot"><span class="mono">%s</span><span class="mono">%d / %d</span></div>' % (
                t(meta.get("pied", meta.get("agence", ""))), i + 1, total),
        }
        try:
            corps = RENDUS[cle](d, x)
        except KeyError as e:
            raise Erreur("diapo « %s » : champ manquant %s" % (cle, e))
        classes = "slide" + (" dark" if cle in SOMBRES else "") + (" papier" if cle == "devis" else "")
        sections.append('<!-- %d · %s -->\n<section class="%s" data-cle="%s">%s</section>' % (i + 1, cle, classes, cle, corps))
    titre = "%s · Proposition %s" % (meta.get("agence", ""), meta.get("prospect", ""))
    page = ('<!doctype html>\n<html lang="%s">\n<head>\n<meta charset="utf-8">\n<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n\n%s\n\n</body>\n</html>\n') % (
        meta.get("langue", "fr"), t(titre), css(theme, theme_dir, out_dir), "\n\n".join(sections))
    return page, avert


def main(argv=None):
    ap = argparse.ArgumentParser(description="Construit la proposition commerciale en HTML.")
    ap.add_argument("contenu", help="fichier JSON du contenu")
    ap.add_argument("--theme", help="fichier JSON du thème (défaut : theme.json à côté du contenu, sinon thème neutre)")
    ap.add_argument("--out", help="dossier de sortie (défaut : dossier du contenu)")
    a = ap.parse_args(argv)
    base_dir = os.path.dirname(os.path.abspath(a.contenu))
    out_dir = os.path.abspath(a.out) if a.out else base_dir
    theme_path = a.theme or os.path.join(base_dir, "theme.json")
    theme, theme_dir = THEME_DEFAUT, base_dir
    if os.path.exists(theme_path):
        with open(theme_path, encoding="utf-8") as f:
            theme = fusion(THEME_DEFAUT, json.load(f))
        theme_dir = os.path.dirname(os.path.abspath(theme_path))
    elif a.theme:
        sys.exit("thème introuvable : %s" % a.theme)
    try:
        with open(a.contenu, encoding="utf-8") as f:
            data = json.load(f)
        page, avert = construire(data, theme, base_dir, theme_dir, out_dir)
    except Erreur as e:
        sys.exit("CONSTRUCTION REFUSÉE\n%s" % e)
    os.makedirs(out_dir, exist_ok=True)
    nom = data.get("meta", {}).get("sortie", "proposition")
    sortie = os.path.join(out_dir, nom + ".html")
    with open(sortie, "w", encoding="utf-8") as f:
        f.write(page)
    for w in avert:
        print("ATTENTION : " + w)
    print(sortie)
    return 0


if __name__ == "__main__":
    sys.exit(main())
