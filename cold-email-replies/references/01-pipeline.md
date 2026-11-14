# Une sonde, étape par étape

L'agent tourne en boucle (`--loop`, toutes les 3 minutes par défaut) ou par cron (`--once`). Chaque sonde fait les mêmes étapes, dans cet ordre, et chacune reprend là où la précédente s'est arrêtée.

| # | Étape | Ce qui se passe | Garde-fou |
| --- | --- | --- | --- |
| 0 | Verrou | Une seule sonde à la fois, même si deux processus se recouvrent pendant un déploiement | Verrou en base, expire seul après 15 min |
| 1 | Filigrane | Au tout premier démarrage, l'heure courante est notée. Les réponses plus anciennes sont ignorées | Pas de rafale de réponses sur un historique ancien |
| 2 | Envois interrompus | Une réponse restée « en cours d'envoi » plus de 10 min vient d'un arrêt brutal | Passée en « envoi incertain » + alerte. **Jamais renvoyée** |
| 3 | Lecture | Pour chaque campagne : contacts qui ont répondu, puis leur fil. Une ligne par message reçu | Clé = identifiant du message : relire ne crée rien. Le curseur n'avance que si tout a été lu |
| 4 | Classement | Le texte, sans fil cité, sans adresse ni numéro, part au classeur | 5 échecs de suite : à traiter à la main + alerte |
| 5 | Désinscriptions | Les « non » : désinscription de toutes les campagnes, puis liste de blocage | Chaque étape notée : on ne refait que celle qui manque |
| 6 | Commande du livrable | Les « oui » : livrable commandé, ou réutilisé s'il existe déjà pour ce domaine | Plafond par jour, compté et réservé dans la même transaction |
| 7 | Réponse | Livrable prêt : réponse dans le fil d'origine avec le lien et le lien de réservation | L'envoi est réservé en base **avant** l'appel à l'outil. Une seule réponse par contact, garantie par un index unique |
| 8 | Alertes | Slack reçoit les alertes dues, dans l'ordre | Une alerte refusée reste due et repart à la sonde suivante |
| 9 | CRM | Le CRM reçoit les événements dus | Clé d'idempotence par événement |

## Les statuts d'une réponse

```text
received ──► classée
   ├─ non ─────────────► unsubscribe_pending ──► unsubscribed
   ├─ absence, plus tard ► recorded
   ├─ question, doute ──► review                      (alerte, réponse à la main)
   └─ oui, rendez-vous ─► queued ──► waiting ──► sending ──► answered
                            │           │           ├─► send_failed      (refus de l'outil, alerte)
                            │           │           └─► send_uncertain   (résultat inconnu, alerte, jamais renvoyé)
                            │           └─► deliverable_failed           (livrable en échec ou bloqué 36 h, alerte)
                            └─► cancelled                                 (un « non » est arrivé entre-temps)
```

## Ce qui ne peut pas arriver

- **Deux réponses au même contact.** Deux « ok » donnent deux lignes, mais l'index `replies_one_answer` refuse de réserver un deuxième envoi pour le même contact de la même campagne. Le deuxième « ok » ne déclenche pas non plus une deuxième alerte.
- **Une réponse renvoyée après un doute.** Un délai dépassé, une erreur 5xx ou un arrêt en plein envoi peuvent cacher un mail parti. Dans ces trois cas l'agent s'arrête et prévient. Seul un 429 prouve que rien n'est parti : celui-là est retenté à la sonde suivante.
- **Une réponse à un « non ».** Un refus est honoré à toute confiance. Un « non » arrivé après un « oui » annule l'envoi en attente. Une réponse plus récente pas encore classée retient l'envoi jusqu'à son classement.
- **Un livrable payé pour rien.** Sans identifiant de fil, la réponse ne pourrait pas partir : le livrable n'est pas commandé. Même chose pour un contact déjà désinscrit, ou sans domaine exploitable quand le livrable en demande un.
- **Une alerte perdue.** Chaque alerte est une ligne dans une file. Une colonne « dernière alerte » par réponse perdrait la première quand deux arrivent dans la même sonde, par exemple « NOUVEAU LEAD » puis « audit envoyé » quand le livrable est réutilisé et part tout de suite.

## Où vit l'état

Un fichier SQLite (`REPLY_AGENT_DB`, `reply-agent.sqlite3` par défaut). Tables : `replies` (une ligne par message reçu), `deliverables`, `alerts` et `crm_events` (deux files de sortie), `settings` (filigrane, curseurs, verrou, alertes quotidiennes).

Sur un hébergement à disque éphémère, mettez ce fichier sur un volume persistant. Perdu, il fait repartir le filigrane à zéro : rien n'est renvoyé, mais les réponses en cours sont oubliées et doivent être reprises à la main.

`python3 scripts/run.py --status` liste les réponses par statut et celles qui attendent un humain.
