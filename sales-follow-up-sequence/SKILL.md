---
name: sales-follow-up-sequence
description: Pilote les sequences de follow-up commercial d'une agence depuis son CRM (app maison, HubSpot, Notion ou simple tableau) apres envoi d'une proposition commerciale, d'un devis (page Vercel) ou d'un lien Stripe. Cadence 3 emails (T0 proposition, J+2 preuves, J+6 clarification) puis action humaine ; garde-fous anti-overkill ; le CRM est la source de verite. Prerequis : acces en lecture/ecriture a ton CRM (contrat de champs dans references/crm-contract.md) et un canal d'envoi email. Use when the user asks for "suivi commercial", "sequence de follow-up", "relance devis", "relance proposition commerciale", "Activé, séquence de follow-up", "active sequence de follow-up", "dernier mail envoye", "derniere sequence", "mettre a jour le CRM", "envoyer les emails de relance", or any workflow that must read real-time CRM lead/deal/payment status before drafting, sending, logging, or scheduling follow-up emails.
---

# Sales Follow-Up Sequence

## Mission

Piloter le suivi commercial de ton agence apres proposition commerciale, sans envoyer d'email inutile ni dangereux. Le skill doit :

- Lire l'etat du CRM en temps reel avant toute decision.
- Verifier le statut du lead, la proposition, le paiement, les activites recentes et les dernieres relances.
- Generer le bon email de sequence avec les templates du skill.
- Envoyer uniquement si l'utilisateur demande explicitement l'envoi et si tous les garde-fous passent.
- Mettre a jour le CRM apres envoi : dernier email envoye, derniere sequence, prochaine relance, activite timeline.

Le CRM est la source de verite. Une information dans le fil de conversation ne suffit jamais pour envoyer.

« Le CRM » = celui de ton agence : une app maison (Supabase/Postgres + API), un CRM SaaS (HubSpot, Pipedrive…), une base Notion ou un simple tableau. Le skill ne suppose aucun outil precis ; il suppose les champs decrits dans `references/crm-contract.md`.

## Ressources

- Lire `references/email-templates.md` pour les templates Email 1 / Email 2 / Email 3, variables, signatures et variantes.
- Lire `references/crm-contract.md` avant toute integration CRM, query Supabase/API, ou mise a jour de champs.
- Lire `references/sequence-rules.md` pour la cadence, les statuts bloquants, l'idempotence et les decisions par contexte.
- Lire `references/source-playbooks.md` pour les principes importes des autres skills lead-gen, email sequence, cold email, sales enablement et RevOps.

## Skills Amont A Respecter

Ce skill intervient apres les assets commerciaux produits en amont. Quand ces assets existent, les traiter comme sources de verite :

- `sales-call-analyzer` produit le brief commercial structure depuis la transcription.
- `devis-vercel-generator` produit la page devis publique (URL type `https://devis-{client-slug}.vercel.app`) avec PDF telechargeable, calculateur ROI et lien Stripe.
- `campaign-proposal` peut produire une proposition campagne plus classique.

Le follow-up ne regenere pas ces assets. Il verifie qu'ils existent, recupere l'URL, la reference devis, le prix, la validite et le lien de paiement, puis cadence les relances dans le CRM.

## Regle D'Or

Avant d'envoyer le moindre email, rafraichir le lead depuis le CRM et reevaluer l'eligibilite. Si le statut, le paiement, la reponse client, l'etape pipeline ou les champs de sequence ont change, stopper l'envoi et expliquer pourquoi.

Ne jamais envoyer sur la base d'un snapshot ancien, d'une page deja ouverte, d'un export CSV, d'un souvenir de conversation ou d'un digest precedent.

## Modes De Travail

### 1. Audit / Digest

Utiliser ce mode si le user demande quoi relancer, un resume de pipeline ou les leads a traiter.

Sortie attendue :
- leads eligibles ;
- leads bloques ;
- prochaine action recommandee ;
- raison exacte ;
- email qui serait envoye, en brouillon uniquement.

### 2. Preparation

Utiliser ce mode si le user demande de preparer les emails.

Sortie attendue :
- email personnalise ;
- sujet ;
- sequence step ;
- date/heure cible ;
- donnees CRM manquantes ;
- aucune action externe sans validation.

### 3. Envoi + Update CRM

Utiliser ce mode uniquement si le user demande explicitement d'envoyer ou d'activer la sequence.

Workflow obligatoire :
1. Rafraichir le lead et ses activites depuis le CRM.
2. Verifier les blockers.
3. Determiner le step exact a envoyer.
4. Construire l'email depuis les templates.
5. Envoyer l'email par le canal configure.
6. Relire ou confirmer le succes provider.
7. Mettre a jour le CRM dans la meme operation logique.
8. Ajouter une activite timeline avec l'idempotency key.
9. Retourner un compte-rendu court.

Si l'etape 7 echoue, le resultat doit etre signale comme partiellement execute avec action de correction. Ne jamais pretendre que la sequence CRM est a jour si elle ne l'est pas.

## Eligibilite D'Un Lead

Un lead est eligible seulement si tous les criteres sont vrais :

