---
name: client-onboarding-flow
description: Orchestrateur end-to-end d'onboarding client pour une agence de lead-gen Meta Ads. Prend EN ENTRÉE UNIQUEMENT le formulaire d'onboarding rempli par un nouveau client, puis enchaîne automatiquement les skills lead-gen dans l'ordre (deep-search → competitor-ads-research → demonte-ton-offre → campaign-proposal → vsl-copywriter → meta-ads-copywriter) via des sous-agents, et livre un dossier client complet dans `{PROJECT_DIR}/{client}/`. Prérequis : ces skills enfants installés. Étape optionnelle : persister les livrables dans ta propre base Supabase. Use when the user says "onboarde {client}", "lance l'onboarding {client}", "flow complet {client}", "déploie le flow pour {client}", "onboarding {client}", "fais tout le flow {client}", "pipeline complet {client}". Trigger phrases : "onboarding client", "flow complet", "déploie le pipeline {client}", "onboarde le client {client}".
---

# Client Onboarding Flow (Master Orchestrator)

Skill maître qui orchestre l'ensemble du pipeline lead-gen post-onboarding de ton agence. **Input unique** : le formulaire d'onboarding rempli par le client. **Output** : un dossier client complet `{PROJECT_DIR}/{client}/` contenant tous les livrables intermédiaires + finaux.

> `{PROJECT_DIR}` = la racine de tes dossiers clients (ex. `~/clients`). La définir une fois (env `PROJECT_DIR`, cf. `.env.example`) ou la demander à l'utilisateur au premier run.

Ce skill ne fait AUCUN travail lui-même : il enchaîne les skills lead-gen existants dans le bon ordre, en transmettant à chaque étape les outputs de l'étape précédente.

---

## 🎯 Quand utiliser ce skill

Trigger sur :
- "Onboarde {client}"
- "Lance l'onboarding pour {client}"
- "Déploie le flow complet pour {client}"
- "Pipeline complet {client}"
- "Fais tout le flow {client}"
- "Onboarding {client}"

NE PAS trigger pour :
- Lancer un seul skill (utiliser directement le skill concerné)
- Produire un livrable isolé (VSL seule, brief concurrents seul, etc.)

---

## 📥 Input unique : formulaire d'onboarding

Le seul input attendu est **le formulaire d'onboarding client rempli**. Il peut arriver sous 3 formes :
1. Un fichier markdown / pdf / docx que l'utilisateur fournit (chemin local)
2. Un texte collé directement dans la conversation
3. Un lien vers une réponse Typeform / Tally / Google Forms

Si le formulaire est manquant ou incomplet, le skill **demande** au client le fichier ou le contenu avant de démarrer. Ne JAMAIS halluciner de réponses.

### Champs critiques attendus dans le formulaire

Le skill doit pouvoir extraire ces 12 champs minimum (nommés différemment selon le formulaire). En cas d'absence d'un champ critique, **demander** à l'utilisateur (1 seul tour) puis continuer.

| # | Champ | Usage downstream |
|---|---|---|
| 1 | `client_name` | Nom du dossier `{PROJECT_DIR}/{client_name}/` |
| 2 | `niche` / `secteur` | DeepSearch (YOUR NICHE) |
| 3 | `product` / `offre` | DeepSearch (PRODUCT) + VSL + Meta Ads |
| 4 | `geography` / `marché géo` | DeepSearch (GEOGRAPHY) + Competitor Research |
| 5 | `target_avatar` / `ICP` | DeepSearch + VSL + Meta Ads |
| 6 | `competitors` (liste de 3-6 marques) | Competitor Ads Research |
| 7 | `funnel_type` (`instant_form` ou `vsl`) | Campaign Proposal + VSL |
| 8 | `price_point` (€) | VSL + Meta Ads |
| 9 | `objectif_test` (CPL cible, volume, durée) | Campaign Proposal |
| 10 | `tonality` / `voix de marque` | VSL + Meta Ads |
| 11 | `differenciation` / `mécanisme unique` | VSL + Meta Ads |
| 12 | `proof_assets` (témoignages, chiffres clients) | VSL + Meta Ads |

