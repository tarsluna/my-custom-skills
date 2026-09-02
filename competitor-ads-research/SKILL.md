---
name: competitor-ads-research
description: Extrait et analyse les publicités Meta (Facebook + Instagram) des concurrents d'un client depuis la Meta Ads Library, puis génère un brief stratégique au branding. Output = bibliothèque de créatives téléchargées (PNG/MP4), CSV des copies, analyse markdown des angles/patterns/hooks gagnants, et document .docx final livrable client. Adapté du skill ComposioHQ "competitive-ads-extractor" et calibré sur le process de l'agence (5 angles : Douleur/Désir/Preuve/Contre-intuitif/Urgence). Use when the user asks to "analyse les pubs des concurrents", "scrape les ads de {concurrent}", "veille concurrentielle Meta {client}", "competitor ads research", "ad library {marque}", "extraire les pubs Facebook de {marque}", "brief concurrents {client}". Trigger phrases : "analyse concurrentielle Meta", "scrape ad library", "veille pubs Facebook", "research concurrents Meta Ads", "spy ads {marque}".
---

# Competitor Meta Ads Research

Skill qui extrait les publicités Meta des concurrents d'un client, les télécharge, les catégorise, identifie les patterns gagnants et produit un brief stratégique au branding. Adapté du skill open-source [`ComposioHQ/competitive-ads-extractor`](https://github.com/ComposioHQ/awesome-claude-skills/blob/master/competitive-ads-extractor/SKILL.md) et calibré sur le process de l'agence (angles, structure de campagne, livrable .docx final).

