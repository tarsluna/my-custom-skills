---
name: meta-lead-notifications
description: Notifie un channel Slack à chaque NOUVEAU lead d'un formulaire Meta Lead Ads (Instant Form), pour un client de ton agence. Poller autonome (launchd sur macOS, ou cron) qui interroge l'API Meta Graph `/{form_id}/leads`, garde un état des leads déjà vus, et poste les nouveaux via Slack `chat.postMessage`. Pas d'email, pas de déploiement, pas de webhook à héberger. Prérequis : un token Meta System User (scope `leads_retrieval`), un token Slack bot `chat:write`, le `page_id` et le(s) `form_id`. Extensions optionnelles en references/ (push CRM par webhook, mail, variante webhook temps réel, injection dans un quiz funnel). Use when the user asks to "setup les notifications de leads", "notif Slack à chaque lead", "préviens-moi quand il y a un nouveau lead Meta", "lead notifications", "alerte nouveau lead dans le channel".
---

# Lead Notifications (Meta → Slack)

Poste un message Slack dès qu'un nouveau lead tombe dans un formulaire **Meta Lead Ads**. Approche **polling** (pas de webhook hébergé) : un agent launchd (ou un cron) lance le script toutes les ~3 min.

## Pourquoi le polling (et pas le webhook)
Le webhook `leadgen` de Meta suppose que la Page du client soit abonnée à TON app Meta (+ une app validée, un endpoint public, un handshake). Le poller marche **inconditionnellement** dès qu'on a le token System User (lecture `/{form_id}/leads`) + un token Slack `chat:write`. C'est le pattern « agent launchd » standard : zéro infra. Latence : l'intervalle (180 s par défaut).
Si tu as besoin du temps réel, la variante webhook est décrite dans `references/setup-meta-instant-form.md`.

## Pré-requis
1. **Token Meta System User** (non-expirant, scope `leads_retrieval` + `pages_manage_ads`) — créé dans Business Manager → Paramètres → Utilisateurs système (voir `references/ids-cheatsheet.md`). Si ton app l'a déjà en variable d'env (ex. `META_ACCESS_TOKEN` d'un projet Vercel : `vercel env pull`), le réutiliser. Sert à obtenir le **page token** (`GET /{page_id}?fields=access_token`).
2. **Token Slack** `chat:write` (workspace du client) + le **bot doit être membre du channel** (sinon `not_in_channel`). Vérifier : `auth.test`, `conversations.info?channel=…` → `is_member:true`.
3. **form_id(s)** du/des formulaire(s) de la campagne + **page_id** (méthodes de récupération dans `references/ids-cheatsheet.md`).

## Setup (4 étapes)
1. **Secrets durables** (chmod 600) dans `~/.config/meta-lead-notifications/<client>.env` (copier `.env.example`) :
   ```
   META_ACCESS_TOKEN=...    SLACK_TOKEN=xoxb-...    SLACK_CHANNEL=Cxxxxxxxx
   PAGE_ID=...              FORM_IDS=form1,form2    CLIENT_NAME="Acme Fermetures"
   STATE_FILE=~/.local/state/meta-lead-notifications/<client>/seen-leads.json
   ```
   (Si le token Meta vient d'un `vercel env pull`, il atterrit dans un fichier temporaire → le copier dans le fichier secrets pour survivre au reboot.)
2. **Valider** : `python3 scripts/poll_and_notify.py --env <secrets> --test` → message de test dans le channel.
3. **Seed** : premier run normal marque les leads existants comme « vus » SANS notifier (anti-spam historique). Forcer l'historique avec `--notify-existing`.
4. **launchd** (macOS) : copier `templates/launchd-notif.plist.template`, remplacer les placeholders `{{CLIENT}}`, `{{SKILL_DIR}}`, `{{ENV_FILE}}`, `{{STATE_DIR}}`, → `~/Library/LaunchAgents/com.lead-notif.<client>.plist`, puis `launchctl load`. `StartInterval=180`, `RunAtLoad=true`.
   Sur Linux : une ligne cron `*/3 * * * * python3 <skill>/scripts/poll_and_notify.py --env <secrets>` fait le même travail.

## scripts/poll_and_notify.py
- `--env <file>` charge les secrets · `--test` envoie 1 message et sort · `--seed` re-marque l'existant comme vu · `--notify-existing` notifie aussi l'historique.
- Idempotent via `STATE_FILE` (set de `leadgen_id`). Fire-safe : une erreur Slack n'efface pas l'état du lead non-notifié (il sera retenté au run suivant).
- Mappe les clés de question connues (full_name/email/phone_number/company_name + qualif) → libellés FR ; toute clé inconnue est dumpée telle quelle. Adapter le dict `LABELS` aux clés de question de ton formulaire.
- `CLIENT_NAME` (env) sert d'en-tête du message Slack.

## scripts/slack_watch_ghl_key.py (annexe)
Utilitaire indépendant : surveille un channel Slack et détecte l'envoi d'une clé API GoHighLevel (JWT v1 ou `pit-…` v2) par le client, pour enchaîner un branchement CRM sans relance manuelle. Env : `SLACK_TOKEN`, `SLACK_WATCH_CHANNEL`, `GHL_WATCH_STATE`, `GHL_KEY_OUT`.

## Garde-fous
- Token jamais imprimé. Secrets en chmod 600.
- Premier run = seed silencieux (jamais de spam de l'historique).
- Si `chat.postMessage` renvoie `not_in_channel` → inviter le bot dans le channel (action humaine), puis le run suivant rattrape.

## Extensions optionnelles (references/)
- `references/ids-cheatsheet.md` — où trouver CHAQUE identifiant (page_id, form_id, token System User, channel Slack, app Meta…).
- `references/crm-webhook.md` — pousser aussi le lead dans ton CRM via un webhook générique (contrat + payload + dédup).
- `references/email-notification.md` — prévenir le client par mail (natif CRM vs SMTP custom).
- `references/setup-meta-instant-form.md` — variante webhook temps réel (récepteur `leadgen` hébergé).
- `references/setup-quiz-funnel.md` — le client a un quiz funnel maison : injecter la notif dans son backend.

## Fiche d'instance (à tenir par client)
- **<CLIENT>** (date de mise en service) : channel `<SLACK_CHANNEL_ID>` (#nom-du-channel), forms `<FORM_ID_1>`+`<FORM_ID_2>`, page `<PAGE_ID>`. Secrets `~/.config/meta-lead-notifications/<client>.env`. Agent `com.lead-notif.<client>` (180 s). Logs dans `<STATE_DIR>/notif.log`.
