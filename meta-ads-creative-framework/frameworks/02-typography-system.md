# 02 — Typography System : Hierarchie Typo, Tailles, Fonts

Reference typographique complete pour les creatives Meta Ads dans Figma.

---

## Hierarchie typographique

| Niveau | Role | Taille Feed (1080x1080) | Taille Story (1080x1920) | Font style | Line height | Letter spacing |
|--------|------|-------------------------|--------------------------|------------|-------------|----------------|
| H1 | Hook / headline | 64-80px | 72-96px | Bold / Black, sans-serif | 1.1 (tight) | -2% (tight) |
| H2 | Subheadline / benefice | 36-48px | 42-56px | Semibold, sans-serif | 1.2 | 0% (normal) |
| Body | Details / preuve | 24-32px | 28-36px | Regular, sans-serif | 1.3 | 0% (normal) |
| CTA | Bouton text | 28-36px | 32-40px | Bold, CAPS ou Title Case | 1.0 | +1% (aere) |
| Caption | Disclaimer / source | 18-22px | 20-24px | Light, sans-serif | 1.3 | +0.5% |
| Number | Stat / KPI hero | 80-120px | 96-140px | Black / Extra Bold | 1.0 | -3% (tres tight) |

### Regles de ratio

- **Contraste H1 vs Body** : ratio de taille >= 2:1 (ex: H1 a 72px, Body a 32px = ratio 2.25:1)
- **Contraste H1 vs H2** : ratio >= 1.5:1
- **CTA vs Body** : le CTA doit etre plus gros que le body (ratio >= 1.1:1)
- Un seul niveau de heading par bloc visuel. Pas de H1 + H2 + H3 sur la meme zone

---

## Fonts recommandees

Toutes disponibles sur Google Fonts et dans Figma nativement.

### Primary (corps, sous-titres, texte courant)

| Font | Style | Usage ideal | Poids recommandes |
|------|-------|-------------|-------------------|
| **Inter** | Clean, geometrique, neutre | SaaS, B2B, tech, data | Regular 400, Semibold 600, Bold 700 |
| **Montserrat** | Moderne, arrondi, professionnel | Consulting, agences, services | Regular 400, Semibold 600, Bold 700, Black 900 |
| **DM Sans** | Geometrique, contemporain | Startups, apps, moderne | Regular 400, Medium 500, Bold 700 |

### Impact (hooks, headlines, statements bold)

| Font | Style | Usage ideal | Poids recommandes |
|------|-------|-------------|-------------------|
| **Bebas Neue** | Condensed, all-caps, poster | Urgence, promo, FOMO, fitness | Regular 400 (un seul poids, toujours caps) |
| **Anton** | Extra bold, condensed, brut | Hook disruptif, statements choc | Regular 400 (un seul poids) |
| **Oswald** | Semi-condensed, autoritaire | B2B serieux, data, finance | Regular 400, Medium 500, Bold 700 |

### Friendly (coaching, B2C, approchable)

| Font | Style | Usage ideal | Poids recommandes |
|------|-------|-------------|-------------------|
| **Poppins** | Arrondi, chaleureux, lisible | Coaching, bien-etre, education | Regular 400, Semibold 600, Bold 700 |
| **Nunito** | Tres arrondi, doux, accessible | B2C grand public, sante, famille | Regular 400, Semibold 600, Bold 700 |

### Premium (luxe, high-ticket, consulting premium)

| Font | Style | Usage ideal | Poids recommandes |
|------|-------|-------------|-------------------|
| **Playfair Display** | Serif elegant, classique | Luxury, consulting premium, finance | Regular 400, Bold 700, Black 900 |

> **Important** : Playfair Display doit toujours etre pairee avec une sans-serif (Inter, DM Sans, Montserrat) pour le body text. Ne jamais utiliser une serif seule sur une creative Meta.

---

## Combinaisons recommandees par archetype

### Urgence / Performance
```
H1: Bebas Neue 80px (CAPS)
H2: Inter Semibold 42px
Body: Inter Regular 28px
CTA: Inter Bold 32px (CAPS)
```

### Confiance / Premium
```
H1: Playfair Display Bold 72px
H2: Montserrat Semibold 40px
Body: Montserrat Regular 26px
CTA: Montserrat Bold 30px (Title Case)
```

