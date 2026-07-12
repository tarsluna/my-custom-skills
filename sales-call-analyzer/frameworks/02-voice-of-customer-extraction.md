# Framework 02 — Voice of Customer Extraction

**Objectif** : capturer le **vocabulaire spécifique à l'industrie du prospect** pour que la landing page parle sa langue, pas celle d'une agence marketing générique.

**Pourquoi c'est critique** : dans la transcription Acme, le gérant dit "chantier" 12+ fois. Utiliser "deal" ou "client" dans la calculette ROI casserait la personnalisation. Le devis doit refléter exactement comment le prospect parle de son business.

---

## 🗣️ 1. Le mot pour "deal" — `industry_vocab.deal_word`

Le prospect a un mot spécifique pour désigner une transaction signée. Scanner la transcription pour ce mot récurrent.

### Dictionnaire de correspondance par industrie

| Industrie | `deal_word` | `deal_word_plural` | `customer_word` |
|---|---|---|---|
| BTP / menuiserie / rénovation | chantier | chantiers | propriétaire |
| Santé / dentiste / kiné / ostéo | patient | patients | patient |
| Coaching / formation / consulting | client / dossier | clients / dossiers | apprenant / coaché |
| Immobilier | mandat / transaction | mandats / transactions | vendeur / acquéreur |
| Avocat / expert-comptable | dossier | dossiers | client |
| B2B SaaS / enterprise | deal / contrat | deals / contrats | compte |
| Restaurant / hôtel | couvert / réservation | couverts / réservations | client |
| Auto / concession | commande / livraison | commandes / livraisons | acquéreur |
| Agence immo neuf / promoteur | lot / réservation | lots / réservations | acquéreur |
| E-commerce | commande | commandes | client |
| Cabinet recrutement | mission / placement | missions / placements | candidat / client |

### Règle d'extraction

1. Compter les occurrences des mots candidats dans la transcription.
2. Le mot le plus utilisé par le **prospect** (pas the operator) gagne.
3. Si the operator utilise "client" mais le prospect dit "chantier" → le prospect gagne.
4. Si aucun des mots de la table ci-dessus n'apparaît, fallback = "client".

### Exemple Acme

Comptage dans la transcription :
- "chantier" : 14 occurrences (par le gérant)
- "client" : 6 occurrences (mixte)
- "projet" : 3 occurrences

→ `industry_vocab.deal_word = "chantier"`, `deal_word_plural = "chantiers"`.

Dans la calculette ROI de la landing page, le label devient **"Chantiers signés"** au lieu de **"Clients signés"**.

---

## 🎯 2. Le mot pour "customer / prospect" — `industry_vocab.customer_word`

Le prospect a aussi un mot pour désigner son client final.

### Extraction

Scanner pour les mots : propriétaire, patient, apprenant, vendeur, acquéreur, acheteur, client final, usager, abonné, membre...

### Exemple Acme

le gérant parle de "propriétaires" (pour fenêtres de maison) et "particuliers". Le mot dominant est "propriétaire".

→ `industry_vocab.customer_word = "propriétaire"`.

---

## 💰 3. Sensibilité prix — `pricing` et `icp.budget_range_label`

Scanner les signaux de sensibilité prix :

### Signaux "prix bloquant" (le prospect a été brûlé par les promos)
> « Ça bloquait souvent au niveau du prix. »
> « Les gens comparaient 3 devis. »
> « Ils voulaient du low-cost. »

### Signaux "prix OK si valeur" (le prospect accepte de payer)
> « On sait que notre produit est plus cher, mais il est meilleur. »
> « Nos clients acceptent de payer pour la qualité. »

### Signaux sur le budget publicitaire confirmé
Quand the operator demande "OK pour 500 € de budget Meta ?" et le prospect accepte → capturer dans `pricing.recommended_ad_budget_eur`.

