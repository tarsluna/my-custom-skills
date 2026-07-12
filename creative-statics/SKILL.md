---
name: creative-statics
description: Pipeline complet de production de créatives Meta Ads statiques éditoriales haute qualité pour un client. Consomme les outputs de onboarding + deep-search + competitor-ads-research + meta-ads-copywriter, produit des créatives PNG Feed 4:5 / Story 9:16 / Carousel 1:1 via Python PIL + fal.ai (FLUX schnell), passe chaque batch au Claude Council (Brand Guardian + UX Researcher + UI Designer + Copywriter), applique un framework de copywriting validé (agency check, traçabilité verbatim/white space, voix Acme), et package une livraison zip avec cron launchd toutes les 2 h + delivery matinal. Trigger phrases : "créatives Meta statiques", "pipeline créatives client", "générer le pack ads", "lancer le cron créa", "faire les ads du client", "créatives éditoriales pour {client}", "package créatives Meta".
---

# Creative Statics Pipeline

Ce skill est l'orchestrateur de production de créatives statiques Meta Ads. Il hérite des patterns construits sur le client Acme Agency (avril 2026), validés par un Council de 3 sous-agents + un copywriter expert qui a auditée les 40+ créatives produites.

**Input unique** : un client avec les 4 livrables amont (onboarding, deep search, competitor analysis, copy pack).
**Output** : un dossier `creatives/` avec 30+ créatives éditoriales + zip sur Desktop + cron autonome toutes les 2 h.

---

## 🎯 Quand utiliser ce skill

Trigger sur :
- « Fais les créatives Meta pour {client} »
- « Lance le pipeline créa pour {client} »
- « Je veux un pack de 30 ads pour {client} »
- « Déploie le cron créatives {client} »
- « Package les ads du client »
- « Créatives éditoriales {client} »

NE PAS trigger pour :
- Produire une seule créative ad-hoc → utiliser directement PIL ou Figma
- Réécrire du copy sans produire de visuel → utiliser `meta-ads-copywriter`
- Faire l'audit concurrentiel → utiliser `competitor-ads-research`
- Onboarder un nouveau client → partir du brief d'onboarding (ICP, verbatims, ticket, ton, do/don't, brand assets)

---

## 📥 Dépendances amont obligatoires

Avant de lancer ce skill, les 4 livrables suivants **doivent exister** pour le client concerné :

| # | Skill producteur | Output consommé |
|---|---|---|
| 1 | le brief d'onboarding client | `00-onboarding/onboarding-form.md` — ICP, verbatims, ticket, tonality, do/don't |
| 2 | `deep-search` | `01-deep-search/01-market-awareness.md · 02-competitor-research.md · 03-psychographic.md` |
| 3 | `competitor-ads-research` | `02-competitor-ads/analysis.md` (white spaces, saturated angles, top hooks) + `data.csv` |
| 4 | `meta-ads-copywriter` | `05-meta-ads/ads-multi-variantes.md` (hooks, primary text, headlines, CTAs par variante) |

Si un livrable manque → **STOP**. Demander à l'utilisateur de lancer le skill manquant.

---

## 🗂️ Structure du skill

```
creative-statics/
├── SKILL.md                                ← ce fichier (orchestration)
├── frameworks/
│   ├── 01-pipeline-14-steps.md             ← archéologie du process (archaeologist agent)
│   ├── 02-design-system.md                 ← design system complet (UI agent)
│   └── 03-copywriting-framework.md         ← audit copy + framework (copywriter agent)
├── assets/
│   ├── fonts/
│   │   ├── InstrumentSerif-Regular.ttf     ← hero display, chiffres
│   │   ├── InstrumentSerif-Italic.ttf      ← hooks éditoriaux
│   │   ├── SpaceGrotesk-Bold.ttf           ← logo, chips, CTA, body
│   │   ├── SpaceGrotesk-Medium.ttf
│   │   └── SpaceGrotesk-Regular.ttf
│   ├── angles_pool_template.json           ← 20 angles template à adapter par client
│   └── state_template.json                 ← état initial rotation
├── scripts/
│   ├── build_iteration.py                  ← générateur autonome (FAL + PIL)
│   ├── audit_heuristic.py                  ← audit sans LLM (contrast, dimensions, poids)
│   ├── package_delivery.py                 ← zip + Desktop + notif macOS + Mail.app
│   ├── run_cron.sh                         ← wrapper launchd iterate
│   └── run_delivery_morning.sh             ← wrapper launchd deliver 8h
├── templates/
│   ├── creative-brief-visual-template.md   ← brief visuel client
│   ├── launchd-iterate.plist.template      ← plist cron avec placeholders
│   ├── launchd-deliver.plist.template
│   └── council-brief-template.md           ← prompt pour chaque seat Council
└── checklists/
    ├── copy-validation-6-points.md         ← checklist pré-production copy
    ├── visual-quality-gate.md              ← checklist pré-export
    └── iteration-go-no-go.md               ← gate entre 2 itérations
```

