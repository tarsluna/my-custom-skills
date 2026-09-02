# Règles de structuration des campagnes Meta

Règles non négociables sauf instruction contraire explicite du client.

## 1. Nombre de campagnes

**Par défaut : 1 seule campagne.**

Créer une 2ème campagne UNIQUEMENT si :
- Offres réellement différentes (produit A et produit B sans rapport stratégique)
- Objectifs Meta différents (Leads vs Conversions vs Sales vs Trafic)
- Géographies très distinctes nécessitant un budget cloisonné
- Budgets séparés exigés par le client (compta multi-BU)

Justification : la consolidation budgétaire est une règle Meta depuis l'update Andromeda. Fragmenter en plusieurs campagnes sur petit budget tue l'algorithme avant qu'il sorte de la learning phase (50 events / 7 jours requis).

## 2. Nombre d'ad sets

**2 ad sets maximum** par campagne en phase de test.

- **Ad set 1 — Audience par intérêts** : audience définie par 3-8 intérêts pertinents + critères géo/âge/sexe. Permet de tester si les signaux d'intérêt explicites convertissent.
- **Ad set 2 — Audience Broad** : uniquement géo + âge + sexe. Aucun intérêt, aucune exclusion. Laisse Meta optimiser librement. C'est l'ad set qui scale en général le mieux post-Andromeda.

Pas de lookalike, pas de retargeting en phase 1. Ces ad sets viendront en phase 2 (scaling) après validation de la phase de test.

## 3. Nombre de créatives

**5 à 10 créatives par campagne**, dupliquées dans les 2 ad sets.

- 5 créatives = minimum viable pour la diversité d'angles
- 10 créatives = standard si budget ≥ 50€/jour
- Au-delà de 10 : risque de fragmentation des impressions et de cannibalisation

Diversité créative > volume créatif. Chaque créative doit explorer un angle distinct, pas une variation cosmétique du même message.

## 4. Budget

| Budget quotidien | Recommandation |
|---|---|
| < 30€/jour | Déconseillé. Ne sortira jamais de learning phase. |
| 30-50€/jour | Minimum viable. 1 campagne, 2 ad sets, 5 créatives. |
| 50-100€/jour | Standard PME. 1 campagne, 2 ad sets, 7-10 créatives. |
| 100-200€/jour | Confortable. 1 campagne, 2 ad sets, 10 créatives, scaling rapide. |
| > 200€/jour | Possibilité de séparer testing/scaling en 2 campagnes. |

## 5. Objectifs Meta

| Funnel | Objectif Meta recommandé |
|---|---|
| Instant Form | **Leads** (Génération de prospects) avec optimisation Lead Form |
| VSL → Calendly | **Conversions** (Sales / custom event "RDV pris") |
| VSL → Landing → Call | **Conversions** (Lead form custom) |
| E-commerce direct | **Sales** (Achat) |

Ne JAMAIS choisir Trafic ou Engagement pour de la lead gen. Toujours optimiser sur l'event business le plus proche de la vente.

## 6. Convention de nommage

```
[CLIENT] - [OFFRE] - [OBJECTIF] - [DATE]
```

Exemples :
- `AcmeClosing - Méthode 5JC - Leads - 2026-04`
- `AcmeConseil - Audit Stratégie - Conversions - 2026-04`

Ad sets :
- `[CAMPAGNE] / Intérêts - [détails]`
- `[CAMPAGNE] / Broad - [géo]`

Créatives :
- `[CAMPAGNE] / [Format] / [Angle] / V[n°]`
- Ex : `AcmeClosing-5JC / FaceCam / Douleur / V01`
