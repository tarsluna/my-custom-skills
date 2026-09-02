# Placeholders — template.html

Liste exhaustive des tokens `{{…}}` dans `templates/template.html` et le champ `brief.json` qui les remplit.

Tous les tokens sont **mustache-style** (`{{TOKEN}}`). Le script `scripts/generate.mjs` fait un `String.prototype.replaceAll` pour chaque.

---

## Tokens globaux (meta)

| Token | Source `brief.json` | Exemple (Acme) | Fallback si manquant |
|---|---|---|---|
| `{{DEVIS_REF}}` | `meta.devis_ref` | `LF-20260421-002` | Auto-généré `LF-{YYYYMMDD}-{seq3digits}` où seq = sous-dossiers existants + 1 |
| `{{DATE_FR}}` | dérivé de la date du jour | `21/04/2026` | Date système au format `DD/MM/YYYY` |
| `{{YYYYMMDD}}` | dérivé de la date du jour | `20260421` | Date système au format `YYYYMMDD` (pour filename PDF) |
| `{{DEADLINE_FR}}` | `meta.decision_deadline_iso` | `28/04/2026` | Date + 7 jours si absent |

---

## Tokens agence (émetteur)

| Token | Source | Exemple | Fallback |
|---|---|---|---|
| `{{AGENCY_NAME}}` | `agency.name` (optionnel dans `brief.json`) ou env `AGENCY_NAME` | `Mon Agence` | `Votre agence` |
| `{{AGENCY_TAGLINE}}` | `agency.tagline` ou env `AGENCY_TAGLINE` | `Leads qualifiés en automatique.` | `Leads qualifiés en automatique.` |
| `{{AGENCY_OWNER_NAME}}` | `agency.owner_name` ou env `AGENCY_OWNER_NAME` | `Prénom Nom` | `[Your Name]` |

Utilisés dans : `<title>`, logo nav / footer / header PDF (`{{AGENCY_NAME}}`), tagline footer + pied de PDF (`{{AGENCY_TAGLINE}}`), signature « {{AGENCY_OWNER_NAME}}, CEO » du bloc Émetteur (page + PDF), phrase finale du subtitle hero, section PREUVE, objet du devis.

---

## Tokens client (destinataire)

| Token | Source | Exemple | Fallback |
|---|---|---|---|
| `{{CLIENT_FULL_NAME}}` | `meta.prospect_full_name` | `Prénom Acme` | **STOP** (requis) |
| `{{CLIENT_COMPANY}}` | `meta.company_legal_name` | `Fermetures Acme` | **STOP** (requis) |
| `{{CLIENT_ROLE}}` | `meta.role_title` | `Gérant` | `Décideur` |
| `{{CLIENT_NAME_SLUG}}` | dérivé de `meta.company_legal_name` | `Fermetures-Acme` | espaces → tirets |
| `{{CLIENT_ADDRESS_LINE}}` | `contact.address_line` | `1 rue de l'Exemple` | `—` |
| `{{CLIENT_POSTAL_CODE}}` | `contact.postal_code` | `00000` | `` |
| `{{CLIENT_CITY}}` | `contact.city` | `Villexemple` | **STOP** (requis pour targeting) |
| `{{CLIENT_PHONE}}` | `contact.phone` | `01 23 45 67 89` | `—` |
| `{{CLIENT_EMAIL}}` | `contact.email` | `contact@example-client.com` | **STOP** (requis) |

---

## Tokens hero / copie

| Token | Source | Exemple | Règle |
|---|---|---|---|
| `{{HERO_H1_HTML}}` | `dream_state.headline_hook` | `Moins de RDV. <em>Mieux qualifiés.</em><br>Sans diluer vos 40 ans d'image premium.` | Le mot clé du "dream" dans `<em>` bleu italic. Rythme X. Y. Sans Z. Max 12 mots. Voir `frameworks/03-dream-vs-objection-hero.md`. |
| `{{FINI_LES_1}}` | `objections.headline_subtitle_bullets[0]` | `prospects qui "comparent 3 devis"` | Verbatim du call, entre guillemets si citation. |
| `{{FINI_LES_2}}` | `objections.headline_subtitle_bullets[1]` | `RDV à 55 km qui n'ont pas le budget` | idem |
| `{{FINI_LES_3}}` | `objections.headline_subtitle_bullets[2]` | `promos low-cost qui salissent votre marque` | idem |
| `{{SERVICES_INTRO}}` | dérivé de l'industrie | `Tout le nécessaire pour générer des demandes de devis qualifiées sur vos fenêtres, portes, portails et pergolas — et protéger le temps de votre commercial.` | Phrase contextuelle sur les produits/services du prospect. Fallback neutre : `Tout le nécessaire pour générer des leads qualifiés sur votre offre et protéger le temps de votre commercial.` |

