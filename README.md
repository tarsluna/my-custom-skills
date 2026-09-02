# My Custom Skills

**21 skills Claude Code** (Agent Skills) pour faire tourner une agence de génération de leads et de
média-buying Meta Ads, de bout en bout : onboarding client → recherche marché → offre & copy → créatives →
lancement et pilotage des campagnes → notifications de leads → vente, relance et devis.

Chaque skill est un dossier autonome avec son `SKILL.md` (déclencheurs, entrées, étapes, livrables) et,
selon le cas, des `frameworks/`, `templates/`, `references/`, `scripts/`. Ce sont des skills de
**méthodologie** : ils encodent une façon de travailler, pas une infra. Aucune clé, aucune donnée client ;
tout ce qui dépend de ton compte passe par des variables d'environnement ou des placeholders explicites.

## Installation en une ligne

```bash
curl -fsSL https://raw.githubusercontent.com/tarsluna/my-custom-skills/main/install.sh | bash
```

Ça clone le repo dans `~/.claude/my-custom-skills` et crée un lien symbolique par skill dans
`~/.claude/skills/`. Relance Claude Code : les skills apparaissent. Ensuite, `git pull` dans le clone met
tout à jour.

Autres options :

```bash
git clone https://github.com/tarsluna/my-custom-skills.git && bash my-custom-skills/install.sh --copy   # copies indépendantes
bash ~/.claude/my-custom-skills/install.sh --check       # état de l'installation
bash ~/.claude/my-custom-skills/install.sh --uninstall   # retire les liens
```

Ou à la main : copie le dossier d'un skill dans `~/.claude/skills/` (ou le dossier de skills de ton agent).

## Le pipeline, par phase

### 0 · Orchestration
| Skill | Rôle |
|---|---|
| [`client-onboarding-flow`](./client-onboarding-flow/SKILL.md) | Orchestrateur : prend le formulaire d'onboarding d'un nouveau client et enchaîne tout le pipeline (deep-search → competitor-ads-research → offre → campaign-proposal → VSL → Meta Ads) via des sous-agents. |

### 1 · Recherche & stratégie
| Skill | Rôle |
|---|---|
| [`deep-search`](./deep-search/SKILL.md) | Les 3 études DeepSearch (Market Awareness, Competitor Research, Psychographic Research) → 3 rapports sourcés. |
| [`competitor-ads-research`](./competitor-ads-research/SKILL.md) | Extrait et analyse les pubs Meta des concurrents (Ads Library) → brief stratégique. |
| [`data-scraping`](./data-scraping/SKILL.md) | Moteur de sourcing B2B : scrape → qualification → dédup → export. |

### 2 · Offre & copy de vente
| Skill | Rôle |
|---|---|
| [`vsl-copywriter`](./vsl-copywriter/SKILL.md) | Script de Video Sales Letter world-class à partir des 3 rapports deep-search. |
| [`vsl-end-to-end-builder`](./vsl-end-to-end-builder/SKILL.md) | Pipeline VSL complet : brief → recherche → script → production → déploiement. |
| [`meta-ads-copywriter`](./meta-ads-copywriter/SKILL.md) | Scripts de pub face-cam (≥ 30 s) + copies texte Meta (primary text / headline / description). |
| [`cold-traffic-landing-page`](./cold-traffic-landing-page/SKILL.md) | Landing page brandée haute conversion pour trafic froid Meta / TikTok / YouTube. |
| [`campaign-proposal`](./campaign-proposal/SKILL.md) | Le document « Proposition de Campagne Meta Ads » remis au client : structure, ciblage, angles créatifs, nommage, questions de formulaire, génération .docx. |

### 3 · Production créative
| Skill | Rôle |
|---|---|
| [`creative-brief`](./creative-brief/SKILL.md) | Brief créatif structuré pour le creative strategist. |
| [`creative-statics`](./creative-statics/SKILL.md) | Pipeline de créatives statiques éditoriales Meta (14 étapes, council de review). |
| [`creative-statics-v2`](./creative-statics-v2/SKILL.md) | La V2 : GPT Image 2 via Higgsfield, matrice de variations, brand-lock. |
| [`meta-ads-creative-framework`](./meta-ads-creative-framework/SKILL.md) | Framework visuel Figma : layouts, typo, couleurs, CTA. |

### 4 · Lancement & pilotage des campagnes
| Skill | Rôle |
|---|---|
| [`meta-campaign-launcher`](./meta-campaign-launcher/SKILL.md) | Campagnes Meta de A à Z via la Graph API (campagne + ad sets + ciblage + créas), tout en PAUSED. |
| [`rework-campaign`](./rework-campaign/SKILL.md) | Audit d'un compte Meta Ads : score des créas et ad sets (CPL/CPA, hook rate, hold rate…), kill / scale / itère. |

### 5 · Leads & automatisations
| Skill | Rôle |
|---|---|
| [`meta-lead-notifications`](./meta-lead-notifications/SKILL.md) | Un message Slack à chaque nouveau lead d'un formulaire Meta Lead Ads : poller autonome (launchd ou cron) sur la Graph API, état des leads déjà vus, zéro webhook à héberger. |

### 6 · Vente, relance & devis
| Skill | Rôle |
|---|---|
| [`cold-call-expert`](./cold-call-expert/SKILL.md) | Scripts de cold call B2B high-ticket (recherche compilée : 30MPC, Gong, Cegelski, Colucci…). |
| [`outbound-sequence-writer`](./outbound-sequence-writer/SKILL.md) | Séquences cold email B2B (2 à 6 emails) : brief, angles, framework (PAS / AIDA / BAB / 4U / SLAP), cadence, sortie JSON avec merge tags pour Emelia, Lemlist, Smartlead, Instantly, LGM… |
| [`sales-call-analyzer`](./sales-call-analyzer/SKILL.md) | Transcription d'appel de vente → brief structuré JSON + markdown (voice of customer, dream vs objection). |
| [`sales-follow-up-sequence`](./sales-follow-up-sequence/SKILL.md) | Relances commerciales pilotées depuis ton CRM après une proposition, un devis ou un lien de paiement : cadence T0 / J+2 / J+6 puis action humaine, garde-fous anti-overkill. |
| [`devis-vercel-generator`](./devis-vercel-generator/SKILL.md) | Page de devis personnalisée (HTML + PDF) déployée sur Vercel, depuis le brief de `sales-call-analyzer`. |

## Frameworks de référence transverses
Eugene Schwartz (5 niveaux de conscience) · Market Sophistication · Alex Hormozi (Value Equation, Grand Slam Offer) ·
Imperium Acquisition · RMBC · 10 frameworks Meta Ads · 30MPC (cold call).

## Dépendance externe
`client-onboarding-flow` appelle aussi le skill **`demonte-ton-offre`** (reconstruction d'offre irrésistible), publié séparément :
[gquthier/autonomous-offer-rebuild](https://github.com/gquthier/autonomous-offer-rebuild). Installe-le dans `~/.claude/skills/demonte-ton-offre/`
si tu veux le pipeline complet ; les autres skills fonctionnent sans.

## Prérequis et clés
Certains skills appellent des services externes (Meta Graph API, Higgsfield, fal.ai, Vercel, Slack, un CRM).
Les clés se fournissent **uniquement** par variables d'environnement ou fichier `.env` local (un `.env.example`
est fourni quand c'est nécessaire). Rien n'est stocké dans le repo.

## Licence
MIT — voir [`LICENSE`](./LICENSE). Utilisable, modifiable et redistribuable librement.
