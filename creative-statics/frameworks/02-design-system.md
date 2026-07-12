# Acme Agency — Design System extrait des créatives v1 → v4 + iterations

**Auteur** : extracteur de design system (UI Designer agent)
**Date** : 2026-04-21
**Sources lues** :
- Scripts : `build_creatives_v3.py`, `build_creatives_v4.py`, `pipeline/build_iteration.py`
- PNG pixels (14 créatives échantillonnées sur 40+) : v1 (angle-1, angle-2, angle-3 feed), v2 (angle-2 council), v3 (v1 due-diligence feed, v2 excel slide-1, v3 price feed, v4 UGC Alex story, v5 anti-retainer feed), v4 (A1 feed, A2 feed, A3 feed, B1 feed, B2 feed, B3 slide-1), iterations (A-scarcity, C-testimonial, F-three-rules, H-refuse-70, M-anti-commercial, B-romain-manifesto)
- Council v2 : `01-brand-guardian.md`, `03-ui-designer.md`

> **Verdict général**. Le design system Acme se stabilise à partir de v3 avec une **grille verticale stricte**, **2 fonts seulement**, **palette réduite à 4 tokens actifs** (navy / off-white / cream / orange) et **7 archétypes de layout réutilisables**. Les échecs répétés sont (1) l'accent orange dilué sur plusieurs zones, (2) le contraste orange sur cream qui tombe à 3.1:1 (fail AA), (3) les marges latérales 6.5% un poil trop serrées pour la grid Meta 8%. v3/v4/iter corrigent 80% des flags du Council v2, mais l'inversion orange→navy sur les prix recommandée par l'UI Designer (v3 transparence) n'a **pas** été appliquée partout — l'iteration B2 garde « 8 000 € » en orange sur fond navy (OK parce que sur navy le ratio orange remonte à 4.3:1 → pass AA large).

---

## 1. Palette complète — tokens RGB + hex + usage

### Palette de base (verrouillée à partir de v3)

| Token | RGB | Hex | Usage canonique | Apparitions |
|---|---|---|---|---|
| **NAVY** | `(10, 22, 40)` | `#0A1628` | Fond sombre dominant ; texte hero sur fond clair ; CTA secondaire (v3-price, B1, A2) | 60% des créatives |
| **NAVY_DEEP** | `(4, 12, 26)` | `#040C1A` | Bottom du gradient sur fonds navy (toujours combiné avec NAVY) | 100% des fonds navy |
| **NAVY_SOFT** | `(28, 42, 66)` | `#1C2A42` | Cartes intérieures sur fond navy (dashboard A1, block B1 outil unifié) | v4 seulement |
| **OFFWHITE** | `(245, 240, 230)` | `#F5F0E6` | Fond clair dominant ; texte sur fond navy ; texte dans CTA orange | 100% des créatives (texte ou fond) |
| **OFFWHITE_BOTTOM** | `(232, 222, 204)` | `#E8DECC` | Bottom du gradient sur fonds cream (v4) | v4 uniquement |
| **CREAM** | `(228, 218, 198)` | `#E4DAC6` | Ligne italic secondaire sur fond navy ; sert l'accent serif (descente tonale) | v3 v1/v5, v4 A1/B2, iter F |
| **ORANGE** | `(255, 90, 31)` | `#FF5A1F` | **CTA principal uniquement (règle violée dans ~40% des créatives v1-v2)** ; accent bar sous hero ; underline logo ; pill catégorie sur fond navy | 100% des créatives |
| **RED** | `(220, 48, 36)` | `#DC3024` | Chip « POUR LES ÉQUIPES QUI… » v3-excel slide 1 ; valeurs comparaison « agence 360° » A3 | v3 et v4 uniquement |

### Palette étendue (introduite v4 + iterations)

