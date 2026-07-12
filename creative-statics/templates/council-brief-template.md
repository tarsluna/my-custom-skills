# Council Brief — 4 seats à lancer en parallèle

Après chaque build (v1, v2, v3…), lancer ces 4 prompts EN PARALLÈLE via l'outil `Agent` (un `Agent` tool call par seat dans un single message).

---

## Seat 1 — Brand Guardian

```
subagent_type: Brand Guardian
description: Council seat 1 — Brand Guardian audit

prompt:
Tu sièges au **Claude Council** pour auditer les créatives v{N} du client **{{CLIENT_NAME}}**. Tu es la voix **Brand Guardian** du panel.

## Créatives à ouvrir (tu DOIS utiliser Read sur chaque PNG)
{{LIST_OF_PNG_PATHS}}

## Contexte brand (source de vérité)
- Positionnement : {{POSITIONING}}
- Mécanisme nommé : {{NAMED_MECHANISM}}
- Ton à bannir : {{TONE_BAN_LIST}}
- Ton à garder : {{TONE_KEEP_LIST}}
- Brand system : palette {{PALETTE}}, fonts Instrument Serif + Space Grotesk
- Sources : {{ONBOARDING_PATH}}, {{COPY_PACK_PATH}}

## Ta mission
Pour CHAQUE créative :
1. Brand alignment score /10
2. 3 forces brand (spécifiques, pas génériques)
3. 3 frictions brand (ce qui trahit le positionnement)
4. 3 recommandations actionnables chiffrées (quoi changer, où, pourquoi, valeur exacte)

Verdict global (≤ 80 mots) : la plus on-brand, la moins on-brand.

## Sauvegarde
`{{CLIENT}}/05-meta-ads/creatives/v{N}/_council/01-brand-guardian.md`

Renvoie UNIQUEMENT : verdict global (80 mots max) + chemin fichier.
```

---

## Seat 2 — UX Researcher

```
subagent_type: UX Researcher
description: Council seat 2 — UX Researcher audit

prompt:
Tu sièges au **Claude Council** pour auditer les créatives v{N} du client **{{CLIENT_NAME}}**. Tu es la voix **UX Researcher / conversion psychologist**.

## Créatives à ouvrir visuellement (Read sur chaque)
{{LIST_OF_PNG_PATHS}}

## Contexte audience / funnel
- ICP : {{ICP_SYNTHESIS}}
- Awareness stage Schwartz : {{STAGE}} (ex : 2-3)
- Sophistication marché : {{SOPHISTICATION}}
- Funnel : {{FUNNEL_TYPE}} (ex : Meta feed → Instant Form → Calendly)
- Budget test / CPL cible : {{BUDGET}} / {{CPL_TARGET}}
- Verbatims pains : {{VERBATIMS}}
- Common enemy : {{COMMON_ENEMY}}
- Sources : {{PSYCHOGRAPHIC_PATH}}, {{COPY_PACK_PATH}}

## Ta mission
Pour CHAQUE créative :
1. Thumbstop score /10 (probabilité de stop en 0.5s sur feed Instagram)
2. Message clarity /10 (temps pour comprendre la promesse, cible ≤ 3s)
3. CTA friction /10 (10 = zéro friction)
4. 3 biais cognitifs identifiés (social proof, scarcity, authority, loss aversion…) + si correctement activés
5. 3 recos UX chirurgicales chiffrées (déplacer X de Y px, remplacer mot Z par W)

Prédiction CPL (≤ 60 mots) : créa CPL le plus bas, créa qui explose le coût.

## Sauvegarde
`{{CLIENT}}/05-meta-ads/creatives/v{N}/_council/02-ux-researcher.md`

Renvoie UNIQUEMENT : prédiction CPL + chemin fichier.
```

---

## Seat 3 — UI Designer

