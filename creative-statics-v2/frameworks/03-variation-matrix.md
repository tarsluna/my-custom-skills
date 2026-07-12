# Framework 03 — Variation Matrix

Le cœur de la V2 : ne pas produire 30 variantes du même visuel, mais une **matrice testable**. Chaque créative est un point dans un espace à 5 dimensions, et chaque cellule **isole une variable de test**.

---

## 1. Les 5 dimensions

| Dim | Valeurs possibles | Source |
|---|---|---|
| **angle** | pain-led · proof-led · comparison · transparency · scarcity · common-enemy · before-after · manifesto · lead-magnet · social-proof · authority · transformation | copy pack + `white_spaces` (framework 02) |
| **awareness** | 2 (problem) · 3 (solution) · 4 (product) | Schwartz, copy framework V1 |
| **format** | feed-4x5 · story-9x16 · feed-1x1 | Meta specs |
| **design_style** | S1…S12 | framework 01 |
| **test_variable** | hook · visual_style · cta · color_archetype · format · proof_element | ce framework §3 |

Une **cellule** = une combinaison concrète : `{angle, awareness, format, design_style, test_variable, copy{hook,sub,body,cta}, prompt}`.

---

## 2. Composition par défaut d'un pack lead gen (≈ 24-30 créatives)

```
6-8 angles  ×  ~3 styles design / angle  ×  formats répartis
```

Répartition format recommandée (lead gen Meta) :
- **Feed 4:5 — 60%** (format #1, meilleur coût/lead historique)
- **Story 9:16 — 25%** (reach, retargeting)
- **Carousel 1:1 — 15%** (éducatif, multi-proof)

Répartition angle recommandée :
- **≥ 50% white-spaces** (différenciation — framework 02)
- **~30% pain-led** (tracés verbatims psychographic)
- **~20% proof-led / authority** (chiffres sourçables, fondateur)
- **0% angle saturé** sans twist common-enemy explicite

Répartition style (diversité) : couvrir **≥ 6 styles distincts** sur le pack, choisis selon l'`accent_archetype` du client (table framework 01 §3).

---

## 3. La variable de test (1 par cellule)

Pour qu'un test soit lisible côté Meta, **une seule chose change** entre deux variantes comparées :

| test_variable | Ce qui change, le reste constant | Question business |
|---|---|---|
| `hook` | même visuel/style, hook A vs B | quelle accroche stoppe le scroll ? |
| `visual_style` | même copy, style S2 vs S9 | quel univers visuel performe ? |
| `cta` | même créative, CTA « Réserver » vs « Voir si éligible » | quelle friction CTA convertit ? |
| `color_archetype` | même layout, palette Confiance vs Énergie | quel registre émotionnel ? |
| `format` | même concept en 4:5 vs 9:16 | quel placement coûte le moins/lead ? |
| `proof_element` | avec chiffre vs avec témoignage | quelle preuve crédibilise ? |

→ Le pack doit contenir **au moins une paire de test propre par variable** pour donner au client une roadmap d'itération claire.

---

## 4. Schéma JSON d'une cellule (`variation-matrix.json`)

```json
{
  "id": "A1-coutreorientation-feed-dataviz",
  "angle": "transformation",
  "angle_source": "white_space:cout-reorientation-ratee",
  "awareness": 2,
  "format": "feed-4x5",
  "design_style": "S7",
  "test_variable": "proof_element",
  "copy": {
    "hook": "Une année ratée coûte 10 000 €.",
    "sub": "Une mauvaise orientation aussi.",
    "body": "On t'aide à choisir avant, pas à réparer après.",
    "cta": "Faire le point",
    "trace": { "hook": "[W]cout-reorientation [P]cout-annee-prepa", "cta": "[C]controle" }
  },
  "style_ref": "02-competitor-ads/creatives/ref-clean-02.png",
  "brand_assets": ["assets/logo.png"],
  "prompt": "<master-prompt GPT Image 2 généré depuis art-direction-prompt.template.md>",
  "render": { "resolution": "2k", "aspect_ratio": "4:5" },
  "status": "pending"
}
```

`status` : `pending` → `generated` → `council_pass` / `council_fail` → `locked` (après brand-lock) → `selected` (curation finale).

---

## 5. Algorithme de construction (Phase C)

```
1. insights = load(competitor-insights.json)        # framework 02
2. angles = pick_angles(                              # ≥50% white_spaces, 0 saturated
       white_spaces=insights.white_spaces,
       pains=psychographic.verbatims,
       proofs=copy_pack.sourced_numbers)
3. pour chaque angle:
     styles = recommend_styles(angle, client.accent_archetype)   # framework 01 §3
     choisir 2-3 styles distincts
     pour chaque style:
         format = balance_formats(target_ratio=60/25/15)
         test_variable = assign_test(angle, style)     # garantir ≥1 paire/variable
         copy = write_copy(angle, awareness, voice)     # 6-checks + trace
         cell = build_cell(...)
4. valider: distribution format ✓, ≥6 styles ✓, ≥1 paire de test/variable ✓
5. dump variation-matrix.json
```

---

## 6. Garde-fous matrice
- [ ] Distribution format ≈ 60/25/15 (±10%) ?
- [ ] ≥ 6 styles design distincts sur le pack ?
- [ ] ≥ 50% des angles ∈ white_spaces ?
- [ ] 0 angle saturé sans twist explicite ?
- [ ] ≥ 1 paire de test propre par `test_variable` utilisée ?
- [ ] Chaque cellule a un `prompt` complet (7 blocs — framework 01) ?
- [ ] Chaque copy tracée `[V][W][P][C]` + 6-checks ?
- [ ] Pas plus de variations que ce qu'on curera (qualité > volume) ?

---

## 7. Anti-pattern à éviter
- ❌ 30 créatives = 30 hooks différents sur **le même** visuel → ce n'est pas un test de style, c'est un test de hook déguisé en pack.
- ❌ Changer hook **ET** style **ET** format entre deux variantes → test illisible, on ne sait pas ce qui a fait bouger le CPL.
- ❌ Générer 60 cellules « au cas où » → coût GPT Image 2 + Council noyé. Viser 24-30, curer à la fin.
- ✅ Matrice équilibrée, chaque cellule justifiée par un angle tracé + un style adapté + une variable de test claire.