**Crédit** : structure inspirée du skill `competitive-ads-extractor` de ComposioHQ + use case original de Sumant Subrahmanya (Lenny's Newsletter).

---

## 🎯 Quand utiliser ce skill

Trigger sur :
- "Analyse les pubs Meta des concurrents de {client}"
- "Scrape les ads de {concurrent}"
- "Veille concurrentielle Meta {client}"
- "Competitor ads research {client}"
- "Ad library {marque}"
- "Spy ads {marque}"
- "Extraire les pubs Facebook de {marque}"
- "Brief concurrents Meta {client}"

NE PAS trigger pour :
- Écrire des pubs originales pour le client → `meta-ads-copywriter`
- Faire un audit des ads du client lui-même → futur skill `meta-ads-audit`
- Recherche client avatar / ICP → `deep-search`

---

## ⚙️ Stack technique requise

Ce skill s'appuie sur le **MCP server `trypeggy/facebook-ads-library-mcp`** qui doit être installé et configuré dans Claude Code AVANT utilisation.

### Outils MCP attendus
Si le MCP est installé, ces outils sont disponibles :
- `mcp__fb_ad_library__get_meta_platform_id` — résout nom de marque → page ID
- `mcp__fb_ad_library__get_meta_ads` — extrait les ads actives d'une page
- `mcp__fb_ad_library__analyze_ad_image` — analyse vision des images
- `mcp__fb_ad_library__analyze_ad_video` — analyse vidéo (Gemini)
- `mcp__fb_ad_library__analyze_ad_videos_batch` — batch vidéo (économie tokens)
- `mcp__fb_ad_library__search_cached_media` — recherche médias en cache

### Si le MCP n'est pas installé
Le skill bascule en **mode fallback dégradé** :
1. Demande à l'utilisateur les URLs Meta Ads Library directement (`https://www.facebook.com/ads/library/?id=...`)
2. Utilise WebFetch sur les pages Meta Ads Library
3. Extrait manuellement texte + screenshots descriptifs
4. Indique clairement dans le livrable que l'analyse est en mode dégradé sans téléchargement réel des médias

### Prérequis API (côté MCP)
- **ScrapeCreators API key** (obligatoire pour le MCP) — `scrapecreators.com`
- **Google Gemini API key** (optionnelle, pour analyse vidéo) — `aistudio.google.com`

---

## 📦 Pipeline 6 phases

### Phase 1 — Inputs & cadrage
Le user doit fournir (ou tu dois demander) :
- **Nom du client** (pour structurer les outputs)
- **Marché / niche** du client (ex : closing francophone, SaaS B2B, coaching mindset...)
- **Liste des concurrents à analyser** (3 à 10 marques) — par nom de page Facebook
- **Géographie cible** (FR / BE / CH / international)
- **Profondeur d'analyse** : Quick (10 ads/concurrent) / Standard (25 ads) / Deep (50+ ads)
- **Période** : Active maintenant / Last 30 days / Last 90 days

Si certaines infos manquent, demander avant de lancer.

### Phase 2 — Résolution des marques (MCP)
Pour chaque concurrent :
1. Appeler `mcp__fb_ad_library__get_meta_platform_id` avec le nom de la marque
2. Stocker le `page_id` correspondant
3. En cas d'ambiguïté (plusieurs résultats), demander à l'utilisateur de confirmer

### Phase 3 — Extraction des ads (MCP)
Pour chaque `page_id` :
1. Appeler `mcp__fb_ad_library__get_meta_ads` avec :
   - `page_id`
   - `country` (filtré sur la géo cible)
   - `ad_active_status` : ACTIVE
   - `limit` : selon profondeur (10 / 25 / 50)
2. Récupérer pour chaque ad : ID, texte primaire, headline, description, CTA, format, durée d'activité, URL média, dates start/stop
3. **Indicateur "winner"** : ad active depuis > 21 jours = signal fort de performance (règle maison)

### Phase 4 — Analyse des créatives (MCP)
1. Téléchargement local des médias dans `creatives/[concurrent]/`
2. Pour images : `mcp__fb_ad_library__analyze_ad_image` → extraction texte, couleurs, composition, hook visuel
3. Pour vidéos : `mcp__fb_ad_library__analyze_ad_videos_batch` (en batch pour économiser les tokens) → hook 3s, structure, CTA, ton, format
4. Catégorisation automatique de chaque ad selon les **5 angles** :
   - **Douleur** (Pain) — verbalise la galère du prospect
   - **Désir** (Dream) — peint la transformation finale
   - **Preuve** (Social Proof) — case study, testimonial, chiffre
   - **Contre-intuitif** (Pattern Interrupt) — casse une croyance commune
   - **Urgence** (Scarcity / FOMO) — deadline, places limitées

### Phase 5 — Détection des patterns gagnants
Pour chaque concurrent ET en agrégé sur tous les concurrents :
- **Top hooks** (premiers 3 secondes / première phrase de la primary text)
- **Top CTAs** (les plus fréquents et ceux des winners > 21j)
- **Distribution par angle** (% des ads qui jouent quel angle)
- **Distribution par format** (FaceCam vs UGC vs Static vs Carousel vs VSL)
- **Frameworks de copy récurrents** (extraction des structures : Hook → Problem → Solution → CTA, etc.)
- **Pain points partagés** (problèmes que TOUS les concurrents ciblent — angle saturé)
- **White spaces** (angles qu'AUCUN concurrent n'exploite — opportunités pour l'agence)

### Phase 6 — Génération du livrable
Trois outputs sont produits dans `projects/{client}/competitor-research/{date}/` :

1. **`creatives/[concurrent]/`** — toutes les images et vidéos téléchargées
2. **`data.csv`** — une ligne par ad avec colonnes : `concurrent | ad_id | format | angle | hook | primary_text | headline | cta | jours_actif | winner | media_path`
3. **`analysis.md`** — analyse markdown détaillée (insights bruts, sert de source au .docx)
4. **`Brief-Concurrents-{Client}-{date}.docx`** — livrable final client au branding minimal (titre noir sur blanc, structure simple, généré avec `assets/build_research_brief.py`)

---

## 📄 Structure du document final (`.docx`)

Le brief client suit une structure fixe, ultra-simple, anti style IA :

### Section 1 — Brief stratégique
1 paragraphe court (4-7 phrases). Contexte, marché analysé, nombre de concurrents, nombre d'ads analysées, période.

### Section 2 — Vue d'ensemble du marché
- Total ads analysées
- Concurrents et volume d'ads par concurrent
- Distribution par angle (Douleur/Désir/Preuve/Contre-intuitif/Urgence)
- Distribution par format

### Section 3 — Patterns gagnants détectés
Pour chaque pattern (3-5 patterns max) :
- Nom du pattern
- Combien de concurrents l'utilisent
- Exemples concrets (1-2 verbatims d'ads winners)
- Pourquoi ça marche (1 phrase)

### Section 4 — Angles saturés vs white spaces
- **Saturé** : angles que TOUS les concurrents jouent → à éviter ou à twister
- **White space** : angles qu'AUCUN concurrent n'exploite → opportunité pour l'agence

### Section 5 — Top hooks détectés
Liste de 8-12 hooks verbatim extraits des ads winners (>21j d'activité). Pas d'analyse, juste les hooks bruts.

### Section 6 — Top CTAs détectés
Liste de 5-8 CTAs récurrents.

### Section 7 — Recommandations
3-5 recommandations actionnables pour la prochaine campagne du client. Format direct :
- **Recommandation 1** : Test l'angle "[X]" en format [Y] avec hook "[Z]"
- **Recommandation 2** : Évite l'angle "[saturé]" — déjà couvert par 4 concurrents
- etc.

### Annexe — Liste des ads analysées
Tableau simple : Concurrent | Ad ID | Angle | Hook | Jours actif | Winner ✓

---

## 📁 Structure du skill

```
competitor-ads-research/
├── SKILL.md                              ← orchestration (ce fichier)
├── frameworks/
│   ├── 5-angles.md                       ← référence des 5 angles + critères de classification
│   ├── winner-detection-rules.md         ← règles "ad winner" (>21j, fréquence, etc.)
│   └── pattern-extraction.md             ← comment extraire les patterns récurrents
├── templates/
│   ├── brief-research-structure.md       ← template markdown source du livrable
│   └── csv-schema.md                     ← schéma exact du data.csv
├── prompts/
│   ├── classify-angle.md                 ← prompt pour classifier une ad dans un des 5 angles
│   └── extract-hook.md                   ← prompt pour extraire le hook 3s
└── assets/
    └── build_research_brief.py           ← générateur .docx ultra-simple
```

---

## 🎯 Règles non négociables (agence)

1. **Toujours classifier en 5 angles**, jamais inventer d'autres catégories
2. **Toujours flagger les "winners"** (> 21 jours d'activité) — c'est notre signal #1
3. **Toujours identifier les white spaces** — c'est ce qui justifie nos campagnes
4. **Le brief final est en français**, ton direct, anti style IA
5. **Pas plus de 5 recommandations** dans le doc final (sinon noyé)
6. **Le .docx est noir sur blanc Calibri** — branding minimal de l'agence (titre uniquement)
7. **Confidentialité** : ne JAMAIS recommander de copier verbatim. On s'inspire, on twiste, on dépasse.

---

## 💬 Exemples de prompts d'activation

### Quick research (1 concurrent)
```
Analyse les pubs Meta de Closer Evolution pour le projet TopCo.
10 ads max, France, actives uniquement.
```

### Standard research (set concurrentiel)
```
Veille concurrentielle Meta pour TopCo :
- Closer Evolution
- OFAP
- Closing Mastery
- Closing Influence
25 ads par concurrent, France + Belgique, last 90 days.
```

### Deep research multi-marché
```
Research concurrents Meta pour le client {X} :
6 concurrents [liste], 50 ads chacun, FR/BE/CH, 90 derniers jours.
Focus sur l'angle "transformation 6 mois".
```

---

## ✅ Quality gate (avant livraison)

- [ ] Tous les concurrents demandés ont été résolus en `page_id`
- [ ] Au moins 80% des ads attendues ont été extraites (vs profondeur demandée)
- [ ] Tous les médias sont téléchargés dans `creatives/[concurrent]/`
- [ ] `data.csv` contient une ligne par ad avec toutes les colonnes
- [ ] Chaque ad est classifiée dans UN des 5 angles (pas "Autre")
- [ ] Les winners (>21j) sont flaggés
- [ ] L'analyse markdown identifie au moins 3 patterns gagnants
- [ ] L'analyse markdown identifie au moins 1 white space
- [ ] Le `.docx` final ne dépasse pas 4 pages (sinon trop long)
- [ ] Aucune phrase IA dans le doc final ("Dans ce brief, nous allons...", "Il est important de noter...")
- [ ] Le doc s'ouvre proprement dans Word et reste 100% modifiable

---

## 📌 Style éditorial du doc final

**À FAIRE** :
- Phrases courtes (15-25 mots)
- Verbatims directs des ads (entre guillemets)
- Chiffres concrets (X ads sur Y concurrents)
- Recommandations affirmatives ("Lance X" pas "Tu pourrais envisager X")

**À NE PAS FAIRE** :
- "Cette analyse révèle que..."
- "Il est intéressant de noter que..."
- "Nous observons une tendance..."
- Listes à puces de plus de 8 items
- Émojis (sauf si demande explicite)
- Anglicismes inutiles ("pain points" → "douleurs", "winners" → "ads gagnantes")