---

## 🔁 Pipeline — les 14 étapes

```
                     AMONT (skills séparés)
┌───────────────────────────────────────────────────┐
│ 1. Onboarding form                                │
│ 2. Deep search (3 rapports)                       │
│ 3. Competitor ads analysis + data.csv             │
│ 4. Copy pack (ads-multi-variantes.md)             │
└───────────────────────────────────────────────────┘
                          │
                          ▼
┌───────────────────────────────────────────────────┐
│ CE SKILL (creative-statics)           │
│                                                   │
│ 5. Brief visuel (archétype couleur, fonts, fond)  │
│ 6. Build v1 — 3-5 créatives typographiques pures  │
│ 7. Council v1 (Brand + UX + UI + Copy) ← 4 seats  │
│ 8. Rédaction _strategy.md v2                      │
│ 9. Build v2 — corrections + fal.ai backgrounds    │
│ 10. (optionnel) Build v3 — new formats            │
│     (timeline, diptych, comparison chart)         │
│ 11. Génération angles_pool.json (20 angles)       │
│ 12. build_iteration.py autonome (cron toutes 2 h) │
│ 13. Audit heuristique auto par itération          │
│ 14. Packaging ZIP + Desktop + Mail.app optionnel  │
└───────────────────────────────────────────────────┘
```

Détail complet des 14 étapes + inputs/outputs/outils par étape : voir `frameworks/01-pipeline-14-steps.md`.

---

## 🎨 Design system — locked

Extrait de 40+ créatives produites + Council audit. **Chaque décision de design ci-dessous est justifiée par un verdict Council traçable dans `frameworks/02-design-system.md`**.

### Les 2 fonts (point final, jamais plus)

- **Instrument Serif Regular** — chiffres hero, titres droits
- **Instrument Serif Italic** — hooks éditoriaux, sublines poétiques
- **Space Grotesk Bold** — logo, chips, CTA, body, stats

Fonts embarquées dans `assets/fonts/` (OFL, Google Fonts).

### Palette de base verrouillée (4 tokens actifs)

| Token | Hex | Usage canonique |
|---|---|---|
| `NAVY` | `#0A1628` | Fond sombre dominant, texte hero |
| `OFFWHITE` | `#F5F0E6` | Fond clair, texte sur navy, texte dans CTA |
| `CREAM` | `#E4DAC6` | Descente tonale (ligne 2 italique) |
| `ACCENT` | client-specific (`#FF5A1F` chez Acme) | **CTA principal uniquement** |

Palette étendue optionnelle : `GREEN` trust, `GREY` sub labels, `RED` alerte, `NAVY_SOFT` cards intérieures. Voir `frameworks/02-design-system.md`.

### Règle d'or #1 (la plus violée sur v1)

> **Un seul accent couleur = un seul point focal = le CTA.** Si la chip catégorie est en orange, le hero doit rester navy/offwhite. Council score < 8 si violée.

### Contraste — règle absolue

- Hero (chiffre ou hook) : **AAA ≥ 7:1**
- Body : AA ≥ 4.5:1
- CTA pill : pass AA large text (≥ 3:1 à texte ≥ 37px bold)
- **Exception bannie** : ORANGE sur OFFWHITE/CREAM pour texte-clé = 3.1:1 (fail AA) → violation identifiée sur Acme v1 angle-3 prix, corrigée en v3+.

### Grille verticale locked (normalisée sur W=1080)

```
y=0.055×H  → logo Acme + underline orange
y=0.145×H  → eyebrow chip (catégorie)
y=0.20×H   → hero hook italique OU hero chiffre serif
y=0.45×H   → accent bar orange / divider
y=0.50×H   → sub italique OU zone layout (dashboard/diptych/chart)
y=0.62×H   → body + stats rail
y=H-0.075×H-ctaH → CTA pill centré (safe Meta 14%+)
```

### 7 archétypes layout validés

