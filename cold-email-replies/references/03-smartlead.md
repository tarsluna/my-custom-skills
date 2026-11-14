# L'outil d'envoi : Smartlead

L'agent n'utilise que cinq appels. Base : `https://server.smartlead.ai/api/v1`. La clé part dans l'URL (`?api_key=`), comme l'exige l'API : aucun message d'erreur de l'agent ne contient l'URL.

| Besoin | Appel | Notes |
| --- | --- | --- |
| Contacts qui ont répondu | `GET /campaigns/{id}/leads?emailStatus=is_replied&event_time_gt=…&limit=100&offset=…` | La doc montre `data[].lead` sur une page, `leads[]` à plat sur une autre : les deux sont lus. `lead_category_id` porte la classification native |
| Fil d'un contact | `GET /campaigns/{id}/leads/{lead_id}/message-history` | `history[]` (`type: REPLY`, `time`, `email_body`, `message_id`, `stats_id`) ou `messages[]` (`direction: inbound`, `received_at`, `body`) |
| Répondre dans le fil | `POST /campaigns/{id}/reply-email-thread` | `email_stats_id`, `email_body`, `add_signature: false`, `reply_email_time`, `reply_message_id`. Part de la boîte qui a envoyé la campagne |
| Désinscrire | `POST /leads/{lead_id}/unsubscribe` | De toutes les campagnes. `{ok: false}` veut dire « déjà fait » |
| Bloquer | `POST /leads/add-domain-block-list` | `{"domain_block_list": ["adresse@domaine"]}` : on bloque l'adresse, pas tout le domaine. Vérifiez une fois dans le compte qu'elle apparaît bien dans la liste |

## Lire sans deviner

Un message dont il manque l'identifiant, la date ou le corps est **compté**, jamais deviné. Il ne déclenche aucune réponse, le curseur de la campagne n'avance pas, et l'équipe reçoit une alerte par jour (« Réponses illisibles »). Traitez-les dans la boîte de Smartlead.

Le texte gardé est celui que le prospect a écrit : le fil cité est retiré (HTML et texte), les espaces sont resserrés.

## Interpréter l'envoi

| Réponse de l'API | Résultat | Suite |
| --- | --- | --- |
| 2xx, corps JSON sans `success: false` ni `ok: false` | envoyé | `answered`, alerte, CRM |
| 2xx, corps avec `success: false` ou `ok: false` | **refusé** | `send_failed`, alerte, réponse à la main |
| 2xx, corps illisible | incertain | `send_uncertain`, alerte, jamais renvoyé |
| 429 | limite de débit | retenté à la sonde suivante, rien n'est parti |
| 5xx, délai dépassé, connexion coupée | incertain | `send_uncertain`, alerte, jamais renvoyé |
| autre 4xx | refusé | `send_failed`, alerte |

Un 200 ne prouve rien tant que le corps n'a pas été lu. Au premier envoi réel, ouvrez le fil dans Smartlead et vérifiez que la réponse y est.

## Débit

Environ 60 requêtes par minute documentées. L'agent attend 1,1 s entre deux contacts (`smartlead.pace_seconds`). Une campagne qui reçoit beaucoup de réponses d'un coup est lue en plusieurs sondes : c'est normal.

## Planning de campagne

Une campagne réglée sur les jours ouvrés et les heures de bureau n'envoie rien le soir ni le week-end, et les réponses arrivent surtout pendant ces heures. Une soirée sans réponse ne dit rien de l'agent : regardez d'abord le planning de la campagne et `--status`.

## Plusieurs campagnes

`SMARTLEAD_CAMPAIGN_IDS=101,202`. Chaque campagne a son curseur. Tout ce qui n'est pas un numéro est ignoré.

## Autre outil d'envoi

Instantly, lemlist ou un autre outil : écrivez un client qui expose les mêmes cinq méthodes que `scripts/reply_agent/smartlead.py` (`list_replied_leads`, `fetch_replies`, `reply_in_thread`, `unsubscribe_lead`, `add_to_block_list`) et branchez-le dans `scripts/run.py`. Le reste de l'agent ne change pas.
