# 01 — Layout System : Grilles & Compositions par Format Meta

Reference des layouts, zones safe, et compositions pour chaque format publicitaire Meta (Facebook / Instagram).

---

## Feed Carre (1080 x 1080px)

### Zones

| Zone | Position | Dimensions | Usage |
|------|----------|------------|-------|
| Safe text | 120px margins (tous cotes) | 840 x 840px utile | Zone ou le texte est garanti lisible |
| Hero zone | Top 60% | 1080 x 648px | Image principale, visuel hero, screenshot |
| CTA zone | Bottom 20% | 1080 x 216px | Bouton CTA, offre, urgence |
| Logo zone | Top-left ou bottom-right | 80 x 80px | Logo client, discret mais present |
| Buffer zone | Entre hero et CTA (20%) | 1080 x 216px | Sous-titre, preuve sociale, separateur |

### 3 Layouts Feed

**Layout A — Hero Image + Text Overlay**
```
┌─────────────────────────┐
│  [Logo 80x80]           │
│                         │
│     HERO IMAGE          │
│     (pleine largeur)    │
│                         │
│  ┌───────────────────┐  │
│  │  H1: Hook text    │  │
│  │  H2: Sous-titre   │  │
│  └───────────────────┘  │
│                         │
│     [ CTA BUTTON ]      │
│                         │
└─────────────────────────┘
```
- Utilisation : produit en action, screenshot, visuel fort
- Le texte est en overlay sur un fond semi-transparent (rgba noir 60-70%)
- Ideal pour : e-commerce, SaaS avec UI, coaching avec photo

**Layout B — Split 50/50 (Image | Texte)**
```
┌────────────┬────────────┐
│            │            │
│   IMAGE    │  H1: Hook  │
│   (50%)    │  H2: Proof │
│            │  Body text │
│            │            │
│            │  [CTA]     │
│            │            │
└────────────┴────────────┘
```
- Utilisation : B2B, consulting, comparaisons
- Image a gauche (540px), texte a droite (540px)
- Background texte : couleur solide de la palette
- Ideal pour : temoignages, avant/apres, comparatifs

**Layout C — Full Bleed + Floating Card**
```
┌─────────────────────────┐
│                         │
│    BACKGROUND IMAGE     │
│    (full bleed, blur    │
│     ou gradient overlay)│
│                         │
│  ┌───────────────────┐  │
│  │  FLOATING CARD    │  │
│  │  H1 + H2 + CTA   │  │
│  │  (fond solide,    │  │
│  │   border-radius   │  │
│  │   16-24px)        │  │
│  └───────────────────┘  │
│                         │
└─────────────────────────┘
```
- Utilisation : premium, SaaS, offres high-ticket
- Card : fond blanc ou dark, shadow subtile, padding 40px
- Ideal pour : offres premium, lead magnets, webinaires

---

## Story / Reel (1080 x 1920px)

### Zones

| Zone | Position | Dimensions | Usage |
|------|----------|------------|-------|
| Zone safe top | Top 250px | 1080 x 250px | EVITER : barre de profil, icones UI Instagram |
| Zone safe bottom | Bottom 350px | 1080 x 350px | EVITER : CTA natif, swipe up, textes systeme |
| Content zone | Milieu | 1080 x 1320px | Zone exploitable pour le contenu |
| Text safe | 80px left/right | 920px de large | Marge laterale pour le texte |

### 3 Layouts Story/Reel

**Layout D — Full Screen + Bottom CTA**
```
┌─────────────────────────┐
│   ⚠ SAFE ZONE TOP       │  250px — ne rien mettre d'important
│   (UI bars)              │
├─────────────────────────┤
│                         │
│                         │
│   FULL SCREEN           │
│   VISUAL                │
│   (image ou video)      │
│                         │
│   ┌──────────────────┐  │
│   │ H1: Hook text    │  │
│   └──────────────────┘  │
│                         │
├─────────────────────────┤
│                         │
│   [ CTA FULL WIDTH ]    │
│                         │
│   ⚠ SAFE ZONE BOTTOM    │  350px — ne rien mettre sous le CTA
└─────────────────────────┘
```
- Utilisation : visuels immersifs, UGC, produit plein ecran
- Texte en overlay avec fond semi-transparent
- CTA en barre pleine largeur, 72px de haut, au-dessus de la safe zone bottom

**Layout E — Top Hook + Center Visual + Bottom CTA**
```
┌─────────────────────────┐
│   ⚠ SAFE ZONE TOP       │
├─────────────────────────┤
│                         │
│   H1: HOOK TEXT         │
│   (centré, gros)        │
│                         │
│   ┌──────────────────┐  │
│   │                  │  │
│   │  VISUAL CENTER   │  │
│   │  (screenshot,    │  │
│   │   photo, graph)  │  │
│   │                  │  │
│   └──────────────────┘  │
│                         │
│   H2: Sous-titre/proof  │
│                         │
│   [ CTA BUTTON ]        │
│                         │
│   ⚠ SAFE ZONE BOTTOM    │
└─────────────────────────┘
```
- Utilisation : pedagogique, preuve sociale, data
- Structure en 3 blocs verticaux equilibres
- Ideal pour : stats, temoignages, resultats clients

