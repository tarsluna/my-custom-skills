# Visual Quality Gate — Meta Ads Creatives

Checklist finale avant export et upload sur Meta. Chaque creative doit passer TOUS les checks obligatoires. Si un check echoue, corriger avant d'exporter.

---

## Safe zones

- [ ] **Feed (1080x1080)** : aucun texte critique dans les 120px de marge (tous cotes)
- [ ] **Story/Reel (1080x1920)** : rien d'important dans les 250px du top (UI bars)
- [ ] **Story/Reel (1080x1920)** : rien d'important dans les 350px du bottom (CTA natif, swipe)
- [ ] **Story/Reel** : texte dans les marges laterales de 80px respectees
- [ ] **Carousel** : pas de texte critique dans les 40px des bords lateraux (zone de preview slide adjacente)

---

## Contraste et lisibilite

- [ ] **Contraste WCAG AA** sur tous les textes body : ratio >= 4.5:1
- [ ] **Contraste WCAG AA** sur tous les textes large (H1, H2 >= 24px bold) : ratio >= 3:1
- [ ] **CTA = element au contraste le plus eleve** de toute la creative
- [ ] **Pas de texte clair sur fond clair** (zero tolerance)
- [ ] **Pas de texte jaune ou vert clair sur fond blanc**
- [ ] **Test luminosite reduite** : texte lisible avec ecran a 30% de luminosite

---

## CTA

- [ ] **CTA visible** et clairement identifiable comme bouton
- [ ] **Tap target >= 44 x 44px** (Apple HIG minimum)
- [ ] **Hauteur bouton >= 56px** (Feed) ou **>= 64px** (Story/Reel)
- [ ] **Texte bouton >= 28px**
- [ ] **Un seul CTA** par creative (pas deux actions concurrentes)
- [ ] **CTA positionne dans la zone correcte** : bottom 20% (Feed), au-dessus safe zone (Story)
- [ ] **Action claire et unique** : "Reserver", "Decouvrir", "Commencer" (pas "Cliquer ici")

---

## Typographie

- [ ] **Maximum 2 familles de fonts** dans la creative
- [ ] **Hierarchie respectee** : H1 est le texte le plus gros, CTA > Body
- [ ] **Ratio H1/Body >= 2:1** en taille
- [ ] **Line height H1 : ~1.1** (tight, compact)
- [ ] **Line height Body : ~1.3** (confortable)
- [ ] **Maximum 15 mots** de texte visible par creative (c'est une pub, pas un article)
- [ ] **H1 : max 2 lignes** (Feed) ou **3 lignes** (Story)

---

## Lisibilite mobile

- [ ] **Preview a 375px de large** effectuee (iPhone SE / iPhone mini)
- [ ] **Tous les textes lisibles** a cette taille sans plisser les yeux
- [ ] **CTA suffisamment gros** pour etre tape avec le pouce
- [ ] **Pas d'elements minuscules** perdus dans la composition

---

## Texte et compliance Meta

- [ ] **Texte < 20% de l'image** (ancienne regle Meta, toujours bonne pratique pour la diffusion)
- [ ] **Pas de claims visuels interdits** :
  - Pas d'avant/apres sante ou perte de poids
  - Pas de resultats financiers "garantis"
  - Pas de references a des attributs personnels ("En tant que femme de 40 ans...")
  - Pas de contenu trompeur visuellement (faux boutons, faux notifications)
- [ ] **Pas de texte offensant, discriminatoire ou sensationnaliste**
- [ ] **Disclaimers presents** si necessaire (mentions legales, conditions)

---

## Couleurs et palette

- [ ] **Palette coherente** avec l'archetype defini dans le brief
- [ ] **Regle 60/30/10 respectee** : une couleur dominante, une secondaire, une accent
- [ ] **Pas de 3 couleurs a parts egales** dans la composition
- [ ] **Color styles Figma lies** aux tokens du `03-color-system.md`

---

## Congruence

- [ ] **Congruence avec la Landing Page** : meme palette, meme typo, meme ambiance visuelle
- [ ] **Congruence avec le copywriter** : meme promesse, meme mecanisme, meme CTA
- [ ] **Congruence entre les variantes** : meme direction artistique, variation de contenu (pas de style)
- [ ] **Carousel : continuite visuelle** entre toutes les slides (palette, grid, elements traversants)

---

## Dark mode

- [ ] **Si fond dark** : verifie sur mobile avec luminosite haute (pas de noir delave)
- [ ] **Si fond light** : verifie que la creative se demarque dans un feed majoritairement clair
- [ ] **Les overlays** sont opaques et lisibles sur les deux modes

---

## Export technique

- [ ] **Ratio exact** : 1:1 pour Feed/Carousel, 9:16 pour Story/Reel
- [ ] **Resolution** : PNG @2x (2160px) pour images statiques
- [ ] **Format** : PNG ou JPG 95% (si PNG > 10 MB)
- [ ] **Color space** : sRGB (pas P3, pas Adobe RGB)
- [ ] **Pas de transparence/alpha** sur les exports finaux
- [ ] **Taille fichier < 30 MB** par image
- [ ] **Nommage** : `[Client]-[Format]-[Variant]-[Date].png`

---

## Verdict final

| Status | Signification | Action |
|--------|--------------|--------|
| PASS | Tous les checks sont valides | Exporter et uploader sur Meta |
| WARN | 1-2 checks mineurs echouent (non-bloquants) | Corriger si possible, documenter si pas possible |
| FAIL | 1+ check critique echoue (safe zone, contraste, CTA, compliance) | Corriger obligatoirement avant export |

**Checks critiques (FAIL immediat si echoue) :**
- Safe zones non respectees
- Contraste WCAG insuffisant sur du texte important
- CTA non cliquable (trop petit ou mal place)
- Claim visuel interdit par Meta
- Export au mauvais ratio ou mauvaise resolution

---

Date du quality gate : _______________
Resultat : PASS / WARN / FAIL
Notes : _______________