1. **Hero Number Big** — chiffre IS_REG `W×0.22-0.30` dominant
2. **Hook Italique 3-lines** — IS_ITA `W×0.070-0.082` × 3 lignes
3. **Timeline Horizontal** — track 6px avec milestones Gantt-like
4. **Diptych Before/After** — 2 cards 42%/42% + flèche
5. **Comparison Chart 3 colonnes** — colonne gagnante highlighted navy
6. **Stat Hero Card** — chiffre géant + underline + sub italique + proof rail
7. **Manifesto Carousel** — 3-4 slides rythme hook numéroté → récap CTA

### Formats Meta supportés

| Format | Dimensions | Contrainte clé |
|---|---|---|
| Feed 4:5 | 1080 × 1350 | **Format #1 prioritaire** — 70 % du pack |
| Story 9:16 | 1080 × 1920 | Safe zones top/bottom Instagram ≈ 220px |
| Feed 1:1 / Carousel | 1080 × 1080 | Swipe indicator, max 4 slides |

---

## ✍️ Copy framework — traçabilité obligatoire

Extrait de l'audit copy Acme v1-v4 par le copywriter expert du Council. **Chaque hook qui sort du pool doit passer les 6 points de validation**. Voir `frameworks/03-copywriting-framework.md` pour le détail complet.

### Principe n°0 — traçabilité

Tout hook doit être traçable à :
- `[V]` un verbatim psychographic
- `[W]` un white space concurrentiel
- `[P]` une preuve chiffrée sourçable
- `[C]` un core belief client

**Phrase sans annotation → kill ou réécriture.**

### Les 6 checks obligatoires par hook

