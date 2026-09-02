---
name: meta-campaign-launcher
description: Configure de A à Z des campagnes Meta Ads (Facebook/Instagram) pour un client directement via la Graph API — campagne(s) + ad sets + ciblage + créatives/ads, tout en PAUSED (prêt-au-départ, rien ne diffuse). Supporte 2 objectifs : LEADGEN (formulaire instantané Meta natif) ou CONVERSION (pixel + événement sur une landing/page perso). Lit le token Meta System User depuis la variable d'env META_ACCESS_TOKEN. Encode toutes les contraintes API réelles (DSA UE, bid_strategy, budget sharing, advantage_audience vs age, moyen de paiement, CGU lead ads, standard_enhancements obsolète) apprises en prod. Use when the user asks to "crée/setup une campagne Meta pour {client}", "lance les ads Meta de {client}", "configure le compte Ads {client}", "setup campagne lead-gen Meta", "campagne conversion Meta sur la landing", "mets les créas en campagne sur Meta", "déploie les ads sur le compte publicitaire". Trigger phrases : "campagne Meta", "setup compte Ads", "lancer les ads", "configurer campagne publicitaire", "Meta Ads campaign", "déployer campagne client".
---

# Meta Campaign Launcher

Skill qui **configure des campagnes Meta Ads de bout en bout via la Graph API**, pour un client, **directement sur son compte publicitaire**. Toute la structure (campagne → ad sets → ciblage → créatives → ads) est créée en **statut PAUSED** : prêt-au-départ, rien ne diffuse, rien ne dépense tant que l'humain n'active pas.

> Ce skill code les appels Graph API lui-même (curl / Python `urllib`). Il **ne dépend pas** de l'app pour créer les objets — il s'en sert uniquement pour récupérer le token. C'est la méthode validée en prod (juin 2026).

## 🎯 Deux modes

| Mode | Objectif Meta | Destination | Prérequis spécifiques |
|---|---|---|---|
| **LEADGEN** (défaut) | `OUTCOME_LEADS` | Formulaire instantané Meta natif (on-ad) | Page a accepté les **CGU Lead Ads** (action humaine, 1×/page) ; un lead form |
| **CONVERSION** | `OUTCOME_SALES` (ou `OUTCOME_LEADS` site) | Landing / page perso + pixel | **Pixel** installé sur la page + **événement** de conversion (ex. `Lead`, `Purchase`) |

Le user choisit le mode. En cas de doute, demander. Une agence de service (prod vidéo, conseil…) → souvent **LEADGEN**. Un produit avec tunnel d'achat / landing trackée → **CONVERSION**.

---

## 🚨 RÈGLES DURABLES — contraintes API réelles (apprises en prod, à respecter SUR CHAQUE RUN)

Ces erreurs ont toutes été rencontrées en vrai. Les anticiper évite des allers-retours.

### R1 — `is_adset_budget_sharing_enabled=false` à la création de campagne (si budget au niveau ad set)
Sans CBO, l'API exige ce champ. POST `/campaigns` avec `is_adset_budget_sharing_enabled=false`. (error_subcode 4834011 sinon.)

### R2 — `bid_strategy=LOWEST_COST_WITHOUT_CAP` obligatoire sur l'ad set
Si pas de bid amount, l'ad set exige une bid_strategy explicite. (error_subcode 2490487 sinon.)

### R3 — DSA UE obligatoire : `dsa_beneficiary` + `dsa_payor` sur l'ad set
Toute pub ciblant l'UE exige le bénéficiaire ET le payeur (= nom légal du client). (error_subcode 3858081 sinon.)

### R4 — Advantage+ Audience force `age_max >= 65`
Si `targeting.targeting_automation.advantage_audience=1`, impossible de fixer age_max < 65. → Pour respecter un ciblage 25-60 strict, **ne PAS activer advantage_audience** (broad classique). (error_subcode 1870189 sinon.)

### R5 — Moyen de paiement OBLIGATOIRE pour créer une AD
`POST /ads` échoue (error_subcode 1359188 "Aucun moyen de paiement") si le compte n'a pas de `funding_source`. **Campagne/ad set/creative/lead form se créent sans paiement, mais PAS les ads.** Vérifier `funding_source` AVANT de tenter les ads. Le "draft sans payer" de l'Ads Manager web n'est PAS exposé par l'API → pas de contournement API.

### R6 — `standard_enhancements` (degrees_of_freedom_spec) est OBSOLÈTE
Ne plus envoyer `degrees_of_freedom_spec.creative_features_spec.standard_enhancements`. (error_subcode 3858504 sinon.) Laisser Meta gérer, ou utiliser les feature flags individuels si vraiment besoin.

### R7 — CGU Lead Ads = action HUMAINE (mode LEADGEN)
La Page doit avoir accepté les Conditions de Service Lead Ads. **Non automatisable par token** (`leadgen_tos_accepted` se vérifie en lecture mais s'accepte uniquement via l'UID admin sur `https://www.facebook.com/ads/leadgen/tos?page_id=<PAGE_ID>`). Si `leadgen_tos_accepted:false` → STOP, demander au user de l'accepter, puis reprendre.

