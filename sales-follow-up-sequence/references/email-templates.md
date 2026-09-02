# Templates Email Follow-Up

Utiliser ces templates comme base. Corriger les fautes, personnaliser, et ne jamais envoyer avec des placeholders.

## Variables

| Variable | Description |
|---|---|
| `{{first_name}}` | Prénom du prospect. Fallback : `Bonjour,` si absent. |
| `{{client_name}}` | Nom entreprise ou nom court du client. |
| `{{agency_name}}` | Nom de ton agence (apparait dans les sujets et les messages WhatsApp). |
| `{{proposal_url}}` | Lien devis/proposition commerciale. Obligatoire. |
| `{{case_study_links}}` | Trois liens case studies séparés par ` | `. Obligatoire pour Email 2. |
| `{{whatsapp_url}}` | `https://wa.me/<ton numero au format international sans +>` (ex. `https://wa.me/33600000000`). A configurer une fois. |
| `{{signature}}` | Signature standard ci-dessous. |

## Signature Standard

```text
{{your_name}}
{{your_role}} - {{agency_name}}
{{your_phone}}
```

Exemple : `Prenom Nom` / `CMO - Acme Agency` / `+33 6 00 00 00 00`. Renseigner une fois dans la config du skill ou du CRM ; ne jamais envoyer avec les placeholders.

## Email 1 — Envoi De La Proposition Commerciale

Sequence step : `proposal_sent`

Timing : immediatement apres creation/envoi du devis.

Subject :

```text
Devis {{client_name}} - {{agency_name}}
```

Body :

```text
Hello {{first_name}},

Merci pour ton temps aujourd’hui.

Comme convenu, voici le lien vers ta proposition commerciale personnalisée :
{{proposal_url}}

N’hésite pas à revenir vers moi si tu as des questions, notamment sur WhatsApp.

Une fois que tu es prêt à passer le pas pour avancer, le devis et le paiement sont directement intégrés dans la proposition.

Excellente journée à toi,

PS : tu as un calculateur de ROI à l’intérieur qui peut s’avérer utile pour te projeter.

{{signature}}
```

Notes :
- Ne pas survendre. Le devis vient d’être envoyé, l’objectif est de rendre l’action simple.
- Si un call de walkthrough a été convenu, ajouter une ligne : `Comme vu ensemble, je peux aussi te le parcourir en 10 minutes si tu veux valider les points clés.`

## Email 2 — J+2 Études De Cas

Sequence step : `case_studies_j2`

Timing : J+2 après Email 1, seulement si pas de paiement/réponse/changement de statut.

Subject :

```text
Étude de cas {{agency_name}}
```

Body :

```text
Bonjour {{first_name}},

J’espère que tu vas bien.

Je voulais aussi te partager quelques études de cas de clients qui étaient dans une situation assez similaire à la tienne :

{{case_study_links}}

L’objectif du mois d’essai est simple : tester le canal proprement, obtenir des signaux réels, puis décider sur des chiffres plutôt que sur des suppositions.

Hâte de travailler avec toi.

PS : je te remets ta proposition ici :
{{proposal_url}}

{{signature}}
```

Notes :
- Ne jamais inventer les liens.
- Si aucun case study pertinent n’est disponible, ne pas envoyer automatiquement. Produire un brouillon qui demande à l'utilisateur de fournir les liens.
- Adapter la phrase "situation similaire" si le prospect est très différent des cases studies.

## Email 3 — J+6 Clarification / Accès Espace

Sequence step : `clarity_check_j6`

Timing : J+6 après Email 1, seulement si pas de paiement/réponse/changement de statut.

Subject :

```text
Accès à ton espace
```

Body :

```text
Bonjour {{first_name}},

Rapidement, on avait eu un bon feeling au rendez-vous, mais je n’ai pas eu de retour de ta part sur la proposition.

Est-ce que tout était clair pour toi ? Est-ce qu’il y a des éléments que je peux te partager pour t’aider à trancher ?

Tu peux aussi m’envoyer un vocal sur WhatsApp ici :
{{whatsapp_url}}

Belle journée,

{{signature}}
```

Notes :
- Cet email doit rester court.
- Ne pas culpabiliser le prospect.
- Après cet email, privilégier une action manuelle WhatsApp/appel plutôt qu’une séquence email automatique.

## Variantes Courtes WhatsApp

Utiliser uniquement si le CRM indique que WhatsApp est autorisé ou déjà utilisé.

### Après Email 1

```text
Hello {{first_name}}, je viens de t’envoyer la proposition {{agency_name}} par email. Le devis + paiement sont intégrés dedans. Dis-moi si tu veux que je te la parcoure rapidement.
```

### Après Email 2

```text
Hello {{first_name}}, je t’ai partagé quelques cas clients par email + le lien de ta proposition. Si tu veux, tu peux me faire un vocal ici avec tes questions.
```

### Après Email 3

```text
Hello {{first_name}}, je voulais juste savoir si tout était clair sur la proposition. Si le timing n’est pas bon, dis-le moi simplement et je te laisse tranquille.
```
