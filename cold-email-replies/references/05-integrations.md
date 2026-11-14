# Brancher le livrable, Slack, le CRM et la réservation

Toutes les sorties sont des appels HTTP simples, configurés par variables d'environnement. Une sortie non configurée est sautée sans bloquer le reste.

## Le livrable offert

`deliverable.mode` dans la configuration.

### `static` : un même lien pour tous

Un guide, une vidéo, une page de démonstration. `deliverable.static_url` est envoyé tel quel, tout de suite. Pas besoin de domaine : un « oui » depuis une adresse Gmail est servi aussi.

### `webhook` : un livrable fabriqué pour chaque prospect

Votre générateur (audit, maquette, estimation…) expose deux routes. `DELIVERABLE_API_URL` pointe sur la première ; `DELIVERABLE_API_KEY`, facultatif, part dans l'en-tête `x-api-key`.

```http
POST {DELIVERABLE_API_URL}
idempotency-key: <identifiant local du livrable>
{"key": "jardins-martin.example", "domain": "jardins-martin.example", "email": "…", "first_name": "…",
 "last_name": "…", "company_name": "…", "source": "cold_email_reply"}

200 {"id": "abc123", "status": "queued"}            # ou "ready" avec "url", ou "failed"
```

```http
GET {DELIVERABLE_API_URL}/abc123
200 {"id": "abc123", "status": "ready", "url": "https://audit.example.com/r/abc123", "company_name": "Jardins Martin"}
```

- `status` : `queued`, `ready` ou `failed`. Toute autre forme est une erreur.
- `url` doit être un lien public `https://…`. Un livrable « prêt » sans lien valable passe en échec, sans réponse.
- `company_name` facultatif : le nom propre de l'entreprise si votre générateur l'a trouvé (sur son site, par exemple). L'agent le préfère au nom saisi dans la liste, sauf s'il est tout en capitales.
- L'agent interroge le `GET` à chaque sonde tant que le livrable n'est pas prêt, et abandonne avec une alerte après `deliverable.stuck_hours`.

**Réutilisation.** Un livrable existe déjà pour ce domaine depuis moins de `deliverable.reuse_days` jours : il est réutilisé, sans compter dans le plafond.

**Plafond.** `deliverable.max_per_day` livrables neufs par jour (fuseau `timezone`). Au-delà, les « oui » attendent le lendemain, avec une seule alerte par jour.

**Domaine.** Le champ site du contact d'abord, sinon le domaine de son adresse s'il est professionnel. Jamais le texte de la réponse. Les messageries grand public (`consumer_mailboxes`) ne donnent pas de domaine, quelle que soit l'extension.

## Slack

Créez un webhook entrant sur le canal de l'équipe et mettez son URL dans `SLACK_WEBHOOK_URL`. Sans lui, les alertes s'affichent sur la sortie d'erreur.

| Alerte | Quand |
| --- | --- |
| `NOUVEAU LEAD` | Dès qu'un oui ou une demande de rendez-vous est classé, avant le livrable |
| `NOUVEAU LEAD · à traiter à la main` | Oui impossible à servir seul : pas de domaine, contact déjà désinscrit, pas d'identifiant de fil |
| `audit envoyé` | La réponse est confirmée par l'outil, avec le lien du livrable et celui de la réservation |
| `Question d'un prospect`, `Réponse à lire`, `Réponse non classée` | Aucune réponse automatique, à traiter à la main |
| `Désinscription à vérifier` | Un « non » exécuté malgré une confiance faible |
| `Envoi refusé…`, `Envoi au résultat inconnu`, `Envoi interrompu…` | Ne pas relancer : vérifier le fil, répondre à la main |
| `Livrable en échec`, `Livrable toujours pas prêt…`, `Envoi annulé` | Rien n'est parti |
| `Plafond…`, `Réponses illisibles…` | Une fois par jour au plus |

Les titres `NOUVEAU LEAD` et `audit envoyé` se changent dans `alerts`. Le texte du prospect est échappé : un `<!channel>` glissé dans une réponse ne prévient pas tout le canal.

## CRM

`CRM_WEBHOOK_URL` reçoit un `POST` JSON par événement. `CRM_WEBHOOK_SECRET`, facultatif, part dans `x-webhook-secret`. L'en-tête `idempotency-key` permet d'ignorer un événement reçu deux fois.

```json
{
  "event": "deliverable_sent",
  "stage": "Audit envoyé",
  "email": "camille.martin@jardins-martin.example",
  "first_name": "Camille", "last_name": "Martin", "company_name": "Jardins Martin",
  "website": "https://www.jardins-martin.example", "domain": "jardins-martin.example",
  "campaign_id": "101", "lead_id": "5001",
  "reply_excerpt": "Ok, envoyez-moi ça.",
  "deliverable_url": "https://audit.example.com/r/jardins-martin",
  "booking_url": "https://cal.example.com/canopee/audit-offert-30-min",
  "occurred_at": "2026-03-10T10:11:00.000000Z"
}
```

| Événement | Étape (`crm.stages`) | Quand |
| --- | --- | --- |
| `new_lead` | `null` par défaut (pas d'envoi) | Oui classé |
| `deliverable_sent` | `Audit envoyé` | Réponse confirmée |
| `booked` | `Appel booké` | `--booked EMAIL` |

Mettez une étape à `null` pour ne pas envoyer l'événement. Un CRM injoignable garde l'événement en file : il repart à la sonde suivante, dans l'ordre.

Pas de webhook ? Zapier, Make ou n8n reçoivent ce JSON et créent la fiche dans HubSpot, Pipedrive, Notion ou un tableur.

## La réservation

`booking_url` (configuration) ou `BOOKING_URL` (environnement) : le lien mis dans la réponse. Utilisez un événement dédié au cold email (Calendly, Cal.com…) pour savoir d'où vient chaque rendez-vous.

Quand un prospect réserve, faites appeler `--booked EMAIL` par votre automatisation de réservation **avant** qu'elle n'envoie un livrable de son côté (voir le piège n° 2 dans [04-pitfalls.md](04-pitfalls.md)).

Sans lien de réservation, la phrase qui le propose disparaît du mail, et un avertissement s'affiche au démarrage.

## Héberger la boucle

- **Un processus** : `python3 scripts/run.py --loop` sur une machine ou un service de type worker. Mettez la base SQLite sur un disque persistant.
- **Un cron** : `*/3 * * * * cd /chemin/du/skill && python3 scripts/run.py --once`. Le verrou en base empêche deux sondes de se chevaucher.
- **Interrupteur** : `REPLY_AGENT_ENABLED` absent ou à `0`, l'agent refuse de démarrer et ne fait strictement rien.
