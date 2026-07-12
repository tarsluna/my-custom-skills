---
name: meta-ads-creative-framework
description: Framework visuel pour creer des creatives Meta Ads dans Figma. Complement du meta-ads-copywriter. Definit layouts, typo, couleurs, CTA visuels par format (Feed 1080x1080, Story/Reel 1080x1920, Carousel 1080x1080). Trigger phrases: "creatives Meta", "design pubs Meta", "template Figma ads", "framework visuel pubs", "creer des visuels Meta", "specs Figma pubs", "direction artistique Meta Ads".
---

# Meta Ads Creative Framework (Visual Design System for Figma)

Framework visuel complet pour produire des creatives Meta Ads performantes dans Figma. Ce skill est le **complement visuel** du `meta-ads-copywriter` : le copywriter fournit les textes (scripts, hooks, CTAs), ce framework definit **comment les mettre en forme visuellement** (layouts, typo, couleurs, boutons, exports).

---

## Quand utiliser cette skill

Trigger quand l'utilisateur demande :
- "Cree-moi des creatives Meta dans Figma"
- "J'ai besoin des specs visuelles pour mes pubs"
- "Template Figma pour mes ads Meta"
- "Direction artistique pour campagne Meta"
- "Framework visuel pour les pubs Facebook/Instagram"
- "Specs design pour Feed / Story / Reel / Carousel"
- Toute reference explicite a "meta-ads-creative-framework"

NE PAS trigger quand l'utilisateur demande :
- Des scripts ou copies texte -> utiliser `meta-ads-copywriter`
- Un VSL long -> utiliser `vsl-copywriter`
- De la recherche client -> utiliser `deep-search`

---

## Structure de la skill

```
meta-ads-creative-framework/
├── SKILL.md                              <- orchestration principale (ce fichier)
├── frameworks/
│   ├── 01-layout-system.md               <- grilles & compositions par format Meta
│   ├── 02-typography-system.md           <- hierarchie typo, tailles, fonts recommandees
│   ├── 03-color-system.md                <- palettes, contrastes, psychologie couleur
│   ├── 04-cta-visual-patterns.md         <- boutons, placement, tailles, animations
│   └── 05-format-specs.md                <- specs techniques par placement Meta (Feed, Story, Reel)
├── templates/
│   ├── figma-component-checklist.md      <- checklist pour construire les composants Figma
│   └── creative-brief-visual.md          <- template de brief visuel (input)
└── checklists/
    └── visual-quality-gate.md            <- checklist avant export
```

---

## Pipeline (4 phases)

### Phase 1 — Charger le brief visuel

**1.1** Identifier le client slug (ex : `TopCo`, `maje-conseil`).

**1.2** Verifier si un brief visuel existe deja :
```
projects/clients/{client-slug}/creative-brief-visual.md
```

**1.3** Si un brief existe, le lire. Sinon, charger `templates/creative-brief-visual.md` et demander a l'utilisateur de remplir les champs minimum :

**Champs minimum requis :**
- **Client / Projet** : nom et contexte
- **Archetype couleur** : Urgence / Confiance / Energie / Authority (cf. `frameworks/03-color-system.md`)
- **Formats demandes** : Feed / Story / Reel / Carousel (et nombre de variantes)
- **Assets disponibles** : logo, photos, screenshots, temoignages visuels
- **Ton visuel** : UGC brut / Clean corporate / Bold disruptif / Premium epure

