# Cheatsheet — Où trouver TOUS les identifiants

Aucune valeur réelle ici : uniquement la **méthode** pour retrouver chaque ID/secret. Une fois trouvés, ils vont dans le fichier secrets du client (`.env.example` à la racine du skill), jamais dans le skill.

## Si ton agence a déjà une app Meta / un backend
Source unique de la majorité des secrets : **l'env de prod de ton app** (ex. projet Vercel : `vercel env pull /tmp/.env.prod.pulled` depuis le repo, puis lire les variables ci-dessous). Ne pas travailler depuis un vieux backup du repo : les variables webhook/token peuvent y manquer.

| Élément | Où le trouver dans ton propre code (à adapter) |
|---|---|
| Endpoint d'ingestion CRM | la route HTTP qui accepte un lead externe (souvent `/api/integrations/webhook/[token]`) |
| Logique d'ingestion + mapping | le module qui normalise `name/email/phone/company` → table `leads` |
| Mail auto natif au lead | le module d'email « nouveau lead » + son transport SMTP |
| Meta Lead Ads (fetch lead) | le module qui fait Page token → `leadgen_forms` → `leads` |

## Secrets & valeurs — comment les obtenir
| Quoi | Variable | Où la trouver |
|---|---|---|
| Token Meta System User | `META_ACCESS_TOKEN` | Business Manager → Paramètres → **Utilisateurs système** → créer/choisir un System User (rôle admin) → « Générer un token » → cocher `leads_retrieval`, `pages_manage_ads`, `pages_read_engagement`, `pages_show_list` → **ne jamais expirer**. Attribuer la Page du client à ce System User (Actifs → Pages). |
| Page ID | `PAGE_ID` | Page Facebook → À propos → « ID de la Page » ; ou `GET /me/accounts?access_token=<System User token>` (liste `id`, `name`, `access_token` par Page). |
| Form ID(s) | `FORM_IDS` | Ads Manager → colonne « Formulaire » de l'annonce ; ou **Meta Business Suite → Outils de publication → Formulaires Instant Forms** (l'ID est dans l'URL) ; ou `GET /{page_id}/leadgen_forms?access_token=<page token>` (`id`, `name`, `status`). |
| Page Access Token | (dérivé) | `GET /{page_id}?fields=access_token&access_token=<System User token>` — c'est ce que fait `poll_and_notify.py`. |
| Meta verify (webhook) | `META_VERIFY_TOKEN` | Chaîne arbitraire que TU choisis ; doit être identique côté app Meta (Webhooks) et côté récepteur. |
| Meta app | `FB_APP_ID`, `FB_APP_SECRET` | developers.facebook.com → ton app → Paramètres → Général. Nécessaire uniquement pour la variante webhook. |
| Version Graph | `META_GRAPH_VERSION` | ex. `v21.0` — prendre la dernière stable listée dans le changelog Graph API. |
| SMTP (mail custom) | `SMTP_HOST/PORT/SECURE/USER/PASS/FROM` | Ton fournisseur transactionnel (AWS SES : `email-smtp.<region>.amazonaws.com:587`, `SMTP_SECURE=false` ; ou Brevo, Postmark…). |

## Slack (PAS dans l'env de l'app)
- **Token** : api.slack.com/apps → ton app → OAuth & Permissions → Bot Token Scopes `chat:write` (+ `channels:read`, `channels:history` pour `slack_watch_ghl_key.py`) → Install to Workspace → `xoxb-…`. Un token par workspace client (ou un token user partagé si ton agence gère tout depuis un seul workspace).
- **Stockage** : HORS de tout repo — un fichier secrets chmod 600 ou ton gestionnaire de mots de passe, puis `export SLACK_TOKEN=…`.
- **Channel ID** (`Cxxxxxxxx`) : Slack → clic droit sur le channel → « Voir les détails » → l'ID est en bas ; ou `conversations.list`. Inviter le bot dedans (`/invite @bot`) sinon `not_in_channel`.
- Tenir une table `client → channel ID → nom du channel` dans la fiche d'instance du SKILL.md.

## Railway (CLI) — uniquement pour les variantes webhook / quiz funnel
- Installer la CLI officielle à jour (`npm i -g @railway/cli`) ; une vieille version peut renvoyer `Unauthorized`. `railway whoami` pour vérifier le compte.
- ⚠️ Services NON liés GitHub (`railway status --json` → `source.repo: null`) → déployer via `railway up`, pas `variables --set` seul (voir `setup-quiz-funnel.md`).
