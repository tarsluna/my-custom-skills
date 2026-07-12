# Framework 02 — Competitor Inspiration Engine

Comment transformer `02-competitor-ads/data.csv` (+ `analysis.md` + captures `creatives/`) en **carburant créatif** pour la V2. Principe : **s'inspirer des meilleures ads concurrentes, jamais les copier.**

---

## 1. Source de vérité : `data.csv`

Produit par `competitor-ads-research`. Colonnes :

```
competitor, category, observed_status, primary_angle, secondary_angle,
likely_audience, sample_hook, inference_confidence, notes
```

- `observed_status` : `verified_capture` (ad réellement vue) vs `inferred_only` (déduit du positionnement). **Privilégier les `verified_capture`** pour l'inspiration de style — ce sont de vraies ads qui tournent.
- `inference_confidence` : `high` / `medium` / `low` — pondère la confiance dans l'angle.
- `sample_hook` : le hook observé/inféré — sert à **détecter les formulations saturées** (pas à les recopier).

---

## 2. Ce qu'on extrait (`competitor_mine.py` → `competitor-insights.json`)

### a) `top_angles` — les angles qui dominent le marché
Agréger `primary_angle` + `secondary_angle` sur tout le CSV, compter les occurrences. Les plus fréquents = ce que le prospect voit déjà partout.
→ **Usage** : soit on les **évite** (pour se différencier), soit on les **attaque frontalement** (common-enemy : « Tout le monde te promet X. Nous on fait Y »).

### b) `saturated` — angles à bannir tels quels
Un angle est saturé s'il apparaît chez **≥ 3 concurrents** (ou ≥ 40% du CSV). Liste noire automatique. Croisée avec la banlist du copy framework V1 (« agence 360° », « sur mesure », « expert/n°1 », « clés en main »…).
→ **Usage** : aucun hook client ne sort sur un angle saturé sans twist différenciant explicite.

### c) `white_spaces` — les catégories vides
Croiser les angles présents dans le CSV avec les angles pertinents pour l'ICP (`analysis.md` section white spaces + psychographic). Ce que **zéro concurrent** ne travaille = terrain de jeu prioritaire.
→ **Usage** : 50%+ des angles du pack V2 doivent viser un white space (différenciation maximale).

### d) `style_refs` — référence visuelle de STYLE (si captures dispo)
Si `02-competitor-ads/creatives/` contient des captures d'ads concurrentes, sélectionner les **2-3 visuellement les plus fortes** (lisibilité, thumbstop, exécution). Elles deviennent des **références de style** passées à GPT Image 2 via `input_images`.

> ⚠️ **Référence de STYLE uniquement.** On dit à GPT Image 2 : *"use the visual composition / lighting / energy of the reference as inspiration, but the brand, colors, product and text must be 100% [client]"*. On ne reprend **jamais** le copy, le logo, ni les claims du concurrent. C'est de l'inspiration d'exécution, pas du plagiat.

---

## 3. Règle d'or : inspiration ≠ copie

| ✅ On s'inspire de… | ❌ On ne copie jamais… |
|---|---|
| La **composition** (split-screen, hero centré, collage) | Le copy / les hooks concurrents |
| L'**énergie / le ton visuel** (premium, brut, fun) | Le logo / la marque concurrente |
| Le **format gagnant** (ce qui tourne longtemps = ce qui marche) | Les claims chiffrés du concurrent (non sourcés pour nous) |
| Les **white spaces** qu'ils laissent vides | Leur palette exacte (on garde celle du client) |
| Les **angles saturés** (pour les éviter/retourner) | Reproduire une ad à l'identique |

Le copy client reste **100% traçable** (`[V][W][P][C]`) et validé 6-checks. Le `data.csv` informe la **stratégie d'angle** et l'**inspiration de style**, pas le texte.

---

## 4. Du CSV à la matrice — flux concret

```
data.csv ──► competitor_mine.py ──► competitor-insights.json
                                       │
                ┌──────────────────────┼───────────────────────┐
                ▼                      ▼                       ▼
          saturated[]            white_spaces[]            style_refs[]
                │                      │                       │
        (banlist angles)      (angles prioritaires)   (input_images GPT Image 2)
                │                      │                       │
                └──────────► variation-matrix.json ◄───────────┘
                              (Phase C — angles choisis)
```

Concrètement, à la Phase C, pour composer la matrice :
1. Retirer tout angle ∈ `saturated` (sauf twist common-enemy explicite).
2. Prioriser les angles ∈ `white_spaces` (≥ 50% du pack).
3. Compléter avec pain-led / proof-led tracés sur les verbatims psychographic.
4. Attacher à chaque cellule la `style_ref` pertinente (si dispo) pour conditionner GPT Image 2.

---

## 5. Exemple travaillé (studease — orientation scolaire)

Extrait `data.csv` :
- Diplomeo → `recherche de formation simplifiée` (marketplace)
- Study Advisor → `retours d'experience etudiants` (preuve sociale peer)
- Acadomia → `bilan d'orientation personnalise` (premium institutionnel)

**Mining** :
- `top_angles` : « simplifier la recherche », « preuve sociale étudiante », « expertise/bilan » → **dominants**.
- `saturated` : « bilan personnalisé » + « expert orientation » (institutionnel, déjà pris par Acadomia & co).
- `white_spaces` : **personne ne parle de l'angoisse parent×ado**, ni du **coût d'une mauvaise orientation** (année perdue = ~10k€). Terrain libre.
- `style_refs` : si captures dispo, garder l'exécution la plus claire comme inspiration de composition.

**Angles V2 retenus** (white-space first) :
1. *Coût d'une réorientation ratée* (white space) — style S7 data-viz / S12 documentary
2. *Angoisse parent : « et s'il se trompe de voie ? »* (white space, verbatim psy) — style S4 human / S3 lifestyle
3. *Anti-marketplace : « pas un annuaire de plus »* (common-enemy vs Diplomeo) — style S10 brutalist
→ Aucun ne recopie un concurrent ; tous tracent sur un verbatim ou un white space.

---

## 6. Checklist inspiration concurrentielle
- [ ] `competitor_mine.py` a tourné → `competitor-insights.json` existe ?
- [ ] Aucun angle du pack ∈ `saturated` (sauf twist explicite) ?
- [ ] ≥ 50% des angles ∈ `white_spaces` ?
- [ ] `style_refs` passées en STYLE only (pas de copy/logo concurrent repris) ?
- [ ] Chaque hook client tracé `[V][W][P][C]` indépendamment du concurrent ?
