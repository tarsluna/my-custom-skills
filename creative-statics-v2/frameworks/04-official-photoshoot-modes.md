# Framework 04 — Official Higgsfield Photoshoot Modes (ported)

Porté de **`github.com/higgsfield-ai/skills`** → `higgsfield-product-photoshoot` (MIT,
© 2026 Higgsfield AI — voir `NOTICE.md`). C'est le moteur de génération **préféré** de
la V2 : il garde l'**enhancer de prompt côté serveur**.

---

## ⚠️ Règle d'or : NE PAS bypasser l'enhancer

> `higgsfield product-photoshoot create --mode <mode>` appelle un **enhancer serveur**
> qui détient le vocabulaire photographique par mode, puis soumet à `gpt_image_2`.
> Appeler `higgsfield generate create gpt_image_2 --prompt …` (ou notre SDK brut
> `gpt_image2_generate.py`) **bypasse l'enhancer et produit un résultat nettement moins bon.**

Conséquence pour la V2 :
- **Engine `cli` (défaut, qualité max)** : on passe un **prompt d'intention COURT** + le `mode` + les images de référence. Le backend assemble le prompt complet. → `scripts/photoshoot_cli.py`
- **Engine `sdk` (contrôle total / fallback)** : on passe notre **prompt 7-blocs complet** (framework 01) à `gpt_image_2` en direct. À réserver aux cas où l'enhancer ne donne pas le contrôle voulu, ou si la CLI n'est pas installée. → `scripts/gpt_image2_generate.py`

En `cli`, le champ `prompt` (7-blocs) de la cellule n'est PAS envoyé tel quel — on envoie `intent` (court). Le 7-blocs reste utile comme documentation d'art-direction et pour l'engine `sdk`.

---

## Les 10 modes officiels

| Mode | Quand l'utiliser | Aspect ratio défaut |
|---|---|---|
| `product_shot` | produit sur fond neutre / studio / catalogue (Shopify) | backend |
| `lifestyle_scene` | produit en situation réelle, mains, action, ambiance | backend |
| `closeup_product_with_person` | crop serré mains/visage partiel — application beauté, démonstration | backend |
| `moodboard_pin` | pin Pinterest vertical 2:3, feel moodboard | 2:3 |
| `hero_banner` | header site / email / campagne, format large | 16:9 / wide |
| `social_carousel` | 3–10 slides connectées IG/LinkedIn/FB | count = nb slides |
| **`ad_creative_pack`** | **pack coordonné de statics Meta/TikTok/Pinterest/Google** | count = nb variantes |
| `virtual_model_tryout` | produit porté/utilisé par un mannequin IA | backend |
| `conceptual_product` | surréaliste / CGI / lévitation / splash / sculptural | backend |
| `restyle` | transformer l'esthétique/saison d'une image existante | hérite source |

Pour `ad_creative_pack` et `social_carousel`, `--count` = nombre de variantes/slides ; **le backend verrouille le système visuel** sur tout le pack (cohérence garantie).

---

## Mapping : nos 12 styles design (framework 01) → mode officiel

| Style V2 | Mode officiel | Note |
|---|---|---|
| S1 Editorial Typographic | `ad_creative_pack` / `hero_banner` | ou rester PIL V1 si typo pure |
| S2 Photoreal Product Hero | `product_shot` | + brand asset produit en `--image` |
| S3 Lifestyle / UGC | `lifestyle_scene` | |
| S4 Human / Founder | `closeup_product_with_person` / `virtual_model_tryout` | ou **Soul ID + `text2image_soul_v2`** si visage récurrent |
| S5 Bold 3D / CGI | `conceptual_product` | |
| S6 Magazine Collage | `moodboard_pin` / `ad_creative_pack` | |
| S7 Data-Viz / Chart | `hero_banner` | souvent meilleur en **V1 PIL** (précision) |
| S8 Diptych Before/After | `ad_creative_pack` | |
| S9 Minimalist Luxury | `product_shot` / `moodboard_pin` | |
| S10 Brutalist Statement | `ad_creative_pack` / `hero_banner` | |
| S11 Soft Gradient / Aura | `hero_banner` | |
| S12 Documentary / Real-Object | `lifestyle_scene` / `product_shot` | |

Chaque cellule de `variation-matrix.json` porte donc un champ **`mode`** (officiel) +
**`intent`** (prompt court pour l'enhancer). Le `design_style` reste pour l'art-direction
humaine et l'engine `sdk`.

---

## Le prompt d'intention (`intent`) — court, pas le 7-blocs

L'enhancer attend une **description d'intention courte** (ce que veut l'utilisateur),
pas le prompt technique. Bonnes pratiques (de la SKILL officielle) :

- Décrire **produit + contexte + usage** : *"bottle of cold-brew on a sunlit kitchen counter, IG feed"*
- Ajouter l'**offre / hook / mood** si pertinent : *"premium DTC ad, 'réveille-toi vraiment' hook"*
- Laisser l'enhancer gérer lumière/preset/angle (ne pas sur-spécifier).
- Le **texte incrusté** (hook/CTA) : GPT Image 2 le rend bien (catalogue : *"any brief with on-image text"*). Pour un rendu charte-exact → `brand_lock_pass.py` par-dessus.

> Garder la voix/copy 100% client (6-checks, traçabilité) — l'`intent` cite le hook
> client validé, jamais un hook concurrent.

---

## Soul ID (visage récurrent) — `scripts/soul_id.py`

Pour un spokesperson/fondateur récurrent (S4) :
1. `python scripts/soul_id.py create --name founder --soul-2 --image r1.jpg --image r2.jpg …` (5–20 photos approuvées, plan Basic+)
2. Stocker le `reference_id` dans `client-brand-profile.json → render.soul_id`
3. Générer ces cellules via Soul : `higgsfield generate create text2image_soul_v2 --prompt "…" --soul-id <id> --quality 2k --wait` (≈ 0.12 cr/image — bien moins cher que GPT Image 2)

---

## Bootstrap CLI (une fois)
```bash
curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh
higgsfield auth login         # interactif — à lancer par G
higgsfield account status     # vérifie plan + auth
python scripts/photoshoot_cli.py --check   # health check côté pipeline
```