Quand the operator annonce "790 € le premier mois" et le prospect confirme → `pricing.lf_fee_eur = 790`.

### Exemple Acme

- Signaux prix bloquant : "ça bloquait souvent au niveau du prix" → l'ICP doit fuir les comparateurs de prix
- Budget Meta confirmé en fin d'appel : 500 €
- Fee LF : 790 €

→ `pricing.lf_fee_eur = 790`, `pricing.recommended_ad_budget_eur = 500`, `pricing.engagement = "none"` (test 1 mois).

---

## 🎭 4. ICP (Ideal Customer Profile) — `icp`

Extraire du call :
- **Tranche d'âge** des clients finaux
- **Segment socio-éco** (premium, milieu, low-cost)
- **Géographie** du client final (s'il n'est pas le même que le prospect)
- **Phase de vie** (propriétaire, locataire, dirigeant, salarié…)

### Exemple Acme

le gérant décrit :
- "30 à 70 ans, propriétaires de leur maison"
- "Pas vendeurs de prix, ils veulent du solide"
- "Département, département voisin partiel, département voisin nord"

→
```json
"icp": {
  "description": "Propriétaires 30-70 ans, projet menuiserie extérieure premium, refusent les promos low-cost",
  "age_range": "30-70 ans",
  "budget_range_label": "5 000 € à 15 000 € par chantier"
}
```

---

## 🔄 5. Stade du cycle d'achat — `sales_process_current`

Où en est le prospect dans son cycle de décision ?

### Signaux "phase découverte" (test, pas encore décidé)
> « Je veux voir ce que ça donne. »
> « On teste. »

### Signaux "phase décision imminente"
> « Je me décide cette semaine. »
> « Je vous confirme vendredi. »

### Exemple Acme

le gérant dit :
> « Je me décide cette semaine. »

→ Un follow-up est booké **vendredi 24/04/2026 à 11h**.

```json
"follow_up": {
  "next_call_iso": "2026-04-24T11:00:00+02:00",
  "channel": "whatsapp"
},
"meta": {
  "decision_deadline_iso": "2026-04-25"
}
```

---

## 📞 6. Structure commerciale actuelle — `sales_process_current`

Scanner pour comprendre comment le prospect vend AUJOURD'HUI :
- Combien de commerciaux ?
- Quels canaux d'acquisition ?
- Quel volume de leads/mois ?
- Quel % de closing ?

### Exemple Acme

> « On a 1 commercial + moi à temps partiel (20-25% du temps). »
> « 70% des appels viennent du bouche-à-oreille. »
> « On reçoit environ 30 appels/mois. »

→
```json
"sales_process_current": {
  "team_structure_label": "1 commercial + le gérant à temps partiel (20-25%)",
  "current_pain_in_process": "Commercial déplacé 60 km pour des prospects pas qualifiés — coûts carburant en hausse"
},
"economics": {
  "current_monthly_volume_label": "~30 appels entrants / mois",
  "primary_acquisition_channels": ["Bouche-à-oreille (70%)", "Enseigne physique", "Google recherches locales"]
}
```

---

## ✅ Check-list Voice of Customer

- [ ] `industry_vocab.deal_word` renseigné (jamais "deal" par défaut)
- [ ] `industry_vocab.deal_word_plural` renseigné
- [ ] `industry_vocab.customer_word` renseigné
- [ ] `icp.description` en 1 phrase nette
- [ ] `icp.age_range` si mentionnée
- [ ] `icp.budget_range_label` formule humaine (pas juste un nombre)
- [ ] `pricing.lf_fee_eur` + `pricing.recommended_ad_budget_eur` extraits du call si confirmés
- [ ] `sales_process_current.team_structure_label` décrit l'équipe co actuelle
- [ ] `economics.primary_acquisition_channels` liste les 2-3 canaux principaux
- [ ] `follow_up.next_call_iso` au format ISO si une date de RDV de suivi a été posée
