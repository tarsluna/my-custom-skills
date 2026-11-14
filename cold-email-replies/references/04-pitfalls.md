# Les pièges du premier jour en production

Ce qui s'est réellement passé le jour où l'agent a servi ses premiers « oui ». Les chiffres sont arrondis ; le métier et les noms sont retirés.

## 1. Un tiers des mails a rebondi, presque tous vers Gmail

**Ce qui s'est passé.** Au premier soir de campagne, environ un tiers des envois avaient rebondi, et la grande majorité des rebonds visaient des adresses Gmail. Les boîtes d'envoi étaient sur un autre domaine que la marque de l'agence, et Gmail les refusait.

**Pourquoi c'est grave pour l'agent.** Un rebond est un prospect qui ne répondra jamais. L'agent ne voit que les réponses : il ne peut pas signaler un problème de délivrabilité, il reçoit juste moins de « oui ».

**Ce qu'il faut faire.**
- Avant de lancer : `python3 scripts/run.py --check-leads contacts.csv` donne la part de Gmail, Microsoft et autres messageries grand public dans la liste.
- Envoyez une petite vague d'abord et regardez le taux de rebond par fournisseur dans l'outil.
- Si Gmail refuse : sortez les messageries grand public de la campagne, ou changez de boîtes d'envoi (domaine proche de la marque, SPF, DKIM et DMARC alignés, boîtes chauffées). C'est une décision humaine : l'agent ne touche pas à la campagne.

## 2. Le prospect qui réserve peut recevoir l'audit une deuxième fois

**Ce qui s'est passé.** Le mail de l'agent contient l'audit et un lien de réservation. Or l'outil de réservation avait déjà sa propre automatisation : à chaque rendez-vous, il fabriquait et envoyait un « pré-audit avant l'appel ». Un prospect venu du cold email aurait donc reçu le même audit deux fois. Le doublon a été repéré le jour même, pas corrigé.

**Ce qu'il faut faire.**
- Donnez au cold email un **événement de réservation dédié**. Vous saurez d'où vient chaque rendez-vous, et l'automatisation de réservation pourra traiter ces rendez-vous à part.
- Avant que l'automatisation de réservation n'envoie quoi que ce soit, demandez à l'agent :

  ```bash
  python3 scripts/run.py --booked prospect@entreprise.example --json
  # {"already_sent": true, "deliverable_url": "https://…", "answered_at": "…"}
  ```

  Si `already_sent` vaut `true`, n'envoyez pas de deuxième livrable : un rappel du rendez-vous avec le même lien suffit. La commande pousse aussi l'étape « Appel booké » au CRM.

## 3. La campagne n'envoie qu'en semaine, aux heures de bureau

**Ce qui s'est passé.** Le soir, plus aucune réponse n'arrivait depuis le milieu d'après-midi. Ce n'était pas l'agent : la campagne était réglée sur les jours ouvrés, aux heures de bureau.

**Ce qu'il faut faire.** Avant de chercher une panne, regardez le planning de la campagne, puis `--status`. Une réponse reçue la nuit est traitée à la sonde suivante, quel que soit le planning d'envoi.

## 4. Un e-mail en échec s'affichait comme un succès

**Ce qui s'est passé.** Côté CRM, un envoi refusé était affiché comme parti. Corrigé le jour même.

**La règle qui en sort, appliquée partout ici.** Un statut « envoyé » ne se pose que sur une confirmation lue dans le corps de la réponse. Un 200 avec `success: false` est un refus. Un 200 illisible est un doute. Le CRM et l'alerte « audit envoyé » ne partent qu'après une confirmation. Voir le tableau de [03-smartlead.md](03-smartlead.md).

## 5. L'outil d'envoi classe aussi : en tenir compte, sans le laisser décider

**Ce qui s'est passé.** Smartlead pose sa propre étiquette (« Interested », « Meeting Request »). Des demandes de rendez-vous n'étaient pas traitées comme des « oui » par l'agent. Elles le sont devenues, et l'étiquette de l'outil a été ajoutée comme second avis.

**La règle.** L'étiquette de l'outil confirme un oui quand l'agent hésite. Elle ne retourne jamais un « non », un report ou une absence. Détail dans [02-classification.md](02-classification.md).

## 6. Une vingtaine de minutes entre le « ok » et l'audit

**Ce qui s'est passé.** Le premier « ok » réel a reçu son audit une vingtaine de minutes plus tard : le temps de fabriquer un audit personnalisé. Le prospect a ensuite décliné l'appel.

**Ce qu'il faut faire.**
- L'alerte « NOUVEAU LEAD » part dès le classement, sans attendre le livrable. Elle dit que le livrable partira tout seul : **personne ne répond à la main pendant ce temps**, sinon le prospect reçoit deux messages.
- Un livrable toujours pas prêt au bout de 36 h (`deliverable.stuck_hours`) passe en alerte, sans réponse automatique.
- L'audit seul ne suffit pas à obtenir le rendez-vous. Depuis ce premier refus, le mail propose explicitement un appel pour présenter le reste, avec le lien de réservation. Gardez cette phrase.

## 7. Les données de test se retrouvent dans le CRM

**Ce qui s'est passé.** Le soir même, il a fallu trier les fiches de test des vraies dans le pipeline.

**Ce qu'il faut faire.** Testez avec `--dry-run` : il ne touche ni l'outil d'envoi, ni Slack, ni le CRM. Pour l'essai réel, un seul contact de test, nommé comme tel, supprimé après. Les événements CRM portent une clé d'idempotence (`Idempotency-Key`) : votre CRM peut ignorer un doublon.

## 8. Au premier démarrage, l'historique est ignoré

Le filigrane posé au premier démarrage empêche l'agent de répondre à des réponses vieilles de plusieurs jours, que l'équipe a peut-être déjà traitées. Conséquence : les réponses antérieures restent à traiter à la main. Lancez l'agent avant la campagne, pas après.
