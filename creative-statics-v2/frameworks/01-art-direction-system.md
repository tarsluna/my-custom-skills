# Framework 01 — Art-Direction System (design system → prompts GPT Image 2)

La V1 dessine la typo en PIL. La V2 **décrit** la créative à GPT Image 2 dans un langage d'art-direction. Ce framework traduit le design system verrouillé (`../../creative-statics/frameworks/02-design-system.md`) en **directives de prompt** + définit **12 styles design** réutilisables.

---

## 1. Anatomie d'un master-prompt GPT Image 2

Un prompt qui produit une créative ad-grade contient **toujours** ces 7 blocs, dans cet ordre :

```
[1 FORMAT]        Aspect ratio + dimensions cibles + plateforme (Meta Feed/Story/Carousel)
[2 STYLE]         L'un des 12 styles design (§3) + référence(s) visuelle(s)
[3 SCÈNE]         Sujet principal : produit / humain / abstrait / scène lifestyle
[4 PALETTE]       Hex exacts + rôles (fond / accent / texte) — repris du brand profile
[5 TEXTE]         Le texte EXACT à incruster (hook court + CTA), avec rôle typo + emphase
[6 COMPOSITION]   Grille verticale, safe zones, zone de respiration, point focal unique
[7 QUALITÉ]       Directives rendu : éditorial, photoréaliste, lumière, netteté, contraste
                  + NEGATIVE : pas de watermark, pas de texte parasite, pas de mains déformées
```