**Layout F — Stacked Cards (3 blocs)**
```
┌─────────────────────────┐
│   ⚠ SAFE ZONE TOP       │
├─────────────────────────┤
│                         │
│   ┌──────────────────┐  │
│   │ CARD 1: Hook     │  │
│   │ (fond accent)    │  │
│   └──────────────────┘  │
│                         │
│   ┌──────────────────┐  │
│   │ CARD 2: Preuve   │  │
│   │ (fond primary)   │  │
│   └──────────────────┘  │
│                         │
│   ┌──────────────────┐  │
│   │ CARD 3: CTA      │  │
│   │ (fond CTA color) │  │
│   └──────────────────┘  │
│                         │
│   ⚠ SAFE ZONE BOTTOM    │
└─────────────────────────┘
```
- Utilisation : offres multi-benefices, listes, steps
- 3 cards empilees avec 24px de gap
- Chaque card : padding 32px, border-radius 16px
- Ideal pour : listes de benefices, comparatifs, processus en 3 etapes

---

## Carousel (1080 x 1080px, 3 a 10 slides)

### Structure narrative

| Slide | Role | Contenu type |
|-------|------|-------------|
| Slide 1 | Hook visuel (pattern interrupt) | Statement bold, question provocante, stat choc, image arrêt-scroll |
| Slides 2-3 | Probleme / douleur | Reformulation du pain, empathie, "tu connais ca..." |
| Slides 4-5 | Mecanisme / solution | Presentation du comment, named mechanism, etapes |
| Slides 6-7 | Preuve | Resultats, temoignages, chiffres, screenshots |
| Slide 8-9 | Benefices | Vision du resultat, transformation |
| Derniere slide | CTA + recap offre | Bouton CTA, offre resumee, urgence |

### Continuite visuelle entre slides

- **Meme palette** : couleurs identiques sur toutes les slides
- **Meme grid** : alignement vertical coherent (le texte est a la meme hauteur)
- **Elements traversants** : une ligne, un gradient, ou un element graphique qui "passe" d'une slide a la suivante
- **Numerotation** : optionnelle mais efficace (1/7, 2/7...) en haut a droite
- **Progression de couleur** : le fond peut evoluer progressivement (ex: light -> dark vers le CTA)

### Tips Carousel

- Slide 1 = 80% de la bataille. Si elle ne scroll-stop pas, les suivantes ne seront jamais vues
- Swipe indicator sur slide 1 : petite fleche ou "Swipe ->" discret en bas a droite
- Derniere slide = jamais une image seule, toujours texte + CTA
- Tester avec 3 slides minimum, 5-7 optimal, 10 max

---

## Grille de composition universelle

### Rule of Thirds
```
     360px    360px    360px
   ┌────────┬────────┬────────┐
   │        │        │        │  360px
   │   1    │   2    │   3    │
   │        │        │        │
   ├────────┼────────┼────────┤
   │        │        │        │  360px
   │   4    │   5    │   6    │
   │        │        │        │
   ├────────┼────────┼────────┤
   │        │        │        │  360px
   │   7    │   8    │   9    │
   │        │        │        │
   └────────┴────────┴────────┘
```
- Les intersections (points forts) sont les emplacements ideaux pour les elements cles (visage, CTA, headline)
- 1080 / 3 = 360px par colonne et par ligne

### Points focaux Golden Ratio
- Point focal principal : 1/3 depuis le haut, 1/3 depuis la gauche (360, 360)
- Point focal secondaire : 2/3 depuis le haut, 2/3 depuis la gauche (720, 720)
- Utiliser ces points pour placer le regard du sujet ou le CTA

### Patterns de lecture

**Z-pattern (Feed carre)** : l'oeil parcourt en Z
```
1 ────────── 2
              \
               \
3 ────────── 4
```
- Point 1 : logo ou element brand
- Point 2 : hook / headline
- Diagonale : image / preuve
- Point 4 : CTA

**F-pattern (Story vertical)** : l'oeil parcourt en F
```
1 ────────── 2
│
3 ──────
│
4
```
- Ligne 1 : hook (lu en entier)
- Ligne 2 : sous-titre (debut lu)
- Ensuite : scan vertical sur la gauche
- Placer les elements importants a gauche

---

## Spacings standards

| Element | Valeur | Usage |
|---------|--------|-------|
| Margin externe | 40-80px | Espace entre le contenu et le bord du frame |
| Gap entre blocs | 24-32px | Espace entre les sections (titre, image, CTA) |
| Padding interne card | 32-40px | Espace dans les cards / containers |
| Gap texte (line spacing) | 8-16px | Espace entre lignes de texte |
| CTA margin top | 24-40px | Espace au-dessus du bouton CTA |

Utiliser des multiples de 8px pour tous les spacings (8, 16, 24, 32, 40, 48, 56, 64, 72, 80).