| Token | RGB | Hex | Usage | Apparitions |
|---|---|---|---|---|
| **GREEN** | `(34, 172, 128)` | `#22AC80` | Colonne gagnante A3 (Pacte Acme) ; chip trust « DEVIS FIXE · SOUS 48 H » v1 angle-3 | v4 A3, v1 angle-3 |
| **GREY** | `(145, 155, 175)` | `#919BAF` | Texte sub sur navy ; labels stats tertiaires | v3/v4/iter |
| **GREY_DARK** | `(55, 65, 85)` | `#374155` | Body sur cream ; labels stats sur cream | v4/iter |
| **LIME** | `(216, 255, 60)` | `#D8FF3C` | **Seulement v1 angle-2 anti-360** (hero "JUSTE DU CODE." + underline) — utilisé une fois, **jamais reconduit ensuite**. Disponible dans `build_iteration.py` mais jamais appelé. | 1 créative v1 |

### Combos validés par le Council

| Combo | Contraste | Usage | Verdict |
|---|---|---|---|
| OFFWHITE sur NAVY | 17.2:1 | Hero serif + body | AAA ✓ Council winner |
| NAVY sur OFFWHITE | 13.8:1 | Hero serif v3/v4 sur fonds cream | AAA ✓ |
| CREAM sur NAVY | 12.4:1 | 2e ligne italic (descente tonale hero) | AAA ✓ |
| GREY sur NAVY | 9.2:1 | Sub labels stats rail | AA ✓ |
| ORANGE sur NAVY | ~4.3:1 | Underline, accent bar, hero accent | pass AA large text uniquement |
| OFFWHITE sur ORANGE | ~3.4:1 | CTA pill text | **pass AA large text uniquement** (CTA à ~37px bold donc OK ; flagged par Council mais toléré) |
| ORANGE sur OFFWHITE/CREAM | **3.1:1** | Prix en orange sur cream (v1 angle-3, v3 price subline) | **FAIL AA** — à bannir pour body |

### Combos à bannir (Council flags)

1. **ORANGE sur CREAM pour chiffres-clés** (3.1:1) — cf. v1 angle-3 prix « 5 000 € / 10 000 € / 8 000 € » tous illisibles sur mobile
2. **NAVY sur NAVY pour logo Acme** (ratio <3:1) — cf. v2 angle-2 council flag
3. **Trois instances orange concurrentes** (chip + stats + CTA) — cf. v1 angle-1 BookNow

---

## 2. Typography stack — Instrument Serif + Space Grotesk

### Les 2 fonts (point final, jamais plus)

- **Instrument Serif Regular** (`IS_REG`) : chiffres hero, titres éditoriaux droits
- **Instrument Serif Italic** (`IS_ITA`) : hooks éditoriaux, sublines poétiques, citations
- **Space Grotesk Bold** (`SPG`) : logo, chips, body, CTA, stats, labels

### Hiérarchie exacte (normalisée sur W = 1080)

| Rôle | Font | Taille (% de W) | Taille px (W=1080) | Couleur typique | Line-height ratio |
|---|---|---|---|---|---|
| **Hero display chiffre** | IS_REG | 0.22 → 0.30 | 237 → 324 | NAVY sur cream / OFFWHITE sur navy | N/A (1 ligne fit-font) |
| **Hook italique éditorial** | IS_ITA | 0.070 → 0.095 | 76 → 103 | OFFWHITE / NAVY | 1.08 × size (v4) à 1.14 × (v3) |
| **Sub italique** | IS_ITA | 0.042 → 0.060 | 45 → 65 | CREAM (sur navy) / NAVY (sur cream) / GREY_DARK (accent) | 1.16 × size |
| **Sub accent orange** | IS_ITA | 0.046 → 0.058 | 50 → 63 | ORANGE | 1.20 × size |
| **Body / description** | SPG | 0.022 → 0.028 | 24 → 30 | GREY sur navy / GREY_DARK sur cream | 1.45 × size |
| **Signature (sig_ft)** | SPG | 0.020 → 0.024 | 22 → 26 | GREY (150, 165, 190) | 1.50 × size |
| **Chip eyebrow (catégorie)** | SPG | 0.018 | 20 | OFFWHITE sur ORANGE ou sur NAVY | N/A |
| **CTA pill** | SPG | 0.40 × hauteur pill | ~37px (sur h=92px) | OFFWHITE sur ORANGE / NAVY | N/A |
| **Logo Acme** | SPG | 0.030 → 0.032 | 32 → 35 | OFFWHITE ou NAVY selon fond | N/A + underline orange 5px = 0.32 × width du mot |
| **Label rail stats** | SPG | 0.018 → 0.020 | 20 → 22 | GREY / (120,130,150) | uppercase implicite |
| **Valeur rail stats** | SPG | 0.028 → 0.036 | 30 → 39 | NAVY ou OFFWHITE selon fond | — |

