# Framework 03 — Dossier Facts Checklist

**Objectif** : check-list complète des faits à extraire de la transcription. Chaque champ du `brief-output.json` est listé ici avec son extraction method et un exemple Acme.

**Règle** : si un fait **critique** (contact, raison sociale, adresse) manque dans la transcription → marquer le champ à enrichir via `WebFetch` (voir framework 04). Ne pas inventer.

---

## 📋 Section `meta` (identifiants prospect)

| Champ | Source transcription | Exemple Acme |
|---|---|---|
| `prospect_full_name` | Phrase de présentation au début (Prénom Acme se présente) | "Prénom Acme" |
| `prospect_first_name` | Premier mot du full_name | "le gérant" |
| `company_legal_name` | "Ma société s'appelle X" ou enrichissement site | "Fermetures Acme" |
| `company_display_name` | Version short si le prospect en utilise une | "Acme Fermetures" |
| `industry` | Description spontanée du business | "BTP — menuiseries extérieures (fenêtres, portes, portails, volets, pergolas)" |
| `industry_vocab` | Voir framework 02 | `{deal_word: "chantier", ...}` |
| `decision_deadline_iso` | Phrase "je me décide {date}" | "2026-04-25" |
| `call_date_iso` | Date du call (à demander au user si absent) | "2026-04-21" |

### Slug client (pour path)
Le `client_slug` utilisé dans le chemin de sortie est :
- Priorité 1 : nom de famille du prospect (kebab-case) : "Acme" → `acme`
- Priorité 2 : nom société court : "Fermetures Acme" → `fermetures-acme`

---

## 📞 Section `contact`

