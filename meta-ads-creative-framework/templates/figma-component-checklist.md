# Figma Component Checklist

Checklist pour construire les composants Figma d'une campagne Meta Ads. A suivre dans l'ordre pour chaque nouveau projet client.

---

## 1. Setup initial

- [ ] Creer un nouveau fichier Figma nomme `[Client] — Meta Ads Creatives`
- [ ] Creer une page "Components" pour les composants reutilisables
- [ ] Creer une page par format demande ("Feed 1:1", "Story 9:16", "Carousel")
- [ ] Definir les Color Styles selon `03-color-system.md` (cf. liste des styles a creer)
- [ ] Definir les Text Styles selon `02-typography-system.md` (cf. liste des styles a creer)

---

## 2. Frames de base

- [ ] Frame Feed : 1080 x 1080px, fill couleur Background Primary
- [ ] Frame Story/Reel : 1080 x 1920px, fill couleur Background Primary
- [ ] Frame Carousel slide : 1080 x 1080px, fill couleur Background Primary
- [ ] Guides de safe zones places sur chaque frame :
  - Feed : 120px margins (tous cotes)
  - Story : 250px top, 350px bottom, 80px left/right
  - Carousel : 120px margins + 40px edges laterales

---

## 3. Composant CTA (obligatoire)

- [ ] Creer un composant CTA avec les proprietes suivantes :
  - Auto-layout horizontal
  - Padding : 16px vertical, 48px horizontal (minimum)
  - Border-radius : selon le pattern choisi (999px pill, 8px square, 16px rounded)
  - Fill : Color Style `Meta Ads / CTA / Background`
  - Text : Text Style `Meta Ads / CTA / Feed` ou `Meta Ads / CTA / Story`
- [ ] Creer les variants du CTA :
  - `Type` : Pill / Square / Ghost / Full-width
  - `Size` : Feed (56px height) / Story (64px height)
- [ ] Verifier le tap target >= 44 x 44px sur toutes les variants
- [ ] Le composant CTA est publie et reutilisable

---

## 4. Composant Text Block

- [ ] Creer un composant "Text Block" avec auto-layout vertical :
  - H1 (Text Style lie)
  - H2 (Text Style lie, optionnel, toggle via variant)
  - Body (Text Style lie, optionnel)
- [ ] Creer les variants :
  - `Format` : Feed / Story (change les tailles de texte)
  - `Hierarchy` : H1 only / H1 + H2 / H1 + H2 + Body
- [ ] Verifier que le hug content fonctionne (le bloc s'adapte au texte)

---

## 5. Composant Logo

- [ ] Importer le logo client (SVG de preference, sinon PNG @2x)
- [ ] Creer un composant logo avec contrainte de taille : 80 x 80px max
- [ ] Creer les variants :
  - `Position` : Top-left / Bottom-right
  - `Style` : Full color / Monochrome white / Monochrome dark
- [ ] Verifier la lisibilite du logo a petite taille sur fond dark et light

---

## 6. Composant Overlay

- [ ] Creer un composant "Overlay" pour placer du texte sur des images :
  - Rectangle avec fill `Meta Ads / Overlay / Dark` (rgba noir 65%)
  - Border-radius : 8-16px selon le layout
  - Padding : 24-32px
- [ ] Creer la variant Light : `Meta Ads / Overlay / Light` (rgba blanc 85%)
- [ ] Le composant contient un slot pour le Text Block

---

## 7. Composant Proof Badge (optionnel)

- [ ] Badge pour preuves sociales / resultats :
  - Auto-layout horizontal : icone + texte
  - Fill : accent color ou transparent avec bordure
  - Text : Body style, couleur accent
  - Exemples : "127 clients accompagnes", "4.9/5 sur Google", "+300% de leads"
- [ ] Variants : `Style` (filled / outlined), `Size` (small / medium)

---

## 8. Composant Urgency Strip (optionnel)

- [ ] Bande d'urgence pour les promos / offres limitees :
  - Full width, height 48-56px
  - Fill : rouge urgence ou accent
  - Text : bold, blanc, CAPS
  - Exemples : "OFFRE LIMITEE — 48H", "PLUS QUE 3 PLACES"
- [ ] Placement : top ou bottom de la creative (mais pas dans les safe zones Story)

---

## 9. Assembly des layouts

- [ ] Pour chaque format demande, assembler les composants dans les layouts definis par `01-layout-system.md` :
  - Feed : Layout A, B, ou C selon la direction artistique
  - Story : Layout D, E, ou F
  - Carousel : structure narrative (slide 1 hook, slides 2-N progression, derniere slide CTA)
- [ ] Verifier l'alignement sur la grille Rule of Thirds
- [ ] Verifier que les safe zones sont respectees (aucun composant critique dans les zones interdites)

---

## 10. Variants finales

- [ ] Creer les variants de chaque creative :
  - `Theme` : Light / Dark
  - `Proof` : With proof / Without proof
  - `Urgency` : With urgency strip / Without
- [ ] Nommer les frames selon la convention : `[Format]-[Layout]-[Theme]-[Variant]`
  - Exemple : `Feed-HeroOverlay-Dark-V1`, `Story-StackedCards-Dark-V2`
- [ ] Chaque variant doit etre autonome (pas de dependance a un composant non-inclus)

---

## 11. Export settings

- [ ] Configurer les export settings sur chaque frame finale :
  - Images : PNG @2x (2160px pour Feed, 2160x3840 pour Story)
  - Alternative : JPG 95% si PNG > 10 MB
  - Color profile : sRGB
  - Pas de transparence
- [ ] Verifier que les exports ne depassent pas 30 MB par fichier
- [ ] Nommer les exports : `[Client]-[Format]-[Variant]-[Date].png`
  - Exemple : `TopCo-feed-v1-dark-20260410.png`

---

## 12. Responsive check

- [ ] Ouvrir chaque creative en preview mobile (375px de large)
- [ ] Verifier que tous les textes sont lisibles
- [ ] Verifier que le CTA est assez gros pour etre tape
- [ ] Verifier que les elements importants ne sont pas coupes
- [ ] Si un probleme est detecte : ajuster les tailles (augmenter, jamais reduire)

---

## Resume

| Composant | Obligatoire | Variants minimum |
|-----------|-------------|-----------------|
| Frame de base | Oui | 1 par format |
| CTA Button | Oui | Type x Size (4x2 = 8) |
| Text Block | Oui | Format x Hierarchy (2x3 = 6) |
| Logo | Oui | Position x Style (2x3 = 6) |
| Overlay | Oui | Dark / Light (2) |
| Proof Badge | Optionnel | Style x Size (2x2 = 4) |
| Urgency Strip | Optionnel | 1 |
