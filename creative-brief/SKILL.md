---
name: creative-brief
description: Génère un brief créatif structuré pour le creative strategist (créa strat) de votre agence. Le brief contient toutes les informations nécessaires pour créer les visuels dans Figma — identité de marque, audience cible, paysage concurrentiel, 10 templates créatifs avec copywriting, style visuel, et liens vers tous les documents de référence. Le résultat est injecté dans l'app the platform (onglet "Brief Créatif") via la colonne ai_static_prompt avec le préfixe CREATIVE_BRIEF_JSON:. Use when the user asks to "brief créatif {client}", "creative brief {client}", "brief créa strat {client}", "brief designer {client}", "brief Figma {client}". Trigger phrases: "brief créatif", "creative brief", "brief créa strat", "brief designer", "brief Figma".
---

# Creative Brief Generator

Skill qui produit le **brief créatif structuré** que le creative strategist de votre agence utilise pour créer les visuels publicitaires dans Figma. Le brief centralise toutes les données client (onboarding, deep search, competitor ads) dans un format exploitable par le designer.

**Format de sortie** : JSON structuré injecté dans l'app the platform via `ai_static_prompt` (préfixe `CREATIVE_BRIEF_JSON:`). Le brief est ensuite éditable dans l'onglet "Brief Créatif" de la campagne.

**Règles critiques** :
- **Emojis obligatoires** dans le contenu HTML généré pour structurer visuellement les sections.
- **HTML simple compatible Tiptap** : balises `<p>`, `<h2>`, `<h3>`, `<h4>`, `<strong>`, `<em>`, `<ul>`, `<li>`, `<ol>`, `<a>`. Pas de CSS inline, pas de classes, pas de divs complexes.
- **10 templates créatifs minimum** avec des angles marketing distincts.
- **Français** pour tout le contenu.

---

## 🎯 Quand utiliser ce skill

Trigger sur :
- "Brief créatif pour {client}"
- "Creative brief {client}"
- "Brief créa strat {client}"
- "Brief designer {client}"
- "Brief Figma {client}"
- "Génère le brief créatif pour {client}"

NE PAS trigger pour :
- Créer la proposition de campagne → `campaign-proposal`
- Écrire les scripts d'ads → `meta-ads-copywriter`
- Écrire un script VSL → `vsl-copywriter`
- Recherche client → `deep-search`
- Analyser les pubs concurrentes → `competitor-ads-research`

---

## 📦 Structure du brief généré

Le brief a **7 sections** + **10 templates créatifs** :

### 1. Identité de marque 🏢
- Nom de marque, logo (lien si disponible)
- Site web, drive/assets
- Couleurs de marque (codes hex)
- Polices / typographie
- Guidelines visuelles existantes
- Ton de marque

### 2. Audience cible 🎯
- Persona principal (démographique + psychographique)
- Douleurs / frustrations principales
- Désirs / aspirations
- Objections à l'achat
- Déclencheurs d'achat
- Langage utilisé par la cible
- Insights deep search (si disponible)

### 3. Paysage concurrentiel 🔍
- Concurrents identifiés et leur positionnement
- Styles visuels observés dans les pubs concurrentes
- Angles publicitaires utilisés par les concurrents
- Opportunités de différenciation
- Insights competitor ads research (si disponible)

### 4. Templates créatifs 🎨 (10 minimum)
Pour chaque template :
- **Nom** : identifiant descriptif
- **Format** : Image statique 1080x1080, 1080x1350, ou Carrousel
- **Angle** : Douleur, Désir, Preuve sociale, Contre-intuitif, Urgence, Autorité, Comparaison, Témoignage, Éducatif, Transformation
- **Headline** : phrase courte qui arrête le scroll (max 8 mots)
- **Sub-headline** : phrase de support (max 15 mots)
- **Bullet points** : 3-4 points texte à mettre sur le visuel
- **Style direction** : description courte du style visuel recommandé

### 5. Direction copywriting ✍️
- Ton de voix (formel/informel, tutoiement/vouvoiement)
- Messaging framework (promesse → preuves → CTA)
- Messages clés à utiliser
- Formulations à éviter
- Exemples de bons vs mauvais textes

### 6. Recommandations style visuel 🖼️
- Palette de couleurs recommandée (reprendre brand + complémentaires)
- Typographie recommandée
- Style d'imagerie (photo, illustration, 3D, flat design)
- Mood / ambiance visuelle
- Exemples de styles de référence
- Mise en page recommandée

### 7. Références & Documents 📁
- Liens vers tous les documents source
- Assets de marque (logo, fonts, brand book)
- Documents stratégiques (onboarding, deep search)
- Exemples visuels (competitor ads, inspirations)
- Liens utiles (site web, réseaux sociaux, drive)

---

## 🔄 Pipeline (3 phases)

### Phase 1 — Collecte des données

Lire toutes les sources disponibles pour le client :