- Statut CRM exact ou equivalent configure : `Activé, séquence de follow-up`.
- Pipeline stage compatible : `Proposition`, `Négociation`, ou stage commercial explicitement post-devis.
- Email valide present.
- Prenom ou fallback civilise disponible.
- Proposition/devis URL disponible.
- Paiement non recu.
- Lead non marque `Gagné`, `Perdu`, `Client`, `Onboarding`, `Closed Won`, `Closed Lost`, `Paid`, `Refunded`, `Do not contact`, `Unsubscribed`, `Bounced`.
- Aucune activite humaine recente ne demande une autre action.
- Le meme step de sequence n'a pas deja ete envoye pour cette proposition.
- La prochaine relance est due ou le user demande explicitement un envoi manuel justifie.

Si un critere manque ou est ambigu, preparer un brouillon et demander validation au lieu d'envoyer.

## Donnees A Charger Avant Decision

Lire au minimum :

- lead : id, nom, prenom, email, telephone, entreprise, statut, stage pipeline, owner, tags, notes ;
- proposition : URL, reference, date d'envoi, prix, date de validite, lien Stripe ;
- sequence : statut, step courant, dernier email envoye, derniere sequence envoyee, prochaine relance ;
- paiement : statut Stripe ou champ CRM equivalent, paid_at, invoice/checkout status ;
- activites : emails, appels, notes, WhatsApp, changements de stage depuis la proposition ;
- timestamps : created_at, updated_at, last_contacted_at, next_follow_up.

Si le code de ton CRM est accessible, inspecter les types/API reels avant d'ecrire. Si le repo n'est pas accessible, suivre `references/crm-contract.md` et ne faire que des brouillons ou des instructions d'update.

## Choix Du Step

Utiliser la cadence par defaut :

- `proposal_sent` / Email 1 : immediatement apres envoi de la proposition.
- `case_studies_j2` / Email 2 : J+2 apres Email 1 si pas de paiement, pas de reponse, pas de changement de statut.
- `clarity_check_j6` / Email 3 : J+6 apres Email 1 si pas de paiement, pas de reponse, pas de changement de statut.
- Apres Email 3 : ne pas continuer en automatique par email. Creer une tache manuelle WhatsApp/appel ou proposer une relance breakup si le user la demande.

Les jours sont comptes depuis `proposal_sent_at` ou, a defaut, depuis l'activite Email 1. Voir `references/sequence-rules.md`.

## Construction Des Emails

Lire `references/email-templates.md`, puis :

- Personnaliser `{{first_name}}`, `{{client_name}}`, `{{agency_name}}`, `{{proposal_url}}`, `{{case_study_links}}`, `{{whatsapp_url}}`.
- Corriger les fautes sans changer l'intention commerciale.
- Garder un ton direct, humain, pas corporate.
- Garder un seul job par email : Email 1 = envoyer la proposition, Email 2 = preuve/cas client, Email 3 = lever le doute ou obtenir une reponse courte.
- Ne jamais inventer de cas client. Si les liens case studies ne sont pas disponibles, remplacer Email 2 par une version demandant validation ou bloquer l'envoi.
- Ne jamais laisser de placeholder dans un email envoye.
- Inclure la signature standard de l'utilisateur (definie dans `references/email-templates.md`).

## Garde-Fous Anti-Overkill

Bloquer l'envoi si :

- paiement recu ou statut `paid/won/client/onboarding` ;
- lead a repondu apres le dernier email ;
- un humain a ajoute une note ou change le next step apres la relance planifiee ;
- un appel/WhatsApp est prevu aujourd'hui ;
- le step a deja ete envoye ;
- le lien proposition est absent ou invalide ;
- le lead est en `Perdu`, `Not interested`, `Pas maintenant`, `Do not contact`, `Unsubscribed`, `Bounced` ;
- la date de validite du devis est depassee et aucun nouveau devis n'a ete cree ;
- le CRM ne peut pas etre mis a jour apres envoi.

En cas de doute, ne pas envoyer. Produire un brouillon + raison du blocage.

## Mise A Jour CRM Apres Envoi

Apres succes provider, ecrire :

- `last_followup_email_sent_at` = timestamp d'envoi ;
- `last_followup_sequence_step` = `proposal_sent`, `case_studies_j2`, ou `clarity_check_j6` ;
- `last_followup_sequence_name` = `proposal_followup_v1` ;
- `followup_sequence_status` = `active` ou `completed` apres Email 3 ;
- `next_follow_up` = prochaine date due, ou null si sequence complete ;
- `last_contacted_at` = timestamp d'envoi ;
- activite timeline de type email avec sujet, step, provider id, proposition ref, idempotency key.

Si les colonnes n'existent pas, stocker ces valeurs dans `lead_activities.metadata` et signaler que le schema CRM devrait etre etendu.

## Format De Reponse

Pour un audit :

```markdown
## Leads A Relancer
| Lead | Step | Due | Raison | Action |

## Bloques
| Lead | Raison | Action recommandee |
```

Pour un envoi :

```markdown
Envoye : oui/non
Lead : ...
Step : ...
Sujet : ...
CRM update : ok/partiel/echec
Prochaine relance : ...
Blocage : ...
```

Rester factuel. Ne jamais masquer un blocage ou une incertitude CRM.

## Qualite Minimale

Avant de livrer :

- Verifier qu'aucun placeholder n'est present.
- Verifier que le bon step est choisi par rapport aux timestamps CRM.
- Verifier que le statut n'a pas change entre la selection et l'envoi.
- Verifier que le message ne relance pas quelqu'un qui a deja paye ou repondu.
- Verifier que le CRM a bien une trace exploitable de ce qui vient d'etre fait.
