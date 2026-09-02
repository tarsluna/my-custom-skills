# Setup B — Instant Form Meta (Lead Ads), variante webhook temps réel

> Alternative au polling du SKILL.md quand le client exige le temps réel. Plus d'infra : un récepteur HTTP public + une app Meta abonnée à la Page.

Les leads arrivent dans un formulaire natif Meta (Instant Form). Meta n'écrit nulle part chez
nous : il faut un **récepteur de webhook** qui s'abonne à l'event `leadgen`, récupère le lead
via la Graph API, puis Slack + CRM.

## Architecture
```
Lead remplit l'Instant Form
        │  (event leadgen)
        ▼
Récepteur webhook (petit service HTTP, ex. Express sur Railway)
   GET  /webhook/meta   → handshake hub.challenge (META_VERIFY_TOKEN)
   POST /webhook/meta   → { leadgen_id, page_id, form_id, ad_id }
        │  fetch GET /{leadgen_id}?fields=field_data  (Page Access Token)
        ▼
   notify.js → Slack + CRM (+ mail optionnel)
```
Le fetch du lead s'appuie sur le même flow que le poller :
**Page Access Token** (récupéré via `/me/accounts` ou `/{page_id}?fields=access_token`) car `/{leadgen_id}` l'exige.
Le module `notify.js` = ta fonction de notification (Slack `chat.postMessage` + POST `CRM_WEBHOOK_URL` + mail optionnel), la même que dans `setup-quiz-funnel.md`.

## Étapes

### 1. Déployer le récepteur sur Railway
```bash
mkdir /tmp/meta-webhook && cd /tmp/meta-webhook   # ton service : GET handshake + POST event + notify.js
railway init                   # nouveau projet, ex: "<client>-meta-webhook"
# (ou railway link si le projet existe déjà)
railway up --detach            # build + deploy ; récupérer l'URL publique
```

### 2. Variables d'env Railway
```bash
railway variables \
  --set "META_VERIFY_TOKEN=<chaîne arbitraire, identique côté app Meta>" \
  --set "META_ACCESS_TOKEN=<META_ACCESS_TOKEN System User>" \
  --set "META_GRAPH_VERSION=v21.0" \
  --set "SLACK_TOKEN=<token bot>" \
  --set "SLACK_NOTIF_CHANNEL=<Cxxxxxxxx>" \
  --set "CRM_WEBHOOK_URL=<url d'ingestion, cf. crm-webhook.md>" \
  --set "NOTIFY_CLIENT_NAME=<Nom client>"
railway up --detach   # re-déployer après les vars (service non lié GitHub)
```
> Réutiliser `META_VERIFY_TOKEN` / `META_ACCESS_TOKEN` d'une app Meta existante évite d'en recréer une.
> Le System User token doit avoir accès à la Page du client (sinon générer un Page token dédié).

### 3. Abonner l'app Meta + la Page au champ `leadgen`
Dans l'app Meta (`FB_APP_ID`) → **Webhooks** → objet **Page** :
- Callback URL : `https://<url-railway>/webhook/meta`
- Verify Token : la valeur `META_VERIFY_TOKEN`
- S'abonner au champ **`leadgen`**.

Puis abonner la **Page du client** à l'app (sinon aucun event n'arrive) :
```bash
# token = Page Access Token de la page
curl -X POST "https://graph.facebook.com/v21.0/<PAGE_ID>/subscribed_apps" \
  -d "subscribed_fields=leadgen" -d "access_token=<PAGE_TOKEN>"
```
Vérifier : `GET /<PAGE_ID>/subscribed_apps?access_token=<PAGE_TOKEN>` doit lister l'app avec `leadgen`.

### 4. Test e2e
Utiliser l'outil officiel **Meta Lead Ads Testing Tool**
(`https://developers.facebook.com/tools/lead-ads-testing`) : sélectionner la Page + le form,
"Create Lead" → l'event doit arriver sur `/webhook/meta`, et un message + un lead CRM apparaître.
Vérifier les logs Railway (`railway logs`) : `[meta-webhook] lead traité: <id>`. Nettoyer le lead test.

## Pièges
- **Page token vs User token** : `/{leadgen_id}` requiert un Page Access Token. Le récepteur le
  résout via `/me/accounts` ; si le System User n'a pas la Page, fournir un Page token direct.
- **Handshake 403** : `META_VERIFY_TOKEN` du service ≠ celui saisi dans l'app Meta.
- **Aucun event** : la Page n'est pas abonnée (`subscribed_apps`), ou l'app est en mode Dev.
- **Doublons** : géré en mémoire (`seen` Set) ; un restart du service peut reposter un vieux lead
  → la dédup CRM par `external_id` (= leadgen_id) rattrape côté CRM.