---

## Tokens pricing

| Token | Source | Exemple | Fallback |
|---|---|---|---|
| `{{LF_FEE}}` | `pricing.lf_fee_eur` | `790` | `790` |
| `{{STRIPE_LINK}}` | `pricing.stripe_link` | `https://buy.stripe.com/<your-payment-link>` | **STOP** (requis) |

---

## Tokens industry vocab

Tous tirés de `meta.industry_vocab.*` — voir `frameworks/02-industry-vocab-mapping.md` pour le mapping industrie → vocab.

| Token | Source | Exemple (Acme) | Fallback |
|---|---|---|---|
| `{{DEAL_WORD}}` | `meta.industry_vocab.deal_word` | `chantier` | `client` |
| `{{DEAL_WORD_PLURAL}}` | dérivé (`{deal_word}` + `s`) | `chantiers` | `clients` |
| `{{DEAL_WORD_PLURAL_CAPS}}` | capitalize 1ère | `Chantiers` | `Clients` |
| `{{CUSTOMER_WORD}}` | `meta.industry_vocab.customer_word` | `propriétaire` | `client` |
| `{{CUSTOMER_WORD_PLURAL}}` | dérivé | `propriétaires` | `clients` |
| `{{MEETING_WORD}}` | `meta.industry_vocab.meeting_word` | `RDV téléphonique` | `RDV téléphonique` |
| `{{MEETING_WORD_SHORT}}` | version courte | `RDV` | `RDV` |
| `{{MEETING_WORD_PLURAL}}` | pluriel complet | `RDV téléphoniques` | `RDV téléphoniques` |
| `{{MEETING_WORD_PLURAL_SHORT}}` | pluriel court | `RDV` | `RDV` |
| `{{MEETING_WORD_PLURAL_CAPS}}` | pluriel court capitalized | `RDV` | `RDV` |

Pour BTP/menuiserie (Acme) : `deal_word = chantier`, `customer_word = propriétaire`, `meeting_word = RDV téléphonique`. Voir mapping complet dans le framework 02.

---

## Tokens géo & business

| Token | Source | Exemple | Fallback |
|---|---|---|---|
| `{{GEO_RADIUS_KM}}` | `business.geo_radius_km` | `60` | `50` |
| `{{GEO_ZONE}}` | dérivé (région autour de la ville) | `votre région` | `votre région` — éditeur peut remplacer à la main |

---

## Tokens section cards (adaptation industrie)

| Token | Exemple (Acme BTP) | Exemple (coaching) | Règle |
|---|---|---|---|
| `{{PREQUAL_FILTERS}}` | `Filtre budget, type de projet, urgence, zone` | `Filtre budget, objectif, niveau, timeline` | Dépend de `industry_vocab.prequal_dimensions`. Fallback BTP : budget + type + urgence + zone. |
| `{{PREQUAL_FILTERS_SHORT}}` | `budget, projet, urgence, zone` | `budget, objectif, urgence, niveau` | Version courte pour table + timeline |
| `{{SETUP_DESCRIPTION}}` | `Audit secteur BTP, stratégie d'angles premium (pas de promos low-cost), création compte Meta, paramétrage pixel` | `Audit secteur coaching, stratégie d'angles authentiques, création compte Meta, paramétrage pixel` | Phrase contextuelle à l'industrie |
| `{{CREATIVES_ANGLE_CONTEXT}}` | `votre image 40 ans d'ancienneté` | `votre expertise et vos transformations` | Dépend du dream_state + `business.founded_year` / âge équipe |

---

## Fallbacks — règles générales

Si un champ **"requis" est absent** du brief → le skill s'arrête et demande à l'utilisateur de relancer `sales-call-analyzer` avec les champs manquants.

Les champs "fallback fourni" sont remplis automatiquement sans bloquer.

La liste des champs "STOP" :
- `meta.prospect_full_name`
- `meta.company_legal_name`
- `contact.email`
- `contact.city`
- `pricing.stripe_link`
- `dream_state.headline_hook`
- `objections.headline_subtitle_bullets` (≥ 3 items)