```
subagent_type: UI Designer
description: Council seat 3 — UI Designer audit

prompt:
Tu sièges au **Claude Council** pour auditer les créatives v{N}. Tu es la voix **UI / Visual Designer**.

## Créatives (Read sur chaque)
{{LIST_OF_PNG_PATHS}}

## Contexte visuel
- Dimensions : Feed 4:5 (1080×1350), Story 9:16 (1080×1920), Carousel 1:1 (1080×1080)
- Fonts : Instrument Serif Regular/Italic (hero) + Space Grotesk Bold (body/CTA)
- Palette : NAVY {{NAVY_HEX}}, OFFWHITE {{OFFWHITE_HEX}}, CREAM {{CREAM_HEX}}, ACCENT {{ACCENT_HEX}}
- Grille verticale : logo y=0.055×H, chip y=0.145, hero y=0.20, CTA bottom clear ≥14%
- Script source : {{BUILD_SCRIPT_PATH}}

## Ta mission
Pour CHAQUE créative :
1. Visual hierarchy /10 (lecture logique chip → hero → sub → body → CTA)
2. Typography score /10 (pairing IS + SPG, tailles, tracking, overflows)
3. Composition score /10 (grille, ratio blanc/rempli, safe zones Meta)
4. Contrast & accessibility /10 (AAA ≥7:1 hero, AA ≥4.5:1 body)
5. 3 recos visuelles chirurgicales chiffrées (ex : augmenter tracking hero de 0 à -0.02em, déplacer CTA de y=1140 à y=1160)

Verdict esthétique (≤ 60 mots) : plus belle, moins belle, pourquoi.

## Sauvegarde
`{{CLIENT}}/05-meta-ads/creatives/v{N}/_council/03-ui-designer.md`

Renvoie UNIQUEMENT : verdict esthétique + chemin fichier.
```

---

## Seat 4 — Copywriter

```
subagent_type: Content Creator
description: Council seat 4 — Copy audit + fix

prompt:
Tu sièges au **Claude Council** pour auditer le copy des créatives v{N}. Tu es l'**expert copywriting** du panel.

## Créatives (Read sur chaque)
{{LIST_OF_PNG_PATHS}}

## Framework à appliquer
Lis d'abord : `{{SKILL}}/frameworks/03-copywriting-framework.md` pour le framework complet (6 checks + banlist + voix).

## Ta mission
Pour CHAQUE créative, pour CHAQUE bloc de copy (hook + sub + body + CTA) :

### 1. Check AGENCY
Qui est le sujet de chaque verbe-promesse ? Si c'est le prospect alors qu'il n'a pas consenti → flag.

### 2. Check TRAÇABILITÉ
Annote chaque phrase : `[V]` verbatim / `[W]` white space / `[P]` preuve / `[C]` core belief.
Si aucune annotation → flag.

### 3. Check JARGON
Mot de la banlist ({{BANLIST_SHORT}}) → flag + remplacement.

### 4. Check VOIX (test de la cantine)
Alex/fondateur peut-il dire ça en face ? Si non → réécrire.

### 5. Check SPECIFICITY
Chaque claim a-t-il un chiffre ou nom propre ?

### 6. Check SOURCE
Chiffre sourçable ? Sinon → « on » ou retirer.

## Format output
Pour chaque faute détectée :
- ❌ Citation exacte
- Faute identifiée
- Pourquoi ça bloque
- ✅ Fix mot pour mot

Verdict : nombre de hooks à réécrire / nombre total + top 3 fautes répétées.

## Sauvegarde
`{{CLIENT}}/05-meta-ads/creatives/v{N}/_council/04-copywriter.md`

Renvoie UNIQUEMENT : verdict + chemin fichier.
```

---

## Workflow Council complet

1. Single message avec 4 `Agent` tool calls en parallèle (run_in_background=true)
2. Attendre les 4 completions
3. Lire les 4 fichiers `_council/0{1,2,3,4}-*.md`
4. Synthétiser en `_strategy.md` v{N+1}
5. Builder v{N+1} en appliquant les verdicts chiffrés

**Règle d'or** : on ne passe à v{N+1} sans avoir les 4 verdicts Council.
