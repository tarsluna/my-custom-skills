---
name: cold-email-replies
description: Met en place et pilote un agent qui traite les réponses à une campagne de cold email (Smartlead). Il classe chaque réponse (oui, demande de rendez-vous, question, plus tard, non, absence), envoie aux « oui » le livrable offert (audit, guide, maquette) dans le même fil avec un lien de réservation, alerte l'équipe sur Slack (« NOUVEAU LEAD », puis « audit envoyé ») et fait entrer le prospect dans le CRM. Un « non » désinscrit et bloque, une question part à un humain. Utilise ce skill pour « répondre automatiquement aux réponses du cold email », « envoyer l'audit offert aux prospects qui disent oui », « agent de réponses Smartlead », « traiter les replies », « classer les réponses de campagne », « alerte Slack nouveau lead », ou pour déboguer, simuler ou régler un tel agent. Pas pour écrire la séquence de cold email elle-même, ni pour trouver des contacts.
---

# Agent de réponses au cold email

Un prospect répond à votre campagne. L'agent lit sa réponse, la classe, et agit seul dans les cas sûrs : il envoie le livrable promis aux « oui » et désinscrit les « non ». Tout le reste arrive à l'équipe sur Slack.

Lisez ces fichiers avant de configurer quoi que ce soit. Ils sont le skill, pas une annexe :

| Fichier | À lire pour |
| --- | --- |
| [references/01-pipeline.md](references/01-pipeline.md) | Les étapes d'une sonde, les statuts, ce qui ne peut pas arriver |
| [references/02-classification.md](references/02-classification.md) | Les intentions, le seuil, la classification de l'outil, les deux classeurs |
| [references/03-smartlead.md](references/03-smartlead.md) | Les cinq appels à l'API, comment lire un envoi, débit et planning |
| [references/04-pitfalls.md](references/04-pitfalls.md) | **Les pièges du premier jour en production.** À lire en entier |
| [references/05-integrations.md](references/05-integrations.md) | Livrable, Slack, CRM, réservation, hébergement |

## Les règles qui ne plient pas

1. **Jamais de réponse automatique à un « non ».** Un refus est honoré à toute confiance : désinscription de toutes les campagnes, blocage de l'adresse. Un « non » arrivé après un « oui » annule l'envoi en attente.
2. **La classification de l'outil confirme, elle ne contredit pas.** « Interested » ou « Meeting Request » peut confirmer un oui quand l'agent hésite. Jamais contre un non, un report ou une absence.
3. **Une question va à un humain.** Pas de réponse automatique, une alerte Slack, une réponse à la main.
4. **Une seule réponse par contact, jamais renvoyée sur un doute.** Un envoi au résultat inconnu (délai, 5xx, arrêt brutal) n'est jamais retenté : alerte, vérification du fil, réponse à la main. Un « envoyé » ne se pose que sur une confirmation lue dans le corps de la réponse de l'API.
5. **Local et éteint par défaut.** Simulez avec `--dry-run`. Le mode réel demande `REPLY_AGENT_ENABLED=1` et une demande explicite de l'utilisateur. Les clés vivent dans l'environnement, jamais dans `config.json`, jamais dans un commit.

## Le playbook

### 1. Cadrer l'offre avec l'utilisateur

Demandez seulement ce qui bloque :

- **Le livrable.** Un audit fabriqué pour chaque prospect (`deliverable.mode: webhook`, il faut un générateur qui respecte le contrat de [05-integrations.md](references/05-integrations.md)) ou un même lien pour tous (`static` : guide, vidéo).
- **La phrase du cold email.** L'agent a été conçu pour une campagne qui dit « répondez ok pour le recevoir, non pour ne plus recevoir ». Résumez l'offre en une phrase anglaise dans `classifier.offer_context` : c'est le contexte du classeur.
- **Le lien de réservation.** Un événement dédié au cold email, pour savoir d'où vient chaque rendez-vous.
- **Le plafond.** Combien de livrables neufs par jour l'utilisateur accepte de payer (`deliverable.max_per_day`).

### 2. Écrire la configuration

Copiez `examples/config.example.json` en `config.json` (ignoré par git) et remplacez tout : marque, signataire, livrable, gabarit de réponse, étapes du CRM. Le gabarit doit garder `{link}` et la phrase qui propose l'appel avec `{booking_url}` : un audit seul n'obtient pas le rendez-vous (piège n° 6).

