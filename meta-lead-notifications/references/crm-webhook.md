# CRM webhook — pousser un lead dans ton CRM

En plus de Slack, chaque lead peut être poussé dans ton CRM via un **endpoint d'ingestion HTTP** (webhook entrant). Beaucoup de CRM en exposent un nativement (ou via Zapier/Make/n8n) ; si tu as ta propre app, elle doit en exposer un. **Aucun code applicatif à écrire par client** : on génère juste une clé par client.

## L'endpoint (contrat attendu)
```
POST ${CRM_WEBHOOK_URL}      # ex. https://app.example.com/api/integrations/webhook/<clé>?provider=webhook
Content-Type: application/json
```

Ce que l'endpoint doit faire tout seul :
- **Auth** par une clé dans l'URL (ex. `lf_live_xxx`), liée à un `client_id`.
- **Mapping** générique : reconnaît `full_name|name|nom`, `firstName|prenom`, `email`, `phone|telephone|tel`, `company|entreprise`, `external_id|id|uid`. Tout le reste du JSON est conservé dans un champ libre (`field_data`).
- **Dédup** par hash du body + par `external_id` (par clé/client).
- **Insert** dans `leads` (`status: new`) + log d'audit.
- **Mail auto** au client (voir `email-notification.md`).
- Réponses : `200 {status:'accepted'|'duplicate', lead_id}` · `400` payload vide · `401` clé invalide · `429` rate limit (ex. 60/min/clé).

## Format de payload recommandé
```json
{
  "firstName": "Sophie",
  "email": "sophie@client.example",
  "phone": "+33 6 00 00 00 00",
  "company": "Acme",
  "external_id": "<id unique du lead, ex: session_id quiz ou leadgen_id Meta>",
  "source": "quiz_funnel",        // libre, atterrit dans field_data
  "<champ métier>": "<valeur>"     // ex: type_bien, localisation… → field_data
}
```
> `source` côté table `leads` vaut `webhook` (via `?provider=webhook`) ; le `source` du body
> est conservé dans `field_data` pour contexte.

## Générer la clé d'un client
Si ton CRM gère les clés dans son UI : créer une clé « webhook générique » pour le client et copier l'URL finale.
Si c'est ta propre app, le principe :
1. Générer `<prefix>_` + 16 bytes hex.
2. **INSERT ciblé** d'UNE ligne dans la table des clés (`client_id`, `label`, `key_prefix` pour l'affichage, `key_hash` = sha256 — on ne stocke JAMAIS la clé en clair, `provider`, `revoked_at`, `last_used_at`).
3. Imprimer UNE fois la clé complète + l'URL webhook finale → c'est la valeur de `CRM_WEBHOOK_URL`.

Piège classique : si la colonne `provider` a une contrainte CHECK (ex. `calcom|typeform|zapier|n8n|make|generic|custom`), la valeur `webhook` y est interdite → utiliser **`generic`** (le `?provider=webhook` de l'URL ne touche pas cette colonne, il pilote le `source` du lead).

## Règle prod base de données
INSERT ciblé uniquement, **montrer le SQL avant**. Jamais de DROP/UPDATE de masse/migration depuis ce skill.
Pour révoquer une clé : `UPDATE <table_clés> SET revoked_at = now() WHERE id = '…'`.
