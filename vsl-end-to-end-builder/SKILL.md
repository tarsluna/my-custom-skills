---
name: vsl-end-to-end-builder
description: Pipeline complet pour produire une Video Sales Letter (VSL) de A à Z à partir d'un brief client. Use when the user asks to build, write, draft, structure, or produce a VSL, video sales letter, sales video, video script for ads, or "faire une VSL", "écrire une VSL", "script VSL", "vidéo de vente". Trigger phrases: "create a VSL", "write a VSL", "build a sales video", "VSL script", "vidéo de vente longue", "script de vente vidéo".
---

# VSL End-to-End Builder

Un pipeline structuré pour produire une Video Sales Letter complète : du brief client au script final prêt à tourner, en passant par la stratégie d'angle et l'architecture émotionnelle.

## Quand utiliser ce skill
- L'utilisateur veut produire une VSL pour un client (the platform ou autre).
- L'utilisateur a un produit/offre et veut un script vidéo de vente.
- L'utilisateur demande une refonte de VSL existante.

## Quand NE PAS l'utiliser
- Simple post réseaux sociaux ou ad courte (< 60s) → utiliser un skill copywriting court.
- Page de vente texte uniquement (sans vidéo) → skill sales-page.

## Pipeline (8 étapes)

### Étape 1 — Brief client (discovery)
Poser les questions critiques via `AskUserQuestion` si manquantes :
- **Offre:** produit, prix, modèle économique, garanties
- **ICP:** persona, douleur n°1, désir n°1, niveau de conscience (Schwartz: unaware → most aware), niveau de sophistication marché
- **Objectif:** CTA (call / opt-in / achat), KPI cible, durée cible, plateforme (YouTube ads, Meta ads, organique)
- **Assets:** témoignages, proofs chiffrées, footage existant, brand guidelines
- **Contraintes:** légal, claims interdits, deadline

Sauvegarder dans `00-brief.md`.

### Étape 2 — Recherche & benchmark
- Identifier 2-3 VSL concurrentes ou de référence sur le même marché
- Extraire : hook, big idea, mécanisme unique, structure, durée
- Identifier le **gap d'angle** : qu'est-ce qui n'a pas encore été dit ?

### Étape 3 — Stratégie & big idea
Produire `01-strategy.md` avec :
- **Big Idea:** une phrase qui résume l'angle disruptif
- **Promesse:** outcome + timeframe + sans (douleur évitée)
- **Mécanisme unique:** nom + pourquoi c'est différent + raison logique
- **Angle:** contrarian / nouveau / personnel / data / authority
- **Architecture émotionnelle** en 9 blocs (voir étape 4)

Faire valider la stratégie AVANT d'écrire le script.

### Étape 4 — Architecture émotionnelle (9 blocs)
1. **Hook (0–30s)** — pattern interrupt + promesse choc
2. **Problème** — qualification + amplification douleur
3. **Agitation** — coût de l'inaction
4. **Faux solutions** — pourquoi ce qu'ils essaient échoue (sans attaquer)
5. **Mécanisme unique** — révélation de la nouvelle approche
6. **Proof** — témoignages, data, case studies, credentials
7. **Offre & stack de valeur** — décomposition + ancrage prix
8. **Risk reversal** — garantie qui élimine le risque perçu
9. **Urgence + CTA** — scarcité légitime + action unique et claire

### Étape 5 — Rédaction du script
Produire `02-script.md` :
- Format : `[TIMESTAMP] [VISUAL/B-ROLL] — voix off`
- Phrases courtes, ton parlé (lire à voix haute pour vérifier)
- Une seule idée par phrase
- Transitions verbales fortes ("Mais voici le problème...", "Et c'est là que...")
- Calls to action répétés mais subtils avant le CTA final
- Vérifier durée cible : ~150 mots/min

**Règles d'or :**
- Hook < 10 secondes pour passer le scroll
- Pas de jargon avant le bloc proof
- Toujours nommer le mécanisme (donner un label propriétaire)
- Stack de valeur : 3-7 items max, avec ancrage prix x10 minimum
- Un seul CTA final, formulé 2-3 fois

### Étape 6 — Revue & itération
Checklist de revue :
- [ ] Le hook fonctionne sans son (sous-titres) ?
- [ ] Une grand-mère comprend en première écoute ?
- [ ] Chaque minute apporte une nouvelle info ou émotion ?
- [ ] Le mécanisme est nommé et différencié ?
- [ ] Les objections principales sont traitées ?
- [ ] Le CTA est sans ambiguïté ?
- [ ] La durée correspond à la cible ±15% ?

### Étape 7 — Production notes
Produire `03-production.md` :
- Liste des plans / B-roll par segment
- Notes ton & rythme pour le talent
- Assets graphiques nécessaires (lower thirds, charts, logos)
- Musique / SFX
- Plan de tournage (lieux, matériel, durée)

### Étape 8 — Déploiement
Produire `04-deployment.md` :
- Page de vente associée (headline, subheadline, CTA)
- Tracking : pixels, UTM, événements de conversion
- Plan de distribution : ads (YouTube/Meta), organique, email, retargeting
- A/B tests prévus (hooks alternatifs, miniatures, durées)

## Structure de sortie attendue
```
{project}/vsl/{client}/
├── 00-brief.md
├── 01-strategy.md
├── 02-script.md
├── 03-production.md
└── 04-deployment.md
```

## Templates
Les templates de chaque étape sont dans `projects/vsl/TopCo/` (à promouvoir vers `projects/vsl/_templates/` une fois stabilisés).

## Frameworks de référence
- **Schwartz** — niveaux de conscience marché (unaware → most aware)
- **Sugarman** — slippery slide (chaque phrase fait lire la suivante)
- **Halbert** — A-pile vs B-pile, voice of customer
- **Belcher / Brunson** — VSL structure classique (Hook → Story → Offer)
- **the platform** — Offre Irrésistible (value stack + risk reversal + scarcity)

## Notes
- TOUJOURS faire valider la stratégie (étape 3) avant d'écrire le script.
- TOUJOURS lire le script à voix haute avant de finaliser.
- TOUJOURS garder une seule promesse principale (pas de multi-pitch).