Champs du gabarit : `{greeting}`, `{first_name}`, `{company}`, `{link}`, `{booking_url}`, `{sender_name}`, `{brand_name}`, `{deliverable_name}`. Un champ inconnu bloque le chargement.

Vérifiez les numéros de catégorie de l'outil (`tool_categories.positive`) dans le compte Smartlead de l'utilisateur.

### 3. Simuler, sans clé

```bash
python3 scripts/run.py --dry-run --config config.json
```

La simulation rejoue `examples/replies.sample.json` : 14 réponses fictives qui couvrent chaque règle (oui, rendez-vous, question, non contredit par l'outil, absence, report, oui hésitant confirmé par l'outil, boîte Gmail sans site, faux succès de l'API, deux « ok », un oui puis un non). Lisez la sortie avec l'utilisateur, surtout le premier mail envoyé.

Puis écrivez ses vraies formulations, anonymisées, dans un fichier au même format et rejouez-les (`--replies mes-reponses.json`). Corrigez les mots-clés ou le seuil jusqu'à ce qu'aucun « non » ne passe pour un « oui ».

### 4. Contrôler la liste de contacts

```bash
python3 scripts/run.py --check-leads contacts.csv
```

Au-delà de 15 % de messageries grand public, prévenez l'utilisateur avant le lancement (piège n° 1) et proposez une petite vague test. Les contacts sans site ni adresse professionnelle ne pourront pas recevoir un livrable par domaine.

### 5. Brancher les clés

Dans l'environnement du serveur, d'après `.env.example` : `SMARTLEAD_API_KEY`, `SMARTLEAD_CAMPAIGN_IDS`, `SLACK_WEBHOOK_URL`, `CRM_WEBHOOK_URL`, `DELIVERABLE_API_URL`, et `ANTHROPIC_API_KEY` si `classifier.mode` vaut `claude`. Ne lisez jamais un fichier de secrets de l'utilisateur ; demandez-lui de poser les variables.

Pour la production, passez `classifier.mode` à `claude` (`pip install anthropic`, Python 3.10+). Le mode `rules` sert à tester.

### 6. Allumer avant la campagne

```bash
REPLY_AGENT_ENABLED=1 python3 scripts/run.py --once     # une sonde, pour voir
REPLY_AGENT_ENABLED=1 python3 scripts/run.py --loop     # puis en continu, ou --once par cron toutes les 3 min
```

Le premier démarrage pose un filigrane : les réponses plus anciennes sont ignorées et restent à traiter à la main (piège n° 8).

### 7. Vérifier le premier « oui » réel de bout en bout

C'est ce qui a été fait le premier jour. Pour la première réponse positive :

- l'alerte « NOUVEAU LEAD » est arrivée dès le classement ;
- le livrable a été commandé, puis la réponse est partie quand il était prêt (compter une vingtaine de minutes pour un audit fabriqué) ;
- la réponse est **visible dans le fil**, dans l'outil d'envoi, avec le lien du livrable et celui de la réservation ;
- l'alerte « audit envoyé » est arrivée avec le lien ;
- le prospect est dans le CRM à l'étape « Audit envoyé ».

Pendant l'attente, personne ne répond à la main : le prospect recevrait deux messages.

### 8. Piloter

```bash
python3 scripts/run.py --status
```

Chaque jour : traiter les réponses « à la main », vérifier les envois refusés ou incertains dans le fil, regarder le taux de rebond dans l'outil. Pas de réponse le soir ou le week-end ? Regardez le planning de la campagne avant de chercher une panne (piège n° 3).

### 9. Éviter le double livrable à la réservation

Si l'outil de réservation envoie lui-même un livrable avant l'appel, faites-lui appeler `python3 scripts/run.py --booked EMAIL --json` d'abord, et sauter son envoi quand `already_sent` vaut `true` (piège n° 2).

## Ce que vous rendez à l'utilisateur

- `config.json` rempli, la sortie de la simulation sur ses propres formulations, le rapport `--check-leads`.
- La liste des variables d'environnement à poser, sans aucune valeur.
- Ce qui reste à décider par lui : boîtes d'envoi si les rebonds sont hauts, plafond quotidien, `upgrade_questions`, double livrable côté réservation.
