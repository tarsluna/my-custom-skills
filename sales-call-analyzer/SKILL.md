---
name: sales-call-analyzer
description: Analyse une transcription d'appel de vente entre le commercial de l'agence et un prospect, puis produit un brief structuré JSON + markdown que le skill `devis-vercel-generator` consomme pour générer une landing page de devis personnalisée. Le skill extrait le dream state verbatim, les objections verbatim (avec citations exactes), le vocabulaire industrie (chantier vs patient vs deal vs contrat), les faits société (raison sociale, adresse, gérant, téléphone, email), la géographie, l'appétit budgétaire, la timeline de décision, la structure commerciale actuelle, l'expérience avec agences précédentes, et la sensibilité prix. Use when the user asks "analyse l'appel de vente {client}", "brief commercial {client}", "prépare le devis depuis l'appel", "extract dream vs objection from call", "parse transcription vente", "prepare devis brief from call", "analyse transcription {client}". Trigger phrases: "analyse l'appel de vente", "brief commercial", "extract dream vs objection", "parse transcription vente", "prepare devis brief from call", "analyse transcription".
---

# Sales Call Analyzer

Skill qui transforme une **transcription d'appel de vente** (entre le commercial et un prospect) en **brief structuré** (`brief-output.json` + `brief-output.md`) qui sert d'input au skill `devis-vercel-generator`.

**Objectif** : extraire tout ce qu'il faut pour personnaliser un devis Vercel — dream state verbatim, objections verbatim, vocabulaire industrie, faits société, économie du business, timeline de décision, expérience avec agences précédentes.

**Règle d'or** : **verbatim > paraphrase**. Si le prospect a dit "ça bloquait souvent au niveau du prix", on cite exactement ces mots — on ne reformule pas en "problèmes budgétaires côté client". Les citations exactes nourrissent les headlines et les bullets "Fini les X" du devis.

---

## 🎯 Quand utiliser ce skill

Trigger sur :
- "Analyse l'appel de vente {client}"
- "Brief commercial depuis l'appel {client}"
- "Prépare le devis brief pour {client}"
- "Parse la transcription de {client}"
- "Extract dream vs objection from {client} call"
- "Analyse transcription {client}"

NE PAS trigger pour :
- Générer la landing page du devis elle-même → `devis-vercel-generator` (consomme le JSON produit ici)
- Créer la proposition de campagne Meta → un document de proposition de campagne
- Écrire le script VSL → `vsl-copywriter`

---

## 📦 Pipeline (4 phases)

### Phase 1 — Ingestion de la transcription
Le user fournit :
- Un chemin vers la transcription (`.txt`, `.md`, `.vtt`, `.srt`) OU le texte collé directement
- Le nom du client (ou slug)
- (Optionnel) L'URL du site web du prospect pour enrichissement

Si la transcription n'est pas fournie, demander. Si l'URL site n'est pas fournie mais que le nom société est dans la transcription, déduire l'URL probable (`{company}.com`, `{company}.fr`, `{company}-{city}.com`) et l'utiliser pour l'enrichissement en Phase 3.

### Phase 2 — Extraction via frameworks
Lire les 4 frameworks dans l'ordre :

