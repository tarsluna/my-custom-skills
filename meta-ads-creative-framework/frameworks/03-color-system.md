# 03 — Color System : Palettes, Contrastes, Psychologie Couleur

Reference couleur complete pour les creatives Meta Ads. Palettes par archetype client, regles de contraste, et psychologie couleur appliquee a la performance publicitaire.

---

## Palettes par archetype client

### Urgence / Performance
*Agences, SaaS growth, e-commerce promo, FOMO*

| Role | Hex | Apercu | Usage |
|------|-----|--------|-------|
| Primary | `#FF3B30` | Rouge Meta | Headlines, urgence, prix barre |
| Secondary | `#FF6B00` | Orange energie | Accents, badges, highlights |
| Background | `#000000` ou `#1A1A2E` | Noir / dark navy | Fond principal |
| Text | `#FFFFFF` | Blanc pur | Tout le texte sur fond dark |
| Accent | `#00D4FF` | Cyan confiance | Liens, preuves, elements de validation |
| CTA Background | `#FF3B30` | Rouge | Bouton CTA principal |
| CTA Text | `#FFFFFF` | Blanc | Texte du bouton |

**Gradient optionnel** : `linear-gradient(135deg, #FF3B30, #FF6B00)` pour le fond CTA ou les separateurs.

---

### Confiance / Premium
*Consulting B2B, cabinets, services professionnels, finance*

| Role | Hex | Apercu | Usage |
|------|-----|--------|-------|
| Primary | `#0066FF` | Bleu autorite | Headlines, elements cles |
| Secondary | `#1B3A5C` | Navy profond | Sous-titres, containers |
| Background | `#FFFFFF` ou `#F5F5F7` | Blanc / gris tres clair | Fond principal |
| Text | `#1D1D1F` | Noir chaud | Tout le texte sur fond light |
| Accent | `#34C759` | Vert validation | Checkmarks, resultats, preuves |
| CTA Background | `#0066FF` | Bleu | Bouton CTA principal |
| CTA Text | `#FFFFFF` | Blanc | Texte du bouton |

**Gradient optionnel** : `linear-gradient(135deg, #0066FF, #1B3A5C)` pour les headers ou separateurs.

---

### Energie / Transformation
*Coaching, fitness, developpement personnel, formation*

| Role | Hex | Apercu | Usage |
|------|-----|--------|-------|
| Primary | `#FF9500` | Orange chaud | Headlines, elements hero |
| Secondary | `#FFD60A` | Jaune energie | Highlights, badges, accents |
| Background | `#000000` ou gradient dark | Noir | Fond principal |
| Text | `#FFFFFF` | Blanc pur | Tout le texte |
| Accent | `#BF5AF2` | Violet premium | Elements de differenciation, premium |
| CTA Background | `#FF9500` | Orange | Bouton CTA principal |
| CTA Text | `#000000` | Noir | Texte du bouton (contraste fort sur orange) |

**Gradient optionnel** : `linear-gradient(135deg, #FF9500, #FFD60A)` pour le CTA ou `linear-gradient(180deg, #1A1A2E, #000000)` pour le fond.

---

### Authority / Data
*Finance, tech, analytics, SaaS B2B serieux*

| Role | Hex | Apercu | Usage |
|------|-----|--------|-------|
| Primary | `#5856D6` | Indigo | Headlines, KPIs, graphiques |
| Secondary | `#007AFF` | Bleu tech | Sous-titres, liens, data |
| Background | `#F2F2F7` | Gris clair | Fond principal |
| Text | `#1C1C1E` | Noir profond | Tout le texte |
| Accent | `#30D158` | Vert KPI | Resultats positifs, croissance, success |
| CTA Background | `#5856D6` | Indigo | Bouton CTA principal |
| CTA Text | `#FFFFFF` | Blanc | Texte du bouton |

**Gradient optionnel** : `linear-gradient(135deg, #5856D6, #007AFF)` pour les headers ou cards data.

---

## Regles de contraste (WCAG AA)

### Ratios minimum obligatoires

| Type de texte | Ratio minimum | Exemple OK | Exemple KO |
|---------------|---------------|------------|------------|
| Body text (< 24px bold) | **4.5:1** | Blanc sur noir (21:1) | Gris clair sur blanc (1.5:1) |
| Large text (>= 24px bold ou >= 18.66px regular) | **3:1** | Blanc sur bleu #0066FF (8.6:1) | Jaune #FFD60A sur blanc (1.1:1) |
| Elements CTA | **Le plus eleve de la creative** | Rouge #FF3B30 sur noir (5.5:1) | Orange clair sur fond orange |
| Texte decoratif / non-essentiel | 3:1 recommande | Caption grise sur blanc | — |

