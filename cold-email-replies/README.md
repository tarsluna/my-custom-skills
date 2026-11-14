<div align="center">

<img src="https://img.shields.io/badge/SALES-COLD_EMAIL_REPLIES-B8893B?style=flat-square&labelColor=B8893B&color=14120E" alt="SALES · COLD EMAIL REPLIES">

# Autonomous Cold Email Replies

### Chaque « oui » à votre cold email reçoit son audit, dans le même fil, sans que personne ne touche au clavier.

Un agent qui lit les réponses à votre campagne, les classe,<br>
envoie le livrable offert aux prospects qui disent oui avec un lien de réservation,<br>
désinscrit ceux qui disent non, et prévient l'équipe de tout le reste.

**[Installer le skill](#installation)** · **[Lire le playbook](SKILL.md)** · **[Les pièges du premier jour](references/04-pitfalls.md)**

<sub>Claude Code + Codex · Smartlead · Slack · CRM par webhook · simulation sans clé · Python 3.9+, aucune dépendance · MIT</sub>

<br><br>

<a href="https://bizos.cc"><img src="https://img.shields.io/badge/BizOS-build%20autonomous%20companies-14120E?style=for-the-badge&labelColor=14120E" alt="BizOS — build autonomous companies"></a>

<br><br>

<a href="https://x.com/gauthierthiry"><img src="https://img.shields.io/badge/@gauthierthiry-14120E?style=flat-square&logo=x&logoColor=white" alt="X"></a>
<a href="https://youtube.com/@gquthier"><img src="https://img.shields.io/badge/@gquthier-FF0000?style=flat-square&logo=youtube&logoColor=white" alt="YouTube"></a>

</div>

---

## Ce que ça fait

Vous proposez quelque chose de gratuit dans votre cold email : un audit, un diagnostic, un guide. « Répondez ok pour le recevoir. » Les réponses arrivent n'importe quand, et un « ok » qui attend une demi-journée refroidit.

L'agent sonde la campagne toutes les trois minutes et traite chaque réponse :

| Le prospect écrit | L'agent fait |
| --- | --- |
| **Oui** (« ok », « go », « envoyez ») | Slack « NOUVEAU LEAD », commande le livrable, répond dans le fil avec le lien et une proposition d'appel, Slack « audit envoyé », CRM « Audit envoyé » |
| **Demande de rendez-vous** (« on s'appelle ? ») | Comme un oui : le livrable part avec le lien de réservation |
| **Question** (« c'est combien ? ») | Rien d'automatique. Alerte Slack, réponse à la main |
| **Non** (« non merci », « retirez-moi ») | Désinscription de toutes les campagnes, blocage. Jamais de réponse |
| **Plus tard, absence** | Enregistrée, rien à faire |
| **Autre chose, ou l'agent hésite** | Alerte Slack, lecture humaine |

L'étiquette native de l'outil d'envoi (« Interested », « Meeting Request ») sert de second avis : elle confirme un oui quand l'agent hésite, jamais l'inverse.

Ce qui ne peut pas arriver : deux réponses au même contact, une réponse renvoyée après un envoi au résultat inconnu, une réponse à un « non », un livrable payé alors que la réponse ne pourrait pas partir, une alerte perdue quand Slack est en panne. Détail : [references/01-pipeline.md](references/01-pipeline.md).

### Le mail envoyé (exemple fictif)

```text
Bonjour Camille,

Votre audit est prêt : https://audit.example.com/r/jardins-martin

Vous y trouverez votre fiche Google comparée à celles des paysagistes les mieux classés autour de chez vous,
les demandes de devis que vous perdez aujourd'hui et le plan que nous lancerions pour Jardins Martin.

On vous propose de vous présenter le reste de l'audit lors d'un appel. Si vous trouvez ça pertinent,
réservez votre créneau ici : https://cal.example.com/canopee/audit-offert-30-min

Camille
Agence Canopée
```

Marque, métier, personnes et liens sont inventés. Tout se change dans `config.json`.

## Installation

**Claude Code** — skill personnel :

```bash
git clone https://github.com/gquthier/autonomous-cold-email-replies.git \
  ~/.claude/skills/cold-email-replies
```

**Codex** — skill personnel :

```bash
git clone https://github.com/gquthier/autonomous-cold-email-replies.git \
  ~/.codex/skills/cold-email-replies
```

Ouvrez une nouvelle session, puis demandez :

> Avec le skill cold-email-replies, mets en place l'agent de réponses de ma campagne Smartlead. Le livrable, c'est notre audit offert ; le lien de réservation est dans ce dossier. Simule d'abord sur mes vraies formulations.

## Prérequis et clés

- **Python 3.9+**. Aucune dépendance pour la simulation, les tests et le classeur par mots-clés.
- **`pip install anthropic`** (Python 3.10+) seulement pour le classeur de production (`classifier.mode: claude`).
- Les clés vivent dans l'environnement, jamais dans `config.json`. Noms dans [.env.example](.env.example) :

| Variable | Pour |
| --- | --- |
| `REPLY_AGENT_ENABLED` | L'interrupteur. Absent ou `0` : l'agent ne fait rien |
| `SMARTLEAD_API_KEY`, `SMARTLEAD_CAMPAIGN_IDS` | Lire les réponses, répondre dans le fil, désinscrire |
| `ANTHROPIC_API_KEY` | Classer les réponses avec le modèle |
| `DELIVERABLE_API_URL`, `DELIVERABLE_API_KEY` | Votre générateur de livrable (mode `webhook`) |
| `SLACK_WEBHOOK_URL` | Les alertes de l'équipe |
| `CRM_WEBHOOK_URL`, `CRM_WEBHOOK_SECRET` | Le pipeline du CRM |
| `BOOKING_URL` | Le lien de réservation, s'il n'est pas dans la configuration |
| `REPLY_AGENT_DB` | Le fichier SQLite de l'état (disque persistant) |

## Utilisation

Essayez sans aucune clé :

```bash
cd ~/.claude/skills/cold-email-replies
python3 scripts/run.py --dry-run
```

La simulation rejoue 14 réponses fictives et montre, pour chacune, le classement, les alertes, le livrable, la réponse et l'entrée au CRM, puis le premier mail envoyé. Rejouez vos propres formulations avec `--replies mon-fichier.json`.

```bash
python3 scripts/run.py --check-leads contacts.csv      # part de Gmail et Microsoft dans la liste, avant lancement
REPLY_AGENT_ENABLED=1 python3 scripts/run.py --once    # une sonde réelle
REPLY_AGENT_ENABLED=1 python3 scripts/run.py --loop    # en continu (ou --once par cron)
python3 scripts/run.py --status                        # où en est chaque réponse, ce qui attend un humain
python3 scripts/run.py --booked prospect@x.example     # le livrable est-il déjà parti ? (avant tout envoi côté réservation)
python3 -m unittest discover -s tests -v               # 39 tests hors ligne
```

Configuration complète : [examples/config.example.json](examples/config.example.json). Livrable, Slack, CRM et réservation : [references/05-integrations.md](references/05-integrations.md).

## Dans le dépôt

```text
SKILL.md                         Le playbook de l'agent, de l'offre au premier « oui » vérifié
references/01-pipeline.md        Une sonde étape par étape, les statuts, les garanties
references/02-classification.md  Intentions, seuil, étiquette de l'outil, classeurs
references/03-smartlead.md       Les cinq appels à l'API, lire un envoi, débit, planning
references/04-pitfalls.md        Les pièges du premier jour en production
references/05-integrations.md    Livrable, Slack, CRM, réservation, hébergement
scripts/run.py                   La ligne de commande
scripts/reply_agent/             L'agent : lecture, classement, livrable, envoi, alertes, CRM
examples/                        Configuration, réponses et contacts fictifs
tests/                           Tests hors ligne, dont le vrai client sur un faux réseau
```

## Limites honnêtes

- **Testé hors ligne seulement dans ce dépôt.** Les 39 tests et la simulation tournent sans réseau. Le vrai client Smartlead est testé contre des réponses simulées qui suivent la documentation. La logique vient d'un agent qui a tourné en production, mais ce dépôt en est une réécriture : faites un premier essai réel sur un contact de test.
- **La documentation de Smartlead se contredit** sur la forme de certaines réponses. Les lecteurs acceptent les deux formes documentées ; un message qu'ils ne savent pas lire est compté et signalé, jamais deviné. Les numéros de catégorie (« Interested » = 1, « Meeting Request » = 2) sont à vérifier sur votre compte.
- **Le classeur par mots-clés est grossier.** Il sert à tester. En production, utilisez le modèle, et rejouez vos vraies formulations avant de lancer.
- **L'agent ne règle pas la délivrabilité.** Il ne voit que les réponses. Une campagne qui rebondit lui envoie simplement moins de « oui » (piège n° 1).
- **Le double livrable à la réservation** se règle de votre côté : l'agent fournit `--booked`, votre outil de réservation doit l'appeler.
- Un seul outil d'envoi est branché (Smartlead). Un autre demande d'écrire un client de cinq méthodes.
- Respectez le droit de la prospection de votre pays : un « non » est honoré à la première demande, et l'agent ne doit écrire qu'à des personnes que vous avez le droit de contacter.

## Contribuer

Ouvrez une issue avec la commande, la sortie et, pour un problème d'API, la forme anonymisée de la réponse reçue. Gardez les exemples fictifs.

MIT pour le code, les instructions et les exemples de ce dépôt. Smartlead, Slack et les autres outils cités appartiennent à leurs éditeurs ; ce projet n'est affilié à aucun d'eux.

---
