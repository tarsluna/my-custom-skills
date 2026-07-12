# 04 — CTA Visual Patterns : Boutons, Placement, Tailles, Animations

Reference complete des patterns visuels pour les Call-to-Action dans les creatives Meta Ads.

---

## Patterns de boutons CTA

### Tableau de reference

| Pattern | Quand l'utiliser | Style visuel | Border-radius | Padding |
|---------|-----------------|--------------|---------------|---------|
| **Pill button** | Default pour tous formats | Fond solide, coins tres arrondis | 999px (capsule) | 16px 48px |
| **Square button** | B2B, authority, serieux | Fond solide, coins legers | 8px | 16px 48px |
| **Rounded button** | Friendly, coaching, B2C | Fond solide, coins moyens | 16px | 16px 48px |
| **Ghost button** | CTA secondaire, alternative | Bordure uniquement, fond transparent | 999px ou 8px | 16px 48px |
| **Full-width bar** | Story/Reel bottom CTA | Barre pleine largeur, fond solide | 0px (plein) ou 16px top | Width: 100%, H: 72px |
| **Arrow CTA** | Carousel "slide suivante" | Texte + chevron, sans fond | — | — |
| **Floating pill** | CTA sur image/video | Pill avec shadow portee | 999px | 16px 48px |

---

## Specs detaillees par pattern

### Pill Button (default)
```
┌──────────────────────────────────┐
│                                  │
│     DECOUVRIR L'OFFRE  ->        │  <- texte Bold + chevron optionnel
│                                  │
└──────────────────────────────────┘
     border-radius: 999px
     height: 56px (Feed) / 64px (Story)
     padding: 16px 48px
     font: [CTA font] Bold, 32px
     background: [CTA Background color]
     text: [CTA Text color]
     shadow: none (ou 0 4px 12px rgba(0,0,0,0.15) si floating)
```

### Square Button (B2B)
```
┌──────────────────────────────────┐
│                                  │
│     RESERVEZ VOTRE AUDIT         │
│                                  │
└──────────────────────────────────┘
     border-radius: 8px
     height: 56px (Feed) / 64px (Story)
     padding: 16px 48px
     font: [CTA font] Bold, 30px, CAPS
     background: [CTA Background color]
     text: [CTA Text color]
```

### Ghost Button (secondaire)
```
┌──────────────────────────────────┐
│                                  │
│     En savoir plus               │  <- texte Regular ou Semibold
│                                  │
└──────────────────────────────────┘
     border: 2px solid [Brand Primary]
     background: transparent
     border-radius: 999px ou 8px
     height: 48px (plus petit que le primary)
     font: [CTA font] Semibold, 28px
     text: [Brand Primary color]
```

### Full-Width Bar (Story/Reel)
```
┌──────────────────────────────────────┐
│                                      │
│        COMMENCER MAINTENANT          │  <- centré, CAPS
│                                      │
└──────────────────────────────────────┘
     width: 100% (1080px) - 80px margins = 920px visible
     height: 72px
     border-radius: 16px (coins top) ou 0px (full bleed)
     font: [CTA font] Bold, 36px
     background: [CTA Background color]
     text: [CTA Text color]
     position: fixed, au-dessus de la safe zone bottom
```

### Arrow CTA (Carousel)
```
     Slide suivante  →

     font: [Body font] Semibold, 24px
     color: [Brand Primary] ou [Text Secondary]
     position: bottom-right de la slide
     padding-right: 40px
     pas de fond, pas de bordure
     le chevron (→) est en [Brand Primary]
```

---

## Tailles minimum (accessibilite)

| Spec | Valeur minimum | Reference |
|------|----------------|-----------|
| **Tap target** | 44 x 44px | Apple Human Interface Guidelines |
| **Button height Feed** | 56px | Best practice Meta Ads |
| **Button height Story** | 64px | Best practice Meta Ads |
| **Button text size** | 28px minimum | Lisibilite mobile |
| **Padding vertical** | 16px minimum | Confort visuel |
| **Padding horizontal** | 32px minimum | Texte pas colle aux bords |
| **Espace autour du CTA** | 24px minimum | Le CTA doit "respirer" |

> **Regle critique** : si le bouton est trop petit pour etre tape facilement avec le pouce sur un iPhone SE (ecran 375px), il est trop petit. Toujours verifier en preview mobile.

---

## Placement par format

### Feed (1080 x 1080)

