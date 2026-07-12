# Brief commercial — {prospect_full_name}

**Société** : {company_legal_name}
**Industrie** : {industry}
**Date du call** : {call_date_iso}
**Échéance de décision** : {decision_deadline_iso}
**Slug client** : `{client_slug}`

---

## 🎯 Hero devis — Dream vs Objection

### Headline (H1 du devis)

> **{dream_state.headline_hook}**

### Sous-titre (3 bullets "Fini les X")

1. {objections.headline_subtitle_bullets[0]}
2. {objections.headline_subtitle_bullets[1]}
3. {objections.headline_subtitle_bullets[2]}

### Verbatim dream state (citations exactes du prospect)

- « {verbatim_wins[0]} »
- « {verbatim_wins[1]} »
- ...

### Verbatim objections / douleurs (citations exactes du prospect)

- « {verbatim_pains[0]} »
- « {verbatim_pains[1]} »
- « {verbatim_pains[2]} »
- ...

---

## 👤 Les parties — contacts

**Prospect**
- Nom complet : {prospect_full_name}
- Rôle : Gérant / Dirigeant (à confirmer)
- Email : {contact.email}
- Téléphone : {contact.phone}
- WhatsApp : {contact.whatsapp}
- Adresse : {contact.address_line}, {contact.postal_code} {contact.city}

**Société**
- Raison sociale : {company_legal_name}
- SIRET : {meta.siret}
- Créée en : {business.founded_year} ({business.years_in_business} ans)
- Équipe : {business.team_size_label}

---

## 🏢 Business — faits

| Champ | Valeur |
|---|---|
| Année de création | {business.founded_year} |
| Ancienneté | {business.years_in_business} ans |
| Structure équipe | {business.team_size_label} |
| Social proof | {business.social_proof} |
| Rayon géographique | {business.geo_radius_km} km |
| Départements couverts | {business.geo_cities_covered} |

---

## 🎭 ICP (client idéal du prospect)

- **Profil** : {icp.description}
- **Tranche d'âge** : {icp.age_range}
- **Budget par client** : {icp.budget_range_label}

---

## 💶 Économie du business

- **Panier moyen** : {economics.avg_deal_size_eur} €
- **Volume mensuel actuel** : {economics.current_monthly_volume_label}
- **Canaux d'acquisition actuels** : {economics.primary_acquisition_channels}

---

## 💀 Expérience avec agence précédente

> À remplir UNIQUEMENT si une agence précédente a été mentionnée dans le call.

- **Montant perdu** : {prior_agency_pain.amount_wasted_eur} €
- **Durée** : {prior_agency_pain.duration_months} mois
- **Résultats** : {prior_agency_pain.outcome}
- **Cause racine** : {prior_agency_pain.root_cause}

---

## 🧮 Paramètres ROI (pour simulateur landing)

| Champ | Valeur |
|---|---|
| Panier moyen par défaut | {roi_calc_defaults.avg_basket_eur} € |
| Utiliser vocabulaire industrie dans les labels | {roi_calc_defaults.use_industry_vocab_in_calc} |
| Mot "deal" → | **{meta.industry_vocab.deal_word}** / pluriel : {meta.industry_vocab.deal_word_plural} |
| Mot "customer" → | **{meta.industry_vocab.customer_word}** |

---

## 💸 Tarification

- **Fee the platform (mois test)** : {pricing.lf_fee_eur} €
- **Budget Meta recommandé** : {pricing.recommended_ad_budget_eur} €/mois
- **Engagement** : {pricing.engagement}

---

## 🔄 Process commercial actuel du prospect

- **Structure équipe** : {sales_process_current.team_structure_label}
- **Douleur actuelle** : {sales_process_current.current_pain_in_process}

---

## 📅 Follow-up

- **Prochain call prévu** : {follow_up.next_call_iso}
- **Canal** : {follow_up.channel}

---

## ✅ Quality gates

- [ ] Contact & business complets : {quality_gates_passed.contact_and_business_filled}
- [ ] Headline "X. Y. Sans Z." ≤ 12 mots : {quality_gates_passed.headline_hook_format_ok}
- [ ] 3 bullets "Fini les" verbatim : {quality_gates_passed.three_fini_les_bullets_ok}
- [ ] Vocabulaire industrie renseigné : {quality_gates_passed.industry_vocab_populated}
- [ ] ≥ 3 verbatim pains / ≥ 2 verbatim wins : {quality_gates_passed.min_verbatims_ok}
- [ ] Prior agency cleanly handled (rempli ou null) : {quality_gates_passed.prior_agency_cleanly_handled}
- [ ] `avg_basket_eur` cohérent avec l'industrie : {quality_gates_passed.basket_in_industry_range}

### Champs à revoir

{needs_human_review}

---

## ➡️ Prochaine étape

Invoque `devis-vercel-generator` en lui passant ce fichier JSON :

```
projects/{client_slug}/00-sales-brief/brief-output.json
```

Le skill downstream génèrera la landing page Vercel personnalisée (hero, parties, services, simulateur ROI, conditions) en injectant tous les champs ci-dessus.
