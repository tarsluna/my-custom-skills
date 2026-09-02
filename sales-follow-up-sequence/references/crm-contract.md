# Contrat CRM

Ce fichier decrit le contrat attendu par le skill. Si le code ou l'API de ton CRM est accessible, inspecter le schema reel et adapter les noms. Sinon, utiliser ce contrat comme reference et eviter les writes destructifs.

## Contexte Type

Le contrat ci-dessous a ete ecrit pour un CRM maison (app Next.js + TypeScript + Supabase) ; il se transpose a n'importe quel CRM/tableau qui expose l'equivalent de :

- CRM admin/client ;
- pipeline Kanban ;
- stages type `Nouveau`, `Contacté`, `Qualifié`, `Proposition`, `Négociation`, `Gagné`, `Perdu` ;
- table `pipeline_stages` ;
- table `lead_activities` ;
- enrichissement `leads` avec `source`, `pipeline_stage_id`, `assigned_to`, `last_contacted_at`, `next_follow_up`, `tags`, `preferred_contact`, `city`.

Si ton CRM est un tableau (Notion, Sheets), chaque bloc de champs ci-dessous devient une colonne ; les « activites » deviennent une table/onglet journal.

## Donnees A Lire

### Lead

Champs minimaux :

```text
id
first_name
last_name
email
phone
company
status
pipeline_stage_id
assigned_to
last_contacted_at
next_follow_up
tags
notes
preferred_contact
updated_at
```

### Pipeline Stage

```text
id
name
is_won
is_lost
display_order
```

### Proposition / Devis

Si une table dediee existe, lire :

```text
id
lead_id
proposal_url
proposal_ref
proposal_sent_at
pricing_amount_eur
stripe_payment_link
valid_until
status
created_at
updated_at
```

Si aucune table dediee n'existe, rechercher ces valeurs dans :

- `lead_activities.metadata`
- `leads.notes`
- champs custom `proposal_url`, `devis_url`, `stripe_link`, `proposal_sent_at`

### Paiement

Lire le statut paiement depuis la source la plus fiable disponible :

```text
payment_status
paid_at
stripe_checkout_session_id
stripe_payment_intent_id
invoice_status
amount_paid
```

Statuts qui bloquent l'envoi :

```text
paid
succeeded
complete
closed_won
won
client
onboarding
refunded
chargeback
```

Si le statut paiement est ambigu, bloquer l'envoi et demander verification humaine.

### Activites

Lire les activites du lead depuis la date d'envoi de proposition :

```text
id
lead_id
type
title
body
created_at
created_by
metadata
```

Types importants :

```text
email
call
note
meeting
whatsapp
stage_change
payment
proposal_sent
followup_email
```

## Champs A Ecrire Apres Envoi

Si les colonnes existent sur `leads` ou l'objet deal :

```text
last_followup_email_sent_at
last_followup_sequence_step
last_followup_sequence_name
last_followup_sequence_sent_at
followup_sequence_status
followup_sequence_started_at
followup_sequence_completed_at
last_contacted_at
next_follow_up
updated_at
```

Valeurs standards :

```json
{
  "last_followup_sequence_name": "proposal_followup_v1",
  "last_followup_sequence_step": "case_studies_j2",
  "followup_sequence_status": "active"
}
```

Si ces colonnes n'existent pas, ecrire une activite `followup_email` avec metadata complete.

## Activite Timeline Obligatoire

Apres chaque email envoye, creer une activite :

```json
{
  "type": "followup_email",
  "title": "Follow-up - case_studies_j2",
  "body": "Sujet: Etude de cas {{agency_name}}\n\nPreview du message...",
  "metadata": {
    "sequence_name": "proposal_followup_v1",
    "sequence_step": "case_studies_j2",
    "provider": "gmail_or_internal_provider",
    "provider_message_id": "...",
    "proposal_url": "...",
    "proposal_ref": "...",
    "sent_at": "ISO_TIMESTAMP",
    "idempotency_key": "lead:{lead_id}:proposal:{proposal_ref}:step:{step}"
  }
}
```

## Idempotence

Avant envoi, chercher une activite existante avec :

```text
metadata.sequence_name = proposal_followup_v1
metadata.sequence_step = step cible
metadata.proposal_ref = proposition courante
```

Si elle existe, ne pas renvoyer. Retourner "deja envoye" avec la date.

## Transaction Ideale

Le meilleur design applicatif est un endpoint serveur atomique :

```text
POST /api/admin/crm/leads/{lead_id}/follow-up/send
```

Payload :

```json
{
  "sequence_name": "proposal_followup_v1",
  "requested_step": "case_studies_j2",
  "expected_lead_updated_at": "ISO_TIMESTAMP",
  "proposal_ref": "DEV-...",
  "dry_run": false
}
```

L'endpoint doit :

1. Recharger le lead en base.
2. Verifier statut/stage/paiement/idempotence.
3. Envoyer l'email.
4. Mettre a jour les champs sequence.
5. Creer l'activite timeline.
6. Retourner le resultat.

Si l'app ne dispose pas de cet endpoint, faire les memes operations de maniere sequentielle mais signaler le risque de race condition.

## Regle Gmail / Provider

Ne pas envoyer directement par Gmail si le CRM ne peut pas etre mis a jour ensuite. Dans ce cas :

- creer un brouillon ;
- ou retourner le message pret a envoyer ;
- expliquer que l'envoi manuel doit etre logge dans le CRM.