---

## 🗂️ Structure du dossier client final

À la fin du pipeline, le dossier client doit ressembler à ceci :

```
{PROJECT_DIR}/{client}/
├── 00-onboarding/
│   └── onboarding-form.md            ← copie du formulaire input (source de vérité)
├── 01-deep-search/
│   ├── 01-market-awareness.md
│   ├── 02-competitor-research.md
│   ├── 03-psychographic.md
│   ├── DeepSearch-Conscience-Marche-{client}.pdf
│   ├── DeepSearch-Concurrents-{client}.pdf
│   └── DeepSearch-Psychographique-{client}.pdf
├── 02-competitor-ads/
│   ├── creatives/                    ← médias téléchargés
│   ├── data.csv
│   ├── analysis.md
│   └── Brief-Concurrents-{client}-{date}.docx
├── 02b-offre/                         ← offre reconstruite (Offre Irrésistible)
│   ├── offre irrésistible.md            ← offre reconstruite + value stack + garantie + variations
│   └── offre-diagnostic.md            ← diagnostic offre d'origine + scoring Value Equation
├── 03-campaign-proposal/
│   └── Proposition-Campagne-{client}.docx
├── 04-vsl/
│   ├── strategy.md
│   ├── script-v1.md
│   └── VSL-Script-{client}.docx
├── 05-meta-ads/
│   ├── ads-multi-variantes.md
│   └── Meta-Ads-{client}.docx
└── README.md                         ← index du dossier (généré par ce skill en fin de pipeline)
```

---

## 🔁 Pipeline orchestré (6 étapes)

Le skill exécute les étapes **séquentiellement** (chaque étape consomme les outputs de la précédente) — sauf les étapes 1 et 2, parallélisables. Chaque étape est déléguée à un sous-agent qui invoque le skill correspondant.

Ordre : **1. DeepSearch · 2. Competitor Ads** (parallèle) → **2.5 Démonte Ton Offre** → **3. Campaign Proposal** → **4. VSL** → **5. Meta Ads**.

### ⚙️ Règle de délégation

Pour chaque étape, lancer un sous-agent via l'outil `Agent` avec :
- `subagent_type: "general-purpose"`
- Prompt = instruction explicite "Utilise le skill `{skill-name}` avec les inputs suivants : {...}. Sauvegarde les livrables dans `{PROJECT_DIR}/{client}/{step-folder}/`."

Les étapes 1 et 2 peuvent être lancées **en parallèle** (single message, 2 Agent calls) car indépendantes. Étapes 2.5 → 3 → 4 → 5 sont strictement séquentielles (l'étape 2.5 consomme les outputs de 1+2, et 3/4/5 consomment l'offre reconstruite par 2.5).

---

### Étape 0 — Setup
1. Parser le formulaire d'onboarding et extraire les 12 champs critiques.
2. Demander à l'utilisateur les champs manquants (1 seul tour groupé via `AskUserQuestion`).
3. Créer le dossier `{PROJECT_DIR}/{client}/` et ses sous-dossiers vides (`00-onboarding/`, `01-deep-search/`, `02-competitor-ads/`, `02b-offre/`, `03-campaign-proposal/`, `04-vsl/`, `05-meta-ads/`).
4. Sauvegarder une copie normalisée du formulaire dans `00-onboarding/onboarding-form.md`.

### Étape 1 — DeepSearch (skill `deep-search`)
**Lancer en parallèle de l'étape 2.**