### R8 — Lead form : `privacy_policy` obligatoire à la création
Impossible de créer un leadgen_form sans URL de politique de confidentialité (error_subcode 1892075). Si pas d'URL RGPD réelle → utiliser la home du site comme provisoire ET le signaler au user pour correction avant activation. Le form se crée en `status:ACTIVE` (utilisable) mais ne diffuse que via une ad publiée.

### R9 — DCO (Dynamic Creative) : max 10 images par asset_feed_spec
`is_dynamic_creative=true` est un champ de l'**AD SET** (pas de l'ad). L'asset_feed_spec accepte ≤ 10 images. Au-delà → créer des ads dédiées par placement (voir § Placements).

### R10 — Compte peut être SUSPENDU par Meta à tout moment
`account_status=2` + `disable_reason=1` (ADS_INTEGRITY_POLICY) = compte désactivé → toute écriture bloquée (error_subcode 1885316). Fréquent sur comptes neufs. La lecture reste OK. Action user : demande de révision dans Business Manager → Qualité du compte. Vérifier `account_status` au début ET re-vérifier si une écriture échoue soudainement.

### R11 — `daily_budget` en CENTIMES
15 € → `daily_budget=1500`.

### R12 — Tout PAUSED par défaut
Campagne, ad sets, ads : `status=PAUSED`. **Ne jamais activer** sans demande explicite. Aucune action destructive (pas de DELETE/archivage sans go ciblé).

---

## 🔑 Récupération du token Meta (via Vercel)

Le token est un **System User token** (non-expirant, scopes `ads_management`+`pages_manage_ads`+`leads_retrieval`+`business_management`), stocké comme `META_ACCESS_TOKEN` dans les env de prod du projet **app**.

```bash
mkdir -p /tmp/meta-env && cd /tmp/meta-env
vercel link --yes --project <ton-projet-vercel> --scope <ton-scope-vercel>
vercel env pull .env.prod.pulled --environment=production --yes
TOKEN=$(grep '^META_ACCESS_TOKEN=' .env.prod.pulled | sed -E 's/^META_ACCESS_TOKEN=//; s/^"//; s/"$//')
# autres clés utiles présentes : FB_APP_ID, FB_APP_SECRET, META_GRAPH_VERSION, META_REDIRECT_URI, APP_ENCRYPTION_KEY
```

Vérifier le token (scopes + validité) avec `debug_token` :
```bash
APPID=$(grep '^FB_APP_ID=' .env.prod.pulled | sed -E 's/^FB_APP_ID=//; s/"//g')
APPSEC=$(grep '^FB_APP_SECRET=' .env.prod.pulled | sed -E 's/^FB_APP_SECRET=//; s/"//g')
curl -s "https://graph.facebook.com/v21.0/debug_token?input_token=$TOKEN&access_token=$APPID|$APPSEC" | python3 -m json.tool
```

> Si `vercel env pull` n'expose pas META_ACCESS_TOKEN, fallback : variable d'env `META_ACCESS_TOKEN` fournie par tes soins. Ne jamais imprimer le token en clair dans un chat.

---

## 🔁 Pipeline — 7 phases

```
A. Token + identité      → pull token, debug_token, confirmer scopes ads_management
B. Pré-vol compte/page   → account_status, funding_source, page accessible, (leadgen_tos / pixel selon mode)
C. Form ou Pixel         → LEADGEN: lead form (réutiliser si existe) · CONVERSION: résoudre pixel_id + event
D. Campagne(s)           → OUTCOME_LEADS / OUTCOME_SALES, PAUSED, is_adset_budget_sharing_enabled=false
E. Ad sets               → broad / intérêts, budget, optim, DSA, destination, promoted_object
F. Créatives + ads       → DCO (≤10 img) OU ads dédiées par placement ; PAUSED
G. Vérif + récap         → relire account_status + statuts ; livrer un récap JSON des IDs
```

### Phase A — Token + identité
Pull token (ci-dessus), `debug_token`, confirmer `ads_management` + (mode LEADGEN) `leads_retrieval` + `pages_manage_ads`.

### Phase B — Pré-vol (NON destructif, lecture seule)
```bash
ACT=act_<AD_ACCOUNT_ID>; GV=v21.0
# compte : statut + devise + paiement
curl -s "https://graph.facebook.com/$GV/$ACT?fields=name,account_status,disable_reason,currency,funding_source&access_token=$TOKEN"
# account_status doit = 1 (actif). Si 2 → STOP (R10). funding_source présent → ads possibles (R5).
# page identité
curl -s "https://graph.facebook.com/$GV/<PAGE_ID>?fields=name&access_token=$TOKEN"
# page token (pour leadgen)
PT=$(curl -s "https://graph.facebook.com/$GV/<PAGE_ID>?fields=access_token&access_token=$TOKEN" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))")
# mode LEADGEN : CGU lead ads (R7)
curl -s "https://graph.facebook.com/$GV/<PAGE_ID>?fields=leadgen_tos_accepted&access_token=$TOKEN"
# mode CONVERSION : pixels du compte
curl -s "https://graph.facebook.com/$GV/$ACT/adspixels?fields=id,name&access_token=$TOKEN"
```
Si un prérequis manque (compte désactivé, pas de paiement, CGU non acceptées, pas de pixel) → **documenter + demander l'action humaine**, ne pas forcer.

