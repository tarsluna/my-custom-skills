# Regles De Sequence

## Sequence Name

```text
proposal_followup_v1
```

## Steps

| Step | Timing | Objectif | Email |
|---|---:|---|---|
| `proposal_sent` | T0 | livrer la propal et rendre le paiement simple | Email 1 |
| `case_studies_j2` | J+2 | renforcer la confiance avec preuves/cas clients | Email 2 |
| `clarity_check_j6` | J+6 | verifier les blocages et ramener vers WhatsApp | Email 3 |
| `manual_review` | apres J+6 | action humaine, appel, WhatsApp, close/nurture | pas d'email auto |

## Calcul Du Timing

Source prioritaire :

1. `proposal_sent_at` sur proposition/devis.
2. Activite `proposal_sent`.
3. Activite `followup_email` step `proposal_sent`.
4. `last_contacted_at` seulement si les trois premiers manquent.

Email 2 est du a `proposal_sent_at + 2 jours`.

Email 3 est du a `proposal_sent_at + 6 jours`.

Si la date tombe le week-end ou jour ferie non gere par l'app, proposer le prochain jour ouvre. Ne pas inventer de calendrier de jours feries ; utiliser la timezone configuree dans ton CRM ou, par defaut, celle de ton activite commerciale (ex. Europe/Paris).

## Classification

### Hot

Critere : reponse recente, demande de precision, clic fort, paiement initie mais incomplet, call cale.

Action : pas d'email sequence automatique. Creer une action manuelle.

### Warm

Critere : proposition envoyee, pas de reponse, timing encore proche, aucune objection bloquante.

Action : envoyer le prochain step si due.

### Cool

Critere : J+6 passe sans reponse, pas de signe d'engagement.

Action : Email 3 si pas encore envoye, puis tache manuelle.

### Ghost

Critere : Email 3 envoye, aucune reponse, aucune activite.

Action : ne pas continuer automatiquement. Proposer WhatsApp/appel ou close/nurture.

### Paid / Won

Critere : paiement recu ou stage gagne/client/onboarding.

Action : bloquer toute relance commerciale. Declencher onboarding si pertinent.

## Priorite Des Evenements

En cas de conflit, appliquer cet ordre :

1. Paiement recu.
2. Do not contact / unsubscribe / bounce.
3. Stage gagne/perdu/client/onboarding.
4. Reponse client ou activite humaine recente.
5. Call/WhatsApp deja planifie.
6. Sequence step deja envoye.
7. Timing de sequence.

Les points 1 a 6 bloquent l'envoi.

## Reponse Client

Considerer qu'un lead a repondu si une activite apres le dernier email est de type :

```text
reply
inbound_email
whatsapp
call
meeting
note
stage_change
```

Une note interne creee par un humain apres le dernier email doit bloquer l'automatisation si elle contient une prochaine action ou une decision. Ne jamais ecraser une action humaine.

## Next Follow-Up

Apres Email 1 :

```text
next_follow_up = proposal_sent_at + 2 jours
followup_sequence_status = active
```

Apres Email 2 :

```text
next_follow_up = proposal_sent_at + 6 jours
followup_sequence_status = active
```

Apres Email 3 :

```text
next_follow_up = null ou date d'action manuelle choisie
followup_sequence_status = completed
```

## Messages A Ne Jamais Envoyer

Ne pas envoyer :

- "Je me permets de relancer" sans nouvelle valeur.
- "As-tu eu le temps de regarder ?" en boucle.
- Un email d'urgence fake.
- Une relance paiement apres paiement recu.
- Une relance devis si la date de validite est depassee sans nouveau devis.
- Un email avec liens case studies placeholders.

## Output De Decision

Chaque decision doit pouvoir etre auditee :

```json
{
  "lead_id": "...",
  "eligible": true,
  "selected_step": "case_studies_j2",
  "blocked_reason": null,
  "crm_snapshot_at": "ISO_TIMESTAMP",
  "proposal_ref": "...",
  "last_sequence_step": "proposal_sent",
  "next_follow_up": "ISO_TIMESTAMP"
}
```
