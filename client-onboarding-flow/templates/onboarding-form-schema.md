# Schéma normalisé du formulaire d'onboarding client

Ce schéma définit les 12 champs critiques que le skill `client-onboarding-flow` extrait du formulaire d'onboarding client. Il sert de référence pour parser n'importe quel format d'input (markdown, pdf, docx, texte collé, Typeform/Tally/Google Forms).

## Format normalisé (markdown YAML-front)

```markdown
---
client_name: Acme Closing   # exemple fictif
niche: Formation au closing francophone haut ticket
product: Programme « 5 Jours Closer » — formation 5 jours pour closers freelance
geography: France, Belgique, Suisse romande
target_avatar: Closers freelance 25-40 ans qui plafonnent à 3-5K€/mois et veulent passer à 10K+
competitors:
  - Concurrent A (école de closing #1)
  - Concurrent B
  - Concurrent C
  - Concurrent D
funnel_type: vsl                       # vsl | instant_form
price_point: 7500                      # en euros, hors taxes
objectif_test:
  cpl_cible: 35                        # en euros
  volume_cible: 100                    # leads / mois
  duree_test: 30                       # jours
  hypothese_a_valider: "Le hook 'plafond 3K€' performe mieux que le hook 'liberté financière'"
tonality: Direct, anti-bullshit, cash, sans hyperbole, vouvoiement off
differenciation: Méthode « 5 Jours Closer » — seule formation qui place le closer en 14 jours sur des offres validées
proof_assets:
  - "Élève A — 0 → 12K€/mois en 6 semaines"
  - "Élève B — 3K → 15K en 4 mois"
  - "Élève C — 700K€ de volume en 14 jours"
---

## Notes additionnelles libres
[Tout ce que le client a écrit en réponse libre dans le formulaire d'onboarding...]
```

## Mapping vers les skills downstream

| Champ | Utilisé par | Variable downstream |
|---|---|---|
| `client_name` | TOUS | `{client}` |
| `niche` | deep-search | `YOUR NICHE` |
| `product` | deep-search, vsl, meta-ads | `PRODUCT` |
| `geography` | deep-search, competitor-ads | `GEOGRAPHY` |
| `target_avatar` | deep-search, vsl, meta-ads | `DEMO/Market Information` |
| `competitors` | competitor-ads | `--brands` |
| `funnel_type` | campaign-proposal, vsl | `funnel` |
| `price_point` | vsl, meta-ads, campaign-proposal | `price` |
| `objectif_test` | campaign-proposal | `test_objective` |
| `tonality` | vsl (mode), meta-ads | `voice` |
| `differenciation` | vsl, meta-ads | `unique_mechanism` |
| `proof_assets` | vsl, meta-ads | `proof` |

## Champs optionnels (best effort)

Si fournis, ces champs enrichissent les outputs sans être bloquants :
- `landing_url` — URL actuelle du client (audit congruence pour Meta Ads)
- `current_ads` — liens vers les pubs déjà testées par le client
- `crm_link` — outil CRM utilisé (HubSpot, Pipedrive, Notion, etc.)
- `team_size` — taille de l'équipe commerciale (impacte la recommandation funnel)
- `monthly_budget` — budget Meta Ads mensuel cible (impacte structure campagne)

## Champs bloquants

Si UN de ces champs manque, le skill DOIT demander à l'utilisateur avant de démarrer le pipeline :
- `client_name`
- `niche`
- `product`
- `geography`
- `competitors` (au moins 2)
- `funnel_type`
- `price_point`
