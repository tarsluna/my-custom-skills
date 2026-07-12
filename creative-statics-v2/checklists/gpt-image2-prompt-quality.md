# Checklist — GPT Image 2 Prompt Quality

À passer sur chaque `cells[].prompt` AVANT la Phase G (batch). Un prompt faible = une
créative ratée + des crédits brûlés. Cf. `frameworks/01-art-direction-system.md`.

## Les 7 blocs présents
- [ ] [FORMAT] — aspect ratio + plateforme + "mobile-first legible" ?
- [ ] [STYLE] — 1 des 12 styles + seed + (référence en STYLE only si fournie) ?
- [ ] [SCENE] — sujet clair + "match brand asset, don't invent logo" si réf produit ?
- [ ] [PALETTE] — hex exacts cités + "single accent on CTA only" ?
- [ ] [TEXT] — hook exact entre «», CTA exact, "short / correctly spelled / legible" ?
- [ ] [COMPOSITION] — logo top-left, point focal unique, safe zone bottom 15% ?
- [ ] [QUALITY] — directive rendu + NEGATIVE prompt complet ?

## Contraintes texte (GPT Image 2)
- [ ] Hook ≤ 7 mots ?
- [ ] CTA ≤ 4 mots ?
- [ ] Body absent de l'image (livré en primary text Meta) ?
- [ ] NEGATIVE : `no watermark, no gibberish text, no misspelled words, no distorted hands, no fake logos, no duplicated UI chrome` ?

## Cohérence
- [ ] Style ∈ les 12 et cohérent avec l'`accent_archetype` du client ?
- [ ] Si `style_ref` fourni → bloc d'inspiration "STYLE only, brand 100% client" présent ?
- [ ] Si `brand_assets` fourni → "match the reference product/brand" présent ?
- [ ] Format → safe zones spécifiques (Story top/bottom 220px) si 9:16 ?

## Anti-gaspillage
- [ ] Pas 2 cellules avec un prompt quasi-identique (le cache dédoublonne, mais évite le doublon de design) ?
- [ ] Résolution = `2k` (réserver `4k` aux hero/gagnantes) ?
