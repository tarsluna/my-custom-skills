# Archéologie du process — Pipeline créatives Meta Ads Acme Agency

**Date de l'analyse** : 2026-04-21
**Périmètre** : `~/skills/projects/client-slug/05-meta-ads/`
**Objet** : reconstituer le pipeline de production des créatives statiques Meta Ads à partir des artefacts sur disque (scripts, plists, stratégies, audits Council, pool d'angles, states, logs).

---

## 1. Pipeline — étapes ordonnées

| # | Étape | Nature | Produit par |
|---|---|---|---|
| 1 | Onboarding client (form) | Manuel | Client / commercial |
| 2 | Deep research (awareness · competitors · psychographic) | Manuel + skill | `deep-search` |
| 3 | Audit concurrentiel Meta Ads Library | Manuel + skill | `02-competitor-ads/analysis.md` + `data.csv` |
| 4 | Copy pack multi-variantes | Skill | `meta-ads-copywriter` → `ads-multi-variantes.md` |
| 5 | Build v1 — typographique pur (PIL only) | Script Python | `build_creatives.py` |
| 6 | Build v2 — éditorial photo fal.ai + brand fonts | Script Python | `build_creatives_v2.py` |
| 7 | Audit Council v2 (Brand · UX · UI) | 3 sous-agents Claude (manuel) | `creatives/v2/_council/*.md` |
| 8 | Rédaction stratégie v3 (white spaces + corrections Council) | Manuel | `creatives/v3/_strategy.md` |
| 9 | Build v3 — 5 variations contrasteées (due diligence, excel kills, prix-hook, UGC, anti-retainer) | Script Python | `build_creatives_v3.py` |
| 10 | Rédaction stratégie v4 (scission 2 campagnes A/B) | Manuel | `creatives/v4/_strategy.md` |
| 11 | Build v4 — 6 angles × nouveaux formats (timeline, diptych, comparison chart, stat hero, manifeste carousel) | Script Python | `build_creatives_v4.py` |
| 12 | Pipeline autonome — pool rotation d'angles | Script Python | `pipeline/build_iteration.py` + `angles_pool.json` |
| 13 | Audit heuristique automatisé par itération | Script Python | `pipeline/audit_heuristic.py` |
| 14 | Packaging ZIP + notif + email Mail.app | Script Python + osascript | `pipeline/package_delivery.py` |

Orchestration : `run_cron.sh` (iter + audit + package toutes les 2h) et `run_delivery_morning.sh` (package + email à 8h), planifiés par `launchd` via `com.Acme.iterate.plist` et `com.Acme.deliver.plist`.

---

## 2. Inputs requis par étape

| Étape | Inputs consommés |
|---|---|
| 1 onboarding | questionnaire client |
| 2 deep research | onboarding form |
| 3 competitor ads | Meta Ads Library (manuel), transcription CSV |
| 4 copy pack | `00-onboarding/onboarding-form.md` + `01-deep-search/0{1,2,3}*.md` + `02-competitor-ads/analysis.md` |
| 5 build v1 | `ads-multi-variantes.md` (hooks, CTAs), palette brand, fonts système macOS |
| 6 build v2 | `ads-multi-variantes.md`, `assets/fonts/*.ttf` (Space Grotesk + Instrument Serif), `FAL_KEY` env, prompts fal.ai inline |
| 7 council v2 | 3 PNG v2 (Feed 4:5) + brand brief + build_creatives_v2.py (lecture code pour connaître les tailles exactes) |
| 8 strategy v3 | `02-competitor-ads/data.csv` + `03-psychographic.md` + `00-onboarding/onboarding-form.md` + les 3 audits Council v2 |
| 9 build v3 | `_strategy.md` v3, fonts, FAL_KEY, `V2_EXCEL_PROMPT`, `V4_PROMPT` inline |
| 10 strategy v4 | analyse concurrentielle + psychographic + outputs v3 |
| 11 build v4 | `_strategy.md` v4, fonts, FAL_KEY (A1 mockup = PIL only, pas de fal) |
| 12 iteration | `angles_pool.json` (20 angles catalogués), `state.json` (iteration counter + used_angles), fonts, FAL_KEY, `MAX_ITER` |
| 13 audit heuristique | PNG du dossier `iterations/iter-*/` le plus récent |
| 14 delivery | tous les PNG (`creatives/angle-*`, `creatives/v2`, `creatives/v3/*`, `creatives/v4/*`, `iterations/iter-*`) + `_strategy.md` v3/v4 + `ads-multi-variantes.md` |

---

## 3. Outputs produits par étape

| Étape | Outputs |
|---|---|
| 5 v1 | `creatives/angle-{1,2,3}-*/angle-N_*_{feed-1x1,feed-4x5,story-9x16}.png` — 9 PNG |
| 6 v2 | `creatives/v2/{angle-1,angle-2,angle-3}_v2_feed-4x5.png` — 3 PNG + backgrounds dans `_backgrounds/` |
| 7 council v2 | `creatives/v2/_council/0{1,2,3}-*.md` — 3 verdicts scorés |
| 8 strategy v3 | `creatives/v3/_strategy.md` |
| 9 v3 | `creatives/v3/v{1,2,3,4,5}-*/` — 10 PNG + `script-video-v4.md` |
| 10 strategy v4 | `creatives/v4/_strategy.md` |
| 11 v4 | `creatives/v4/{A1,A2,A3,B1,B2,B3}-*/*.png` — 10 PNG |
| 12 iteration N | `iterations/iter-NN-YYYYMMDD-HHMM/*.png` + `iteration-summary.md` ; `state.json` mis à jour |
| 13 audit | `iterations/iter-NN-*/audit.md` avec tableau Dim/Size/Luminance/Variance/Verdict/Findings |
| 14 delivery | `~/Desktop/Acme-Ads-Pack-YYYYMMDD-HHMM.zip` (PNG + README + docs stratégie) + notification macOS + email optionnel |

État actuel confirmé : `state.json` indique `iteration=6`, 6 runs exécutés entre 02:44 et 05:15 le 2026-04-22, 28 entrées `used_angles` (doublons après rotation du pool).

---

## 4. Outils techniques — rôle précis et pièges rencontrés

### Python + PIL (Pillow)
- **Rôle** : toute la composition typographique, les formes (rounded rectangles, pills, ellipses, lignes), les dégradés générés pixel par pixel, les mocks dashboard/timeline/diptych/comparison chart recréés en code.
- **Patterns réutilisés** : helpers `ft()`, `wrap()`, `rr()`, `pill()`, `logo()`, `chip()`, `gradient_bg()`, `fit_font()` (shrink-to-fit pour éviter les débordements).
- **Pièges** :
  - `getbbox()` renvoie des bounds avec offset vertical non nul → décalage à compenser dans tout le positionnement (`y + (h - (b[3]-b[1])) / 2 - b[1]`).
  - Pas de kerning natif pour les glyphes serif → "M€" demande un +6px manuel noté par le Council UI.
  - Wrap naïf sur espaces — les lignes à rupture forcée passent par `body.split("\n")` puis wrap par paragraphe (pipeline v4+).

### fal.ai (FLUX schnell)
- **Rôle** : backgrounds éditoriaux photo-réalistes (laptop bureau, contrats froissés, flat-lay devis, portrait fondateur, chaos Excel).
- **Modèle utilisé** : `fal-ai/flux/schnell`, 4 inference steps, 1 image — choix volontaire pour le ratio coût/vitesse (pas besoin de photoréalisme maximal car tint + blur + overlay suivent).
- **Pièges** :
  - Les dimensions renvoyées ne matchent pas toujours l'input (ex. 1152×1440 demandé → résultat approximatif) — pipeline `build_iteration.py` force `bg.resize((W, H), Image.LANCZOS)`.
  - Caching par slug dans `_backgrounds/` (`if out.exists() and not force: return out`) pour éviter de payer deux fois.
  - Safety checker activé (v2) puis retiré (v3+) pour ne pas bloquer les mood shots "noir éditorial".

### Fonts — Space Grotesk + Instrument Serif
- **Rôle** : Instrument Serif Regular/Italic en hero display (chiffres, italiques éditoriales) ; Space Grotesk Bold pour eyebrow chips, CTA, logo Acme, sublines ; Regular pour body.
- **Location** : `assets/fonts/*.ttf` (download OFL Google Fonts, stocké localement pour être trackable par git).
- **Piège initial** : la v1 utilisait les fonts système macOS (Impact, Arial Black, Helvetica). Les audits Council ont imposé l'introduction d'Instrument Serif pour le registre éditorial financier (hero "1,2 M€").
- **Piège typographique relevé par Council UI** : pas de control de letter-spacing dans PIL → tracking "par défaut" jugé trop lâche à grande taille, recommandation de resserrer à −0.015em non appliquée (limitation PIL).

### launchd
- **Rôle** : planification cron-like sans dépendance externe, survit aux reboots.
- **Deux plists** :
  - `com.Acme.iterate.plist` → 10 créneaux horaires fixes (04:15, 06:15, 08:15, …, 22:15) → `run_cron.sh`.
  - `com.Acme.deliver.plist` → 08:00 quotidien → `run_delivery_morning.sh`.
- **Piège** : `RunAtLoad=false` pour éviter une double exécution au load. Logs séparés `.out` / `.err`. Le script zsh exporte `FAL_KEY` en dur — **secret en clair sur disque**, à isoler (keychain) pour un skill réutilisable.

### osascript
- **Rôle** : deux usages dans `package_delivery.py` :
  1. `display notification` → toast macOS "Acme Ads Pack livré".
  2. `tell application "Mail" ... make new outgoing message ... send` → envoi ZIP par pièce jointe.
- **Piège** : dispatch ≠ delivery (Mail.app doit être configuré avec un compte sortant actif, sinon silently-failed). Timeout 30s sur subprocess.

### Meta Ads Library
- **Rôle** : étape 3 (audit concurrentiel), consommée manuellement avant tout le pipeline code.
- **Output** : `02-competitor-ads/data.csv` (18 ads, 5 concurrents) qui alimente la stratégie v3 (white spaces 1-5).

---

## 5. Boucles de feedback — Council v2 → v3 → v4

Le Claude Council (Brand Guardian + UX Researcher + UI Designer) a audité v2 et généré 3 verdicts scorés. Les corrections suivantes ont été codées en v3 :

| Verdict Council v2 | Correction appliquée en v3 |
|---|---|
| **Brand (angle 1)** : photo stock laptop = cliché corporate 360°, trahit positionnement anti-agence | v3 V1 "Due Diligence" : **zéro photo stock**, typographique pur + mockup dashboard PIL (BookNow MRR +142%) |
| **UI (angle 3)** : prix orange à 3.1:1 sur cream = fail AA | v3 V3 "Price-in-hero" : prix en Instrument Serif 280pt **navy sur cream (contraste AAA 7:1+)**, un seul accent orange (CTA) |
| **UX (angle 3)** : palette crème low-arousal = -30% stop-rate feed | v3 V1 et V5 basculent sur **navy profond** + un accent saturé |
| **Brand (angle 2)** : "Pas de SEO" techniquement faux + typo Interlocuteur avec majuscule | v3 V5 manifesto : "72 000 €" hero choc + copy resserré, garde la recette gagnante |
| **UI (angle 2)** : logo navy sur navy < 3:1 | v3 tout : logo off-white sur navy profond, contraste 15:1+ |
| **UX (angle 1)** : CTA "appel découverte" tiède + stats sous fold | v3 V1 : signature `LE PACTE Acme · Prix affiché · Code à toi · Alex prend l'appel` + CTA centré |
| **Safe zone Meta 14%** non systématique | v3 tout : vérification `H - int(H * 0.085) - cta_h` dans tous les angles |

Les corrections v3 → v4 ont été guidées par la stratégie plutôt que par un Council (pas de `_council` dans v3 ou v4 sur disque). v4 introduit :
- **Scission ICP** en 2 campagnes (Campaign A MVP startup vs Campaign B outil métier TPE/PME).
- **5 nouveaux formats** non utilisés par aucun concurrent : timeline horizontale (A2), diptych before/after (B1), comparison chart (A3), stat hero card (B2), manifeste carousel 3 slides (B3).
- **Mockups PIL** (dashboard A1, diptych B1) pour éliminer toute dépendance fal.ai et stock coded.

---

## 6. Système d'angles rotatif

**Fichiers pivots** :
- `pipeline/angles_pool.json` — 20 angles catalogués (A à T), chacun avec : `id`, `name`, `category` (scarcity, personal_story, social_proof, case_study, authority, manifesto, comparative, transparency, lead_magnet, before_after, product_showcase, common_enemy, video_teaser, trust_seal), `hook`, `sub`, `body`, `cta`, `bg_theme` (navy_deep, light_cream, light_editorial, portrait_dark, split), `format` (feed-4x5 / story-9x16), `visual_strategy`.
- `pipeline/state.json` — `{iteration, used_angles[], runs[]}` persisté après chaque run.
- `pipeline/build_iteration.py` — orchestrateur.

**Algorithme** (`pick_angles` lignes 84-92) :
```
available = [a for a in pool if a["id"] not in used]
if len(available) < count: reset used = []; available = pool[:]
random.shuffle(available); return available[:count]
```
→ **Rotation sans répétition** jusqu'à épuisement du pool, puis reset automatique. L'état courant (`used_angles` a 28 entrées sur 20 angles) prouve qu'une rotation s'est bien produite.

**Cap d'itérations** : `MAX_ITER=6` (env var, défaut 6). Vérifié dans `main()` :
```
if state["iteration"] >= MAX_ITERATIONS and not args.force: sys.exit(0)
```
→ Passé 6 itérations, le launchd tire dans le vide tant que `--force` n'est pas passé. C'est le **frein de sécurité contre l'overproduction** (évite de spammer fal.ai et de saturer le disque). `state.json` confirme `iteration=6` atteint.

**Rendu autonome** (`render_angle`) : prend une spec d'angle et dispatch selon `bg_theme` → `theme_bg()` construit fond + palette, puis compose systématiquement logo + chip (label catégorie auto) + hero italique Instrument Serif (wrap 3 lignes max, shrink-to-fit) + accent line + sub italique + divider + body SPG + CTA pill. **Chaque angle est rendu sans code custom** grâce à une spec JSON structurée — c'est le cœur de la scalabilité du pipeline.

---

## 7. Garde-fous

| Garde-fou | Localisation | Comportement |
|---|---|---|
| **Dimensions Meta** | `audit_heuristic.py` L41-47 | Vérifie exact match parmi `{(1080,1080), (1080,1350), (1080,1920)}`. Sinon → `FAIL`, recommandation "ne pas uploader". |
| **Poids fichier min/max** | `audit_heuristic.py` L50-55 | < 80 KB → WARN (basse qualité) ; > 8 MB → WARN (trop lourd pour Meta 30 MB). |
| **Contraste global (variance)** | `audit_heuristic.py` L56-60 | stddev moyen R/G/B < 20 → faible contraste ; > 85 → contraste écrase texte. Proxy heuristique sans WCAG parsing. |
| **Safe zone CTA bas 14%** | Contrainte design documentée `_strategy.md` v3 | Tous les scripts v3/v4/pipeline placent le CTA à `H - int(H*0.085) - cta_h` ≈ 15% bottom. |
| **WCAG AAA 7:1 hero / AA 4.5:1 body** | Contrainte stratégique v3 | Enforcée par choix de palette (navy sur cream, off-white sur navy) et validée manuellement par Council UI. |
| **Shrink-to-fit headline** | `fit_font()` v3, `while textlength > 0.87*W` v4, `while textlength > 0.82*W` v2 | Empêche overflow horizontal en décrémentant la taille par pas de 4-8 pt. |
| **Wrap hook 3 lignes max** | `build_iteration.py` L262-265 | `while len(hook_lines) > 3 and hook_size > 40: hook_size -= 4` → évite les pavés de texte. |
| **Cap itérations** | `MAX_ITER=6` | Stoppe le launchd cron. |
| **Cache backgrounds fal.ai** | `out.exists() and not force` | Évite refacturation si prompt identique. |
| **Try/except au render level** | `build_iteration.py` L364-371 | Chaque angle rendu isolément — un crash sur angle X n'arrête pas le batch. |
| **Logs append-only** | `pipeline.log`, `cron.log` | Timestamp ISO, aucune rotation → surveillance simple. |

---

## 8. Ce qui devrait devenir un skill réutilisable

Packager un skill `meta-ads-builder` exploitable sur tout client :

### Assets cross-client (à inclure dans le skill)
- **Fonts OFL** — Instrument Serif + Space Grotesk (2 familles suffisent pour couvrir hero/body/CTA) embedded dans `assets/fonts/`.
- **Helpers PIL** factorisés : `ft()`, `wrap()`, `rr()`, `pill()`, `logo()`, `chip()`, `gradient_bg()`, `fit_font()`, `theme_bg()`, `fal_bg()` → module `meta_ads_toolkit.py`.
- **Thèmes backgrounds** paramétrables par clé : `navy_deep`, `light_cream`, `light_editorial`, `portrait_dark`, `split` (ajouter `brand_color_primary`, `brand_color_accent` comme variables).
- **Schéma angle JSON** : `{id, name, category, hook, sub, body, cta, bg_theme, format, visual_strategy}` avec 14 catégories pré-mappées aux labels eyebrow chips.

### Composants pipeline (à paramétrer)
- **Angles pool generator** — à partir du copy pack produit par `meta-ads-copywriter`, générer automatiquement un `angles_pool.json` de 15-25 entrées.
- **Rotation engine** — `state.json` + `pick_angles()` + MAX_ITER cap → générique.
- **Heuristic audit** — 4 checks (dimensions, weight, variance, luminance) + rapport markdown → générique.
- **Packaging delivery** — ZIP + README auto + osascript notif/mail → paramétrer `TARGET_EMAIL` en variable.
- **Launchd plists template** — deux plists avec placeholder `{{CLIENT_SLUG}}` et horaires configurables.

### Flux de production recommandé (skill v2)
1. Consumer skill `onboarding` → `onboarding-form.md`.
2. Consumer skill `deep-search` → 3 fichiers market/competitor/psychographic.
3. Consumer skill `competitor-ads` → `analysis.md` + `data.csv`.
4. Consumer skill `meta-ads-copywriter` → `ads-multi-variantes.md`.
5. **Nouveau skill `meta-ads-builder`** :
   - Phase A : génère `angles_pool.json` à partir du copy pack.
   - Phase B : build un set v1 (5-10 créatives) + lance `council` en 3 sous-agents (Brand / UX / UI) sur les PNG produits.
   - Phase C : consume les verdicts Council → rédige `_strategy.md` v2 + rebuild créatives corrigées.
   - Phase D : installe launchd (optionnel) pour rotation autonome.

### Ce qu'il faut rendre client-agnostic
- **Brand tokens** externalisés dans un YAML/JSON client (palette, fonts, logo SVG, mécanisme nommé type "Le Pacte Acme").
- **Prompts fal.ai** templatés avec variables de marque ("brand_persona_visual", "founder_description").
- **Copy variables** — tous les hooks/CTAs/subs sortent du copy pack, jamais hardcodés dans le build script.
- **FAL_KEY** et email destinataire → env vars injectées par le skill, jamais committées.

### Ce qu'il vaut mieux garder manuel (ne pas skill-iser)
- **Council audits** — les verdicts de qualité restent délégués à 3 sous-agents Claude appelés séparément, avec review humaine intercalée. Automatiser le re-build sur verdict Council = risque de boucle de mauvaise qualité.
- **Rédaction stratégie v_next** (`_strategy.md`) — décision éditoriale qui bénéficie d'un humain + Claude en tandem.

---

## Annexe — Fichiers référencés (chemins absolus)

Scripts :
- `~/skills/projects/client-slug/05-meta-ads/build_creatives.py`
- `~/skills/projects/client-slug/05-meta-ads/build_creatives_v2.py`
- `~/skills/projects/client-slug/05-meta-ads/build_creatives_v3.py`
- `~/skills/projects/client-slug/05-meta-ads/build_creatives_v4.py`
- `~/skills/projects/client-slug/05-meta-ads/pipeline/build_iteration.py`
- `~/skills/projects/client-slug/05-meta-ads/pipeline/audit_heuristic.py`
- `~/skills/projects/client-slug/05-meta-ads/pipeline/package_delivery.py`
- `~/skills/projects/client-slug/05-meta-ads/pipeline/run_cron.sh`
- `~/skills/projects/client-slug/05-meta-ads/pipeline/run_delivery_morning.sh`

Config & state :
- `~/skills/projects/client-slug/05-meta-ads/pipeline/angles_pool.json`
- `~/skills/projects/client-slug/05-meta-ads/pipeline/state.json`
- `~/Library/LaunchAgents/com.Acme.iterate.plist`
- `~/Library/LaunchAgents/com.Acme.deliver.plist`

Stratégie & Council :
- `~/skills/projects/client-slug/05-meta-ads/creatives/v3/_strategy.md`
- `~/skills/projects/client-slug/05-meta-ads/creatives/v4/_strategy.md`
- `~/skills/projects/client-slug/05-meta-ads/creatives/v2/_council/01-brand-guardian.md`
- `~/skills/projects/client-slug/05-meta-ads/creatives/v2/_council/02-ux-researcher.md`
- `~/skills/projects/client-slug/05-meta-ads/creatives/v2/_council/03-ui-designer.md`

Inputs upstream :
- `~/skills/projects/client-slug/00-onboarding/onboarding-form.md`
- `~/skills/projects/client-slug/01-deep-search/0{1,2,3}-*.md`
- `~/skills/projects/client-slug/02-competitor-ads/analysis.md`
- `~/skills/projects/client-slug/02-competitor-ads/data.csv`
- `~/skills/projects/client-slug/05-meta-ads/ads-multi-variantes.md`

Assets :
- `~/skills/projects/client-slug/05-meta-ads/assets/fonts/{SpaceGrotesk-Bold,SpaceGrotesk-Medium,SpaceGrotesk-Regular,InstrumentSerif-Regular,InstrumentSerif-Italic}.ttf`

**Note** : aucun fichier mentionné par la mission n'est manquant sur disque. Tous les artefacts existent et ont été lus.
