# Les pièges rencontrés

Chacun de ces points s'est produit lors du lancement d'origine, ou se lit directement dans ses scripts. Les erreurs générales de l'API (budget en centimes, champs DSA, moyen de paiement) sont dans [autonomous-ad-publishing](https://github.com/gquthier/autonomous-ad-publishing). Les pièges du passage vers un formulaire instantané sont dans [lead-form.md](lead-form.md).

## Accès

**Le token ne voit pas la Page.** Le token était valide et le compte accessible, mais rien ne pouvait être créé : la Page n'était pas attribuée. Teste chaque ressource séparément, dès le début (`check`).

**Le token visible dans la liste des processus.** Passer le token en argument de `curl` l'expose à `ps`. Il passe ici par l'entrée standard.

## Vidéos

**Créer la créative trop tôt.** Une vidéo importée n'est pas utilisable tout de suite. On interroge `status.video_status` toutes les 15 secondes, jusqu'à 20 minutes.

**La vidéo refaite qui n'est jamais envoyée.** Le format a changé plusieurs fois pendant le montage. Une reprise voit une vidéo déjà importée et la saute : l'ancienne version partirait en diffusion. Ce soir-là, un nettoyage complet a réglé le problème avant le nouvel import. Le dépôt compare désormais la taille et la date du fichier.

**La vignette.** La créative vidéo d'origine reçoit un `image_hash`, tiré d'une image extraite à 1,2 seconde de la vidéo.

## Reprise

**Le doublon après coupure.** Si le réseau coupe après que Meta a créé l'objet, la réponse est perdue. Recommencer aveuglément crée un deuxième objet. On cherche donc d'abord par nom.

**Le fichier d'état écrasé.** Plusieurs envois tournaient en parallèle. Sans verrou ni fusion, le dernier à écrire efface le travail des autres.

**La limite de débit.** Les codes 4, 17, 32, 613, 80004 et le sous-code 4841018 demandent d'attendre, pas d'abandonner. On patiente 40 secondes, puis on réessaie. Le code 17 est revenu après une cinquantaine d'écritures d'affilée : relis ce qui existe avant de recréer.

## Structure

**Changer de conversion après coup.** Les adsets ont été recréés quand la conversion sur page merci a été décidée. Fixe-la avant `structure`.

**Une page d'arrivée à changer.** Une audience a reçu sa propre page après l'import. Pas besoin de refaire les pubs : `relink` crée une créative neuve et y rattache la pub existante.

**Le budget et le ciblage changés au dernier moment.** Ils ont été modifiés juste avant le lancement. Modifie la configuration, lance `structure --sync`, et laisse `go` comparer les valeurs.

## Activation

**Lancer avant que tout soit prêt.** La demande de lancement est arrivée alors que l'import n'était pas fini. Le contrôle du nombre de pubs doit rester bloquant, précisément dans ces moments-là.

**Une page d'arrivée tombée.** Un déploiement a retiré des pages de la production pendant quelques minutes, le soir même. Teste les pages juste avant l'activation, pas seulement au début.

**Croire la réponse d'activation.** Meta peut accepter le changement de statut, puis ne pas diffuser. Relis `effective_status` et `issues_info`. Juste après l'activation, `PENDING_REVIEW` est attendu.

## Nettoyage

**Effacer trop large.** Le nettoyage d'origine ne supprimait que les identifiants consignés dans l'état, pour ne jamais toucher à des campagnes existantes sur le même compte. Garde cette limite.

**Meta refuse d'effacer certaines vidéos.** Elles restent dans la bibliothèque du compte, sans être rattachées à une pub. C'est sans effet sur la diffusion. Elles sont listées dans `cleanup_failed`.

## Textes

**Le texte qui parle à la mauvaise audience.** Avec des variantes par adset, un copier-coller suffit. `audience_forbidden` l'attrape avant l'envoi.

**La première ligne trop longue.** Au-delà de 125 caractères, la fin de l'accroche passe derrière « Voir plus ».

## Mesure

**Le test compte.** Une visite de contrôle sur la page merci enregistre une conversion. Retire-la mentalement des premiers résultats.
