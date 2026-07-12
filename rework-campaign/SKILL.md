---
name: rework-campaign
description: Audite un compte Meta Ads, score chaque créative/ad set sur la performance réelle (CPL/CPA, hook rate, hold rate, CTR, CVR, frequency), PAUSE les créas mortes/non-pertinentes, identifie les TOP performers, génère des VARIATIONS des gagnants (nouveaux angles/hooks/proposition de valeur via le skill creative-statics-v2) et les RÉINTÈGRE dans le compte (via meta-campaign-launcher) — boucle d'optimisation rework end-to-end, full-auto avec garde-fous de sécurité. Récupère le token Meta via Vercel (app). Encode un framework de décision kill/keep/scale/iterate chiffré et éprouvé (recherche 36 media buyers + passe adversariale). Use when the user asks to "rework la campagne de {client}", "audite le compte Ads {client}", "optimise les campagnes Meta", "coupe les créas qui marchent pas et relance", "refais les pubs à partir des meilleures", "rework campaign", "optimise et relance le compte publicitaire". Trigger phrases : "rework campaign", "audit compte Meta", "optimiser campagnes", "couper les mauvaises créas", "scaler les gagnants", "relancer des variations des tops".
---

# Rework Campaign

Skill d'**optimisation/rework de compte Meta Ads de bout en bout**. Il transforme un compte qui tourne en une boucle d'amélioration continue :

```
AUDIT (insights réels) → SCORE (kill/keep/scale/iterate) → PAUSE les perdants
   → VARIATIONS des gagnants (creative-statics-v2) → RÉINTÉGRATION (meta-campaign-launcher) → re-mesure
```

Il **réutilise les skills existants** : token & écriture via `meta-campaign-launcher`, génération de créas via `creative-statics-v2`. Sa valeur propre = **l'audit + le scoring + le pilotage de la boucle**, encodés depuis une recherche de 36 media buyers seniors + une passe de vérification adversariale (sécurité du full-auto).