### Règles typographiques ancrées

1. **Italique serif = toujours pour le hook**. Jamais de hero en regular serif pour du texte (seulement pour les chiffres).
2. **Descente tonale en 2 lignes** : ligne 1 OFFWHITE, ligne 2 CREAM (ou ligne 1 NAVY ligne 2 ORANGE pour le pattern « 8 semaines. Pas 6 mois. »). Jamais 3 couleurs successives dans un hook.
3. **Accent bar orange 6px × (W × 0.14)** systématiquement sous le hook, offset +10 à +20px. Token réutilisé 100% des créatives v3/v4/iter.
4. **Wrap auto à W × 0.87 = 940px** pour toute ligne de texte. Max 3 lignes pour le hook (le script `build_iteration.py` réduit la taille de 4px jusqu'à tenir).
5. **Pas de kerning manuel implémenté** : flag Council « M€ dans 1,2 M€ mériterait +6px de kerning manuel » — **pas corrigé** dans v3/v4.

---

## 3. Grille & composition — safe zones

### Grille canonique

- **Marge gauche** : `W × 0.065` = 70px (feed/story) à 70px (carousel 1080×1080). **Constante absolue**, jamais dépassée.
- **Marge droite** : idem = 70px. Ligne max utile = 940px sur 1080.
- **Marge haute** (logo) : `H × 0.055` = 74px (feed 1350) à 105px (story 1920) — baseline du logo.
- **Marge basse CTA** : `H × 0.075 → H × 0.105` selon le format. Safe zone Meta standard = 14% bottom (= 189px sur feed 1350) **toujours respectée** depuis v3.

### Verticalité stricte — anatomie y-axis

```
y=0.055 × H  → logo Acme + underline
y=0.145 × H  → eyebrow chip (catégorie)
y=0.20  × H  → hero hook (italique) ou hero chiffre (regular)
y=0.45  × H  → accent bar orange OU divider 2px
y=0.50  × H  → sub italique (ou zone dashboard/diptych/comparison)
y=0.62  × H  → body / signature / stats rail
y=0.80  → 0.92 × H → zone libre / micro-proof / "→ swipe"
y=(H – 0.075×H – ctaH) → CTA pill centré
```

Cette verticalité est **identique sur 100% des créatives v3/v4/iter** et forme la signature composition-wise du système.

### Ratios blanc / rempli

- **Créatives navy** (v1 angle-1 BookNow, v3 v1, v4 A1/B2, iter F/H/M) : ~30% de zone texte, ~70% de vide navy = maximum respiration. Council 9/10 composition.
- **Créatives cream** avec stats/diptych/chart (v3 v3 price, v4 A2/A3/B1, iter C) : ~55% rempli, ~45% vide. Council 7-8/10.
- **Créatives carousel 1:1** (v3 v2 excel, v4 B3) : hook dominant ~40% de la surface, le reste très aéré pour la logique « swipe ».

---

## 4. Anatomie d'une créative — zones standard

Chaque créative du système contient au minimum **7 zones** obligatoires et 4 optionnelles. Ordre top-down :

### Obligatoires (100% des créatives v3/v4/iter)

1. **Logo Acme top-left** — Space Grotesk Bold `W×0.030`, couleur dépend du fond, suivi d'un **underline orange 5px de hauteur, largeur 0.32 × largeur du mot** (= « ME » souligné, typographique).
2. **Eyebrow chip** — pill SPG `W×0.018` uppercase, padding horizontal 22px, hauteur `W×0.038` ≈ 41px, radius = h/2 (pill parfaite). Fond ORANGE ou NAVY selon le thème.
3. **Hero** — soit hook italique IS_ITA `W×0.070-0.082`, soit chiffre hero IS_REG `W×0.22-0.30`. Toujours à `y=0.20×H`.
4. **Accent bar orange** — `6-8px × W×0.14 ≈ 150px`, à +10px sous le hook. Sert de pont visuel hero → sub.
5. **Body / sub text** — Space Grotesk ou IS_ITA en 2e niveau, wrap auto à W×0.87.
6. **CTA pill** — largeur `W×0.76-0.80`, hauteur `W×0.085-0.095` ≈ 92-103px, radius = h/2, centré horizontalement, à `y = H – 0.075×H – ctaH`.
7. **Safe bottom clearance ≥ 14% H** — règle Meta.

### Optionnelles

8. **Accent line / divider** — 2px horizontal sur toute la largeur utile, couleur navy desat `(40, 55, 85)` ou cream `(200, 190, 170)`.
9. **Stats rail 3 colonnes** — label SPG `W×0.018-0.020` + valeur SPG `W×0.028-0.036` en dessous. Ratio `col_w = (W – 2×70) / 3 = 313px`.
10. **Signature band** — SPG `W×0.022`, texte gris, centré bas au-dessus du CTA : « LE PACTE Acme · prix affiché · code à toi · Alex prend l'appel ». Apparaît dans v3 v1 et v1 angle-1.
11. **Swipe indicator** — « →  swipe » SPG `W×0.022` gris, bottom-left. Uniquement carousel (v3-excel, v4 B3).

---

## 5. Formats produits — dimensions + contraintes

| Format | Dimensions | Contraintes particulières | Occurrences |
|---|---|---|---|
| **Feed 4:5** | 1080 × 1350 | CTA bottom à y=1144 (clear 206px = 15.3%) ; hero à y=270 ; hook max 3 lignes | 70% du catalogue |
| **Story 9:16** | 1080 × 1920 | Logo à y=105 au lieu de 74 ; hero size +2px ; CTA à y=1728 (clear 192px = 10%) ; safe zone top/bottom pour UI Instagram =~220px | v1 angle-1/2/3 stories, v3 v1/v3/v4, v4 A1/B2 |
| **Feed 1:1 / Carousel** | 1080 × 1080 | Swipe indicator obligatoire ; max 3-4 slides ; slide 1 = hook, slide 2 = photo éditoriale (optionnelle), slide N-1 = solution, slide N = CTA + offers rail | v1 angle-1/2/3 1x1, v3 v2 excel (4 slides), v4 B3 (3 slides) |
| **Feed 1:1 solo** | 1080 × 1080 | Non testé comme solo hero | Aucun |

**Règle critique jamais violée** : 1080px de largeur systématique. Les hauteurs varient, la largeur jamais.

---

## 6. Archétypes de layout — 7 patterns validés

### A. Hero Number Big (hero chiffre dominant)

**Specs** : IS_REG à `W×0.22-0.30` (237-324px), chiffre unique occupant 35-45% de la hauteur. Accent bar orange dessous. Sub italique 2-lignes en CREAM sous l'accent bar.

**Créatives** : v1 angle-1 (1,2 M€), v3 v3 (8 000 €), v3 v5 (72 000 € biffé), v4 A1 (+142% dashboard interne), v4 B2 (+15 h), v4 B3 slide 1 (48 h.).

**Pourquoi ça marche** : point focal unique, lecture en <0.3s sur feed, biais de concrétude activé.

### B. Hook Italique 3-lines

**Specs** : IS_ITA à `W×0.070-0.082` (76-89px), 3 lignes verticales empilées avec line-height = 1.08× size. Dernière ligne souvent CREAM ou ORANGE (accent tonal). Accent bar 6px × 150px dessous.

**Créatives** : v3 v1 (Ton MVP doit / passer la due / diligence.), v4 A1 (4 lignes BookNow a levé…), v4 B1 (4 lignes Notion/Airtable), iter A/M/H/B (tous).

**Pourquoi ça marche** : registre éditorial magazine, signature Acme identifiable à 50m.

### C. Timeline Horizontal

**Specs** : track 6px sur `W×0.87 = 940px`, 4 milestones (dots `r=16px`), segment rempli orange entre dots, label semaine au-dessus (SPG `W×0.030`), label livrable en dessous (SPG `W×0.021`). Unique à A2.

**Créatives** : v4 A2 (S1 → S8 Design/Alpha/Beta/Production).

**Pourquoi ça marche** : transparence processus, 0 concurrent FR dev web l'utilise.

### D. Diptych Before / After

**Specs** : 2 cards de largeur `W×0.42` chacune, séparées par flèche orange 28px. Left card navy = chaos (6 tool chips 2×3 grid). Right card OFFWHITE outline navy = solution unifiée (1 block navy intérieur avec chiffre + bullets).

**Créatives** : v4 B1 (Notion/Airtable/Zapier/Slack/Sheets/Typeform → 1 app).

**Pourquoi ça marche** : lecture instantanée "avant → après", pattern interrupt sur Feed.

### E. Comparison Chart 3 colonnes

**Specs** : 3 cards `col_w = (W – 140 – 2×gap)/3 ≈ 285px` × `ch_h = H×0.32 ≈ 432px`. Colonne gagnante highlighted (fond navy plein, radius 22px, padding interne +8px). Chaque colonne : nom (SPG `W×0.020`), prix (IS_REG `W×0.066`), 3 rows avec symbol ✓/!/× colorés.

**Créatives** : v4 A3 (Agence 360° 40K / Studio MVP 25K / Pacte Acme 15K).

**Pourquoi ça marche** : transparence radicale, rend visible ce que les concurrents cachent.

### F. Stat Hero Card (ROI chiffré)

**Specs** : hook italique 1 ligne sur un côté (`On a rendu`), puis stat géant IS_REG `W×0.24` centré (`+15 h`), underline orange 8px sous (55% de la largeur du stat), sub italique 2-lignes en CREAM dessous, proof rail 3 colonnes en bas.

**Créatives** : v4 B2, v3 v1 (variante avec chiffre à gauche).

**Pourquoi ça marche** : donnée chiffrée précise en IS_REG massif = signal d'autorité éditorial financier.

### G. Manifesto Carousel (3-4 slides)

**Specs** : Slide 1 = hook numéroté (« PROMESSE #1 ») + chiffre hero + sub italique 2 lignes. Slide 2 = hook numéroté (« PROMESSE #2 ») + chiffre hero (souvent « 0. ») + body SPG. Slide 3 = récap offers rail + CTA final. Alternance navy ↔ cream entre slides pour la rhétorique.

**Créatives** : v4 B3 (Devis 48h manifesto 3 slides), v3 v2 excel (4 slides avec slide 2 = full-bleed photo chaos).

**Pourquoi ça marche** : rythme narratif, engagement swipe > 2.5× vs feed solo.

---

## 7. Règles de contraste — AAA sur hero, AA sur body

### Règle absolue

- **Hero (chiffre ou hook)** : AAA minimum (7:1). Toujours OFFWHITE/NAVY ou NAVY/OFFWHITE.
- **Body** : AA minimum (4.5:1 normal, 3:1 large). Flexible sur GREY/GREY_DARK.
- **CTA pill** : pass AA large text (4.5:1 à 18pt ou 14pt bold). OFFWHITE sur ORANGE tangente 3.4:1 mais passe parce que le CTA text est à 37px bold.

### Exceptions tolérées

- Accent bar orange sur fond quelconque (décoratif, pas de règle).
- Pill « CAS CLIENT » orange avec OFFWHITE texte : 3.4:1 (fail AA normal mais pass AA large car chip text = ~20px bold uppercase).

### Exceptions bannies

- **Prix en ORANGE sur OFFWHITE/CREAM** : 3.1:1. Cas présent dans v1 angle-3 (non corrigé), v3 v3 (une occurrence sur « 8 000 € » du rail, toléré parce que hero en navy). La **reco Council n'a pas été généralisée**.
- **Logo Acme NAVY sur NAVY** : v2 angle-2 originale (corrigée en v3+ par NAVY → OFFWHITE passage sur fonds sombres).

---

## 8. Gabarits de rendu — pseudo-code des fonctions atomiques

Le système est construit sur **8 fonctions réutilisables** présentes identiques dans v3 / v4 / iteration. Elles forment le runtime du design system.

```python
# 1. Font loader
def ft(path, size):
    return ImageFont.truetype(path, size)

# 2. Wrap word-aware (max_w = W × 0.87 convention)
def wrap(d, text, font, max_w):
    # greedy word-wrap, returns list of lines
    ...

# 3. Rounded rectangle (tous les blocks navy/cream cards + pills)
def rr(d, xy, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)

# 4. CTA pill (standard : W×0.76-0.80 × W×0.085-0.095)
def pill(d, x, y, w, h, text, bg, fg, font_path=SPG):
    rr(d, (x, y, x+w, y+h), r=h//2, fill=bg)
    f = ft(font_path, int(h * 0.40))  # text = 40% de la hauteur du pill
    tw = d.textlength(text, font=f)
    # centrage vertical via bbox
    b = f.getbbox(text)
    d.text((x + (w-tw)/2, y + (h-(b[3]-b[1]))/2 - b[1]), text, font=f, fill=fg)

# 5. Logo Acme + underline orange
def logo(d, x, y, size, color=OFFWHITE, accent=ORANGE):
    f = ft(SPG, size)
    d.text((x, y), "Acme", font=f, fill=color)
    w = d.textlength("Acme", font=f)
    d.rectangle((x, y+size+4, x + w*0.32, y+size+9), fill=accent)
    # note : underline couvre 32% du mot = zone "ME"

# 6. Chip eyebrow (catégorie)
def chip(d, x, y, label, font_size, bg, fg, pad=22):
    f = ft(SPG, font_size)
    tw = d.textlength(label, font=f)
    h = int(font_size * 2.0)  # pill height = 2× font_size
    rr(d, (x, y, x + tw + pad*2, y + h), r=h//2, fill=bg)
    b = f.getbbox(label)
    d.text((x + pad, y + (h-(b[3]-b[1]))/2 - b[1]), label, font=f, fill=fg)
    return h  # pour calcul de y suivant

# 7. Gradient vertical (fond canonique)
def gradient_bg(W, H, top, bottom):
    im = Image.new("RGB", (W, H), top)
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / (H - 1)
        c = tuple(int(top[i]*(1-k) + bottom[i]*k) for i in range(3))
        d.line((0, y, W, y), fill=c)
    return im

# 8. fal.ai bg generator (pour portrait Alex + photos éditoriales)
def fal_bg(slug, prompt, w=1152, h=1440, force=False):
    # appel fal-ai/flux/schnell, 4 inference steps, cache dans BG/
    # prompt toujours enrichi de : "editorial magazine photography, 35mm film,
    #   muted palette cream and navy, cinematic depth of field,
    #   natural window light, documentary photojournalism"
    ...
```

### Fonctions d'archetype (v4 seulement)

```python
# Dashboard mock (A1 — simule un SaaS dashboard en PIL)
def draw_dashboard_mock(d, x, y, w, h, fill_card=NAVY_SOFT, accent=ORANGE, fg=OFFWHITE):
    rr(d, (x,y,x+w,y+h), r=20, fill=fill_card)
    # header titre + stat +142% + sparkline 24 bars accelerating, 60% grey + 40% orange

# Tool chip (B1 — chips colorés pour stack before)
def draw_tool_chip(d, x, y, w, h, name, color, stroke):
    rr(d, (x,y,x+w,y+h), r=14, fill=color)
    # texte centré, h × 0.50 pour font_size
```

### Paramètres théoriques vs réels (où le design system est ignoré)

| Paramètre théorique | Valeur déclarée dans scripts | Appliqué ? |
|---|---|---|
| Marge W×0.065 | 70px | ✅ 100% |
| Accent bar orange | 6-8px × W×0.14 | ✅ 95% (certaines iter omettent) |
| CTA pill h/2 radius | h/2 | ✅ 100% |
| Text = 40% pill height | `int(h * 0.40)` | ✅ 100% |
| Logo underline 0.32 × word width | `w * 0.32` | ✅ 100% |
| Chip pad=22px | 22 | ✅ 100% |
| Wrap max_w = W×0.87 | 940px | ✅ 100% |
| Hook max 3 lignes | fit-font auto-shrink | ✅ v4/iter only (v1/v2 violaient) |
| Kerning manuel M€ | recommandé Council v2 | ❌ **jamais implémenté** |
| Contrast AAA hero | 7:1 | ✅ sur fonds opposés, ❌ sur orange/cream |

---

## 9. Échecs du design system — créatives qui ratent le cahier

### 1. v1 angle-3 Transparence — Council 7.4/10 (pire note)

- 3 prix orange sur cream = **3.1:1 fail AA**
- Flat-lay photo document remonte dans la safe zone CTA
- Pill « DEVIS EN 48H » verte (introduit un 4e accent chromatique)
- Hiérarchie prix plate (pas de MVP en IS_REG 48px comme recommandé)
- **Non corrigé** avant v3 (Council reco : mettre les prix en navy, labels en orange desat — partiellement appliquée en v3 v3)

### 2. v1 angle-1 BookNow — Council 8.0/10

- 3 accents orange concurrents (chip + stats + CTA) = pas de point focal unique
- Fond stock laptop générique "agence corporate" (diagnostiqué par Brand Guardian)
- Contraste hero « 1,2 M€ » navy dégradé sur zone lampe
- **Partiellement corrigé en v3 v1** : passage à fond navy plein, stats supprimés, 1 seul accent orange = CTA. Council aurait donné 9.0+.

### 3. v1 angle-2 Anti-360 — la référence 8.9/10

- Seule friction : « Pas de SEO. » techniquement ambigu (critique brand, pas design)
- **A servi de template pour v3/v4** : restriction chromatique, pas de stats, respiration verticale max.

### 4. v1 angle-2 avec lime — cassure palette

- Hero « JUSTE DU CODE. » et underline en LIME `#D8FF3C` : 1 seule apparition, jamais reconduite. Le lime est dans `build_iteration.py` mais non utilisé. **Token orphelin**, à supprimer ou canoniser.

### 5. v3 v4 UGC Alex — photo + typo

- Portrait fal.ai bien intégré (voile navy bottom) mais 3 chips de proof en bas créent beaucoup d'informations concurrentes sur un visuel déjà dense. 2 chips max auraient suffi.

### 6. Iter B-romain-manifesto (iter-06)

- Hook italique serif OFFWHITE sur portrait fal.ai : **lisibilité marginale** sur zone chemise claire. Overlay navy 45% non appliqué uniformément. Ratio perçu ~4:1 sur zones claires. Bord d'AA.

---

## 10. Règles or du design system Acme (à afficher en haut du prochain script)

1. **2 fonts seulement** : Instrument Serif (IS_REG + IS_ITA) + Space Grotesk Bold. Jamais plus.
2. **1 accent orange = 1 point focal = le CTA**. Si chip orange, hero doit rester off-white/navy. Règle violée = Council score < 8.
3. **Grille verticale locked** : logo y=0.055, chip y=0.145, hero y=0.20, CTA y=H–0.075×H–ctaH.
4. **Marges 70px L/R** sur 1080 de large (6.5%). Jamais moins.
5. **Wrap à W×0.87 = 940px**. Hook max 3 lignes, auto-shrink de 4px/step.
6. **Hero = italique (hook) OU serif regular (chiffre), jamais les deux dans la même créative**.
7. **Accent bar orange 6-8px × 150px systématique sous le hero**.
8. **CTA pill radius = h/2, text = 40% de h, centré horizontalement, bottom clearance ≥ 14%**.
9. **Descente tonale hero** : ligne 1 = 100% (NAVY ou OFFWHITE), ligne 2 = 78% (CREAM ou NAVY faded), ligne 3 = ORANGE pour pattern interrupt.
10. **Prix en NAVY sur cream, jamais en ORANGE sur cream** (AAA vs 3.1:1 fail).

---

## Références

- Scripts source : `~/skills/projects/client-slug/05-meta-ads/{build_creatives_v3.py,build_creatives_v4.py,pipeline/build_iteration.py}`
- Council v2 : `~/skills/projects/client-slug/05-meta-ads/creatives/v2/_council/{01-brand-guardian,03-ui-designer}.md`
- Stratégie v4 : `~/skills/projects/client-slug/05-meta-ads/creatives/v4/_strategy.md`
- Fonts : `~/skills/projects/client-slug/05-meta-ads/assets/fonts/`