Sous-agent prompt :
> Utilise le skill `deep-search` pour le client `{client_name}`. Inputs : niche=`{niche}`, product=`{product}`, geography=`{geography}`, target_avatar=`{target_avatar}`. Produis les 3 rapports DeepSearch (Market Awareness, Competitor Research, Psychographic) en français. Sauvegarde-les dans `{PROJECT_DIR}/{client_name}/01-deep-search/` sous les noms `01-market-awareness.md`, `02-competitor-research.md`, `03-psychographic.md`. Génère ensuite les 3 PDFs brandés (charte de ton agence) en parallèle avec `build_deep_search_pdf.py` (voir Step 4 du skill deep-search). Ne renvoie que les chemins des 6 fichiers créés (3 .md + 3 .pdf).

### Étape 2 — Competitor Ads Research (skill `competitor-ads-research`)
**Lancer en parallèle de l'étape 1.**

Sous-agent prompt :
> Utilise le skill `competitor-ads-research` pour le client `{client_name}`. Concurrents à analyser : `{competitors}`. Marché géo : `{geography}`. Profondeur : 90 jours. Produis le brief complet : creatives téléchargées, `data.csv`, `analysis.md`, et le `.docx` final brandé (charte de ton agence). Sauvegarde tout dans `{PROJECT_DIR}/{client_name}/02-competitor-ads/`. Ne renvoie que les chemins des livrables.

### ⏸ Synchronisation
Attendre la fin des étapes 1 et 2 avant de continuer. Vérifier que les 4 livrables clés existent (`01-market-awareness.md`, `02-competitor-research.md`, `03-psychographic.md`, `analysis.md`). Si un fichier manque, relancer le sous-agent concerné avec un prompt correctif.

### Étape 2.5 — Démonte Ton Offre (skill `demonte-ton-offre`)
**Séquentiel. Consomme les outputs des étapes 1 et 2.** S'exécute APRÈS la research marché/concurrents et AVANT la proposition de campagne, car l'offre reconstruite devient un input de toutes les étapes downstream (Campaign Proposal, VSL, Meta Ads).

Cette étape prend l'offre brute du client (`{product}` + `{price_point}` + `{differenciation}` du formulaire) et la **reconstruit en Offre Irrésistible** calibrée sur le marché/la cible révélés par le DeepSearch et l'analyse concurrentielle.

Sous-agent prompt :
> Utilise le skill `demonte-ton-offre` pour le client `{client_name}`. Démonte et reconstruis l'offre du client en Offre Irrésistible (méthode du skill demonte-ton-offre) calibrée sur la cible et le marché. Inputs :
> - Offre actuelle : `{product}` — prix `{price_point}` — différenciation `{differenciation}`
> - Avatar / ICP : `{target_avatar}`
> - Modèle de business : (inférer depuis la niche `{niche}`)
> - DeepSearch (market awareness + psychographique → stade de conscience, dream outcome réel, pains, VoC) : `{PROJECT_DIR}/{client_name}/01-deep-search/`
> - Analyse concurrentielle (positionnement, claims du marché → sophistication) : `{PROJECT_DIR}/{client_name}/02-competitor-ads/analysis.md`
>
> Applique le processus en 6 phases. Produis 2 fichiers markdown en français :
> - `offre irrésistible.md` : l'offre reconstruite (nom MAGIC, promesse, value stack avec valeurs attribuées, prix + money model, garantie du bon type, scarcity/urgency honnêtes, bonus) + 3+ variations testables par angle marketing.
> - `offre-diagnostic.md` : diagnostic de l'offre d'origine + scoring Value Equation avant/après + raisonnement.
>
> Sauvegarde les 2 fichiers dans `{PROJECT_DIR}/{client_name}/02b-offre/`. Ne renvoie que les chemins des fichiers créés + un résumé en 3 lignes de l'offre reconstruite (nom, promesse, prix).

