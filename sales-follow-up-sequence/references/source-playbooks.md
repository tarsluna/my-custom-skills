# Source Playbooks

Ce fichier resume les principes a importer dans le skill de follow-up. Il ne remplace pas le CRM : il cadre la logique commerciale.

## Sources A Connaitre

| Source | Apport pour ce skill |
|---|---|
| Skill `sales-call-analyzer` | Le brief commercial et les verbatims nourrissent la proposition. Le follow-up doit reprendre les termes du prospect si une personnalisation est demandee. |
| Skill `devis-vercel-generator` | La page devis Vercel est l'asset principal a relancer : URL type `devis-{client-slug}.vercel.app`, PDF telechargeable, ROI calculator, lien Stripe, reference devis, validite. |
| `marketingskills` (repo open source) — skill `email-sequence` | Un email = un job, CTA clair, ton conversationnel, sequence courte, pertinence avant volume. |
| `marketingskills` — `cold-email/references/follow-up-sequences.md` | Eviter les relances vides type "just checking in"; chaque relance doit ajouter une valeur nouvelle. Capper la sequence automatique. |
| `marketingskills` — skill `sales-enablement` | La relance doit aider a conclure : preuve, ROI, objection, next step concret. |
| `marketingskills` — skill `revops` | Le CRM est la source de verite, avec hygiene de stage, SLA, statut, prochaine action et activites auditees. |
| Regle interne de suivi/relance de l'agence | Ne pas relancer plus de deux fois par jour, varier les canaux, stopper proprement apres une sequence sans reponse. |

## Principes A Appliquer

- Chaque email apporte une seule valeur nouvelle.
- La sequence automatique est courte : proposition, preuve, clarification. Apres cela, basculer en tache humaine.
- La preuve doit etre concrete : etude de cas, chiffre, lien devis, ROI calculator, PDF ou lien Stripe. Ne jamais inventer de cas client.
- Le meilleur follow-up n'est pas l'email le plus long, c'est celui qui arrive au bon moment sans ignorer le statut reel du deal.
- Les signaux CRM battent toujours la cadence : paiement, reponse, note humaine, appel planifie, changement de stage, unsubscribe, bounce.
- Si une action humaine est planifiee, l'email automatique doit se taire.
- Si le prospect a deja paye, signe, repondu ou ete passe en client/onboarding, aucune relance commerciale ne part.

## Lien Avec La Page Devis Vercel

Avant Email 1, verifier que la proposition contient :

- URL publique de type `https://devis-{client-slug}.vercel.app` ou URL de proposition valide.
- Reference devis.
- Prix et conditions.
- Date de validite.
- Lien de paiement Stripe si disponible.
- PDF telechargeable si la page est issue de `devis-vercel-generator`.
- Calculateur ROI present ou mentionne dans l'email uniquement si la page le contient.

Si la page devis n'existe pas encore, ce skill ne doit pas improviser un email de proposition. Il doit demander de generer ou renseigner la proposition d'abord.

## Personnalisation Depuis L'Appel

Quand le brief `00-sales-brief/brief-output.json` est disponible, l'utiliser pour enrichir les brouillons :

- dream headline ou enjeu principal ;
- objections verbatim ;
- timeline de decision ;
- sensibilite au prix ;
- budget ads recommande ;
- vocabulaire metier du prospect.

Ne pas injecter ces elements si cela rend l'email lourd. La sequence de base doit rester courte.

## Decision Commerciale

Priorite des signaux :

1. Stop definitif : paiement, client, onboarding, lost, do not contact, unsubscribe, bounce.
2. Pause humaine : reponse prospect, note recente, next step manuel, appel/WhatsApp planifie.
3. Relance due : statut actif + aucune interaction bloquante + step non envoye + timing respecte.
4. Brouillon seulement : donnees incompletes, proposition absente, case studies manquantes, schema CRM incertain.

