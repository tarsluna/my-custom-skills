---
name: campaign-proposal
description: Génère le document officiel "Proposition de Campagne Meta Ads" que votre agence remet à ses clients post-onboarding. Document Word ultra-simple noir sur blanc, branding minimal (titre uniquement), structuré en 3 sections fixes — (1) Brief stratégique & objectif de test, (2) Formulaire de qualification (si Instant Form) ou Script VSL (si funnel VSL), (3) Structure des campagnes Meta (campagne → ad sets → créatives avec angles). Par défaut les créatives sont des IMAGES STATIQUES (pas de scripts vidéo sauf demande explicite de l'utilisateur). NE JAMAIS inclure de section KPIs / seuils de décision / projections dans le document. Use when the user asks to "crée une proposition de campagne", "doc proposition campagne {client}", "campaign proposal {client}", "document campagne Meta", "deck post-onboarding", "proposition stratégique Meta Ads", "structure de campagne pour {client}". Trigger phrases: "proposition de campagne", "campaign proposal", "doc post onboarding", "structure campagne Meta", "doc client Meta Ads".
---

# Campaign Proposal Generator

Skill qui produit le **document officiel de proposition de campagne Meta Ads** que votre agence envoie à ses clients juste après l'onboarding. Le document détaille exactement les campagnes que l'agence va lancer, le funnel d'acquisition choisi, le formulaire de qualification (ou script VSL), et la structure complète des campagnes Meta.

**Format de sortie** : `.pdf` brandé the platform — logo en filigrane centré sur chaque page, page de couverture avec logo + nom du client + date, mise en forme épurée avec les couleurs the platform (bleu #4A7FD4 / bleu foncé #1E2A4A). Simple, professionnel, pas de fioritures excessives. Le client doit voir un document propre et brandé, pas un livrable IA générique.

**Règles critiques** :
- **Créatives = images statiques par défaut.** On ne produit PAS de scripts vidéo (face cam, UGC, etc.) sauf si l'utilisateur le demande explicitement. Les créatives dans ce document sont des visuels statiques avec un angle, un headline et un texte d'accompagnement.
- **Pas de KPIs / seuils de décision / projections.** Le document ne contient JAMAIS de section "KPIs", "métriques", "seuils de décision", "règles d'optimisation" ou "projections". C'est un livrable stratégique orienté client, pas un reporting interne.

---

## 🎯 Quand utiliser ce skill

Trigger sur :
- "Crée une proposition de campagne pour {client}"
- "Doc proposition campagne {client}"
- "Génère le document post-onboarding {client}"
- "Campaign proposal {client}"
- "Structure de campagne Meta pour {client}"
- "Doc stratégique Meta Ads {client}"

NE PAS trigger pour :
- Écrire seulement les scripts d'ads → `meta-ads-copywriter`
- Écrire un script VSL long → `vsl-copywriter`
- Recherche client → `deep-search`

---

## 📦 Structure du document généré

Le document a **3 sections fixes**, dans cet ordre, sans rien d'autre :

### 1. Brief stratégique & objectif de test
- 1 paragraphe court (4-7 phrases max)
- Contexte client + offre cible
- Funnel d'acquisition choisi (Instant Form OU VSL)
- Objectif de test sur la phase 1 (CPL cible, volume cible, durée du test, ce qu'on cherche à valider)

### 2A. Formulaire de qualification (SI Instant Form)
- Liste numérotée des questions
- Pour chaque question : énoncé + type (choix multiple / texte libre / choix unique) + options de réponse
- Logique de qualification claire : **quelles réponses qualifient un lead** vs **quelles réponses le disqualifient**
- Bloc final "Lead qualifié si..." avec règles de scoring

### 2B. Script VSL (SI funnel VSL)
- Insère le script VSL complet (généralement produit par `vsl-copywriter`)
- Format : blocs numérotés avec timestamps
- Pas de notes réa, pas de commentaires — juste le voice over

### 3. Structure des campagnes Meta
Pour CHAQUE campagne (généralement une seule, voir règles ci-dessous) :
- **Nom de la campagne** (convention : `[CLIENT] - [OFFRE] - [OBJECTIF]`)
- **Objectif de campagne** (Leads, Conversions, Trafic, etc.)
- **Budget quotidien**
- **Ad sets** (généralement 2 max) :
  - Ad set 1 : Audience par intérêts (lister les intérêts ciblés, géo, âge, sexe)
  - Ad set 2 : Audience Broad (géo + âge + sexe uniquement, pas d'intérêts)
- **Créatives** : 5 à 10 créatives par campagne, regroupées par angle à tester.
  - **Par défaut = images statiques** : Pour chaque créative, indiquer uniquement : nom, angle marketing, headline image, texte d'accompagnement (primary text). Pas besoin de détailler un script complet — rester synthétique sur l'angle.
  - **Si l'utilisateur demande explicitement des scripts vidéo** : alors et seulement alors, passer en mode scripts avec hook / body / CTA par créative.

---

## 🧠 Règles de structuration des campagnes (philosophie the platform)

Ces règles sont **non négociables** sauf instruction contraire explicite du user :

### Combien de campagnes ?
- **1 seule campagne** par défaut, surtout pour PME/TPE et faibles budgets
- Créer une **2ème campagne SI** :
  - Offres réellement différentes (ex : produit A et produit B sans rapport)
  - Objectifs Meta différents (ex : Leads vs Conversions vs Sales)
  - Géographies très différentes nécessitant un budget séparé
- Sinon : tout dans une seule campagne. La consolidation budgétaire est une règle Meta 2026.

### Combien d'ad sets ?
- **2 ad sets maximum** par campagne pour la phase de test
- Ad set 1 = **Audience par intérêts** (test audience chaude/tiède)
- Ad set 2 = **Audience Broad** (laisse Meta optimiser sans contraintes d'intérêts)
- Cette structure permet de tester audience ET créatives en même temps

### Combien de créatives ?
- **5 à 10 créatives par campagne** (pas par ad set — par campagne, dupliquées dans les 2 ad sets)
- Chaque créative = un angle marketing distinct
- Diversité créative > volume créatif (depuis l'update Andromeda Meta)

### Budget
- Suivre les indications du brief client. Si non précisé : recommander 30-50€/jour minimum pour PME pour permettre la sortie de phase d'apprentissage.
- Allocation : 100% sur la campagne unique (pas de séparation testing/scaling tant que rien n'a été validé).

---

## 🔄 Pipeline (5 phases)

### Phase 1 — Collecte du brief
Le user doit fournir (ou tu dois demander si manquant) :
- Nom du client
- Offre principale (produit/service + prix + promesse)
- Funnel choisi : **Instant Form** ou **VSL** (si pas clair, demander)
- Audience cible (ICP, géo, âge, intérêts potentiels)
- Budget quotidien envisagé
- Objectif test (volume leads cible, CPL cible, durée test)
- Si Instant Form : critères de qualification (qu'est-ce qu'un bon lead ?)
- Si VSL : récupérer le script VSL existant ou indiquer où le trouver

### Phase 2 — Génération du brief stratégique
- Rédiger le paragraphe d'intro (4-7 phrases)
- Style : direct, professionnel, zéro jargon IA, zéro tournure du genre "dans cette proposition, nous allons..."
- Aller droit au but : "L'objectif de cette première phase est de [X]. Pour y parvenir, on lance [Y]."

### Phase 3 — Section formulaire OU script VSL

**Si Instant Form** :
- Construire 4-6 questions max (Meta limite à 15 mais on garde court pour pas tuer la conversion)
- Questions classiques : (1) intention/projet, (2) timeline, (3) budget, (4) contact
- Formuler les options de réponse de façon à ce que les "mauvaises" réponses soient claires
- Définir la règle de qualification : ex "Lead qualifié si Q2 = 'Dans les 3 prochains mois' ET Q3 ≥ 'X €'"

**Si VSL** :
- Insérer le script complet, déjà produit par `vsl-copywriter` ou fourni par le user
- Pas de notes réa dans ce document client — juste le texte des blocs

### Phase 4 — Génération de la structure des campagnes
- Définir le nom de campagne (convention)
- Définir l'objectif Meta exact
- Construire les 2 ad sets (intérêts + broad)
- **Créatives = images statiques par défaut** : pour chaque créative, indiquer le nom, l'angle marketing, le headline de l'image et le primary text. Rester synthétique — pas de script détaillé.
- Si l'utilisateur demande explicitement des scripts vidéo (face cam, UGC, etc.) : alors ajouter hook / body / CTA pour chaque créative.
- Si 5 créatives : couvrir au moins 5 angles distincts (douleur, désir, preuve sociale, contre-intuitif, urgence/scarcity)
- Si 10 créatives : ajouter variations d'angles supplémentaires

**INTERDIT dans ce document** : section KPIs, seuils de décision, métriques de performance, projections, règles d'optimisation. Ce n'est pas un reporting interne.

### Phase 5 — Génération du PDF
Utiliser le builder Python `assets/build_proposal.py` qui génère un PDF brandé the platform :
- Page de couverture : ton logo centré + "Proposition de Campagne" + nom du client + date
- Logo en filigrane (watermark très léger, opacité ~4%) centré sur chaque page
- Couleurs brand : bleu #4A7FD4 pour les titres H2 et lignes, bleu foncé #1E2A4A pour les H1
- Police : Helvetica, propre et lisible
- Footer : "the platform — Confidentiel" en bas de chaque page
- Pas de fioritures excessives — épuré et professionnel

Commande :
```bash
python3 assets/build_proposal.py <input.md> <output.pdf> \
  --client "Nom Client" \
  --logo "path/to/logo.png" \
  --date "DD/MM/YYYY"
```

Le logo par défaut est `projects/logo.png`.

Sauvegarder dans : `projects/{client}/03-campaign-proposal/Proposition-Campagne-{Client}.pdf`

### Phase 6 — Injection dans l'app the platform

Après la génération du PDF, **injecter automatiquement** le contenu structuré de la proposition dans la base de données de l'app the platform. Cela permet aux administrateurs de retrouver la proposition directement dans l'onglet "Proposition" de la campagne et de la modifier via l'éditeur rich text intégré.

**Étapes :**

1. Identifier le `campaign_id` du client dans Supabase (table `campaigns`, chercher par `name` contenant le nom du client ou par `client_id`).

2. Construire un objet JSON structuré avec les 3 sections de la proposition :

```json
{
  "briefHtml": "<p>Contenu HTML du brief stratégique...</p>",
  "qualificationHtml": "<h3>Question 1...</h3><p>...</p>",
  "campaigns": [
    {
      "id": "uuid-généré",
      "name": "Nom de la campagne",
      "objective": "Leads",
      "dailyBudget": "50 €/jour",
      "testDuration": "14 jours",
      "adSets": [
        { "name": "Audience par intérêts", "geo": "France", "age": "25-55", "sex": "Tous", "interests": "liste..." },
        { "name": "Audience Broad", "geo": "France", "age": "25-55", "sex": "Tous", "interests": "aucun" }
      ],
      "creatives": [
        { "name": "Créative 1", "angle": "Douleur", "format": "Image statique 1080x1080", "headline": "...", "primaryText": "..." },
        { "name": "Créative 2", "angle": "Désir", "format": "Image statique 1080x1080", "headline": "...", "primaryText": "..." }
      ]
    }
  ]
}
```

3. Sérialiser en JSON string et le stocker dans la colonne `ai_vsl_prompt` de la campagne avec le préfixe `PROPOSAL_JSON:` :

```bash
# Injection via API REST Supabase
curl -X PATCH "https://YOUR-PROJECT.supabase.co/rest/v1/campaigns?id=eq.{CAMPAIGN_ID}" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=minimal" \
  -d '{"ai_vsl_prompt": "PROPOSAL_JSON:{...le JSON sérialisé...}"}'
```

Les clés se trouvent dans : `<your-app>/.env.local`

**Important** : Le HTML dans `briefHtml` et `qualificationHtml` doit être du HTML simple compatible Tiptap (balises `<p>`, `<h2>`, `<h3>`, `<strong>`, `<em>`, `<ul>`, `<li>`, `<ol>`). Pas de CSS inline, pas de classes, pas de divs complexes.

---

## 📁 Fichiers du skill

```
campaign-proposal/
├── SKILL.md                          ← orchestration (ce fichier)
├── templates/
│   ├── proposal-structure.md         ← template markdown source du document
│   ├── instant-form-questions.md     ← banque de questions de qualification types
│   └── campaign-naming.md            ← convention de nommage des campagnes Meta
├── frameworks/
│   ├── campaign-structure-rules.md   ← règles non négociables (1 campagne, 2 ad sets, 5-10 creas)
│   ├── audience-targeting.md         ← comment construire les 2 ad sets (intérêts + broad)
│   └── creative-angles.md            ← 5 angles types pour générer les créatives
└── assets/
    └── build_proposal.py             ← générateur .docx ultra-simple
```

---

## ✅ Quality gate (avant de livrer le doc au user)

- [ ] PDF généré avec page de couverture (logo + client + date)
- [ ] Section 1 = brief stratégique en 1 paragraphe court (pas 3 paragraphes)
- [ ] Section 2 = soit formulaire avec règle de qualification claire, soit script VSL complet
- [ ] Section 3 = 1 seule campagne (sauf justification explicite), 2 ad sets, 5-10 créatives
- [ ] Chaque créative a un angle clair, un headline et un primary text (images statiques par défaut — scripts vidéo uniquement si demandés)
- [ ] Aucune phrase qui sonne IA ("Dans cette proposition...", "Nous allons explorer...", "Il est important de noter que...")
- [ ] Aucune icône, aucune emoji, aucun cadre coloré dans le .docx
- [ ] Document ouvre proprement dans Word et reste 100% modifiable
- [ ] Le ton est direct, professionnel, et respecte la voix the platform : *"On vous trouve des leads qualifiés en automatique. Vous, vous signez."*

---

## 📌 Style éditorial obligatoire

**À FAIRE** :
- Phrases courtes (15-25 mots)
- "On" direct, tutoiement-vouvoiement business
- Promesses chiffrées
- Affirmations sans hedge ("On lance X" pas "Nous pourrions envisager de lancer X")
- Pas plus de 2 paragraphes par section

**À NE PAS FAIRE** :
- "Cette proposition vise à..."
- "Il est important de souligner que..."
- "Nous allons explorer ensemble..."
- "Dans le cadre de notre collaboration..."
- Listes à puces de plus de 7 items
- Émojis (sauf si demande explicite)
- Tournures ampoulées