**Champs optionnels (demander si pertinent) :**
- Contraintes brand (couleurs imposees, fonts imposees, do/don't)
- References visuelles (liens ou screenshots de pubs admirees)
- Copy deja validee (lien vers le pack `meta-ads-copywriter`)

**1.4** Si le copywriter a deja produit un pack (`projects/clients/{client-slug}/meta-ads/v1.md`), le lire pour recuperer les hooks, CTAs et copies a integrer dans les visuels.

---

### Phase 2 — Definir la direction artistique

**2.1** Charger les frameworks necessaires :
- `frameworks/03-color-system.md` pour la palette
- `frameworks/02-typography-system.md` pour la hierarchie typo
- `frameworks/01-layout-system.md` pour les compositions

**2.2** Determiner la **direction artistique** en fonction de l'archetype client :

| Archetype | Palette | Typo primaire | Typo impact | Layout dominant |
|-----------|---------|---------------|-------------|-----------------|
| Urgence / Performance | Dark + rouge/orange | Inter / DM Sans | Bebas Neue / Anton | Full bleed + floating card |
| Confiance / Premium | Light + bleu/navy | Montserrat / DM Sans | Playfair Display | Split 50/50 clean |
| Energie / Transformation | Dark + orange/jaune | Poppins / Nunito | Anton / Oswald | Hero Image + Text Overlay |
| Authority / Data | Light grey + indigo/bleu | Inter / Montserrat | Oswald | Hero Image + data overlays |

**2.3** Documenter la direction artistique choisie (palette exacte, 2 fonts, layout principal) dans un bloc resume pour validation utilisateur avant de passer aux specs.

---

### Phase 3 — Generer les specs par format

**3.1** Charger `frameworks/01-layout-system.md` et `frameworks/05-format-specs.md`.

**3.2** Pour chaque format demande (Feed, Story, Reel, Carousel), generer :
- **Layout annote** : description precise des zones (hero, text, CTA, logo) avec dimensions en px
- **Specs typo** : tailles exactes par niveau (H1, H2, Body, CTA) pour ce format
- **Specs couleur** : couleurs exactes (hex) pour fond, texte, CTA, accents
- **Specs CTA** : type de bouton, dimensions, placement, style
- **Specs export** : format de fichier, resolution, colorspace

**3.3** Si Carousel demande, definir la **progression narrative** :
- Slide 1 : hook visuel (pattern interrupt)
- Slides 2 a N-1 : progression (pain -> mecanisme -> preuve -> benefice)
- Slide N : CTA + recap offre
- Elements de continuite entre slides (palette, grid, elements visuels traversants)

**3.4** Charger `templates/figma-component-checklist.md` et generer la liste des composants Figma a creer pour ce client.

---

### Phase 4 — Quality gate

**4.1** Charger `checklists/visual-quality-gate.md` et verifier CHAQUE item.

**4.2** Checklist obligatoire :

**Must-haves :**
- [ ] Toutes les safe zones respectees (top/bottom pour Story, margins pour Feed)
- [ ] Contraste WCAG AA sur tous les textes (4.5:1 body, 3:1 large text)
- [ ] CTA visible et cliquable (tap target >= 44px)
- [ ] Max 2 familles de fonts
- [ ] Texte lisible a taille mobile (preview 375px)
- [ ] Exports au bon ratio et bonne resolution
- [ ] Congruence visuelle avec la LP (meme palette, meme typo, meme ambiance)

**Must-avoid :**
- [ ] Pas de texte >20% de l'image (bonne pratique Meta)
- [ ] Pas de claims visuels interdits (avant/apres sante, resultats financiers garantis)
- [ ] Pas de fond transparent sur les exports finaux
- [ ] Pas de color space P3 (utiliser sRGB)

Si un check echoue, corriger avant de sauvegarder. Si impossible, flagger explicitement.

**4.3** Sauvegarder les specs finales :
```
projects/clients/{client-slug}/creative-specs/v1.md
```

**4.4** Message final (en francais) :

> Specs creatives Meta generees pour **{CLIENT}**.
> - `projects/clients/{slug}/creative-specs/v1.md` — specs visuelles pour {N} formats
> - Direction artistique : {archetype} — palette {couleurs principales}, typo {font 1} + {font 2}
> - Formats : {liste des formats avec dimensions}
>
> **Prochaine etape** : ouvrir Figma, creer les composants selon `figma-component-checklist.md`, appliquer les specs, puis exporter avec les settings documentes dans `05-format-specs.md`.

---

## Integration avec l'ecosysteme the platform

Cette skill est le **complement visuel** de la stage 3 du pipeline :

```
[Stage 1] deep-search          -> 3 rapports de recherche
[Stage 2] vsl-copywriter        -> VSL longue (8-12 min)
[Stage 3a] meta-ads-copywriter  -> Scripts + copies texte Meta Ads
[Stage 3b] meta-ads-creative-framework -> Specs visuelles Figma (CE SKILL)
```

**Workflow recommande :**
1. Le copywriter (`3a`) produit les textes (hooks, body, CTAs, copies)
2. Ce framework (`3b`) definit les specs visuelles (layout, typo, couleurs, boutons)
3. Le designer ouvre Figma et assemble les deux pour produire les creatives finales

Les deux skills doivent etre **congruents** : meme promesse, meme mecanisme, meme CTA, meme ton.

---

## Regles absolues (ne jamais enfreindre)

1. **Ce skill produit des SPECS visuelles, pas du copy.** Le texte vient du copywriter.
2. **Toujours valider la direction artistique** avec l'utilisateur avant de generer les specs detaillees.
3. **Respecter les safe zones Meta** sur chaque format. Pas de texte important dans les zones d'UI.
4. **Contraste WCAG AA minimum** sur tous les textes. Pas de compromis.
5. **Max 2 familles de fonts** par creative. Pas d'exception.
6. **Exporter en sRGB**, jamais en P3 pour Meta.
7. **Congruence obligatoire** avec le copywriter et la landing page.
8. **Mobile-first toujours.** Tester visuellement a 375px de large.
9. **Markdown only.** Pas de JSON dans l'output.
10. **Sauvegarder au chemin canonique** : `projects/clients/{client-slug}/creative-specs/v1.md`.
