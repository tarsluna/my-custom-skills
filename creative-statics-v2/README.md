# creative-statics-v2

Pipeline ultra-boosté de **créatives statiques Meta Ads** pour ton offre, généré
avec **GPT Image 2 via fal.ai** (édition en **Nano Banana Pro**). Produit une **matrice de variations** (angles ×
formats × styles design × variable de test), adaptée au branding du client et inspirée
des meilleures ads concurrentes du `data.csv`.

> Skill Claude Code. Version **V2** (moteur IA) — complémentaire de la V1 (typographie
> PIL pure), qui n'est pas remplacée.

## Ce que ça fait

- **S'inspire des concurrents** : mine `02-competitor-ads/data.csv` → angles saturés à éviter, white spaces à attaquer, refs de style (jamais le copy concurrent).
- **Matrice testable** : 6-8 angles × 3 formats × 12 styles design, 1 variable de test par cellule.
- **3 moteurs** (`--engine`) :
  - `fal` (**défaut**, qualité max + scalable) — **GPT Image 2 via fal.ai** (`scripts/engine_fal.py`, clé `FAL_KEY`). API async, pas de CLI locale, pas de limite de jobs concurrents.
  - `cli` (legacy) — `higgsfield product-photoshoot` (non scalable, conservé en repli).
  - `sdk` (fallback) — GPT Image 2 brut via Higgsfield.
  - **Édition** : `python scripts/engine_fal.py --edit <url> --instruction "remplace X par Y" --out edited.png` (Nano Banana Pro — retouche texte fidèle, sans masque).
- **Soul ID** pour un spokesperson récurrent cohérent sur tout le pack.
- **Council 5 seats** (Brand · UX · UI · Copy · AI-Render Fidelity) + **brand-lock PIL** optionnel (logo/CTA pixel-perfect) + audit dimensions/contraste.
- **Copy** validé 6-checks, traçabilité `[V][W][P][C]`, voix client.

## Prérequis

```bash
# CLI officielle Higgsfield (engine cli)
curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh
higgsfield auth login
# SDK Python (engine sdk)
pip install higgsfield-client pillow
# auth (jamais committée) : Keychain
export HF_KEY=$(security find-generic-password -a -s HF_KEY -w)
```

## Quickstart

```bash
# B. inspiration concurrentielle
python scripts/competitor_mine.py --client <slug>
# F. health check + smoke test (no batch)
python scripts/photoshoot_cli.py --check
# G. estimer le coût (no credits) puis générer
python scripts/build_variations.py --matrix variation-matrix.json --dry-run
python scripts/build_variations.py --matrix variation-matrix.json          # engine cli
# I. brand-lock + audit
python scripts/brand_lock_pass.py --in raw/A1.png --out locked/A1.png --format feed-4x5 --brand-profile client-brand-profile.json --cta "Faire le point" --logo-text MARQUE
python scripts/audit_heuristic.py --dir locked --fix
```

Pipeline détaillé : voir `SKILL.md`. Modes & enhancer : `frameworks/04`.

## ⚠️ Coût & sécurité

- **Crédits toujours consommés en API** (pas d'unlimited hors web app). GPT Image 2 ≈ 1 crédit (~$0.07/image) ; Soul 2.0 ≈ 0.12 (~$0.009). **Toujours faire valider le coût d'un batch avant de le lancer.**
- **Aucun secret committé** : clés via env/Keychain uniquement. Pas de données client réelles dans le repo (templates only).

## Attribution

`photoshoot_cli.py`, `soul_id.py`, `frameworks/04` portent du code de
[higgsfield-ai/skills](https://github.com/higgsfield-ai/skills) (MIT). Voir `NOTICE.md`.
