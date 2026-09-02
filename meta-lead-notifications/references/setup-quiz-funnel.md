# Setup A — Quiz Funnel

Le client a un quiz funnel maison dont le **backend reçoit déjà chaque lead** (typiquement un
Express sur Railway avec une route `POST /api/lead`). On injecte les
notifications dans ce backend, au point où le lead est confirmé.

> Le module `notify.js` ci-dessous = ta fonction de notification : `buildLead()` normalise le lead,
> `notifyNewLead()` fait en parallèle Slack `chat.postMessage` + POST `CRM_WEBHOOK_URL` (+ mail si
> configuré, cf. `email-notification.md`), en `Promise.allSettled`. Le même module sert à la variante
> webhook (`setup-meta-instant-form.md`).

## Étapes

### 1. Localiser le backend + la route lead
Trouver le handler qui reçoit le lead final (`grep -rn "api/lead\|/lead" src`). Identifier :
- les champs disponibles (firstName, email, phone, réponses du quiz, traffic/UTM) ;
- un identifiant unique de session pour la dédup (`session_id`).

### 2. Ajouter le module notify.js
```bash
cp notify.js <backend>/src/notify.js     # ton module réutilisable d'un client à l'autre
```
Adapter `buildSlackText()` aux libellés du quiz si le backend a une config de labels
(réutiliser une fonction type `optionLabel(qid, value)` si elle existe → libellés lisibles).
Remplir `extra` avec les champs métier (type de bien, zone, estimation…).

### 3. Brancher dans la route lead (fire-and-forget + idempotence)
```js
import { buildLead, notifyNewLead } from './notify.js';

// Dans POST /api/lead, AVANT d'écrire le lead : vérifier s'il est déjà capturé
let alreadyCaptured = false;
try {
  const prev = await getSessionEvents(id);            // ou équivalent
  alreadyCaptured = prev.some((e) => e.type === 'lead_captured');
} catch {}

// ... upsert du lead + logEvent('lead_captured') ...

res.json({ ok: true, id });                            // répondre AVANT
if (!alreadyCaptured) {
  void notifyNewLead(buildLead({
    id, firstName: b.firstName, lastName: b.lastName, email: b.email, phone: b.phone,
    source: 'quiz_funnel', traffic: b.traffic,
    extra: { /* champs métier lisibles */ },
  }));
}
```
Le `void` + `Promise.allSettled` interne garantit que rien ne bloque ni ne casse la réponse.

### 4. Variables d'env Railway
```bash
cd <backend>
railway variables \
  --set "SLACK_TOKEN=<token bot>" \
  --set "SLACK_NOTIF_CHANNEL=<Cxxxxxxxx>" \
  --set "CRM_WEBHOOK_URL=<url d'ingestion, cf. crm-webhook.md>" \
  --set "NOTIFY_CLIENT_NAME=<Nom client>" \
  --service <service>
```

### 5. ⚠️ Déployer le CODE (railway up)
Si le service n'est pas lié à GitHub (`railway status --json` → `source.repo: null`), un
`variables --set` redéploie l'ANCIENNE image. Il FAUT uploader le code :
```bash
railway up --service <service> --detach
```
Attendre la fin du build (`railway status` jusqu'à `Online` sans `Building/Deploying`). Un
`Crashed` transitoire pendant le swap de conteneur est normal — vérifier `/health` + les logs
(`railway logs --service <service>` doit montrer le boot sans erreur d'import de notify.js).

### 6. Test e2e
POST un faux lead sur le `/api/lead` de prod → vérifier le message Slack + le lead CRM
(un `curl` sur `CRM_WEBHOOK_URL` avec le payload de `crm-webhook.md` pour tester la partie CRM seule, ou inspection directe). Nettoyer les leads de test.

> Le quiz front pointe en général déjà vers ce backend (`ADMIN_API`/`LEAD_WEBHOOK_URL` dans
> son `quiz.js`) → **rien à redéployer côté front**.
