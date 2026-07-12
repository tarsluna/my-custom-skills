# Métriques & Insights API — référence

## Requête de base (ad-level)
```
GET https://graph.facebook.com/v21.0/act_{AD_ACCOUNT_ID}/insights
  ?level=ad
  &fields=ad_id,ad_name,adset_id,campaign_id,spend,impressions,reach,frequency,
    clicks,ctr,cpc,cpm,actions,action_values,cost_per_action_type,
    inline_link_clicks,inline_link_click_ctr,cost_per_inline_link_click,outbound_clicks,
    video_play_actions,video_p25_watched_actions,video_p50_watched_actions,
    video_p75_watched_actions,video_p95_watched_actions,video_p100_watched_actions,
    video_thruplay_watched_actions,video_avg_time_watched_actions,
    quality_ranking,engagement_rate_ranking,conversion_rate_ranking
  &date_preset=last_14d&limit=500&access_token={TOKEN}
```
Pull 3 fenêtres : `last_3d`, `last_7d`, `last_14d` (ou `time_range`) pour comparer récent vs baseline.

## Relier une ad à sa créa (2 appels — `creative_id` ABSENT des insights)
1. `GET /{ad_id}?fields=id,name,creative{id}` (ou batch `?ids=ad1,ad2&fields=creative{...}`)
2. `GET /{creative_id}?fields=id,name,image_url,image_hash,thumbnail_url,video_id,object_story_spec,asset_feed_spec,call_to_action_type,body,title`
   - `video_id` présent → créa vidéo → appliquer hook/hold.
   - `image_url`/`thumbnail_url` → l'asset visuel. `object_story_spec`/`asset_feed_spec` → la copy.

## Parsing — `actions[]` et `cost_per_action_type[]` sont des TABLEAUX d'objets `{action_type, value}`, pas des scalaires
- Lead : `action_type` ∈ {`lead`, `offsite_conversion.fb_pixel_lead`, `onsite_conversion.lead_grouped`}
- Link click : `link_click` ; Purchase : `offsite_conversion.fb_pixel_purchase` / `purchase`
- Toujours extraire `.value` du 1er élément (ex `video_p25_watched_actions[0].value`).
- CPL fiable : recalculer `spend / leads` soi-même (évite les doublons d'attribution du `cost_per_action_type`).

## Formules créatives
```
hook_rate       = video_3s_views / impressions          # 3s = video_play_actions[] ou action_type 'video_view'
hold_rate       = video_thruplay_watched_actions / video_3s_views
completion_rate = video_p100_watched_actions / video_play_actions
CTR (link)      = inline_link_clicks / impressions       # PAS le ctr brut (compte like/expand)
CPC (link)      = spend / inline_link_clicks
CVR             = leads / inline_link_clicks              # ou leads / landing_page_views
CPL             = spend / leads
CPM             = spend / impressions * 1000
frequency       = champ `frequency` (déjà fourni, sur la fenêtre)
```

## Benchmarks (défauts — surcharger par secteur/mandat)
| Métrique | Faible | OK | Fort |
|---|---|---|---|
| Hook rate (3s/impr) | <20-25% | 25-35% | >35% |
| Hold rate (thruplay/3s) | <30% | 40-50% | >50% |
| CTR link (cold B2B) | <0.6% | 0.6-1.0% | >1.2% |
| Frequency cold (7j) | — | <2.5 | (>3 = fatigue) |
| CVR Instant Form | <8% | 10-15% | >15% |
| CPL lead-gen Meta 2025 | — | ~27.66$ moyen | <cible |

CPL B2B réel : services pro 25-80$, consulting/high-ticket 100-315$+ (un lead instant-form ≠ MQL).
Rankings Meta (`quality_ranking`, `engagement_rate_ranking`, `conversion_rate_ranking`) : `below_average` sur ≥2 axes = signal de créa faible.

## Learning phase
- Sortie : ~50 events d'optimisation / **7 jours glissants** / **ad set** (10 pour Purchase/App Install). Lire `effective_status` / learning stage avant toute action.

## Date / fenêtres
- Attribution par défaut : 7-day click / 1-day view → ne pas juger `0 conversion` sur < 7j.
- Exclure le jour courant (incomplet) ; raisonner sur jours clôturés, fuseau du compte.