| Champ | Source | Exemple Acme |
|---|---|---|
| `email` | Mentionné dans le call OU enrichir via site (mentions légales / contact) | À enrichir du site (non mentionné dans l'appel) |
| `phone` | Fixe professionnel mentionné ou en bas du site | "01 23 45 67 89" |
| `whatsapp` | Numéro perso si le prospect l'a donné pour le follow-up | "06 00 00 00 00" |
| `address_line` | Rue mentionnée ou enrichissement site | "1 rue de l'Exemple" |
| `postal_code` | Code postal | "00000" |
| `city` | Ville | "Villexemple" |

**Règle** : si `email` ou `address_line` absents de la transcription → fetch le site prospect avant de livrer le brief (cf. framework 04).

---

## 🏢 Section `business`

| Champ | Source | Exemple Acme |
|---|---|---|
| `founded_year` | "L'entreprise a {X} ans" ou "depuis 19XX" | 1986 |
| `years_in_business` | Calcul : année_courante - founded_year OU dit verbatim "40 ans" | 40 |
| `team_size_label` | Descriptif court | "1 commercial + gérant à temps partiel" |
| `social_proof` | Avis Google / Trustpilot mentionnés ou trouvés sur site | `[{"label": "Google", "rating": "4.9/5", "count": 120}]` |
| `geo_radius_km` | Zone de travail en km | 60 |
| `geo_cities_covered` | Départements ou villes listées | `["Département (00)", "Département voisin partiel (00)", "Département voisin nord (00)"]` |

### Construction du `social_proof`

Si le prospect mentionne "on a X avis Google à Y étoiles" → capturer direct.
Sinon, enrichir via `WebFetch` sur la home du site ou sur Google Business (si URL connue).

---

## 🎭 Section `icp`

Voir framework 02 section 4.

```json
{
  "description": "Propriétaires 30-70 ans, projet menuiserie extérieure premium, refusent les promos low-cost",
  "age_range": "30-70 ans",
  "budget_range_label": "5 000 € à 15 000 € par chantier"
}
```

---

## 💶 Section `economics`

| Champ | Source | Exemple Acme |
|---|---|---|
| `avg_deal_size_eur` | "Mon panier moyen c'est X" | 5000 |
| `current_monthly_volume_label` | "On reçoit X demandes/mois" | "~30 appels entrants / mois" |
| `primary_acquisition_channels` | Canaux listés | `["Bouche-à-oreille (70%)", "Enseigne physique", "Google recherches locales"]` |

### Règle pour `avg_deal_size_eur`

Si le prospect donne une fourchette ("entre 3k et 10k€") → prendre la médiane ou le typique le plus mentionné.
Si plusieurs offres avec paniers différents mentionnés (ex Acme : fenêtres 3k€, pergolas 8k€) → prendre le panier moyen global ou le plus représentatif du volume. Acme = 5000 € (médiane).

---

## 💡 Section `dream_state`

Voir framework 01.

```json
{
  "headline_hook": "Moins de RDV. Mieux qualifiés. Sans diluer vos 40 ans d'image premium.",
  "verbatim_wins": [
    "Il vaut mieux en avoir moins, qu'on a payé un peu plus cher, mais qui correspondent vraiment à l'image",
    "Des gens qui ont le budget",
    "Image haut de gamme préservée"
  ]
}
```

---

## 🚫 Section `objections`

Voir framework 01.

```json
{
  "headline_subtitle_bullets": [
    "Fini les prospects qui \"comparent 3 devis\"",
    "Fini les RDV à 55 km qui n'ont pas le budget",
    "Fini les promos low-cost qui salissent votre marque"
  ],
  "verbatim_pains": [
    "ça bloquait souvent au niveau du prix",
    "pas vraiment les gens qualifiés",
    "mon commercial a été absent de l'entreprise, beaucoup de frais de véhicules de carburant",
    "à un moment donné, je vais mettre de la confusion dans l'esprit... créer aussi une distorsion de l'image de l'entreprise sur le long terme",
    "ça ne m'intéresse pas d'aller perdre du temps"
  ]
}
```

---

## 💀 Section `prior_agency_pain` (OPTIONNELLE)

**Règle critique** : remplir UNIQUEMENT si le prospect a mentionné une agence (ou freelance) précédente. Sinon → `null`.

| Champ | Source | Exemple Acme |
|---|---|---|
| `amount_wasted_eur` | "J'ai mis X sur {durée}" | 15000 |
| `duration_months` | "Ça a duré X mois" | 4 |
| `outcome` | "On a eu X clients / résultats" | "3 clients signés, CA équivalent au montant investi, zéro marge" |
| `root_cause` | Ce qui a foiré (verbatim si possible) | "Leads via promotions low-cost, image premium ruinée, RDV non qualifiés, déplacements 60km inutiles" |

### Exemple Acme

```json
"prior_agency_pain": {
  "amount_wasted_eur": 15000,
  "duration_months": 4,
  "outcome": "3 clients signés sur 4 mois, CA ≈ montant investi, zéro marge",
  "root_cause": "L'agence a lancé des campagnes Meta en promotions low-cost, attirant des prospects hors cible, créant des RDV non qualifiés à 60 km, et diluant l'image premium construite en 40 ans"
}
```

### Si le prospect n'a pas mentionné d'agence précédente

```json
"prior_agency_pain": null
```

**Ne jamais** laisser `{}` vide ou avec des placeholders.

---

## 🧮 Section `roi_calc_defaults`

Paramètres par défaut du simulateur ROI de la landing page.

| Champ | Source | Exemple Acme |
|---|---|---|
| `avg_basket_eur` | = `economics.avg_deal_size_eur` | 5000 |
| `use_industry_vocab_in_calc` | toujours `true` sauf instruction contraire | `true` |

### Règle de cohérence industrie

Après remplissage, vérifier que `avg_basket_eur` est dans la plage réaliste de l'industrie :
- Coaching / formation : 300 – 2000 €
- Santé privée (dentiste, kiné) : 500 – 5000 €
- BTP / menuiserie / piscine : 3000 – 20000 €
- Immobilier / mandat : 5000 – 50000 €
- Enterprise SaaS / consulting : 10000 – 80000 €

Si hors plage → flag `needs_human_review: true` sur le champ.

---

## 💸 Section `pricing`

| Champ | Source | Exemple Acme |
|---|---|---|
| `lf_fee_eur` | Fee annoncé et accepté dans le call (offre test = 790 €) | 790 |
| `recommended_ad_budget_eur` | Budget Meta recommandé / confirmé | 500 |
| `engagement` | "none" pour test 1 mois, "3-months" si engagement | "none" |

---

## 🔄 Section `sales_process_current`

Voir framework 02 section 6.

```json
{
  "team_structure_label": "1 commercial + le gérant à temps partiel (20-25%)",
  "current_pain_in_process": "Commercial déplacé 60 km pour des prospects pas qualifiés — coûts carburant en hausse"
}
```

---

## 📅 Section `follow_up`

| Champ | Source | Exemple Acme |
|---|---|---|
| `next_call_iso` | Date+heure du prochain call bookée à la fin du call | "2026-04-24T11:00:00+02:00" |
| `channel` | "whatsapp" / "phone" / "zoom" / "meet" | "whatsapp" |

Si aucun follow-up booké → `null`.

---

## ✅ Check-list finale (7 gates bloquants)

Avant de générer le JSON final, valider :

- [ ] **Contact complet** : `email`, `phone`, `address_line`, `postal_code`, `city` tous remplis (via transcription OU enrichissement site)
- [ ] **Business** : `founded_year`, `years_in_business`, `team_size_label`, `geo_radius_km` tous remplis
- [ ] **Social proof** : au moins 1 entrée dans `business.social_proof` (enrichir via site si absent)
- [ ] **Headline** : `dream_state.headline_hook` respecte "X. Y. Sans Z." max 12 mots
- [ ] **3 bullets "Fini les"** : exactement 3, chacun tracé à un verbatim
- [ ] **Vocabulaire industrie** : `deal_word` n'est pas "deal" si le prospect a utilisé un autre mot
- [ ] **Verbatims** : ≥ 3 dans `verbatim_pains`, ≥ 2 dans `verbatim_wins`
- [ ] **`prior_agency_pain`** : soit complètement rempli, soit `null`. Jamais partiel.
- [ ] **`avg_basket_eur`** dans la plage réaliste de l'industrie
