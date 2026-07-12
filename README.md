# Meta Ads & Lead-Gen Skills

Un pack de **17 skills** (Claude Agent Skills) pour la génération de leads et le média-buying
Meta Ads, de bout en bout : recherche & stratégie, copywriting, créatives, landing pages,
lancement de campagnes, et analyse d'appels de vente. Chaque skill est autonome (dossier + `SKILL.md`).

> Skills de **méthodologie** réutilisables. Certains produisent des livrables (docs, PDF, HTML) ;
> quelques-uns référencent une persistance optionnelle (ex. une base Supabase à toi) via des
> placeholders — remplace-les par ta propre config. Aucune clé, aucune donnée client incluse.

## Les skills

### 🔍 Recherche & stratégie
| Skill | Rôle |
|---|---|
| [`deep-search`](./deep-search/SKILL.md) | Les 3 études DeepSearch : Market Awareness, Competitor Research, Psychographic Research. |
| [`competitor-ads-research`](./competitor-ads-research/SKILL.md) | Extrait + analyse les pubs Meta des concurrents (Meta Ads Library). |
| [`data-scraping`](./data-scraping/SKILL.md) | Scraping / enrichissement de données prospects. |

### ✍️ Copywriting & VSL
| Skill | Rôle |
|---|---|
| [`meta-ads-copywriter`](./meta-ads-copywriter/SKILL.md) | Scripts d'ads Meta (face-cam) + copy elite. |
| [`vsl-copywriter`](./vsl-copywriter/SKILL.md) | Scripts de Video Sales Letter world-class. |
| [`vsl-end-to-end-builder`](./vsl-end-to-end-builder/SKILL.md) | Pipeline VSL de A à Z depuis un brief. |
| [`cold-call-expert`](./cold-call-expert/SKILL.md) | Scripts de cold call B2B high-ticket. |

### 🎨 Créatives
| Skill | Rôle |
|---|---|
| [`creative-brief`](./creative-brief/SKILL.md) | Brief créatif structuré pour le creative strategist. |
| [`creative-statics`](./creative-statics/SKILL.md) | Pipeline de production de créatives statiques Meta. |
| [`creative-statics-v2`](./creative-statics-v2/SKILL.md) | La V2 boostée du pipeline de créatives. |
| [`meta-ads-creative-framework`](./meta-ads-creative-framework/SKILL.md) | Framework visuel pour créer les créatives dans Figma. |

### 🚀 Landing, devis & campagnes
| Skill | Rôle |
|---|---|
| [`cold-traffic-landing-page`](./cold-traffic-landing-page/SKILL.md) | Landing page cold-traffic haute conversion. |
| [`devis-vercel-generator`](./devis-vercel-generator/SKILL.md) | Page de devis (HTML + PDF) déployée sur Vercel. |
| [`campaign-proposal`](./campaign-proposal/SKILL.md) | Document « Proposition de Campagne Meta Ads ». |
| [`meta-campaign-launcher`](./meta-campaign-launcher/SKILL.md) | Setup de campagnes Meta de A à Z via la Graph API (tout en PAUSED). |
| [`rework-campaign`](./rework-campaign/SKILL.md) | Audit + scoring d'un compte Meta Ads (CPL/CPA, hook/hold rate…). |

### 📞 Vente
| Skill | Rôle |
|---|---|
| [`sales-call-analyzer`](./sales-call-analyzer/SKILL.md) | Analyse une transcription d'appel de vente → brief structuré. |

## Utilisation
Copie le dossier d'un skill dans ton répertoire de skills (ex. `~/.claude/skills/`) ou pointe ton
agent dessus. Chaque `SKILL.md` décrit ses déclencheurs, ses entrées et ses livrables. Les clés API
éventuelles (fal.ai, Meta, etc.) se fournissent via variables d'environnement — jamais en dur.

## Licence
MIT — voir `creative-statics-v2/LICENSE`. Utilisable, modifiable et redistribuable librement.