### Phase C — Form (LEADGEN) ou Pixel (CONVERSION)
- **LEADGEN** : réutiliser un lead form existant (`GET /<PAGE_ID>/leadgen_forms`) ou en créer un avec `scripts/create_lead_form.py`. Respecter R8 (privacy_policy). Questions de qualif optionnelles selon le brief client.
- **CONVERSION** : résoudre le `pixel_id` + l'`event` (ex. `Lead`, `Purchase`, `CompleteRegistration`). Le `promoted_object` de l'ad set sera `{"pixel_id":..., "custom_event_type":"LEAD"}` et la landing = l'URL trackée.

### Phase D — Campagne(s)
`scripts/create_campaign.py`. Objectif selon mode. PAUSED. R1.
Souvent : **plusieurs campagnes** (ex. 1 Broad + 1 Intérêts) pour comparer le ciblage à budget égal.

### Phase E — Ad sets
`scripts/create_adset.py`. R2 + R3 + R4 + R11. `destination_type=ON_AD` (leadgen) ou site (conversion). `promoted_object` = page (leadgen) ou pixel+event (conversion). Targeting FR/age/locales ; intérêts via `GET /search?type=adinterest&q=...`.

### Phase F — Créatives + ads
Deux stratégies (cf. R9) :
- **DCO** : `is_dynamic_creative=true` sur l'ad set + 1 ad avec `asset_feed_spec` (≤10 images, plusieurs bodies/titles/descriptions, CTA SIGN_UP+form OU lien+pixel).
- **Ads dédiées par placement** : ad sets séparés par groupe de placement (Feed `facebook_positions=["feed"]`+`instagram_positions=["stream","explore"]` ; Stories/Reels `facebook_positions=["story","facebook_reels"]`+`instagram_positions=["story","reels"]`), 1 ad par créa au bon ratio. Meilleur contrôle, exploite >10 visuels.
Upload des visuels : `POST /$ACT/adimages` (multipart) → récupérer le `hash`. `scripts/upload_images.py`.

### Phase G — Vérif + récap
Re-lire `account_status` + statuts des objets créés. Livrer un **récap JSON** : campaign_ids, adset_ids, ad_ids, form_id/pixel_id, erreurs, + les **points à finaliser par l'humain** (URL privacy réelle, activation, révision compte si suspendu).

---

## 🗂️ Structure du skill
```
meta-campaign-launcher/
├── SKILL.md                      ← ce fichier
├── references/
│   └── graph-api-cheatsheet.md   ← endpoints, champs, erreurs subcode → fix, IDs de placement
└── scripts/
    ├── pull_token.sh             ← vercel env pull + extraction META_ACCESS_TOKEN (masqué)
    ├── preflight.py              ← Phase B : account_status, funding, page, tos/pixel → GO/NO-GO
    ├── create_campaign.py        ← Phase D
    ├── create_adset.py           ← Phase E (leadgen | conversion, broad | intérêts)
    ├── create_lead_form.py       ← Phase C leadgen
    ├── upload_images.py          ← Phase F upload visuels → hash
    └── create_ads.py             ← Phase F ads (DCO | dédiées par placement)
```

---

## 🛡️ Garde-fous
| Garde-fou | Enforcement |
|---|---|
| Pré-vol avant toute écriture | Phase B — STOP si account_status≠1 / pas de paiement / CGU non acceptées |
| Tout en PAUSED | `status=PAUSED` partout (R12) ; ne jamais activer sans go |
| Aucune action destructive | pas de DELETE/archivage sans go ciblé ; réutiliser les objets existants |
| Token jamais imprimé | scripts affichent "token chargé ✅", pas la valeur |
| Coût/diffusion = humain | l'activation et l'ajout de moyen de paiement restent côté user |
| Sous-agent en parallèle | pour un setup long (multi-campagnes/placements), déléguer à un sous-agent avec ce SKILL.md en contexte |

## 🔗 Amont / aval
- **Amont** : `creative-statics-v2` (les créas), `meta-ads-copywriter` (le copy), la proposition de campagne validée par le client.
- **Aval** : suivi des leads (webhook leadgen natif de l'app → CRM), reporting (insights API).

*Skill né d'un setup réel (juin 2026). Toutes les règles R1-R12 viennent d'erreurs API rencontrées en prod. Toujours PAUSED, jamais destructif, toujours re-vérifier account_status.*