> ⚠️ **Full-auto ≠ imprudent.** Le mode par défaut sur un nouveau compte est **PROPOSITION** (calcule + notifie, n'exécute pas) pendant 14 jours, puis exécution auto sous garde-fous. Toute action est **réversible** (pause, jamais delete) et **bornée** (circuit-breakers). Voir § Garde-fous — c'est la partie load-bearing.

---

## 🧠 Les 4 métriques de décision (imposées) + leur rôle diagnostic

| Métrique | Formule (champs Insights API) | Diagnostique | Seuils repères |
|---|---|---|---|
| **CPL / CPA** | `spend / leads` (parser `actions[]` / `cost_per_action_type[]`) | rentabilité finale | kill > 2x cible (lead-gen) sur 7j ; scale ≤ cible |
| **Hook rate** | `video 3s views / impressions` | les 0-3s (l'accroche) | <20-25% faible, 30-40% fort |
| **Hold rate** | `thruplay / 3s views` | le corps de la vidéo | <30% faible, 40-50% bon, >50% fort |
| **CTR (link)** | `inline_link_clicks / impressions` | promesse/angle/CTA | <0.6% (cold B2B) = angle cassé, >1.2% bon |
| **CVR** | `leads / link_clicks` (ou LPV) | offre/landing/form | Instant Form 10-15%, landing froide 1-3% |
| **Frequency** | champ `frequency` (7j) | saturation | cold <2.5 OK, >3 fatigue, >4 cliff |
| **Volume / signif.** | impressions, spend, conversions | fiabilité du verdict | voir Garde-fou #2 |

**Matrice maîtresse CTR × CVR** (le diagnostic central) :
- **CTR bas + CVR ok** → problème CRÉA/HOOK → `regenerate_creative` (nouveau hook/angle/format)
- **CTR ok + CVR bas** → problème OFFRE/LANDING/match-message → `fix_offer` (NE PAS toucher la créa)
- **CTR bas + CVR bas** → double problème, prioriser la créa
- **CTR ok + CVR ok** → `SCALE`

**Ordre d'audit du funnel** (s'arrêter au 1er maillon cassé, ne jamais juger une étape si l'amont est sous seuil) :
`tracking → volume → hook → hold → CTR → CPC → CVR → CPL`

---

## 🔁 Pipeline rework — 6 phases

```
A. Token + santé compte   → pull token, account_status, circuit-breaker global, tracking gate
B. Pull insights          → /act/insights level=ad sur 7d ET 14d ET 3d + hydrate creative{}
C. Score & classer        → chaque ad → KILL | KEEP | SCALE | ITERATE (decision framework)
D. Actions réversibles    → PAUSE perdants, ajuste budgets gagnants (bornés), JAMAIS delete
E. Variations des winners → creative-statics-v2 (angle-first, modulaire) sur les ITERATE/SCALE
F. Réintégration          → upload + create_ads (meta-campaign-launcher), PAUSED → re-mesure
```

### Phase A — Token + santé du compte (bloquant)
1. Token via `../meta-campaign-launcher/scripts/pull_token.sh`.
2. `account_status` doit = 1 (sinon STOP, cf. R10 du launcher : compte suspendu).
3. **Circuit-breaker global** : si dépense compte +25% J/J, OU CPA compte +30%/24h, OU conversions compte = 0 sur 24h alors qu'il y avait du volume → **LECTURE SEULE + alerte humaine**, aucune action.
4. **Hard gate tracking** : si pixel/CAPI n'a remonté aucun event depuis 6-24h, ou volume d'events −40% vs médiane 7j, ou EMQ dégradée → **geler kill ET scale**, alerter. Un tracking cassé fabrique des `leads=0` qui tueraient les gagnants.

### Phase B — Pull insights (`scripts/fetch_insights.py`)
`GET /act_{id}/insights?level=ad&fields=...` sur 3 fenêtres (3d/7d/14d) + hydratation `creative{}` par batch pour relier chaque ad à son image/vidéo/copy. Champs vidéo inclus (hook/hold). Voir `references/metrics-reference.md` pour la liste exacte des champs et le parsing de `actions[]`.

### Phase C — Score & classer (`scripts/score_creatives.py`)
Applique le **framework de décision** (`references/decision-framework.md`) à chaque ad, avec les gates de volume/maturité/tracking. Sortie : un verdict par ad (`KILL`/`KEEP`/`SCALE`/`ITERATE`) + la raison + le niveau de confiance. **Aucun verdict sous le seuil de significativité** → statut `INSUFFICIENT_DATA`, action `wait`.

### Phase D — Actions réversibles (bornées)
- **PAUSE** (jamais delete) les `KILL` confirmés (tous les garde-fous réunis).
- **Ajuste le budget** des `SCALE` : lire la limite de hausse sans-reset exposée par Meta pour CET ad set (fallback +15-20%), respecter le plafond compte.
- **Circuit-breaker portefeuille** : max N kills/run (défaut 2 ou 15% des ads actives, le plus petit), max N scales/run. Au-delà → flag pour revue humaine.
- Jamais d'édit qui reset le learning (audience/event/placement/créa sur un gagnant) en auto → on **duplique** plutôt qu'éditer.

### Phase E — Variations des gagnants
Pour chaque `ITERATE` (gagnant fatigué) et chaque gagnant à diversifier : appeler **`creative-statics-v2`** avec une **stratégie de variation angle-first et modulaire** (voir § Variation). On décline l'ADN du gagnant, on ne repart jamais de zéro.

### Phase F — Réintégration
Upload des nouvelles créas (`../meta-campaign-launcher/scripts/upload_images.py`) + création des ads (`../meta-campaign-launcher/scripts/create_ads.py`) **en PAUSED**, dans un ad set de test propre (1 variable isolée par cellule, budget égal). Puis re-mesure au prochain run.

---

## 🎯 Framework de décision (résumé — détail chiffré dans `references/decision-framework.md`)

**Gates préalables à TOUT verdict** (si un échoue → `INSUFFICIENT_DATA`/`SKIP`) :
1. **Tracking vivant** (events < 24h, link clicks > 0, un autre ad set convertit).
2. **Maturité** : ad set hors `Learning`/`Learning Limited`, âge ≥ 3-7j, ≥ 50 events/7j.
3. **Volume/significativité** : ≥1000-2000 impressions pour juger hook/CTR ; ≥30-50 conversions (ou spend ≥ plancher absolu) pour juger CPL/kill. **≥90-95% de confiance** exigé pour une action auto (65% = flag humain seulement).
4. **Fenêtre d'attribution écoulée** : ne jamais compter `0 conversion` sur une fenêtre < attribution (7-day click). Juger sur jours clôturés, pas same-day.

**KILL (→ PAUSE)** — toutes vraies :
- **Hard kill structurel** : `spend ≥ max(3×CPL_cible, plancher absolu ~500$/5-6×CPL) ET leads = 0 ET tracking vérifié ET delivery OK`.
- **Kill perf (J10+, hors learning)** : `CPL > 2×cible (lead-gen) sur 5-7 jours OUVRÉS consécutifs ET significance atteinte`. Zone grise 1.5-2× → réduire budget −20%, ré-évaluer 48-72h.
- **Kill créa (hook cassé)** : `hook rate < 15% à 2000+ impressions ET 0 conversion` (sinon flag).

**ITERATE / REFRESH (fatigue → régénérer)** : `frequency > 3 (cold) ET CTR −30% vs pic`, OU `CPM +40% vs baseline`. On régénère, on ne kill pas un concept gagnant fatigué.

**SCALE (gagnant)** — toutes vraies : `CPL ≤ cible sur ≥3-5j consécutifs + hors learning + CTR stable/haut + frequency < 2.0`. → +budget borné (limite sans-reset Meta / fallback +15-20% / 72h).

**KEEP** : tout le reste (laisser tourner, re-mesurer).

---

## 🎨 Stratégie de variation des gagnants (Phase E)

**Hiérarchie créative** (régénérer du haut vers le bas) : `Angle > Hook > Claim/proof > Format > CTA`. L'angle survit à la fatigue et est portable ; un hook ne fait qu'une pub.

**Décliner un gagnant** (modulaire, ne jamais repartir de zéro) : décomposer en 4 modules `[visuel] + [hook 0-3s] + [body=angle] + [CTA]`, garder 3 constants, swapper 1.

**Les 7 angles B2B service** à boucler sur un gagnant : pain-led · proof-led · mechanism · contrarian · time/effort · prix/ROI · autorité.

**Ratio** : 1 angle validé → 8-12 hooks + 3-4 formats. Mais **tester 1 variable isolée par cellule** (un test d'angle ne change QUE l'argument). Ne jamais lancer >3-5 variations/round.

→ **Implémentation** : passer au skill `creative-statics-v2` le brand profile du client + le concept/angle du gagnant + la liste des angles à décliner. Récupérer les PNG générés, les réintégrer en Phase F.

---

## 🛡️ Garde-fous full-auto (LOAD-BEARING — issus de la passe adversariale)

| # | Garde-fou |
|---|---|
| **#0 Fail-safe** | En cas de doute / donnée manquante / ambiguïté → **INACTION + alerte**. Prime sur toutes les autres règles. |
| **#1 Mode proposition 14j** | Nouveau compte → calcule + notifie, **n'exécute pas** pendant 14j. Exécution auto seulement après validation explicite du mandat (CPL cible, budget plancher/plafond, fenêtre attribution, ad sets éligibles). |
| **#2 Hard gate tracking** | Pixel/CAPI down ou events −40% → gel total kill+scale. `leads=0` non vérifié = cause #1 de faux-kill. |
| **#3 Circuit-breaker compte** | Dépense +25% J/J ou CPA +30%/24h → pause totale + alerte. Plafond de dépense quotidien dur (cap client). |
| **#4 Blast radius** | Par run : max N kills (2 ou 15% des ads, le + petit), max 20% du budget déplaçable, max +15% budget compte/jour. Au-delà → revue humaine. |
| **#5 Maturité / learning** | Jamais d'action budgétaire sur un ad set en `Learning`/`Learning Limited`. No-touch 5-7j après launch/edit. Kill en learning seulement si catastrophe vérifiée (≥ plancher absolu + leads=0 + tracking OK). |
| **#6 Attribution** | CPA/CVR jugés sur fenêtre ≥ attribution (7j), jamais 3j ni same-day. |
| **#7 Confiance ≥90-95%** | Action auto seulement à ≥90-95% de confiance statistique. 65% = recommandation humaine, jamais exécution. |
| **#8 Réversible only** | PAUSE jamais DELETE. Dupliquer un gagnant plutôt que l'éditer. Tout est loggé, horodaté, rollback possible. Kill-switch global manuel. |
| **#9 Plancher absolu kill-sans-conv** | Ne jamais hard-kill sans conversion sous ~500$/5-6×CPL (à 1-2×CPL, 0 lead arrive ~37% du temps par hasard sur une créa saine → faux positifs). |

---

## 🗂️ Structure
```
rework-campaign/
├── SKILL.md
├── references/
│   ├── decision-framework.md   ← arbre de décision kill/keep/scale/iterate chiffré + gates
│   ├── metrics-reference.md     ← champs Insights API, formules, parsing actions[], benchmarks
│   └── github-references.md     ← 27 repos/outils Meta Ads de référence (audit, MCP, scrapers)
└── scripts/
    ├── fetch_insights.py        ← Phase B : pull insights ad-level (3d/7d/14d) + hydrate creative
    ├── score_creatives.py       ← Phase C : applique le framework → verdict + confiance par ad
    └── rework_orchestrator.py   ← pipeline A→F, dry-run par défaut, garde-fous, --execute pour agir
```

## 🔗 Skills chaînés
- **Token + écriture** : `../meta-campaign-launcher/` (pull_token.sh, create_ads.py, upload_images.py, create_adset.py + cheatsheet API).
- **Génération de créas** : `../creative-statics-v2/` (build_variations.py, gen_pool.py, gpt_image2 / nano_banana_2).
- **Copy** : `../meta-ads-copywriter/` pour les nouveaux textes/angles.

## 📊 Ce qui reste du jugement humain
1. Définir le **mandat** (CPL cible, budget plancher/plafond, fenêtre attribution) avant le full-auto.
2. Valider les **variations générées** avant réintégration (l'œil tranche l'uncanny valley).
3. Trancher les cas en **zone grise** (CPA 1.1-1.5× cible) et les flags.

*Skill né de la recherche "rework-campaign" (36 media buyers + passe adversariale, juin 2026). Règles chiffrées et garde-fous full-auto issus de comptes réels. PAUSE jamais DELETE, fail-safe = ne rien faire, jamais d'action sur tracking cassé ou en learning phase.*
