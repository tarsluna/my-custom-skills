# Meta Graph API — Cheatsheet campagnes

Version par défaut : **v21.0**. Base : `https://graph.facebook.com/v21.0`. Auth : `access_token=<META_ACCESS_TOKEN>` (System User).

## Hiérarchie
```
Campaign (objective, PAUSED) → Ad Set (budget, ciblage, optim, destination, PAUSED)
  → Ad (status PAUSED) → Ad Creative (object_story_spec | asset_feed_spec)
Lead Form (sur la Page)  |  Pixel (sur le compte/Business)
```

## Endpoints clés
| Action | Méthode | Endpoint |
|---|---|---|
| Vérifier token | GET | `/debug_token?input_token=TOKEN&access_token=APPID|APPSECRET` |
| Comptes accessibles | GET | `/me/adaccounts?fields=id,name,account_status,currency` |
| État compte | GET | `/act_ID?fields=name,account_status,disable_reason,currency,funding_source` |
| Page token | GET | `/PAGE_ID?fields=access_token` |
| CGU lead ads | GET | `/PAGE_ID?fields=leadgen_tos_accepted` |
| Forms existants | GET | `/PAGE_ID/leadgen_forms?fields=id,name,status` |
| Pixels | GET | `/act_ID/adspixels?fields=id,name` |
| Résoudre intérêt | GET | `/search?type=adinterest&q=Entrepreneuriat&limit=5` |
| Créer campagne | POST | `/act_ID/campaigns` |
| Créer ad set | POST | `/act_ID/adsets` |
| Créer lead form | POST | `/PAGE_ID/leadgen_forms` (auth = PAGE token) |
| Upload image | POST | `/act_ID/adimages` (multipart) → `images.<fn>.hash` |
| Créer creative | POST | `/act_ID/adcreatives` |
| Créer ad | POST | `/act_ID/ads` |

## Erreurs subcode → fix (rencontrées en prod)
| subcode | message | fix (règle) |
|---|---|---|
| 4834011 | is_adset_budget_sharing_enabled requis | ajouter `is_adset_budget_sharing_enabled=false` à la campagne (R1) |
| 2490487 | montant/contraintes d'enchère requis | `bid_strategy=LOWEST_COST_WITHOUT_CAP` sur l'ad set (R2) |
| 3858081 | dsa_beneficiary manquant | `dsa_beneficiary`+`dsa_payor` sur l'ad set (R3) |
| 1870189 | age_max < 65 avec Advantage Audience | `advantage_audience=0` (R4) |
| 1359188 | aucun moyen de paiement | ajouter une CB au compte (humain) — bloque les ADS only (R5) |
| 3858504 | standard_enhancements obsolète | retirer `degrees_of_freedom_spec` (R6) |
| 1815089 | CGU lead ads non acceptées | accepter sur facebook.com/ads/leadgen/tos?page_id=… (humain, R7) |
| 1892075 | privacy_policy manquante | fournir `privacy_policy.url` au form (R8) |
| 1885316 | compte désactivé | account_status=2 → demande de révision Meta (humain, R10) |

## Champs ad set — rappels
- `daily_budget` en **centimes** (1500 = 15€) (R11).
- `optimization_goal` : `LEAD_GENERATION` (leadgen) | `OFFSITE_CONVERSIONS` (conversion).
- `destination_type` : `ON_AD` (formulaire instantané) | `WEBSITE` (landing).
- `promoted_object` : `{"page_id":...}` (leadgen) | `{"pixel_id":...,"custom_event_type":"LEAD"}` (conversion).
- `is_dynamic_creative` : `true` au niveau **ad set** pour activer DCO (R9).

## IDs de placement (targeting)
- `publisher_platforms`: `["facebook","instagram"]` (+ `audience_network`, `messenger`)
- Feed : `facebook_positions=["feed"]`, `instagram_positions=["stream","explore"]`
- Stories/Reels : `facebook_positions=["story","facebook_reels"]`, `instagram_positions=["story","reels"]`
- Omettre toutes les positions = **Advantage+ placements** (Meta optimise tout seul).

## Statuts à lire pour vérifier
- Campagne/Ad set : `status` + `effective_status` doivent être `PAUSED`.
- Ad : `effective_status` peut être `IN_PROCESS` (revue créative) tout en étant `PAUSED` — ne diffuse pas.
- Compte : `account_status` (1=actif, 2=désactivé), `disable_reason` (1=integrity policy).

## Locales utiles
- `6` = French (France). (GET `/search?type=adlocale&q=french` pour d'autres.)