1. **AGENCY** — qui fait l'action dans chaque verbe ?
   - Sujet du verbe-promesse = fournisseur (jamais le prospect tant qu'il n'a pas levé la main)
   - ❌ « Devis fixe signé en 48 h » (c'est LUI qui signe)
   - ✅ « Devis fixe envoyé en 48 h » ou « Tu reçois ton devis fixe en 48 h »

2. **AWARENESS STAGE (Schwartz)**
   - Stade 2 (Problem Aware) : **nomme le problème** en vocabulaire prospect
   - Stade 3 (Solution Aware) : **compare** à une catégorie connue
   - Stade 4 (Product Aware) : **cite la preuve unique** (BookNow-level)
   - Mélange 3 stades = 0 conversion

3. **PAIN vs DESIRE POOL**
   - Hook = pain pool (peur, échaudage, perte)
   - Body + CTA = desire pool (lever, scaler, déléguer)
   - Inversé = weak

4. **SPECIFICITY** — chaque claim a-t-il un chiffre ou un nom propre ?
   - « Vite » → « en 5 mois »
   - « Beaucoup » → « 1,2 M€ »
   - « On livre » → « Alex livre »

5. **SOURCE** — chiffre sourçable publiquement ou sur devis ?
   - Si non-sourçable → reformuler en « on », hypothèse, ou retirer

6. **VOIX (test de la cantine)** — Alex peut-il dire ça en face d'un fondateur sans sonner plaquette ?

### Top 5 erreurs copy à bannir absolument (patterns identifiés)

1. **Agency mismatch** — verbe-promesse dont le sujet est le prospect (« signé en 48h »)
2. **Urgence artificielle** — « maintenant » sur achat B2B 5-15 k€ = faux
3. **Claim non sourcé** — chiffres ronds sans source (« 70 % », « jamais en 3 ans »)
4. **Conditionnel passé** — « tu aurais payé… » = reproche
5. **Jargon tech saturé** — « scale », « stack qui scale », stacks listées en hook

### Angles saturés à bannir (tirés de `analysis.md`)

| Expression | Pourquoi interdite | Remplacement |
|---|---|---|
| Agence 360° / sur mesure / clés en main | Tous les concurrents FR dev | « On ne fait que du dev » |
| Expert / n°1 / leader | Claim non sourcé | Chiffre BookNow ou preuve |
| « On conçoit des produits digitaux » | Verbatim Yield + Bob | « On code [la chose précise] » |
| Liste stack tech en hook | Angle saturé | Bénéfice business de la stack |
| « Sur mesure » | Pillar saturé | « Pas de template » ou « sur ton métier » |

### Règles linguistiques ancrées (voix)

1. **Tu direct**, jamais « vous »
2. **Phrases courtes** — moyenne 8-12 mots, max 20
3. **Zéro émoji**
4. **Verbes d'action concrets** (coder, livrer, envoyer, reprendre)
5. **Nom du fondateur cité** — l'incarnation est la preuve
6. **Chiffres preuves en bloc** — 5 mois / 1,2 M€ / 500+ partenaires (jamais un chiffre isolé)
7. **Prix en K€ ou chiffres complets** — « 5 000 € » ou « 5 K€ »
8. **Anti-promesse > promesse** — « on ne fait pas X » percute plus que « on fait Y » sur cible échaudée

---

## 🔁 Pipeline orchestré — exécution

### Phase A — Brief visuel (manuel, 15 min)

1. Lire `00-onboarding/onboarding-form.md` pour extraire : nom fondateur, tonality, prix, proof_assets, brand colors éventuelles.
2. Remplir `templates/creative-brief-visual-template.md` dans le dossier client :
   - Archétype couleur : Confiance / Urgence / Energie / Authority (cf. `frameworks/02-design-system.md` §2)
   - Accent color hex (si brand imposé, sinon orange `#FF5A1F`)
   - Mécanisme nommé (ex : « Le Pacte Acme »)
   - CTA principal
   - Formats prioritaires (par défaut : Feed 4:5 + Story 9:16 + 1 Carousel)

### Phase B — Build v1 (automatique, 15 min)

1. Générer un premier set de 5 créatives typographiques (pas de fal.ai) depuis les 3 angles principaux du copy pack (le plus fort + 2 alternatives).
2. Exécuter `scripts/audit_heuristic.py` → valider dimensions, poids, variance.
3. Output : `creatives/v1/`

### Phase C — Council v1 (4 sous-agents Claude)

**Lancer 4 agents EN PARALLÈLE** via l'outil Agent, chacun avec prompt issu de `templates/council-brief-template.md` :

1. **Brand Guardian** (subagent_type=Brand Guardian) — alignement voix, do/don't, mécanisme
2. **UX Researcher** (subagent_type=UX Researcher) — thumbstop score, clarity, CTA friction, biais
3. **UI Designer** (subagent_type=UI Designer) — hierarchy, typography, contrast AAA/AA, composition
4. **Copywriter** (subagent_type=Content Creator) — agency check, traçabilité `[V][W][P][C]`, jargon, voix

Chaque seat doit :
- Ouvrir chaque PNG via Read
- Scorer sur 10
- Fournir 3 recommandations chirurgicales avec valeurs chiffrées
- Sauvegarder dans `creatives/v1/_council/0{1,2,3,4}-{agent}.md`

**STOP POINT** : ne pas builder v2 sans avoir lu les 4 verdicts. Synthétiser en `_strategy.md` v2.

### Phase D — Build v2 (automatique, 30 min avec fal.ai)

1. Lire les 4 verdicts Council v1.
2. Rédiger `creatives/v2/_strategy.md` avec :
   - Verdict consensus
   - Ce qui change
   - Nouveaux angles qui attaquent les white spaces
3. Builder 5-10 créatives avec fal.ai FLUX schnell pour les backgrounds éditoriaux si pertinent.
4. Re-audit heuristique.

### Phase E — Angles pool generation (automatique, 10 min)

1. Depuis le copy pack + white spaces, générer un `angles_pool.json` de 20 angles
2. Structure obligatoire par angle :
```json
{
  "id": "X-slug-descriptif",
  "name": "Nom court",
  "category": "scarcity|personal_story|social_proof|case_study|authority|manifesto|comparative|transparency|lead_magnet|before_after|product_showcase|common_enemy|video_teaser|trust_seal",
  "hook": "Hook qui passe les 6 checks copy",
  "sub": "Subline éditorial",
  "body": "Body dense, verbatims-based, zéro jargon saturé",
  "cta": "CTA désescaladé si cold",
  "bg_theme": "navy_deep|light_cream|light_editorial|portrait_dark|split",
  "format": "feed-4x5|story-9x16|feed-1x1",
  "visual_strategy": "description courte du layout cible"
}
```

### Phase F — Cron autonome (launchd)

1. Copier `scripts/run_cron.sh` et `run_delivery_morning.sh` vers le dossier client.
2. Générer les plists depuis `templates/launchd-*.plist.template` avec placeholders :
   - `{{CLIENT_SLUG}}` (ex : `client-slug`)
   - `{{SKILLS_ROOT}}` (chemin absolu)
   - `{{FAL_KEY}}` (env — voir sécurité plus bas)
   - `{{TARGET_EMAIL}}` (destinataire delivery matinal)
3. `launchctl load` les 2 plists.
4. L'iterate tourne toutes les 2 h entre 04:15 et 22:15 (10 créneaux/jour), plafonné à `MAX_ITER=6`.
5. Le deliver tourne une fois par jour à 08:00 : repackage + Mail.app si compte configuré.

### Phase G — Livraison finale

1. `package_delivery.py` produit `~/Desktop/{ClientName}-Ads-Pack-YYYYMMDD.zip` avec :
   - Toutes les créatives PNG organisées par version (v1/ v2/ v3/ iterations/)
   - README.md index
   - `docs/` : `_strategy.md` de chaque version + copy pack source
2. Notification macOS « Pack livré ».
3. Optionnel : email via `osascript tell Mail.app` (nécessite compte configuré).

---

## 🛡️ Garde-fous obligatoires

| Garde-fou | Où | Enforcement |
|---|---|---|
| Dimensions Meta exactes | `audit_heuristic.py` | FAIL si ≠ 1080×{1080, 1350, 1920} |
| Poids fichier 80 KB–8 MB | `audit_heuristic.py` | WARN hors fourchette |
| Contraste global (variance) | `audit_heuristic.py` | WARN si < 20 ou > 85 |
| Safe zone CTA bottom ≥ 14% | layout rules | vérifié à chaque build |
| Wrap hook max 3 lignes | `fit_font` + auto-shrink | `build_iteration.py` L262 |
| Cache backgrounds fal.ai | `fal_bg()` force=False | évite refacturation |
| Cap itérations `MAX_ITER=6` | env var | arrête le cron |
| Try/except par angle | `render_angle` isolé | 1 crash ≠ batch abandonné |
| Logs append-only | `cron.log`, `delivery.log`, `pipeline.log` | audit trail |
| Copy validation 6 points | Phase A + Council Phase C | enforce avant production |

### Sécurité

⚠️ **`FAL_KEY` en clair dans `run_cron.sh`** est une dette connue. Pour usage production sur client réel :
1. Migrer la clé vers macOS Keychain :
   ```sh
   security add-generic-password -a "the platform" -s "FAL_KEY" -w "<key>"
   ```
2. Modifier `run_cron.sh` pour lire depuis keychain :
   ```sh
   export FAL_KEY=$(security find-generic-password -a "the platform" -s "FAL_KEY" -w)
   ```

---

## 🧪 Checklists obligatoires

Avant chaque production :
- **copy** : `checklists/copy-validation-6-points.md`
- **visuel** : `checklists/visual-quality-gate.md`
- **itération** : `checklists/iteration-go-no-go.md` (go/no-go entre v_N et v_N+1)

---

## 📊 Ce qui reste manuel (ne PAS automatiser)

Certaines étapes bénéficient du jugement humain + Claude en tandem :

1. **Council audits** — les 4 seats restent 4 sous-agents appelés en parallèle, pas un script qui auto-score
2. **Rédaction `_strategy.md`** — chaque version v_next est une décision éditoriale (quels angles on pousse, quels on kill)
3. **Curation finale du pack** — on sélectionne les 30 meilleures, pas toutes les itérations générées
4. **Réécriture copy post-Council** — le copywriter passe sur chaque hook flaggé

Automatiser ces étapes = risque de boucle de mauvaise qualité (garbage in, garbage out sur le Council).

---

## 🎁 Templates livrés

- `templates/creative-brief-visual-template.md` — input client de Phase A
- `templates/council-brief-template.md` — 4 prompts Council prêts à copier
- `templates/launchd-iterate.plist.template` — cron 2 h avec placeholders
- `templates/launchd-deliver.plist.template` — delivery matinal

---

## 🔗 Références — comment ce skill est né

Construit lors de la session Acme Agency (avril 2026) qui a produit :
- 4 versions de build (v1 PIL pur → v2 fal.ai → v3 white spaces → v4 scission 2 campagnes)
- 40+ créatives, 20 angles dans le pool
- 4 agents Council (Brand Guardian + UX Researcher + UI Designer + Content Creator)
- Cron launchd 10 créneaux/jour + delivery 8 h

L'analyse archéologique complète de cette session est dans `frameworks/01-pipeline-14-steps.md`. Le design system dans `frameworks/02-design-system.md`. Le framework copywriting dans `frameworks/03-copywriting-framework.md`.

Ces 3 frameworks sont le cœur du skill. **À lire avant tout déploiement sur un nouveau client**.

---

*Skill autorisé à produire des créatives jusqu'à 6 itérations par jour. Au-delà, demander à l'utilisateur de relever `MAX_ITER` (renommer en `MAX_ITER` pour un client autre que Acme).*
