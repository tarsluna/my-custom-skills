---
name: creative-statics-v2
description: V2 ultra-boostée du pipeline de créatives statiques Meta Ads pour ton offre. Génère des variations de créatives statiques haute qualité avec GPT Image 2 (via Higgsfield Cloud) comme moteur de rendu natif — la créative complète (visuel + texte incrusté) est rendue par l'IA, pilotée par une art-direction dérivée du design system verrouillé, conditionnée sur le branding du client (palette, fonts, logo, ton) ET sur les meilleures ads concurrentes du fichier 02-competitor-ads/data.csv. Produit une matrice de variations (angles × formats × styles design × variables de test) avec copywriting validé 6-checks, passe Council 4 seats, et passe optionnelle PIL de brand-lock (logo/CTA/contraste pixel-perfect). Trigger phrases : "créatives statiques V2", "créatives GPT Image 2", "variations créatives client", "pack ads ultra qualitatif", "créatives boostées {client}", "génère des variations statiques", "ads concurrents inspiration créative". NE supprime PAS creative-statics (V1 reste l'option FLUX+PIL typographique pure).
---

# Creative Statics **V2** (GPT Image 2 native)

Version ultra-boostée du pipeline de créatives statiques. Là où la **V1** (`creative-statics`) dessine la typo en PIL sur des fonds FLUX, la **V2** fait rendre **la créative complète par GPT Image 2** (visuel + texte incrusté + composition), pilotée par une art-direction issue du design system verrouillé et **conditionnée sur le branding réel du client + les meilleures ads concurrentes**.

> **La V1 n'est pas supprimée.** Choisis :
> - **V1** = créatives éditoriales typographiques pures, brand-lock pixel-perfect, déterministe. Idéale quand la typo EST le visuel (manifesto, hero chiffre, citation).
> - **V2** = créatives photo-réalistes / lifestyle / produit / collage avec texte rendu par l'IA, adaptées au branding client, diversité visuelle maximale. Idéale pour de la lead gen multi-angles à grande échelle.
> En pratique : **un pack mixe les deux** (cf. § Architecture cible).

**Input** : un client avec les 4 livrables amont + un `client-brand-profile.json` rempli.
**Output** : un dossier `creatives-v2/` avec une **matrice de variations** (angles × formats × styles), package zip, et logs traçables.

---

## 🚨 RÈGLES DURABLES (apprentissages live — à respecter SUR CHAQUE CRÉA)

Ces règles sont nées de feedback réel sur des packs livrés. Elles s'appliquent **AVANT toute génération** :

### Règle 1 — Edge-to-edge OBLIGATOIRE (zéro bordure blanche)
La créa doit **remplir 100% du cadre 4:5**. Le logo client se place EN OVERLAY sur la scène (top-left, badge subtil ou directement sur image), le CTA en OVERLAY (pas dans un bandeau réservé). **Jamais** de bande blanche en haut pour le logo ni en bas pour le CTA — Meta affiche déjà son propre chrome, on perd 20-30% de surface pertinente si on ajoute des marges blanches.

→ **Prompt directive** : `"Edge-to-edge composition, image fills the full frame, NO white margins, NO white header bar, NO white footer bar. Logo and CTA are overlays ON the visual content."`

