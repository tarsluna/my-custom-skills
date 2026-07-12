# Framework de décision — kill / keep / scale / iterate

Issu de la recherche 36 media buyers + passe adversariale. Tous les seuils sont des **valeurs par défaut** à surcharger par le mandat client (CPL cible surtout).

## 0. Gates préalables (un seul échec → pas de verdict)

```
GATE_TRACKING   : events conversion < 24h ? link_clicks > 0 ? un autre adset convertit ? EMQ ≥ 6 ?
GATE_MATURITE   : effective_status NOT IN (Learning, Learning Limited) ET age_days ≥ 3 (idéal 7) ET events_7d ≥ 50
GATE_VOLUME     : hook/CTR → impressions ≥ 1000-2000 ; CPL/kill → conversions ≥ 30-50 OU spend ≥ plancher_absolu
GATE_ATTRIB     : fenêtre d'éval ≥ fenêtre d'attribution (7-day click). Exclure jour courant + N derniers jours non clôturés.
GATE_CONFIANCE  : action AUTO seulement si confiance ≥ 90-95%. Sinon → FLAG (recommandation humaine).
```
Si un gate échoue → `INSUFFICIENT_DATA` / `SKIP` (fail-safe = ne rien faire).

## 1. Plancher absolu (anti-faux-kill)

- `plancher_absolu_kill = max(5 × CPL_cible, 500$ équiv. €)` — raison statistique : à 1-2× CPL, 0 lead arrive ~37% du temps sur une créa SAINE (Poisson). À 2.5× CPL ~92% de confiance, 3× ~95%.
- Budget min par ad set (diagnostic seulement, jamais hausse auto) : `(50 × CPA_cible) / 7 ≈ CPA × 7.14`. En dessous → flag « sous-financé, ne sortira jamais du learning » → recommander consolidation.

## 2. KILL (→ PAUSE, jamais delete)

```
HARD_KILL (structurel, autorisé même en learning si catastrophe) :
  spend ≥ plancher_absolu_kill ET leads == 0 ET GATE_TRACKING ok ET delivery ok (impressions ≥ 5000)
  → cause = pixel/offre/audience/form cassé. PAUSE + alerte.

KILL_PERF (J10+, hors learning) :
  CPL > 2 × CPL_cible (lead-gen ; 2.5-3× pour e-com) sur 5-7 jours OUVRÉS consécutifs
  ET GATE_VOLUME (≥ 20-30 conv ou ≥ 5000-10000 impr/variante)
  → PAUSE.
  Zone grise CPL 1.5-2× cible → NE PAS kill : réduire budget −20% max, ré-évaluer 48-72h.
  Zone grise CPL 1.1-1.3× → +3 jours d'observation.

KILL_CREA (hook cassé, haut funnel) :
  hook_rate < 15% à ≥ 2000 impressions ET 0 conversion → PAUSE.
  hook_rate 15-25% → FLAG (pas auto-kill : un mauvais hook peut convertir selon l'offre).
```

## 3. ITERATE / REFRESH (fatigue → régénérer, ne pas tuer le concept)

```
Déclencheurs (n'importe lequel, sur ad MATURE ayant déjà atteint un pic) :
  frequency_7d > 3.0 (cold) / > 6 (warm) ET CTR −30% vs pic
  OU CPM +40% vs baseline 14j
  OU CTR −15..25% sur 7j glissants alignés (jours de semaine) persistant ≥ 2 lectures à 48-72h
Palier progressif avant refresh total :
  freq 2.5 / perf −10-15% → budget −25%
  freq 3.5 / perf −20-30% → budget −50%
  CPM ×2 ou CTR −40% → PAUSE + régénérer
→ Phase E : variations angle-first du concept gagnant.
```

## 4. SCALE (gagnant) — toutes vraies

```
CPL ≤ CPL_cible sur ≥ 3-5 jours consécutifs
ET hors learning (Active)
ET CTR stable ou en hausse
ET frequency < 2.0
ET ≥ 8 conv/jour sur 4 jours consécutifs (règle 20-72-8, idéal)
→ hausse de budget = limite sans-reset exposée par Meta pour cet ad set
   (fallback +15-20% si l'info API est indisponible), max 1 hausse / 72h, max 2 / semaine / ad set.
   Respecter le plafond compte + blast radius.
Horizontal (si frequency > 3 OU CPA marginal > +25% baseline) : DUPLIQUER (post-id) vers nouvelle audience, ne pas éditer l'original.
Stop-scaling : sur CPA MARGINAL = (spend_N − spend_N-1)/(conv_N − conv_N-1) > +25% baseline OU > 80-90% LTV.
```

## 5. KEEP

Tout le reste : laisser tourner, re-mesurer au prochain run.

## 6. Diagnostic CTR × CVR (quoi régénérer)

| CTR | CVR | Diagnostic | Action |
|---|---|---|---|
| bas (<0.8× cible) | ok | créa/hook | `regenerate_creative` (Phase E) |
| ok | bas (<0.6× cible) | offre/landing/match | `fix_offer` (NE PAS toucher la créa) |
| bas | bas | double, volume CVR non fiable | prioriser créa |
| ok | ok | — | `SCALE` |

Cibles défaut lead-gen B2B FR : CTR_link 1.0% (prospecting), CVR 8% (landing) / 12% (instant form).

## 7. Consolidation (levier #1 si « Learning Limited »)

```
budget_min_adset = CPA_cible × 7.14
nb_adsets_max = floor(budget_total_jour / budget_min_adset)
si nb_adsets_actifs > nb_adsets_max → CONSOLIDER (garder top performers, merger/couper le reste)
Audience overlap : <20% OK · 20-30% surveiller · >30% merge/exclure · >40-50% fix immédiat · 60%+ merge d'office
Structure cible : 1-3 ad sets/campagne, variation au niveau CRÉA (pas adset). « Fewer, bigger, better ».
Faire TOUS les changements en UNE fois (chaque edit reset le learning).
```

## 8. Learning phase — edits qui resettent (ne JAMAIS en auto sans intention)
optimization event · audience/ciblage · créa (ajout/swap) · placements · bid strategy · budget delta > limite sans-reset Meta · pause > 7j · nouvelle ad dans l'ad set.
→ Pour changer un gagnant : **dupliquer**, modifier le duplicata.
NB : la vieille règle « +20% = reset garanti » est PÉRIMÉE — Meta expose désormais la limite exacte sans-reset par ad set ; la lire via l'API, fallback +20% conservateur.