### Comment verifier le contraste

1. **Dans Figma** : plugin "Contrast" ou "A11y - Color Contrast Checker"
2. **En ligne** : [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
3. **Regle rapide** : si tu plisses les yeux et que le texte disparait, le contraste est insuffisant

### Combinaisons a eviter absolument

| Combinaison | Pourquoi |
|-------------|----------|
| Texte blanc sur fond jaune | Ratio < 2:1, illisible |
| Texte vert clair sur fond blanc | Ratio < 3:1 |
| Texte gris clair (#AAAAAA) sur fond blanc | Ratio 2.3:1, insuffisant |
| Texte rouge sur fond vert (ou inverse) | Problematique pour les daltoniens (8% des hommes) |
| Texte bleu clair sur fond violet | Contraste faible, fatigue visuelle |

### Regle du "test luminosite reduite"

Reduire la luminosite de l'ecran a 30% et verifier que tous les textes restent lisibles. Sur Meta, beaucoup d'utilisateurs scrollent dans des conditions de luminosite faible (transports, soir, lit).

---

## Psychologie couleur appliquee aux Meta Ads

### Tableau de reference

| Couleur | Emotion primaire | Usage Meta Ads | Quand l'utiliser |
|---------|-----------------|----------------|------------------|
| **Rouge** | Urgence, danger, passion | Prix barres, countdown, promo | Flash sales, FOMO, offres limitees |
| **Orange** | Energie, enthousiasme, action | CTA, badges "nouveau", highlights | Coaching, transformation, lancement |
| **Jaune** | Attention, optimisme, disruption | Highlights, pattern interrupt | Hook slide carousel, avertissements |
| **Vert** | Resultat, argent, validation | Checkmarks, resultats, profits | Preuves, ROI, temoignages, "valide" |
| **Bleu** | Confiance, securite, autorite | Fonds, headlines B2B | B2B, SaaS, consulting, services pro |
| **Violet** | Creativite, premium, transformation | Accents, elements premium | High-ticket, coaching premium |
| **Noir** | Luxe, autorite, puissance | Fonds dark, texte premium | Offres premium, autorite, exclusivite |
| **Blanc** | Clarte, simplicite, espace | Fonds light, respiration | B2B clean, SaaS, minimaliste |
| **Rose** | Douceur, feminite, soin | Accents, fonds pastel | B2C feminin, bien-etre, beaute |

### Dark mode vs Light mode

- **Dark mode (fond noir/dark)** : +15-20% de CTR en moyenne sur Meta (source: tests internes)
  - Raison : le feed Meta est majoritairement clair, le dark se demarque par contraste
  - Le texte blanc sur fond noir est plus lisible sur mobile
  - Sensation de "premium" et d'autorite
  - Recommande par defaut pour la plupart des archetypes

- **Light mode (fond blanc/clair)** :
  - Meilleur pour les marques qui veulent un ton "propre", "corporate", "accessible"
  - Indispensable si la brand guide impose des fonds clairs
  - Bien pour les screenshots d'UI (SaaS) qui sont deja sur fond clair

### Regle de dominance

Dans chaque creative, une seule couleur domine :
- **60%** : couleur de fond (background)
- **30%** : couleur secondaire (texte, containers)
- **10%** : couleur d'accent (CTA, highlights, preuves)

Ne jamais avoir 3 couleurs a parts egales. La hierarchie visuelle depend de la dominance couleur.

---

## Color Styles Figma a creer

Pour chaque projet, creer les color styles suivants dans Figma :

```
Meta Ads / Background / Primary     -> [hex du fond principal]
Meta Ads / Background / Secondary   -> [hex du fond secondaire, cards]
Meta Ads / Text / Primary           -> [hex du texte principal]
Meta Ads / Text / Secondary         -> [hex du texte secondaire, captions]
Meta Ads / Brand / Primary          -> [hex couleur primaire]
Meta Ads / Brand / Secondary        -> [hex couleur secondaire]
Meta Ads / Brand / Accent           -> [hex accent]
Meta Ads / CTA / Background         -> [hex fond bouton]
Meta Ads / CTA / Text               -> [hex texte bouton]
Meta Ads / Semantic / Success        -> #34C759 (vert validation)
Meta Ads / Semantic / Urgency        -> #FF3B30 (rouge urgence)
Meta Ads / Semantic / Info           -> #007AFF (bleu info)
Meta Ads / Overlay / Dark            -> rgba(0, 0, 0, 0.65)
Meta Ads / Overlay / Light           -> rgba(255, 255, 255, 0.85)
```

Remplacer les valeurs `[hex ...]` par les couleurs de la palette choisie pour le client.
