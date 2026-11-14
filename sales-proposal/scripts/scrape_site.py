#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lit le site public du prospect pour préparer la diapo « présentation » :
slogan et titres, description, coordonnées publiées, photos de ses réalisations.

    python3 scripts/scrape_site.py https://exemple.fr dossier-de-sortie

Écrit dossier-de-sortie/site.json et télécharge les photos dans dossier-de-sortie/photos-brutes/.
Bibliothèque standard uniquement. Le script ne lit que le site donné (même nom de domaine)
et s'arrête à quelques pages : c'est une lecture, pas une aspiration.
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
PAGES_UTILES = re.compile(r"realisation|réalisation|album|galerie|gallery|projet|project|portfolio|avant|reference|chantier|travaux|work", re.I)
A_ECARTER = re.compile(r"logo|icon|picto|sprite|avatar|badge|google|facebook|instagram|noun-|marque|flag|favicon", re.I)
MAX_PAGES, MAX_PHOTOS, POIDS_MIN = 6, 40, 15000


def lire(url, binaire=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read()
    return data if binaire else data.decode("utf-8", "replace")


def propre(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    depart, sortie = sys.argv[1], sys.argv[2]
    if not depart.startswith("http"):
        depart = "https://" + depart
    hote = urllib.parse.urlparse(depart).netloc.replace("www.", "")
    os.makedirs(os.path.join(sortie, "photos-brutes"), exist_ok=True)

    accueil = lire(depart)
    liens = []
    for h in re.findall(r'href="([^"#]+)"', accueil):
        u = urllib.parse.urljoin(depart, h)
        if urllib.parse.urlparse(u).netloc.replace("www.", "") == hote and PAGES_UTILES.search(u) and u not in liens:
            liens.append(u)
    pages = [(depart, accueil)]
    for u in liens[:MAX_PAGES - 1]:
        try:
            pages.append((u, lire(u)))
        except Exception as e:
            print("page ignorée", u, e)

    infos = {
        "url": depart,
        "titre": propre("".join(re.findall(r"<title>(.*?)</title>", accueil, re.S)[:1])),
        "description": html.unescape("".join(re.findall(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', accueil)[:1])),
        "h1": [propre(x) for x in re.findall(r"<h1[^>]*>(.*?)</h1>", accueil, re.S)][:5],
        "h2": [propre(x) for x in re.findall(r"<h2[^>]*>(.*?)</h2>", accueil, re.S)][:12],
        "emails": sorted(set(e for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", accueil)
                             if not re.search(r"example|domaine|xxx|sentry|wix", e)))[:5],
        "telephones": sorted(set(re.findall(r"(?:\+33|0)[1-9](?:[ .]?\d{2}){4}", propre(accueil))))[:5],
        "pages_lues": [u for u, _ in pages],
        "photos": [],
    }

    vues = set()
    for url_page, corps in pages:
        for balise in re.findall(r"<(?:img|a|source)[^>]+>", corps):
            alt = re.search(r'(?:alt|title)="([^"]*)"', balise)
            for src in re.findall(r'(?:data-src|data-lazy|src|href)="([^"]+\.(?:jpe?g|png|webp))"', balise, re.I):
                u = urllib.parse.urljoin(url_page, src)
                if u in vues or A_ECARTER.search(u):
                    continue
                vues.add(u)
                if len(infos["photos"]) >= MAX_PHOTOS:
                    break
                try:
                    data = lire(u, binaire=True)
                except Exception:
                    continue
                if len(data) < POIDS_MIN:
                    continue
                nom = "%02d-%s" % (len(infos["photos"]) + 1, re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(urllib.parse.urlparse(u).path))[-60:])
                with open(os.path.join(sortie, "photos-brutes", nom), "wb") as f:
                    f.write(data)
                infos["photos"].append({"fichier": "photos-brutes/" + nom, "source": u, "page": url_page,
                                        "legende_du_site": html.unescape(alt.group(1)) if alt else "", "octets": len(data)})

    with open(os.path.join(sortie, "site.json"), "w", encoding="utf-8") as f:
        json.dump(infos, f, ensure_ascii=False, indent=1)
    print("titre :", infos["titre"])
    print("h1 :", infos["h1"])
    print("%d photos dans %s" % (len(infos["photos"]), os.path.join(sortie, "photos-brutes")))
    print(os.path.join(sortie, "site.json"))


if __name__ == "__main__":
    main()