1. **`frameworks/01-dream-vs-objection-framework.md`** — cible le dream state verbatim + objections verbatim. Méthode : scanner la transcription pour 4 types de phrases (pain exprimée, dream exprimée, contre-exemple, objection sur l'offre).
2. **`frameworks/02-voice-of-customer-extraction.md`** — mine le vocabulaire industrie (le mot pour "deal" : chantier/patient/deal/contrat), ICP, sensibilité prix, stade du cycle d'achat.
3. **`frameworks/03-dossier-facts-checklist.md`** — check-list complète des faits à extraire (raison sociale, adresse, gérant, SIRET si mentionné, téléphone, email, industrie, géo, panier moyen, team co, volume, timeline, budget confirmé, objections, dreams, concurrents, expérience agences).
4. **`frameworks/04-enrichment-from-website.md`** — si un champ critique manque (email, raison sociale légale, adresse, SIRET), fetch le site web du prospect via `WebFetch` avant de finaliser. Liste les URL patterns probables.

### Phase 3 — Enrichissement depuis le site web (conditionnel)
Si après Phase 2 un de ces champs est vide :
- `contact.email`
- `meta.company_legal_name`
- `contact.address_line`, `contact.postal_code`, `contact.city`
- `business.founded_year`
- `business.social_proof` (avis Google)

Alors : utiliser `WebFetch` sur l'URL du prospect en suivant `frameworks/04-enrichment-from-website.md`. Chercher la page `/mentions-legales`, `/contact`, `/about`, et la home. Remplir les champs manquants.

### Phase 4 — Génération du brief
Produire deux fichiers dans `projects/{client_slug}/00-sales-brief/` :
- `brief-output.json` — contrat structuré avec le skill downstream (schéma : `templates/brief-output.json`)
- `brief-output.md` — version human-readable (template : `templates/brief-output.md`)

Le `{client_slug}` est le nom client kebab-case (ex : "Prénom Acme" → `acme` ou `fermetures-acme`).

Créer le dossier s'il n'existe pas.

---

## 🧪 Exemple de référence : Acme (menuisier extérieur, données fictives)

La transcription d'exemple (Fermetures Acme, menuiserie extérieure) est le **gold standard** de ce skill. Le fichier `templates/brief-output-example.json` contient l'extraction complète (données inventées), à utiliser comme référence de qualité.

Caractéristiques clés du cas Acme (à repérer dans toute transcription similaire) :
- **Objection verbatim typique** : *"ça bloquait souvent au niveau du prix"* → devient `Fini les prospects qui "comparent 3 devis"`.
- **Dream verbatim typique** : *"il vaut mieux en avoir moins, qu'on a payé un peu plus cher, mais qui correspondent vraiment à l'image"* → devient le headline `Moins de RDV. Mieux qualifiés. Sans diluer vos 40 ans d'image premium.`
- **Vocabulaire industrie** : "chantier" (et pas "client" ou "deal") → `industry_vocab.deal_word = "chantier"`.
- **Panier moyen** : 5000 € (menuiserie extérieure, premium) → `roi_calc_defaults.avg_basket_eur = 5000`.
- **Prior agency pain** : 15 000 € sur 4 mois, 3 clients, zéro marge, image salie → section `prior_agency_pain` remplie complètement.

---

## 🏗️ Structure du skill

```
sales-call-analyzer/
├── SKILL.md                                       ← ce fichier
├── frameworks/
│   ├── 01-dream-vs-objection-framework.md         ← extraction verbatim dream/pain
│   ├── 02-voice-of-customer-extraction.md         ← vocabulaire industrie + ICP + pricing
│   ├── 03-dossier-facts-checklist.md              ← check-list des faits à extraire
│   └── 04-enrichment-from-website.md              ← règles de fetch du site prospect
└── templates/
    ├── brief-output.json                          ← schéma JSON vide (contrat downstream)
    ├── brief-output-example.json           ← exemple rempli = gold standard
    ├── brief-output.md                            ← template markdown human-readable
    └── prompt-to-run-skill.md                     ← prompt template pour invoquer le skill
```

---

## ✅ Quality Gates (bloquants avant livraison)

Ne pas livrer le brief tant que ces 7 gates ne passent pas :

- [ ] **Contact + Business** : tous les champs de `contact` (email, téléphone, adresse, code postal, ville) et `business` (année création, ancienneté, taille équipe, social proof, géo radius) sont remplis. Si un champ manque dans la transcription → enrichir via `WebFetch` sur le site prospect (voir framework 04).
- [ ] **Headline rhythm** : `dream_state.headline_hook` respecte le rythme **"X. Y. Sans Z."** (3 segments, max 12 mots total). Exemple : *"Moins de RDV. Mieux qualifiés. Sans diluer vos 40 ans d'image premium."*
- [ ] **Subtitle bullets** : `objections.headline_subtitle_bullets` contient **exactement 3 bullets**, chacun commence par **"Fini les"** et référence une douleur verbatim du call.
- [ ] **Vocabulaire industrie** : `industry_vocab.deal_word` n'est **jamais** "deal" si le prospect a utilisé un autre mot (chantier, patient, contrat, dossier, commande, projet...). Par défaut si rien trouvé : "client".
- [ ] **Verbatim count** : au moins **3 verbatim** dans `objections.verbatim_pains` et **2 verbatim** dans `dream_state.verbatim_wins`. Chaque verbatim = citation exacte entre guillemets.
- [ ] **Prior agency** : section `prior_agency_pain` remplie uniquement si le prospect a mentionné une agence précédente. Sinon → `null` (pas d'objet vide, pas de placeholders).
- [ ] **ROI basket sanity** : `roi_calc_defaults.avg_basket_eur` est cohérent avec l'industrie — coaching/formation ≈ 300-2000 €, BTP/menuiserie ≈ 3000-15000 €, enterprise SaaS ≈ 10000-80000 €, santé privée ≈ 500-5000 €. Si la valeur est à l'extérieur de la plage de l'industrie → flag et re-vérifier.

Si un gate ne passe pas : re-scanner la transcription OU fetcher le site web OU ajouter une note `needs_human_review: true` dans le JSON sur le champ concerné.

---

## 📌 Style éditorial (pour le brief généré)

**À FAIRE** :
- Champs en français (labels JSON en anglais technique, valeurs en français)
- Citations verbatim **entre guillemets français** « … » ou guillemets droits `"…"` selon le fichier (JSON = guillemets droits ; .md = guillemets français OK)
- Phrases courtes dans le .md
- Promesses chiffrées quand elles sont dans le call (âge équipe, budget, volume leads)
- Ton direct, orienté action

**À NE PAS FAIRE** :
- Paraphraser un verbatim (garde les mots exacts du prospect)
- Ajouter des infos qui ne sont ni dans la transcription ni dans le site web (pas d'invention)
- Utiliser des mots corporate type "synergie", "accompagnement", "valeur ajoutée"
- Laisser des champs null sans les lister explicitement dans `needs_human_review`

---

## 🔗 Chaînage avec le skill downstream

Après avoir produit `brief-output.json`, le workflow naturel est :

1. User valide le brief (lit le .md).
2. User invoque `devis-vercel-generator` avec le chemin du JSON.
3. Le skill downstream génère la landing page Vercel personnalisée (copie de la structure `devis-template/index.html` avec les valeurs du JSON injectées).

Le JSON est **le seul point de contact** entre les deux skills. Tout ce qui n'est pas dans le JSON ne sera pas dans la landing page.

---

## 📬 Output final au user (après génération)

Après avoir écrit les 2 fichiers, répondre au user en français avec :

> ✅ Brief commercial généré pour **{Client}**.
>
> 📁 Fichiers :
> - `projects/{client_slug}/00-sales-brief/brief-output.json`
> - `projects/{client_slug}/00-sales-brief/brief-output.md`
>
> **Extractions clés :**
> - Dream headline : *"{headline_hook}"*
> - 3 "Fini les" : {3 bullets}
> - Vocabulaire industrie : {deal_word}
> - Panier moyen : {avg_basket_eur} €
> - Timeline décision : {decision_deadline_iso}
> - Budget confirmé : {lf_fee_eur} + {recommended_ad_budget_eur} €
>
> **Quality gates :** {N}/7 passés. {liste des gates non passés si applicable}
>
> Prochaine étape : invoque `devis-vercel-generator` avec le JSON pour générer la landing page du devis.