### Règle 2 — CTA en MAJUSCULES + aligné avec la colonne copy
Le CTA (quel qu'il soit) doit être :
- **En MAJUSCULES** (`AUDIT GRATUIT`, pas `Audit gratuit`) — plus punchy, plus pro, plus lisible thumbnail
- **Aligné verticalement avec le headline et la subline** dans la même colonne (gauche, centre ou droite) — pas en bas-droite isolé quand le headline est en haut-gauche. Le viewer doit faire UN SEUL scan vertical.

→ **Prompt directive** : `"CTA button label in ALL CAPS (e.g. «AUDIT GRATUIT»). Place the CTA directly below the headline+subline in the same vertical column. Same horizontal alignment as the headline."`

### Règle 3 — Phase A bis : scrape OBLIGATOIRE du site client AVANT brand profile
Avant de remplir `client-brand-profile.json`, on **doit** récupérer du site officiel du client :
- **Palette exacte** (extraire les hex via curl + grep `#[0-9a-fA-F]{6}` + CSS vars)
- **Fonts** chargées (extraire `font-family` + liens Google Fonts/CDN dans le HTML)
- **Ton de la communication** (hero hook, taglines, headlines)
- **Style visuel dominant** (dark/light, gradient, illustration vs photo, density)
- **Logo** (URL `/logo.png` ou `og:image`)

Sans ça, la créa parle un langage générique au lieu du langage de la marque.

→ **Bash directive** (à exécuter avant Phase B) :
```bash
SITE_URL="https://<client-domain>"
HTML=$(curl -sL "$SITE_URL" -A "Mozilla/5.0")
echo "$HTML" | grep -oE "#[0-9a-fA-F]{6}" | sort -u    # palette
echo "$HTML" | grep -oE 'font-family:[^;]+' | sort -u  # fonts
echo "$HTML" | grep -oE 'href="[^"]*\.css[^"]*"'       # CSS files (pour deep-dive)
echo "$HTML" | python3 -c "import sys, re; print(re.findall(r'og:image[^>]+content=\"([^\"]+)\"', sys.stdin.read())[:3])"
echo "$HTML" | grep -oE '<title>[^<]+</title>'         # titre
```

Persiste tout ça dans `client-brand-profile.json → _site_scrape` ET utilise les vrais hex/fonts dans le bloc `palette` + `fonts` du profile, jamais des valeurs inventées par défaut.

> ⚠️ **Cas rebrand / site introuvable** : si le client a changé de nom (ancien nom dans la base, nouveau nom à utiliser), chercher le **nouveau** site (WebSearch "nouveau-nom + secteur", vérifier SIREN/activité cohérente). Scraper le nouveau site. **Ne JAMAIS mentionner l'ancien nom** dans aucun livrable (créatives ET docs). Vérifier en fin de run : `grep -rli "ancien-nom" <dossier-livraison>` doit renvoyer 0. (Cas déjà rencontré sur un client en rebrand.) Si le slug client est ambigu (homonymes), demander confirmation au lieu de deviner.

### Règle 4 — Moteur de génération RÉEL = CLI HiggsField `higgsfield generate create`
La méthode qui marche en prod (validée sur plusieurs packs clients réels) est la **CLI officielle** `higgsfield` (brew), PAS les scripts `build_variations.py`/`photoshoot_cli.py` (legacy). Auth : `higgsfield auth login` (token expire → re-login si "Not authenticated"). Modèles : `higgsfield model list`.

```bash
higgsfield generate create <model> --prompt "<prompt>" --aspect_ratio "4:5" --resolution "2k" --json
# avec --wait pour bloquer jusqu'à complétion (≈175s/image isolée), sinon poll via generate get/list
higgsfield generate cost <model> --prompt x --aspect_ratio 4:5 --resolution 2k   # AVANT tout batch
```

### Règle 5 — Choix du modèle + coûts (vérifier `generate cost` avant batch)
| Modèle (slug) | Coût 2k | Notes |
|---|---|---|
| `gpt_image_2` (GPT Image 2) high | **7 crédits** (CHER) | pas de ratio 4:5 (3:4/1:1/9:16/16:9 only) |
| `nano_banana_2` (Nano Banana Pro) | **2 crédits** | ⭐ DÉFAUT : 4:5 natif + excellent texte FR + premium |
| `nano_banana` (flash) | 1 crédit | qualité moindre |
**Recommandation** : `nano_banana_2` par défaut (rapport qualité/prix/format imbattable). GPT Image 2 high seulement si budget large et demande explicite. **Toujours annoncer le coût estimé** (nb cellules × coût) avant de lancer.

### Règle 6 — Limite de concurrence `concurrent_jobs_limit: 8`
Le compte a une limite de **8 jobs simultanés**. Lancer 40+ `generate create` en parallèle → erreur `upgrade_plan` et batch perdu. **Utiliser `gen_pool.py`** (fenêtre glissante `max_concurrent: 6`, pool à workers) — c'est le script de prod fiable :
```bash
python3 ~/skills/projects/clients/_creative-batch/gen_pool.py <plan>.json
# plan.json = {"model":"nano_banana_2","max_concurrent":6,"resolution":"2k","log":"...","items":[{"id","aspect","prompt","outdir"}]}
```

### Règle 7 — Parsing JSON : 2 formats selon le modèle + récupération
`generate create --json` renvoie un format DIFFÉRENT selon le modèle : `gpt_image_2` → `{"id":"uuid"}`, `nano_banana_2` → `["uuid"]`. **Parser avec une regex UUID générique**, pas `"id":`. ⚠️ **Le job se crée et débite les crédits même si le parsing client échoue.** En cas d'échec apparent, NE PAS relancer (double facturation) : récupérer les jobs via `higgsfield generate list --size 40 --json` (les `completed` ont `result_url`) et matcher par prompt. (Bug vécu : ~38 crédits "perdus" récupérés ainsi.)

### Règle 8 — Livraison : N sélectionnées + dossier `non-choisies/`
Générer ~20 cellules/client, **auditer chaque créative visuellement** (Read le PNG : valeur prop claire en 1 coup d'œil ? format edge-to-edge ? CTA majuscules aligné colonne ? texte FR net ? DA respectée ?). Garder les **15 meilleures** (équilibre angles × formats × styles) à la racine, déplacer le reste dans **`non-choisies/`** (ressources bonus pour le client). Les créatives avec défaut texte IA (lettre parasite, accents criants) → régénérer (le prompt est bon, c'est aléatoire) ; si non régénérable → `_a-regenerer/`. Varier les **formats** (4:5, 1:1, 9:16, 16:9) ET les **styles** (photo doc, typo éditoriale, dataviz, citation, infographie, split, mockup).

---

## 🎯 Quand utiliser V2 plutôt que V1

| Situation | Skill |
|---|---|
| Le client veut du **photoréalisme**, du lifestyle, du produit-en-contexte, de l'humain | **V2** |
| Besoin de **diversité visuelle** maximale (10 styles design différents dans un pack) | **V2** |
| Le client a un **branding fort** (palette, mascotte, produit photographiable) à respecter | **V2** |
| Texte court à incruster (hook + CTA), GPT Image 2 le rend bien | **V2** |
| Créative **100% typographique éditoriale**, contraste AAA garanti, fonts exactes obligatoires | **V1** |
| Chiffre hero massif, manifesto texte pur, citation, comparison-chart précis | **V1** |
| Reproductibilité pixel-perfect exigée (légal, charte stricte) | **V1** (ou V2 + brand-lock pass) |

Trigger V2 sur : « créatives statiques V2 », « variations GPT Image 2 », « pack ultra qualitatif {client} », « génère des variations créatives », « inspire-toi des ads concurrentes pour les visuels ».

NE PAS trigger pour : une seule créative ad-hoc (→ `scripts/gpt_image2_generate.py` direct), réécrire du copy sans visuel (→ `meta-ads-copywriter`).

---

## 📥 Dépendances amont obligatoires

Mêmes 4 livrables que la V1, **plus** un profil de marque structuré :

| # | Producteur | Output consommé par V2 |
|---|---|---|
| 1 | le brief d'onboarding client | `00-onboarding/onboarding-form.md` — ICP, verbatims, ticket, ton, do/don't, **brand assets** |
| 2 | `deep-search` | `01-deep-search/{01-market-awareness,02-competitor-research,03-psychographic}.md` |
| 3 | `competitor-ads-research` | **`02-competitor-ads/data.csv`** (colonnes : `competitor, category, observed_status, primary_angle, secondary_angle, likely_audience, sample_hook, inference_confidence, notes`) + `analysis.md` (white spaces) + `creatives/` (captures d'ads si présentes) |
| 4 | `meta-ads-copywriter` | `05-meta-ads/ads-multi-variantes.md` — hooks, primary text, headlines, CTAs |
| 5 | **CE SKILL (Phase A)** | `client-brand-profile.json` rempli depuis `templates/client-brand-profile.template.json` |

Si `data.csv` ou un livrable manque → **STOP**, demander de lancer le skill manquant. Le `data.csv` est le carburant de l'**inspiration concurrentielle** (cf. `frameworks/02-competitor-inspiration-engine.md`).

---

## 🧠 Principe directeur V2 — les 3 lois

1. **L'IA rend la créative, le design system la dirige.** GPT Image 2 ne reçoit jamais « fais une belle ad ». Il reçoit une **art-direction structurée** (palette hex exacte, archétype layout, hiérarchie typo, safe zones, directive qualité) dérivée de `frameworks/01-art-direction-system.md`. Garbage prompt = garbage image.

2. **On s'inspire des concurrents, on ne les copie pas.** Le `data.csv` + les captures `creatives/` servent à (a) identifier les **angles saturés à éviter**, (b) extraire les **white spaces** non travaillés, (c) donner à GPT Image 2 une ad concurrente forte comme **référence de STYLE** (jamais de copy). La copy reste 100% client, validée 6-checks. Voir `frameworks/02-competitor-inspiration-engine.md`.

3. **Diversité testable > volume.** Le pack n'est pas 30 variantes du même visuel. C'est une **matrice** : N angles × M formats × K styles design, chaque cellule isolant **une variable de test**. Voir `frameworks/03-variation-matrix.md`.

---

## 🎨 Moteur de rendu — GPT Image 2 via Higgsfield (2 engines)

Le client a choisi **GPT Image 2** (modèle OpenAI, excellent en rendu de texte/instructions). Deux façons de l'appeler — la première est **préférée** :

### ⭐ Engine `cli` (défaut, qualité max) — `scripts/photoshoot_cli.py`
Pilote la **CLI officielle** `higgsfield product-photoshoot create --mode <mode>`, qui appelle un **enhancer de prompt côté serveur** (vocabulaire photo par mode) puis soumet à `gpt_image_2`. C'est le moteur du skill officiel `higgsfield-product-photoshoot` (porté ici, MIT — cf. `frameworks/04` + `NOTICE.md`).

> ⚠️ **Règle d'or** : appeler `gpt_image_2` en direct **bypasse l'enhancer et dégrade nettement la qualité**. → En `cli`, on envoie un **prompt d'intention COURT** + le `mode` + images de réf ; le backend assemble le prompt complet.

### Engine `sdk` (contrôle total / fallback) — `scripts/gpt_image2_generate.py`
Appelle `gpt_image_2` en direct via le SDK Cloud avec notre **prompt 7-blocs complet** (framework 01). À réserver aux cas où l'on veut le contrôle total du prompt, ou si la CLI n'est pas dispo.

`build_variations.py --engine cli|sdk` (défaut `cli`). En `cli`, chaque cellule utilise `mode`+`intent` ; en `sdk`, elle utilise `prompt`.

### Higgsfield Cloud = agrégateur
1 auth → catalogue de modèles (GPT Image 2, Soul V2, FLUX.2, Nano Banana, Seedream…), swappable par cellule.

### Auth (jamais imprimée)
Résolution des credentials dans cet ordre (cf. `frameworks/higgsfield-api` partagé avec higgsfield-ugc) :
`HF_KEY` → `HF_CREDENTIALS` → `XFIELD_KEY` → `HF_API_KEY`+`HF_API_SECRET` → `secrets/api-keys.md`.

### ⚠️ Slug du modèle — À RÉSOUDRE, ne jamais hardcoder à l'aveugle
La CLI officielle expose `gpt_image_2`. Le SDK Cloud utilise des chemins type `provider/model/version/text-to-image`. **Le slug exact de GPT Image 2 sur Higgsfield Cloud doit être confirmé** via le catalogue live AVANT toute génération facturée :

```bash
# Résoudre le slug réel (health check, ne consomme pas de crédits)
python skills/creative-statics-v2/scripts/gpt_image2_generate.py --list-models | grep -i gpt
# ou via la CLI officielle si installée :
higgsfield model list | grep -i gpt
```

Le script `gpt_image2_generate.py` prend `--model-slug` en paramètre et stocke le slug résolu dans `client-brand-profile.json → render.model_slug`. Tant que le slug n'est pas confirmé, **ne lance pas de batch facturé**.

### Capacités exploitées
- **Text-to-image** : créative complète depuis l'art-direction prompt.
- **Reference images** (`--start-image` / `input_images`) : conditionnement sur **brand assets** (logo, produit, photo fondateur) + **1 ad concurrente** comme référence de style.
- **Résolutions** : `1k` / `2k` / `4k`. Défaut pack = `2k` (upscale `4k` pour hero).
- **Aspect ratios** : mappés aux formats Meta (4:5 → `1024x1280`-class, 9:16, 1:1).

### Garde-fou crédits — pricing vérifié (Higgsfield, mai 2026)
Coût **par image** sur Higgsfield Cloud (crédits ; basic plan $5 ⇒ 70 crédits ⇒ 1 crédit ≈ $0.071). Source : higgsfield.ai/pricing (vérifié 3-0 par la recherche).

| Modèle | crédits/image | ≈ $ /image | Note |
|---|---|---|---|
| **GPT Image** *(choix client)* | **1** | **~$0.07** | défaut officiel du skill `higgsfield-product-photoshoot` |
| **Soul 2.0** | **0.12** | **~$0.009** | photoréalisme fashion-grade, **~10× moins cher** (alt cheap) |
| Soul (v1) | 0.25 | ~$0.018 | |
| Seedream / Flux Kontext | 1 / 1.5 | ~$0.07 / $0.11 | |
| FLUX.2 Pro / Flex / Max | 1 / 3 / 4 | ~$0.07 / $0.21 / $0.29 | |
| Nano Banana Pro | 2 | ~$0.14 | meilleur texte-dans-l'image |

Batch type 27 images GPT Image 2 ≈ **27 crédits ≈ ~$1.9**. `build_variations.py --dry-run --cost-per-image 1` imprime l'estimation en crédits.

⚠️ **Crédits toujours consommés en API.** Les tiers « Unlimited » et les générations gratuites sont **réservés au web app** — CLI / SDK / MCP **consomment toujours des crédits** (vérifié). Donc tout batch programmatique = facturé.

**Ne lance jamais un batch facturé sans approbation G** sur : (1) le coût estimé, (2) le slug confirmé, (3) le profil de marque validé.

> 💡 **Optimisation coût** : pour les cellules **photoréalistes pures sans texte** (lifestyle S3, produit S2), envisager **Soul 2.0** (~10× moins cher que GPT Image 2) — le slug est swappable par cellule (`render.model_slug`). Garder **GPT Image 2** pour les cellules qui portent un hook incrusté (meilleur rendu de texte).

---

## 🗂️ Structure du skill

```
creative-statics-v2/
├── SKILL.md                                  ← ce fichier (orchestration V2)
├── README.md  ·  NOTICE.md  ·  LICENSE        ← repo GitHub privé + attribution MIT (port higgsfield-ai/skills)
├── frameworks/
│   ├── 01-art-direction-system.md            ← design system → prompts GPT Image 2 (12 styles design)
│   ├── 02-competitor-inspiration-engine.md   ← mine data.csv + creatives/ → vecteurs d'inspiration
│   ├── 03-variation-matrix.md                ← grille angles × formats × styles × tests
│   ├── 04-official-photoshoot-modes.md       ← modes officiels (porté higgsfield-ai/skills, MIT)
│   └── 05-native-concept-formats.md          ← ⭐ banque de ~14 FORMATS natifs réutilisables (notes iOS, advertorial, iMessage, tweet, UGC selfie, portrait autorité, POV, listicle, mockup produit, témoignage, infographie, dataviz, post natif, pattern-interrupt) — prompts paramétrables, client-agnostic
├── scripts/
│   ├── photoshoot_cli.py                      ← ⭐ ENGINE PRÉFÉRÉ : `higgsfield product-photoshoot` (enhancer serveur)
│   ├── soul_id.py                             ← Soul ID (visage récurrent) — porté MIT
│   ├── gpt_image2_generate.py                ← engine SDK : GPT Image 2 brut (contrôle total / fallback)
│   ├── competitor_mine.py                     ← parse data.csv → angles forts / saturés / white spaces
│   ├── build_variations.py                    ← orchestre la matrice (--engine cli|sdk) → génération
│   ├── brand_lock_pass.py                     ← passe PIL optionnelle (logo/CTA/contraste pixel-perfect)
│   └── audit_heuristic.py                      ← audit sans LLM (dimensions, poids, contraste, safe zone)
├── templates/
│   ├── client-brand-profile.template.json     ← profil de marque (palette, fonts, logo, ton, refs)
│   ├── art-direction-prompt.template.md       ← template du master-prompt GPT Image 2
│   ├── variation-matrix.template.json         ← grille de test à remplir par client
│   └── council-brief-template.md              ← 5 prompts Council (4 V1 + AI-render fidelity)
└── checklists/
    ├── brand-fidelity-gate.md                 ← la créative respecte-t-elle le branding ?
    ├── gpt-image2-prompt-quality.md           ← le prompt est-il assez dirigé ?
    └── visual-quality-gate.md                 ← dimensions, contraste, safe zone, lisibilité texte IA
```

---

## 🔁 Pipeline V2 — 9 phases

```
            AMONT (skills séparés)  →  onboarding · deep-search · competitor-ads(data.csv) · copy pack
                                          │
                                          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ CE SKILL (creative-statics-v2)                                 │
│                                                                            │
│ A. Brand profile      → remplir client-brand-profile.json                  │
│ B. Competitor mining  → competitor_mine.py → top angles / saturés / WS     │
│ C. Variation matrix   → variation-matrix.json (angles×formats×styles×test) │
│ D. Copy par cellule   → hooks/CTA validés 6-checks + traçabilité [V][W][P][C]│
│ E. Art-direction      → 1 master-prompt GPT Image 2 par cellule            │
│ F. Resolve + smoke    → résoudre slug GPT Image 2, 1 image test (approbation)│
│ G. Batch generate     → build_variations.py (GPT Image 2, refs, 2k)        │
│ H. Council 5 seats    → Brand + UX + UI + Copy + AI-render fidelity         │
│ I. Brand-lock + pack  → brand_lock_pass.py (option) + audit + zip Desktop   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Phase A — Brand profile (manuel + Claude, 20 min)
1. Lire `00-onboarding/onboarding-form.md` + tout asset de marque fourni.
2. Remplir `templates/client-brand-profile.template.json` dans le dossier client (`05-meta-ads/client-brand-profile.json`) :
   - `palette` (3-5 hex avec rôles), `fonts` (noms + fallback), `logo` (chemin + zone de pose), `tone`, `do`, `dont`
   - `brand_assets` : chemins/URLs des images de référence (produit, logo, fondateur, ambiance)
   - `render` : `model_slug` (vide tant que non résolu), `default_resolution`, `aspect_map`
   - `accent_archetype` : Confiance / Urgence / Énergie / Authority / Luxe
3. **Si pas de brand assets photographiables** → GPT Image 2 génère tout (lifestyle/abstrait on-brand). Si assets dispo → conditionner dessus (cohérence produit/visage).

### Phase B — Competitor mining (auto, 5 min)
```bash
python scripts/competitor_mine.py --client <slug>
```
Parse `02-competitor-ads/data.csv` → produit `competitor-insights.json` :
- **top_angles** (les `primary_angle`/`secondary_angle` les plus fréquents + leurs `sample_hook`)
- **saturated** (angles présents chez ≥ N concurrents → à éviter ou attaquer frontalement)
- **white_spaces** (catégories absentes du CSV mais pertinentes pour l'ICP — croisé avec `analysis.md`)
- **style_refs** (si `creatives/` contient des captures : les 2-3 meilleures retenues comme **référence de STYLE** pour GPT Image 2)

### Phase C — Variation matrix (Claude, 15 min)
Construire `variation-matrix.json` depuis `templates/variation-matrix.template.json`. Cf. `frameworks/03-variation-matrix.md`. Objectif : **un pack équilibré et testable**, pas du volume. Défaut lead gen :
- **6-8 angles** (mix white-spaces + pain-led + proof-led), jamais d'angle saturé sans twist
- **3 formats** (Feed 4:5 prioritaire 60%, Story 9:16 25%, Carousel 1:1 15%)
- **par angle, 2-3 styles design** parmi les 12 (cf. `frameworks/01`)
- **DIVERSITÉ DE FORMAT/CONCEPT (anti-homogénéité) : piocher 8-12 concepts DISTINCTS dans `frameworks/05-native-concept-formats.md`** (notes iOS, advertorial, iMessage, tweet, UGC selfie, portrait autorité, POV, listicle, mockup produit, témoignage, infographie, dataviz, post natif, pattern-interrupt). ⚠️ Ne jamais livrer 12 variations du même style éditorial — c'est l'erreur n°1. Les formats natifs surperforment souvent le « beau branding » sur Meta.
- chaque variation isole **une `test_variable`** (`hook` | `visual_style` | `concept_format` | `cta` | `color_archetype` | `format` | `proof_element`)

### Phase D — Copy par cellule (Claude, 20 min)
Pour chaque cellule : hook + sub + body + CTA, validés par les **6 checks** (`checklists/...` hérité V1) et tracés `[V][W][P][C]`. Pas d'angle saturé, pas d'agency-mismatch, voix client. Cf. framework copy V1 (réutilisé tel quel — `../creative-statics/frameworks/03-copywriting-framework.md`).

### Phase E — Art-direction (Claude, 20 min)
Pour chaque cellule, produire **un master-prompt GPT Image 2** depuis `templates/art-direction-prompt.template.md`, qui encode : palette hex, archétype de style, hiérarchie typo, **texte exact à incruster** (hook court + CTA), format/safe zones, référence(s) de style, directives qualité. Le prompt vit dans la matrice (`variation-matrix.json → cells[].prompt`).

### Phase F — Bootstrap + smoke test (auto, 5 min)
1. **Engine cli (défaut)** : `python scripts/photoshoot_cli.py --check` (CLI installée + auth + plan). Si absente : `curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh` puis demander à G `higgsfield auth login`. **Engine sdk** : résoudre le slug (`gpt_image2_generate.py --list-models`).
2. Générer **1 seule image test** sur l'angle le plus fort. La lire (Read), vérifier brand-fidelity + lisibilité texte IA.
3. **STOP POINT** : montrer l'image + coût estimé (`build_variations.py --dry-run`) à G → approbation avant Phase G.

### Phase G — Batch generate (auto, 20-40 min selon volume)
```bash
# défaut : engine cli (enhancer serveur officiel, qualité max)
python scripts/build_variations.py --client <slug> --matrix variation-matrix.json
# contrôle total du prompt 7-blocs : engine sdk
python scripts/build_variations.py --client <slug> --matrix variation-matrix.json --engine sdk
```
Génère chaque cellule (refs incluses), download dans `creatives-v2/raw/`, logs append-only. Try/except par cellule (1 crash ≠ batch perdu). Cache par hash (évite refacturation). `ad_creative_pack`/`social_carousel` : `count` = nb variantes, le backend verrouille le système visuel.

### Phase H — Council 5 seats (sous-agents Claude, parallèle)
Lancer **5 agents EN PARALLÈLE** (`templates/council-brief-template.md`) :
1. **Brand Guardian** — alignement palette/ton/do-dont, le visuel ressemble-t-il au client ?
2. **UX Researcher** — thumbstop, clarté, friction CTA
3. **UI Designer** — hiérarchie, contraste AA/AAA, composition, safe zones
4. **Copywriter** — agency check, traçabilité `[V][W][P][C]`, jargon, voix
5. **AI-Render Fidelity** *(nouveau V2)* — artefacts IA (mains/texte déformé/logo halluciné), lisibilité du texte rendu par GPT Image 2, cohérence produit vs brand asset, uncanny valley
Chaque seat ouvre les PNG (Read), score /10, 3 recommandations chiffrées → `creatives-v2/_council/0{1..5}-{seat}.md`.
**STOP POINT** : synthèse `_strategy-v2.md` avant régénération des cellules flaggées.

### Phase I — Brand-lock + packaging (auto, 10 min)
1. **(option) Brand-lock pass** : `brand_lock_pass.py` ré-incruste en PIL le **logo exact + CTA pill + mentions légales** par-dessus la sortie GPT Image 2 quand le texte IA n'est pas assez net / la charte exige une font exacte. C'est le pont V2↔V1.
2. `audit_heuristic.py` : dimensions Meta, poids, contraste, safe zone.
3. Package : `~/Desktop/{ClientName}-Ads-V2-Pack-YYYYMMDD.zip` (PNG par angle/format/style + `_strategy-v2.md` + matrice + copy source + insights concurrents).

---

## 🆚 Ce que V2 apporte vs V1 (récap des recommandations intégrées)

| Reco issue de la recherche | Intégration V2 |
|---|---|
| **GPT Image 2** texte-dans-l'image (faiblesse #1 de FLUX schnell) | Moteur de rendu natif — hook + CTA incrustés par l'IA |
| Conditionnement **brand assets** (produit/logo/visage cohérents) | `start-image` / `input_images` depuis `brand_assets` |
| **Référence de style concurrente** (s'inspirer du meilleur) | `competitor_mine.py` → `style_refs` injectées dans le prompt (style only, jamais copy) |
| **Diversité visuelle** (12 styles design) | `frameworks/01` + matrice : 2-3 styles/angle |
| **Adaptation branding client** (palette/fonts/ton) | `client-brand-profile.json` → art-direction prompt |
| **Variations testables** (angles/formats/tests) | `frameworks/03` variation matrix, 1 test_variable/cellule |
| **Higgsfield = agrégateur** (1 auth, multi-modèles) | Slug configurable → swap GPT Image 2 ↔ Soul V2 ↔ Seedream ↔ Nano Banana sans réécrire la pipeline |
| **Identité cohérente sur le pack** (Soul ID) | Hook prévu : si spokesperson récurrent → Soul ID (cf. `frameworks/01` § identité) |
| Garder le **brand-lock pixel-perfect** (force de V1) | `brand_lock_pass.py` PIL optionnel par-dessus l'IA |
| **Upscale** hero | `--resolution 4k` sur les variations gagnantes |

---

## 🛡️ Garde-fous obligatoires

| Garde-fou | Enforcement |
|---|---|
| **Slug GPT Image 2 confirmé** avant batch facturé | `--list-models` + champ `render.model_slug` rempli |
| **Smoke test 1 image** + approbation G avant batch | Phase F STOP POINT |
| **Coût estimé annoncé** avant batch | `build_variations.py --dry-run` imprime crédits estimés |
| Dimensions Meta exactes (1080×{1080,1350,1920}) | `audit_heuristic.py` FAIL si ≠ |
| **Référence concurrente = STYLE only** | `competitor_mine.py` n'extrait jamais le copy concurrent dans la copy client |
| Copy 6-checks + traçabilité | Phase D, hérité V1 |
| **Aucun secret imprimé** (HF_KEY, etc.) | Script print « clé configurée ✅ » sans valeur |
| Artefacts IA (texte/mains/logo) | Council seat #5 AI-Render Fidelity |
| Cache par hash de prompt | `build_variations.py` évite refacturation |
| Try/except par cellule | 1 crash ≠ batch abandonné |
| Logs append-only | `creatives-v2/logs/*.log` |

### Sécurité
- `HF_KEY` **jamais en clair** dans un script versionné. Lire depuis env ou Keychain :
  ```sh
  security add-generic-password -a "$USER" -s "HF_KEY" -w "key_id:key_secret"
  export HF_KEY=$(security find-generic-password -a "$USER" -s "HF_KEY" -w)
  ```
- Ne jamais renvoyer la clé dans un chat (Telegram/Discord) — « clé configurée ✅ ».

---

## 📊 Ce qui reste manuel (jugement humain)
1. **Council audits** — 5 sous-agents, pas un auto-score.
2. **Rédaction `_strategy-v2.md`** — quels angles/styles on pousse, lesquels on kill.
3. **Curation finale** — sélectionner les meilleures variations, pas tout générer.
4. **Validation brand-fidelity** — l'œil humain tranche l'uncanny valley.
5. **Approbation coût** — toujours avant un batch facturé.

---

## 🔗 Héritage & références
- **V1** : `../creative-statics/` — design system (`frameworks/02`), copy framework (`frameworks/03`), checklists 6-points. **V2 réutilise le copy framework tel quel** et **adapte** le design system en art-direction (`frameworks/01-art-direction-system.md`).
- **API Higgsfield** : `../../higgsfield-ugc/references/higgsfield-api.md` (auth, SDK Python/JS, lifecycle). V2 `subscribe()` recommandé (V1 `generate()` déprécié). Auth `Authorization: Key KEY_ID:KEY_SECRET` (`HF_KEY`/`HF_CREDENTIALS`), clés sur `cloud.higgsfield.ai/api-keys`.
- **Prior art OFFICIELLE à forker en priorité** (vérifié par la recherche) :
  - **`higgsfield-ai/skills`** (327★, MIT) — skill **`higgsfield-product-photoshoot`** avec 10 modes ad (`product_shot`, `lifestyle_scene`, `hero_banner`, **`ad_creative_pack`** = pack de statics Meta/TikTok/Pinterest/Google, `virtual_model_tryout`…) + **`higgsfield-soul-id`** (consistance d'identité). ⭐ **Son backend de gen est déjà `gpt_image_2`** → valide notre choix de modèle. Soul proposé en backend alternatif dans le cookbook.
  - **`higgsfield-ai/cli`** (253★, MIT) — commande **`marketing-studio`** (avatars, produits, ad references, brand kits, ad formats) + 18 modèles image (`gpt_image_2`, `text2image_soul_v2`, `nano_banana_2`, `flux_2`, `seedream_v4_5`, `marketing_studio_image`).
  - **`higgsfield-ai/higgsfield-client`** (SDK Python officiel — moteur de `gpt_image2_generate.py`).
- **Autres** : `tenfoldmarc/meta-ads-generator-skill` (URL→ads + refs concurrentes), `robonuggets/higgsfield-skill` (MCP wrapper).
- **Identité/produit** : Soul ID (`createSoulId()`, `custom_reference_id`) pour spokesperson récurrent ; **Product Placement** pour insérer le produit exact dans une scène générée (style S2).

*Skill V2 — moteur GPT Image 2. La V1 reste l'option typographique pure. Cap itérations à régler par client. Toujours approuver le coût avant un batch facturé.*