### Règles de prompting GPT Image 2 (spécifiques)
- GPT Image 2 **suit bien les instructions de texte** : mets le texte exact entre guillemets, précise *"the headline text reads exactly: «…»"*. Garde le texte **court** (un hook de 3-7 mots passe ; un paragraphe se déforme).
- **Un seul accent couleur = un seul point focal** (règle d'or héritée). Dis-le explicitement : *"single orange accent reserved for the CTA only"*.
- Précise la **place du texte** dans le cadre (top-left logo, hero centré haut, CTA pill bas centré, safe-zone 14% en bas).
- Donne **les hex** : *"background deep navy #0A1628, off-white #F5F0E6 text, single accent #FF5A1F"*.
- Pour la cohérence de marque : passe les **brand assets en référence** (`input_images`) et dis *"match the product/brand in the reference image, do not invent a different logo"*.
- **NEGATIVE prompt systématique** : `no watermark, no extra gibberish text, no distorted hands, no fake logos, no lorem ipsum, no duplicated UI chrome`.

### Le texte IA n'est pas pixel-perfect
GPT Image 2 rend bien un hook court, mais : (a) les polices exactes de marque ne sont pas garanties, (b) les longues lignes se déforment, (c) le kerning/contraste peut rater. → Deux parades :
1. Garder le texte incrusté **minimal** (hook + CTA), déplacer le body en *primary text* Meta (hors visuel).
2. **Brand-lock pass** (`scripts/brand_lock_pass.py`) : ré-incruster en PIL le logo + CTA + légal avec les fonts exactes quand la charte l'exige.

---

## 2. Tokens repris du design system (adaptés par client)

Le design system Acme est **un exemple**, pas une loi universelle. Pour chaque client, on remappe via `client-brand-profile.json`. Ce qui reste **invariant** (les lois) :

| Loi invariante | Traduction prompt |
|---|---|
| 1 accent = 1 point focal = CTA | *"single accent color, used only on the CTA"* |
| Contraste hero AAA (≥7:1) | *"high contrast headline, fully legible on mobile"* |
| Grille verticale (logo haut, hero, CTA bas) | bloc COMPOSITION explicite |
| Safe zone bottom ≥ 14% (Meta) | *"keep bottom 15% clear of critical text, CTA above it"* |
| Respiration (30-45% de vide) | *"generous negative space, uncluttered, editorial breathing room"* |
| Max 2 familles de police | *"two type families max: one serif display, one grotesk for UI"* |
| Largeur 1080 systématique | dimensions cibles fixes |

Ce qui **varie par client** (depuis le brand profile) : palette hex, fonts nommées, logo, ton, archétype couleur (Confiance/Urgence/Énergie/Authority/Luxe), assets photographiables.

---

## 3. Les 12 styles design (diversité visuelle du pack)

Chaque style est un **preset d'art-direction**. La matrice de variations pioche 2-3 styles par angle pour garantir la diversité. Chaque style ci-dessous donne : usage, prompt-seed, format favori.

### S1 — Editorial Typographic (pont vers V1)
Texte-roi sur fond uni/gradient. Hook serif italique + CTA pill. **Style favori pour brand-lock pass.**
*Seed* : `editorial magazine cover, bold serif headline, deep solid background #HEX, single accent, minimalist, lots of negative space`. Format : Feed 4:5, Carousel.

### S2 — Photoreal Product Hero
Produit photographié studio, fond gradient on-brand, hook court en surimpression haute. Conditionné sur `brand_assets` produit.
*Seed* : `studio product photography, soft gradient backdrop in brand palette, dramatic rim light, product centered, short headline overlay top`. Format : Feed 4:5, 1:1.

### S3 — Lifestyle / UGC-style
Scène de vie réaliste (main qui tient le produit, bureau, usage réel), look iPhone authentique. Idéal lead gen B2C.
*Seed* : `authentic lifestyle photo, natural light, real person using the product, candid, shallow depth of field, phone-camera realism`. Format : Story 9:16, Feed 4:5.

### S4 — Human / Founder Authority
Portrait fondateur/spokesperson, regard caméra, overlay navy bas, hook autorité. **Si récurrent → Soul ID** (cf. §5).
*Seed* : `editorial portrait, confident founder, soft window light, dark vignette bottom for text legibility, documentary tone`. Format : Feed 4:5, Story.

### S5 — Bold 3D / CGI
Rendu 3D produit ou objet symbolique, couleurs saturées on-brand, énergie. Pour archétype Énergie.
*Seed* : `glossy 3D render, vibrant brand colors, floating product, soft studio reflections, premium CGI`. Format : 1:1, Feed 4:5.

### S6 — Magazine Collage / Cutout
Collage éditorial (découpes, scotch, annotations manuscrites), look « moodboard ». Pattern-interrupt fort.
*Seed* : `editorial paper collage, cutout textures, handwritten annotations, mixed media, scrapbook energy, brand palette`. Format : Feed 4:5, Carousel.

### S7 — Data-Viz / Chart
Graphe/stat dominant (courbe, barres, dashboard mock) rendu propre. Pour proof-led.
*Seed* : `clean data visualization, single big number, upward chart, financial UI aesthetic, brand accent on key metric`. Format : Feed 4:5, 1:1. *(Souvent meilleur en V1 PIL pour la précision.)*

### S8 — Diptych Before / After
Split-screen avant/après, contraste chaos→ordre. Lecture instantanée.
*Seed* : `split screen before and after, left messy desaturated, right clean brand-colored, clear visual contrast, arrow between`. Format : Feed 4:5, 1:1.

### S9 — Minimalist Luxury
Vide maximal, 1 objet, typo fine, palette désaturée premium. Pour archétype Luxe/Authority.
*Seed* : `luxury minimalist composition, single hero object, muted premium palette, fine serif type, vast negative space, soft shadow`. Format : Feed 4:5, Story.

### S10 — Brutalist / Bold Statement
Typo massive, couleurs franches, contraste brut. Pour common-enemy / anti-establishment.
*Seed* : `brutalist poster, oversized bold type, high contrast flat colors, raw grid, confrontational layout`. Format : Feed 4:5, 1:1.

### S11 — Soft Gradient / Aura
Dégradés doux modernes (mesh gradient), glow, ambiance app/SaaS premium. Pour tech/SaaS.
*Seed* : `modern mesh gradient background, soft glow, glassmorphism accents, premium SaaS aesthetic, short headline`. Format : Feed 4:5, Story.

### S12 — Documentary / Real-Object
Photo réaliste d'un objet de preuve (document, écran, lettre, produit usé) — crédibilité brute.
*Seed* : `documentary still life, real object as proof, natural texture, honest unstyled realism, single accent highlight`. Format : Feed 4:5.

### Table de correspondance archétype couleur → styles recommandés
| Archétype client | Styles prioritaires |
|---|---|
| **Confiance** (B2B services) | S1, S4, S7, S12 |
| **Urgence** (offre/scarcity) | S10, S8, S1 |
| **Énergie** (DTC jeune) | S5, S3, S11 |
| **Authority** (premium/expert) | S4, S9, S1 |
| **Luxe** | S9, S2, S6 |

---

## 4. Mapping format → dimensions / safe zones (prompt)

| Format | Cible | Safe zone à dire dans le prompt |
|---|---|---|
| Feed 4:5 | 1080×1350 | *"keep critical text within central 85%, CTA above bottom 15%"* |
| Story 9:16 | 1080×1920 | *"keep top 220px and bottom 220px clear of text (IG UI), CTA mid-low"* |
| Carousel 1:1 | 1080×1080 | *"square, swipe indicator bottom-right, hook dominant top half"* |

GPT Image 2 ne sort pas toujours exactement 1080×1350 → `audit_heuristic.py` resize/pad au format Meta exact, et `brand_lock_pass.py` recadre proprement si besoin.

---

## 5. Identité cohérente sur le pack (Soul ID — hook futur)

Si le client a un **spokesperson/fondateur récurrent** à montrer sur plusieurs créatives (style S4), l'incohérence de visage entre images IA tue la crédibilité. Parade Higgsfield : **Soul ID** — on entraîne un identifiant de visage fidèle une fois (≥ photos de réf), puis on le réutilise dans chaque génération compatible.

> V2 ne l'active pas par défaut (GPT Image 2 simple suffit pour la plupart des lead-gen). Si besoin d'un visage cohérent récurrent : créer le Soul ID (cf. `higgsfield-api.md` § Soul ID), stocker l'id dans `client-brand-profile.json → render.soul_id`, et l'injecter dans les cellules de style S4. Demander les photos approuvées au client.

---

## 6. Checklist art-direction (avant d'envoyer un prompt)
- [ ] Les 7 blocs présents (format, style, scène, palette, texte, composition, qualité) ?
- [ ] Hex de marque cités explicitement ?
- [ ] Texte incrusté ≤ 7 mots pour le hook, CTA ≤ 4 mots ?
- [ ] Un seul accent / un seul point focal nommé ?
- [ ] Safe zone bottom dite ?
- [ ] NEGATIVE prompt (no watermark / gibberish / distorted hands / fake logo) ?
- [ ] Référence brand asset passée si cohérence produit/visage requise ?
- [ ] Style ∈ les 12, cohérent avec l'archétype couleur du client ?