### Energie / Transformation
```
H1: Anton 80px (CAPS)
H2: Poppins Semibold 44px
Body: Poppins Regular 28px
CTA: Poppins Bold 34px (CAPS)
```

### Authority / Data
```
H1: Oswald Bold 76px
H2: Inter Semibold 40px
Body: Inter Regular 26px
CTA: Inter Bold 30px (CAPS)
```

---

## Regles typographiques absolues

### Regles de composition

1. **Maximum 2 familles de fonts par creative.** Une pour les titres (impact), une pour le reste (primary). Pas d'exception.
2. **Jamais 3 familles.** Si tu hesites, utilise une seule famille avec variation de poids (Regular, Bold, Black).
3. **Le hook (H1) doit etre l'element textuel le plus gros** de la creative. Rien ne doit le concurrencer visuellement.
4. **Un seul bloc de texte principal par zone visuelle.** Pas de paragraphes multiples sur un visuel de pub.

### Regles de lisibilite

5. **Line height H1 : 1.1** (tight). Les headlines doivent etre compactes et percutantes.
6. **Line height Body : 1.3** (confortable). Le texte courant doit respirer.
7. **Letter spacing H1 : -2%** (tight). Les gros titres sont plus beaux serres.
8. **Letter spacing CTA en CAPS : +1%** (aere). Les majuscules necessitent plus d'espace pour la lisibilite.
9. **Maximum 2 lignes pour un H1** sur Feed. Maximum 3 lignes sur Story.
10. **Maximum 15 mots par bloc de texte visible** (hors copies Meta texte). La pub est un panneau, pas un article.

### Regles pour sous-titres video

11. **Taille minimum : 36px** pour les sous-titres sur video.
12. **Fond semi-transparent** : rectangle arrondi noir a 60-80% d'opacite derriere le texte.
13. **Maximum 2 lignes affichees simultanement.**
14. **Police : meme font que le Body** de la creative (coherence).
15. **Position : centre-bas**, au-dessus de la safe zone bottom (Story/Reel).

### Regles d'accessibilite

16. **Contraste texte/fond >= 4.5:1** pour body text (WCAG AA).
17. **Contraste texte/fond >= 3:1** pour large text (H1, H2 >= 24px bold ou >= 18.66px).
18. **Pas de texte blanc sur fond clair.** Jamais.
19. **Pas de texte jaune ou vert clair sur fond blanc.** Contraste insuffisant.
20. **Tester la lisibilite a 375px de large** (taille ecran mobile). Si illisible, augmenter la taille.

---

## Text Styles Figma a creer

Pour chaque projet, creer les text styles suivants dans Figma :

```
Meta Ads / H1 / Feed          -> [Font Impact] Black, 72px, LH 1.1, LS -2%
Meta Ads / H1 / Story         -> [Font Impact] Black, 88px, LH 1.1, LS -2%
Meta Ads / H2 / Feed          -> [Font Primary] Semibold, 42px, LH 1.2, LS 0%
Meta Ads / H2 / Story         -> [Font Primary] Semibold, 50px, LH 1.2, LS 0%
Meta Ads / Body / Feed         -> [Font Primary] Regular, 28px, LH 1.3, LS 0%
Meta Ads / Body / Story        -> [Font Primary] Regular, 32px, LH 1.3, LS 0%
Meta Ads / CTA / Feed          -> [Font Primary] Bold, 32px, LH 1.0, LS +1%
Meta Ads / CTA / Story         -> [Font Primary] Bold, 36px, LH 1.0, LS +1%
Meta Ads / Caption / Feed      -> [Font Primary] Light, 20px, LH 1.3, LS +0.5%
Meta Ads / Caption / Story     -> [Font Primary] Light, 22px, LH 1.3, LS +0.5%
Meta Ads / Number / Feed       -> [Font Impact] Black, 100px, LH 1.0, LS -3%
Meta Ads / Number / Story      -> [Font Impact] Black, 120px, LH 1.0, LS -3%
Meta Ads / Subtitle / Video    -> [Font Primary] Bold, 36px, LH 1.2, LS 0%
```

Remplacer `[Font Impact]` et `[Font Primary]` par les fonts choisies pour le client selon l'archetype.
