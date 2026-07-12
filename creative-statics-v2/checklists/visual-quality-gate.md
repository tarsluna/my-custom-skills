# Checklist — Visual Quality Gate (V2)

Passe finale avant packaging. Combine l'audit automatique (`audit_heuristic.py`) et
l'œil humain. Ce que la machine ne juge pas (esthétique, artefacts IA) = Council seat #5.

## Automatique (`audit_heuristic.py`)
- [ ] Dimensions ∈ {1080×1080, 1080×1350, 1080×1920} (sinon `--fix`) ?
- [ ] Poids fichier ∈ [80 KB, 8 MB] ?
- [ ] Contraste σ ∈ [20, 90] (ni plat ni cramé) ?
- [ ] Pas de flag `BOTTOM_SAFEZONE_BUSY` (texte trop bas) ?

## Lisibilité (humain)
- [ ] Hook lisible en thumbnail (test : réduire à 150px de large) ?
- [ ] CTA lisible et contrasté ?
- [ ] Aucune faute / texte déformé sur le rendu IA (sinon brand-lock ou regen) ?

## Composition (humain)
- [ ] Point focal unique évident ?
- [ ] Respiration suffisante (pas surchargé) ?
- [ ] Logo bien posé, non coupé, non halluciné ?
- [ ] Safe zone Meta respectée (rien de critique sous 86% de hauteur) ?

## Diversité du pack (sur l'ensemble)
- [ ] ≥ 6 styles design distincts représentés ?
- [ ] Distribution format ≈ 60/25/15 (Feed/Story/Carousel) ?
- [ ] Pas 30 variantes du même visuel ?
- [ ] Au moins 1 paire de test propre par `test_variable` utilisée ?

## Final
- [ ] Curation faite (on garde les meilleures, pas tout) ?
- [ ] `_strategy-v2.md` rédigé (SHIP/FIX/REGEN/KILL par créative) ?
- [ ] Coût total du batch loggé et conforme à l'estimation approuvée ?
