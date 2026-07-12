# Références GitHub — outils & skills Meta Ads (rework-campaign)

Issu du scout de la recherche (juin 2026). Repos open-source à étudier comme référence d'implémentation. **Ne pas dépendre d'eux à l'exécution** — ce skill code ses propres appels API via `meta-campaign-launcher`. Utiles pour s'inspirer des frameworks/seuils.

## ⭐ Références maîtresses (audit + rework loop)
- **AgriciDaniel/claude-ads** (~6.2k★) — LA référence. Skill Claude Code, 250+ checks Meta/Google. `/ads audit` = 6 sous-agents parallèles (meta, creative, tracking, budget, compliance). Règles kill explicites (« 3x Kill Rule »), détection suppression similarité créa (>60% overlap = pénalité Andromeda), pipeline regen créa 4 étapes (dna → create → generate → photoshoot). Quasi exactement la boucle audit+regenerate voulue. (fork auto-updaté : **Hainrixz/claude-ads**)
- **TheMattBerman/meta-ads-kit** (~260★) — Analog open-source le plus proche en agent. 5 skills chaînés : bleeder/winner ID + fatigue, budget-optimizer (scale winners/cap losers), ad-copy-generator (asset_feed_spec-ready), pixel-capi. Upload des nouvelles ads en PAUSED + approval gate. Blueprint direct.
- **mathiaschu/meta-ads-analyzer** (~370★) — Skill + MCP de DIAGNOSTIC. Encode « Breakdown Effect », Learning Phase/Limited, root-cause fatigue. Le cerveau « pourquoi ça échoue » avant de décider quoi kill/regen.
- **nowork-studio/NotFair** (~2.9k★) — plugin Claude Code ; `meta-ads-audit` score la santé compte sur 7 dimensions (pixel, attribution, structure, créa, audience, spend, scaling readiness) = rubrique d'audit prête à l'emploi.

## Exécution / MCP (couche écriture)
- **pipeboard-co/meta-ads-mcp** (~995★) — MCP le plus mature (42 outils). Dynamic Creative testing natif, reco budget. BSL 1.1.
- **serkanhaslak/meta-mcp** (~5★) — 77 outils/24 modules, couverture la plus large (dup ad → swap creative → relaunch).
- **gomarble-ai/facebook-ads-mcp-server** (~330★) — MCP READ-ONLY insights, idéal phase audit sans risque d'écriture.
- **attainmentlabs/meta-ads-cli** (~30★) — CLI YAML, SAFETY-FIRST : campagnes PAUSED par défaut, `--live` requis, garde-fous budget. Bon modèle de couche mutation gardée.
- **facebook/facebook-python-business-sdk** (~3k★) — SDK officiel, fondation pour scripts custom.

## Frameworks / stratégie (knowledge)
- **coreyhaines31/marketingskills** (~34k★) — 50+ skills. `ad-creative` (génère/itère/scale headlines/copy/ads) = référence pour le générateur de variations. Très actif.
- **ivangfalco/ads-skills** (~175★) — 16 fichiers stratégie Meta (Operating System, Creative Cadence OS, fatigue, Advantage+) + 12 scripts Python API. B2B-leaning.
- **adkit/ads-skills** — frameworks de planning campagne (mechanics corrects, pas d'hallucination de settings).

## Créative intelligence / swipe (input variations)
- **ComposioHQ/awesome-claude-skills** → `competitive-ads-extractor` — extrait/analyse les ads concurrentes (FB/LinkedIn ad libraries).
- **minimaxir/facebook-ad-library-scraper** (~300★) — scraper API officielle Ad Library.
- **epctex-support/facebookads-scraper** / **domini-67/facebook-ads-library-scraper** — scrapers Apify (sans approbation API).
- **AnanyaP-WDW/AdTestPro** — pré-teste les créas contre des audiences synthétiques AVANT launch = gate de validation entre regen et push.

## Data / reporting
- **fivetran/dbt_facebook_ads** & **fivetran/dbt_ad_reporting** — modèles dbt analytics-ready (ad/adset/campaign), multi-canal.
- **AdvaySanketi/Meta-Ads-Project** — pipeline collecte/analyse + embeddings + Streamlit.
- **nikD305/Meta-Ads-Automation-n8n** — workflow n8n launch+monitor sans Ads Manager.
- **facebookresearch/Ad-Library-API-Script-Repository** — scripts officiels Meta Ad Library.

## Avancé
- **adcontextprotocol/adcp** — Ad Context Protocol (standard émergent pour agents IA).
- **AparnaIyer06/AdOptima.ai** — RL (DQN/PPO) pour bidding/budget temps réel.