1. **Onboarding** : `projects/{client}/00-onboarding/` — toutes les réponses du formulaire d'onboarding.
2. **Deep Search** : `projects/{client}/01-deep-search/` — analyse approfondie du client, marché, persona.
3. **Competitor Ads** : `projects/{client}/02-competitor-ads/` — analyse des publicités concurrentes.
4. **Campaign Proposal** : `projects/{client}/03-campaign-proposal/` — proposition de campagne si déjà générée.

Si un dossier n'existe pas, continuer avec les données disponibles. Demander au user les infos manquantes critiques (nom du client, offre principale).

### Phase 2 — Génération du brief

Générer les 7 sections HTML + 10 templates créatifs structurés.

**Règles de rédaction** :
- Emojis pour structurer visuellement chaque section
- HTML simple compatible Tiptap (pas de CSS inline, pas de classes)
- Français, ton direct et professionnel
- Données spécifiques au client (pas de placeholders génériques)
- Chaque template doit avoir un angle marketing distinct
- Les headlines doivent être percutants et courts (max 8 mots)
- Inclure tous les liens et documents disponibles dans la section références

### Phase 3 — Injection dans l'app the platform

Après la génération du brief, **injecter automatiquement** le contenu structuré dans la base de données de l'app the platform.

**Étapes :**

1. Identifier le `campaign_id` du client dans Supabase (table `campaigns`, chercher par `name` contenant le nom du client ou par `client_id`).

2. Construire l'objet JSON structuré :

```json
{
  "brandIdentityHtml": "<h3>🏢 Marque</h3><p>...</p>",
  "targetAudienceHtml": "<h3>🎯 Persona principal</h3><p>...</p>",
  "competitiveLandscapeHtml": "<h3>🔍 Analyse concurrentielle</h3><p>...</p>",
  "templates": [
    {
      "id": "tpl-1",
      "name": "Template 1 — Douleur",
      "format": "Image statique 1080x1080",
      "angle": "Douleur",
      "headline": "...",
      "subHeadline": "...",
      "bulletPoints": ["...", "...", "..."],
      "styleDirection": "..."
    },
    {
      "id": "tpl-2",
      "name": "Template 2 — Désir",
      "format": "Image statique 1080x1350",
      "angle": "Désir",
      "headline": "...",
      "subHeadline": "...",
      "bulletPoints": ["...", "...", "..."],
      "styleDirection": "..."
    }
  ],
  "copywritingDirectionHtml": "<h3>✍️ Ton de voix</h3><p>...</p>",
  "visualStyleHtml": "<h3>🎨 Palette de couleurs</h3><p>...</p>",
  "referencesHtml": "<h3>📁 Assets de marque</h3><ul><li>...</li></ul>"
}
```

3. Sérialiser en JSON string et le stocker dans la colonne `ai_static_prompt` de la campagne avec le préfixe `CREATIVE_BRIEF_JSON:` :

```bash
# Injection via API REST Supabase
curl -X PATCH "https://YOUR-PROJECT.supabase.co/rest/v1/campaigns?id=eq.{CAMPAIGN_ID}" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=minimal" \
  -d '{"ai_static_prompt": "CREATIVE_BRIEF_JSON:{...le JSON sérialisé...}"}'
```

Les clés se trouvent dans : `<your-app>/.env.local`

**Important** : Le HTML dans les champs `*Html` doit être du HTML simple compatible Tiptap (balises `<p>`, `<h2>`, `<h3>`, `<h4>`, `<strong>`, `<em>`, `<ul>`, `<li>`, `<ol>`, `<a>`). Pas de CSS inline, pas de classes, pas de divs complexes.

---

## 📁 Fichiers du skill

```
creative-brief/
├── SKILL.md          ← orchestration (ce fichier)
```

---

## ✅ Quality gate (avant de livrer le brief)

- [ ] Les 7 sections HTML sont remplies avec du contenu spécifique au client
- [ ] 10 templates créatifs avec 10 angles distincts
- [ ] Chaque template a un headline, sub-headline, 3+ bullet points, et une direction style
- [ ] Emojis présents dans chaque section pour la structuration visuelle
- [ ] HTML compatible Tiptap (pas de CSS inline, pas de divs)
- [ ] Section références contient tous les liens/documents disponibles
- [ ] JSON injecté dans Supabase avec préfixe CREATIVE_BRIEF_JSON:
- [ ] Brief visible dans l'onglet "Brief Créatif" de l'app the platform
- [ ] Aucune phrase générique/placeholder — tout est spécifique au client

---

## 📌 Style éditorial obligatoire

**À FAIRE** :
- Emojis pour structurer visuellement (🎯 🔍 🎨 ✍️ 📁 etc.)
- Phrases directes et actionables
- Données chiffrées quand disponibles
- Liens cliquables vers les sources
- Français courant, pas de jargon IA

**À NE PAS FAIRE** :
- Placeholders génériques ("[insérer ici]", "à définir")
- Sections vides ou trop courtes
- HTML complexe (divs, classes CSS, styles inline)
- Anglicismes inutiles
- Tournures passives ou vagues