```
┌─────────────────────────┐
│                         │
│      (contenu)          │
│                         │
│                         │
│                         │
│                         │
│                         │
│  ───── Bottom 20% ───── │  <- zone CTA (216px)
│                         │
│     [ CTA BUTTON ]      │  <- centré horizontalement
│                         │
└─────────────────────────┘
```
- Position : bottom 20% de la creative (a partir de 864px)
- Alignement : centre horizontal
- Le CTA est le dernier element lu (Z-pattern)

### Story / Reel (1080 x 1920)

```
┌─────────────────────────┐
│                         │
│      (contenu)          │
│                         │
│                         │
│                         │
│                         │
│  [ CTA FULL WIDTH ]     │  <- a 1570px du top (bottom - 350px safe)
│                         │
│   ⚠ SAFE ZONE 350px     │  <- ne pas descendre en dessous
└─────────────────────────┘
```
- Position : au-dessus de la safe zone bottom (350px du bas)
- Soit a Y = 1920 - 350 - 72 (hauteur bouton) = 1498px du top
- Full-width bar ou pill button centré
- Laisser 24px minimum entre le contenu et le CTA

### Reel (1080 x 1920)

- Meme logique que Story mais safe zone bottom = 300px
- Position CTA : Y = 1920 - 300 - 72 = 1548px du top
- Le Reel a moins d'UI overlay en bas que la Story

### Carousel (derniere slide)

```
┌─────────────────────────┐
│                         │
│   RECAP OFFRE           │
│   - Benefice 1          │
│   - Benefice 2          │
│   - Benefice 3          │
│                         │
│     [ CTA BUTTON ]      │  <- centré vertical et horizontal
│                         │
│   "Places limitees"     │  <- urgence sous le CTA
│                         │
└─────────────────────────┘
```
- Position : centré verticalement dans le tiers inferieur de la slide
- Toujours accompagne d'un element d'urgence ou de recap sous le bouton
- Le CTA de la derniere slide est le plus gros de tout le carousel

---

## Etats visuels du bouton

### Etat normal (image statique)
- Couleur de fond solide (pas de gradient sauf si direction artistique le demande)
- Shadow optionnelle pour effet floating : `0 4px 12px rgba(0, 0, 0, 0.15)`
- Le bouton doit etre l'element au contraste le plus eleve de la creative

### Etat hover (non applicable sur mobile, mais utile pour les previews desktop)
- Opacity 90% ou couleur 10% plus foncee
- Non critique pour les ads Meta (mobile-first)

---

## Animations CTA (pour video/motion)

### Apparition
```
Timing: 300ms ease-out
Transform: scale(0.8) -> scale(1.0)
Opacity: 0 -> 1
Declenchement: quand le CTA apparait dans le script (fin du body, debut du CTA)
```

### Pulse (attention)
```
Timing: 2s ease-in-out, infinite loop
Transform: scale(1.0) -> scale(1.05) -> scale(1.0)
Subtil, pas agressif
Declenchement: apres l'apparition, en boucle
```

### Slide-up (Story/Reel)
```
Timing: 400ms ease-out
Transform: translateY(40px) -> translateY(0)
Opacity: 0 -> 1
Declenchement: quand la barre CTA entre en scene
```

### Regles d'animation

1. **Ne PAS animer le texte du CTA lui-meme.** Le texte doit rester fixe et lisible.
2. **L'animation du bouton ne doit pas durer plus de 400ms.** Au-dela, ca ralentit le message.
3. **Un seul type d'animation par CTA.** Pas de scale + slide + pulse en meme temps.
4. **Le pulse doit etre subtil** (max 5% de scale). Un pulse agressif donne un aspect spam.
5. **Le CTA doit etre deja visible et lisible** avant toute animation (pas d'animation d'entree obligatoire sur les 3 premieres secondes).

---

## Checklist rapide CTA

Avant de valider un CTA sur une creative :

- [ ] Tap target >= 44 x 44px
- [ ] Hauteur bouton >= 56px (Feed) ou >= 64px (Story)
- [ ] Texte bouton >= 28px
- [ ] Contraste bouton = le plus eleve de la creative
- [ ] Un seul CTA par creative (pas 2 boutons, pas "ou alors...")
- [ ] Texte du CTA = une seule action claire ("Reserver mon audit", "Decouvrir l'offre")
- [ ] Espacement >= 24px autour du bouton
- [ ] Position dans la zone CTA du format (bottom 20% Feed, au-dessus safe zone Story)
- [ ] Congruent avec le CTA du copywriter (meme action, meme formulation)