⚠️ **Honnêteté** : si la research révèle que le marché est mauvais (pas de douleur massive, pas de pouvoir d'achat) ou que l'offre est sur une commodité faible marge, le sous-agent doit le signaler dans le diagnostic plutôt que de forcer une stratégie premium inadaptée.

> 💡 **Note de transmission** : à partir de cette étape, les étapes 3/4/5 utilisent en priorité l'offre reconstruite (`02b-offre/offre irrésistible.md`) plutôt que l'offre brute du formulaire. La promesse, la garantie, le mécanisme unique et le stack reconstruits doivent se retrouver dans la proposition de campagne, la VSL et les Meta Ads.

### Étape 3 — Campaign Proposal (skill `campaign-proposal`)
**Séquentiel. Consomme les outputs des étapes 1, 2 et 2.5.**

Sous-agent prompt :
> Utilise le skill `campaign-proposal` pour le client `{client_name}`. Inputs :
> - Funnel type : `{funnel_type}`
> - Objectif test : `{objectif_test}`
> - Price point : `{price_point}` (utiliser le prix de l'offre reconstruite si différent)
> - **Offre reconstruite (source de vérité pour la promesse/garantie/mécanisme) : `{PROJECT_DIR}/{client_name}/02b-offre/offre irrésistible.md`**
> - DeepSearch reports : `{PROJECT_DIR}/{client_name}/01-deep-search/`
> - Competitor analysis : `{PROJECT_DIR}/{client_name}/02-competitor-ads/analysis.md`
>
> Produis le document `.docx` officiel de proposition de campagne (3 sections fixes : brief stratégique, formulaire/VSL placeholder, structure des campagnes Meta). Le brief stratégique doit refléter l'offre reconstruite. Sauvegarde dans `{PROJECT_DIR}/{client_name}/03-campaign-proposal/Proposition-Campagne-{client_name}.docx`.

### Étape 4 — VSL (skill `vsl-copywriter`)
**Séquentiel. Consomme étapes 1 + 2 + 3.**

Si `funnel_type == "instant_form"` → **skip cette étape** et passer directement à l'étape 5. Le funnel Instant Form n'a pas besoin de VSL.

Si `funnel_type == "vsl"` :

Sous-agent prompt :
> Utilise le skill `vsl-copywriter` pour le client `{client_name}`. Mode : choisir entre `coach-dtc` ou `b2b-specialist` selon la `tonality` du brief. Inputs :
> - **Offre reconstruite (promesse, garantie, mécanisme unique, value stack) : `{PROJECT_DIR}/{client_name}/02b-offre/offre irrésistible.md`**
> - 3 DeepSearch reports : `{PROJECT_DIR}/{client_name}/01-deep-search/`
> - Competitor analysis : `{PROJECT_DIR}/{client_name}/02-competitor-ads/analysis.md`
> - Price point : `{price_point}` (aligner sur l'offre reconstruite)
> - Differenciation : utiliser le mécanisme unique de l'offre reconstruite
> - Proof assets : `{proof_assets}`
>
> La VSL doit vendre l'offre reconstruite (sa promesse, sa garantie, son stack). Produis le script VSL complet + strategy doc + le `.docx` final brandé (charte de ton agence) ultra-simple. Sauvegarde dans `{PROJECT_DIR}/{client_name}/04-vsl/`.

### Étape 5 — Meta Ads Copywriter (skill `meta-ads-copywriter`)
**Séquentiel. Étape finale.**

Sous-agent prompt :
> Utilise le skill `meta-ads-copywriter` pour le client `{client_name}`. Inputs :
> - **Offre reconstruite + variations d'angles : `{PROJECT_DIR}/{client_name}/02b-offre/offre irrésistible.md`** (les variations d'angles de l'offre alimentent directement les variantes d'ads)
> - 3 DeepSearch reports : `{PROJECT_DIR}/{client_name}/01-deep-search/`
> - Competitor analysis : `{PROJECT_DIR}/{client_name}/02-competitor-ads/analysis.md`
> - Campaign proposal : `{PROJECT_DIR}/{client_name}/03-campaign-proposal/`
> - VSL (si existe) : `{PROJECT_DIR}/{client_name}/04-vsl/`
> - Price point : `{price_point}` (aligner sur l'offre reconstruite)
> - Tonality : `{tonality}`
> - Proof assets : `{proof_assets}`
>
> Les hooks et la promesse des ads doivent refléter l'offre reconstruite. Produis 3 variantes minimum de scripts face caméra (30s/60s/90s) + ad copies (primary text / headline / description) en français markdown, puis le `.docx` final brandé (charte de ton agence). Sauvegarde dans `{PROJECT_DIR}/{client_name}/05-meta-ads/`.

---

## 📋 Étape finale — README index

À la toute fin, écrire un fichier `{PROJECT_DIR}/{client}/README.md` qui :
1. Récapitule le client et la date du flow
2. Liste tous les livrables produits avec leur chemin
3. Indique les next steps pour l'agence (lancement campagne, validation client, etc.)

Utiliser le template `templates/client-readme.md` de ce skill comme base.

---

## 🗄️ Étape post-pipeline (OPTIONNELLE) — Persister les livrables dans ta propre base

Si ton agence a une app/CRM interne où le client consulte ses rendus, tu peux **injecter automatiquement les références des livrables** dans une table `ai_deliverables` de ta base Supabase (+ upload des fichiers dans un bucket Storage privé). Cela rend les livrables visibles et téléchargeables depuis un panneau « AI Delivery / Rendus » sur la page client côté admin. **Si tu n'as pas de base : sauter cette étape**, le dossier local + `README.md` est le livrable.

### Pré-requis (à vérifier une seule fois par machine)

1. **Table `ai_deliverables` + bucket `ai-deliverables`** dans ton projet Supabase. Schéma minimal fourni : `assets/ai_deliverables.sql` (à coller dans le SQL Editor Supabase). Il suppose une table `profiles` (un client = une ligne, colonnes `company`, `full_name`).
2. **Variables d'environnement** disponibles dans le shell (à exporter dans `~/.zshrc` une bonne fois pour toutes, cf. `.env.example`) :
   ```sh
   export SUPABASE_URL="https://<your-project-ref>.supabase.co"
   export SUPABASE_SERVICE_ROLE_KEY="<service_role_key>"   # PAS l'anon key
   export PROJECT_DIR="$HOME/clients"
   ```
   La `service_role_key` se trouve dans le Dashboard Supabase → Project Settings → API → `service_role` secret (ou dans le `.env.local` de ton app).

3. Le **client doit déjà exister** dans la table `profiles` (créé via ton app ou à la main). Le script résout l'UUID en cherchant par `company` puis `full_name` (ilike, insensible à la casse).

### Commande à exécuter

À la toute fin du pipeline, lancer :

```sh
python3 <chemin-du-skill>/assets/inject_to_database.py \
    --client-folder "$PROJECT_DIR/{client_folder}" \
    --client-name "{client_name_or_company}"
```

Options disponibles :
- `--dry-run` → preview sans écriture (recommandé en première exécution pour vérifier la catégorisation)
- `--client-folder` → chemin absolu du dossier client local
- `--client-name` → nom du client tel qu'enregistré dans `profiles.company` ou `profiles.full_name`

### Ce que fait le script

1. **Scan récursif** du dossier client local `{PROJECT_DIR}/{folder}/`
2. **Catégorise** chaque fichier en `deliverable_type` selon son chemin (00-onboarding, 01-deep-search, 02-competitor-ads, 03-campaign-proposal, 04-vsl, 05-meta-ads)
3. **Résout l'UUID Supabase** du client via l'API REST (`GET /rest/v1/profiles?company=ilike.{name}`)
4. **Upload** chaque fichier dans le bucket privé `ai-deliverables` sous `{client_id}/{chemin relatif}` (upsert)
5. **Upsert** chaque fichier dans `ai_deliverables` via `POST /rest/v1/ai_deliverables?on_conflict=client_id,relative_path` avec le header `Prefer: resolution=merge-duplicates`. **Idempotent** : peut être relancé sans créer de doublons.
6. **Logs** le récapitulatif (nombre de fichiers, UUID du client)

### Schéma des données injectées

Chaque ligne dans `ai_deliverables` contient :
| Colonne | Source |
|---|---|
| `client_id` | UUID résolu depuis `profiles` |
| `skill_name` | toujours `client-onboarding-flow` |
| `deliverable_type` | inféré depuis le chemin (cf. enum dans `assets/ai_deliverables.sql`) |
| `deliverable_name` | nom du fichier (basename) |
| `relative_path` | chemin dans le bucket Storage (ex: `{client_id}/04-vsl/VSL-Script-Acme.docx`) |
| `file_size_bytes` | `stat.st_size` |
| `file_extension` | extension lowercase (`md`, `docx`, `csv`, etc.) |
| `status` | `available` |
| `generated_at` | `mtime` du fichier |

### Erreurs possibles & remèdes

| Erreur | Cause | Fix |
|---|---|---|
| `client '…' introuvable dans profiles` | `profiles.company` ne matche pas | Créer le client dans ton app ou ajuster `--client-name` |
| `HTTP 401` | Mauvaise service_role_key | Re-exporter `SUPABASE_SERVICE_ROLE_KEY` |
| `HTTP 404 ai_deliverables` | Table non créée | Coller `assets/ai_deliverables.sql` dans le SQL Editor Supabase |
| `HTTP 404` sur l'upload | Bucket `ai-deliverables` absent | Créer le bucket (privé) — inclus dans le SQL |
| `HTTP 23514 (check constraint)` | `deliverable_type` non reconnu | Le helper a renvoyé `other` — vérifier `infer_deliverable_type` |

### Vérification post-injection

Ouvrir la page client de ton app (ex. `https://<ton-app>/admin/clients/{client_id}`, ou `http://localhost:3000/...` en dev local) : le panneau « Rendus » doit afficher tous les fichiers groupés par étape, avec un bouton de téléchargement par fichier (servi depuis Supabase Storage via URL signée).

---

## ✅ Output final attendu

À la fin du pipeline, le skill renvoie à l'utilisateur un message court (5-10 lignes max) avec :
- ✓ Dossier créé : `{PROJECT_DIR}/{client}/`
- ✓ Livrables clés (chemins des `.docx` finaux)
- ✓ Étape skippée si applicable (ex. VSL skippé pour funnel Instant Form)
- ⚠️ Erreurs / champs manquants si détectés

**Ne PAS dump le contenu des livrables dans la conversation.** Les livrables vivent dans le dossier client. La conversation reste épurée.

---

## ⚠️ Règles de robustesse

1. **Idempotence** : si le dossier client existe déjà, demander à l'utilisateur s'il veut écraser, fusionner ou créer une nouvelle version (`{client}-v2/`).
2. **Échec d'une étape** : si un sous-agent échoue, capturer l'erreur, la logger dans `{PROJECT_DIR}/{client}/_errors.log`, et demander à l'utilisateur s'il faut retry, skip, ou abandonner.
3. **Pas de hallucination** : si une étape manque d'inputs critiques (ex. concurrents non fournis pour l'étape 2), arrêter et demander.
4. **Pas de doublon** : ne JAMAIS refaire le travail d'un skill. L'orchestrateur ne fait que router et synchroniser.
5. **Anti-IA** : respecter le ton anti-IA déjà encodé dans chaque skill enfant. Ce skill ne génère aucun contenu marketing lui-même.

---

## 📦 Structure du skill

```
client-onboarding-flow/
├── SKILL.md                          ← ce fichier (orchestration + persistance optionnelle)
├── .env.example                      ← variables de l'étape optionnelle
├── assets/
│   ├── inject_to_database.py         ← script d'injection des livrables dans TA base Supabase (optionnel)
│   └── ai_deliverables.sql           ← schéma minimal attendu par le script
└── templates/
    ├── onboarding-form-schema.md     ← schéma normalisé des 12 champs
    └── client-readme.md              ← template du README index final
```
