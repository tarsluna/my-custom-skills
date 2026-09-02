# Notification par mail

**Toujours proposer la notif mail au client.** Mais distinguer 2 cas — souvent le natif suffit.

## Cas 1 — Mail natif du CRM (par défaut, RIEN à coder) ✅
Dès qu'un lead entre dans le CRM (via le webhook d'ingestion, cf. `crm-webhook.md`), la plupart des CRM
envoient **automatiquement** un mail « nouveau lead » au compte client.
- Destinataire : l'**email du compte client**.
- Expéditeur : le SMTP transactionnel du CRM (ex. `Ton CRM <noreply@your-crm.example>`).
- Contenu : récap du lead + lien vers la fiche CRM.
- **Respecte les préférences** du compte : ne s'envoie pas si le client a désactivé les notifs
  nouveau lead / par email. Vérifier aussi que les leads de scraping/gmaps sont exclus si ton CRM les ingère.

→ Pour (dés)activer pour un client : basculer les deux flags de préférence du compte
(ex. `notify_new_lead`, `notify_new_lead_email`) dans l'UI du CRM ou par un UPDATE ciblé.

**Conséquence importante :** si le client veut juste « être prévenu par mail à chaque lead » sur
l'adresse de son compte, il n'y a **rien d'autre à faire** que de vérifier que les flags sont à
`true`. Le push CRM déclenche le mail.

## Cas 2 — Mail vers une AUTRE adresse (custom)
Si le client veut notifier une boîte **différente** de son compte (ex: `leads@client.example`, ou
une équipe commerciale), ajouter une fonction `notifyEmail()` dans le module de notification du
backend (le même `notify.js` qui fait Slack + CRM, cf. `setup-quiz-funnel.md`), pilotée par :
- `NOTIFY_EMAIL_TO` = adresse(s) destinataire(s)
- `SMTP_HOST/PORT/USER/PASS/FROM/SECURE` = mêmes valeurs que ton CRM/app (pull depuis l'env)
- `npm i nodemailer` dans le backend qui envoie.

Règle : la fonction ne s'active que si `NOTIFY_EMAIL_TO` + `SMTP_HOST` sont présents (sinon no-op),
et elle est appelée en fire-and-forget (`Promise.allSettled`) pour ne jamais bloquer la réponse HTTP.

## Quel cas choisir ?
| Demande du client | Solution |
|---|---|
| « Préviens-moi par mail » (son adresse) | Cas 1 — vérifier flags `notify_new_lead*` = true |
| « Envoie aussi à mon commercial / une boîte dédiée » | Cas 2 — `NOTIFY_EMAIL_TO` + SMTP |
| « Pas de mail, juste Slack » | Cas 1 — flags à `off` |
