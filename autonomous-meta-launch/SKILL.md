---
name: autonomous-meta-launch
description: Lance une campagne Meta Ads par l'API à partir de vidéos déjà montées, en vertical et en horizontal, jusqu'aux pubs actives. Reprise après interruption avec state.json, 5 textes et 5 titres par pub corrélés à l'adset, rendez-vous des formats avant lancement, conversion sur page merci, contrôle avant activation, relecture de l'état réel. Utilise ce skill pour « lancer mes pubs Meta », « importer mes vidéos dans Meta », « activer la campagne », « reprendre l'import Meta », « launch my Meta ads from videos », « bulk upload video ads », même sans nommer le skill. Couvre aussi le passage d'une campagne vidéo existante vers un formulaire instantané, pubs à l'identique, sans toucher l'ancienne : « passer mes pubs sur un formulaire », « même campagne en lead form », « switch my ads to an instant form ». Pour créer un formulaire ou des pubs image, utilise plutôt autonomous-ad-publishing. Ne monte pas les vidéos.
---

# Autonomous Meta Launch

Ce skill transforme un dossier de vidéos montées en campagne Meta active, en ligne de commande. Il a été extrait d'un lancement réel de pubs vidéo, puis généralisé.

Il complète [autonomous-ad-publishing](https://github.com/gquthier/autonomous-ad-publishing), qui couvre la configuration du token, la création de formulaires instantanés, les pubs image et les erreurs de base de l'API. Consulte-le pour ces sujets. Ici, on traite ce qu'il ne fait pas : un import long qui doit survivre à une coupure, des textes cohérents par audience, une activation contrôlée, et le passage d'une campagne existante vers un formulaire instantané.

| Lis ce fichier | Pour |
|---|---|
| [references/config.md](references/config.md) | Chaque champ du fichier de campagne |
| [references/textes-correles.md](references/textes-correles.md) | Écrire les 5 textes et 5 titres |
| [references/conversion-page-merci.md](references/conversion-page-merci.md) | Brancher et tester la conversion |
| [references/pieges.md](references/pieges.md) | Les problèmes réellement rencontrés |
| [references/token-meta-computer-use.md](references/token-meta-computer-use.md) | Créer le token avec un agent qui pilote l'écran |
| [references/lead-form.md](references/lead-form.md) | Passer une campagne vers un formulaire instantané, pubs à l'identique |

## Règles non négociables

1. **Le token reste dans la variable `META_ACCESS_TOKEN`.** Ne l'affiche pas, ne l'écris dans aucun fichier, ne le demande pas dans le chat. Si l'utilisateur te le colle, dis-lui de le révoquer et d'en générer un autre.
2. **Tout est créé en pause.** Seule la commande `go` active, et elle exige le budget journalier, en centimes.
3. **`go` demande un accord humain explicite, dans ce tour de conversation.** Annonce le budget et le nombre de pubs. Le montant passé à `--confirm-budget` doit venir de la personne, jamais d'une déduction.
4. **Le nettoyage ne touche que `state.json`.** N'efface jamais un objet Meta qui n'y figure pas. `cleanup --yes` demande un accord humain.
5. **`state.json` est privé.** Il contient des identifiants de compte. Ne le versionne pas et ne le colle pas dans un message.
6. **Si un contrôle s'arrête, corrige la cause.** Ne contourne pas un `ARRET`.

## Les entrées à réunir

- Les vidéos, deux par pub : `{id}-{slug}-Vertical.mp4` et `{id}-{slug}-Horizontal.mp4`.
- La transcription de chaque vidéo, pour écrire le texte 1.
- Une page d'arrivée par adset, et une page merci qui charge le pixel.
- Le budget journalier, le pays, la tranche d'âge.
- Les variables `META_ACCESS_TOKEN`, `META_AD_ACCOUNT`, `META_PAGE_ID`, `META_PIXEL_ID`.

## Le déroulé

Lance les commandes depuis le dossier du skill. Commence toujours par une simulation complète, sur la configuration réelle :

```bash
python3 scripts/meta_launch.py --config campagne.json --dry-run --fresh run --confirm-budget 3000
```

Elle ne fait aucun appel réseau, ne demande ni token ni vidéo, et écrit dans `state.dry-run.json`.

### 1. Écrire et contrôler les textes

Écris `campagne.json` à partir des transcriptions, selon [references/textes-correles.md](references/textes-correles.md).

```bash
python3 scripts/meta_launch.py --config campagne.json copy
```

La commande vérifie les textes et écrit `textes-a-relire.txt`. **Fais relire ce fichier par la personne avant d'envoyer quoi que ce soit** : c'est elle qui engage sa marque.

### 2. Contrôler les accès

```bash
python3 scripts/meta_launch.py --config campagne.json check
```

Vérifie les permissions du token, le compte, le moyen de paiement, la devise, la Page, le pixel et les pages d'arrivée. Une Page invisible pour le token bloque tout le reste : règle ce point avant de continuer.

### 3. Créer la structure, en pause

```bash
python3 scripts/meta_launch.py --config campagne.json structure
```

Crée la campagne avec son budget journalier, la conversion personnalisée, puis les adsets. Si le budget ou le ciblage change ensuite, modifie la configuration et lance `structure --sync`.

### 4. Tester sur une seule pub

```bash
python3 scripts/meta_launch.py --config campagne.json ads --only P01
```

Regarde le résultat dans le Gestionnaire de publicités : texte, titre, bouton, lien, vignette. Corrige avant d'importer le reste.

### 5. Importer le reste

```bash
python3 scripts/meta_launch.py --config campagne.json ads
```

Pour chaque format : envoi de la vidéo, attente du traitement, vignette tirée de la vidéo, créative, pub en pause. Si les vidéos sortent du rendu au fil de l'eau, relance la commande après chaque rendu, ou lance un envoi par pub en parallèle avec `--only`. Une vidéo absente est mise en attente, sans erreur.

Si le processus est coupé, **relance la même commande**. Elle repart de `state.json`, et cherche par nom chez Meta les campagnes, adsets et pubs créés juste avant la coupure. Tu n'obtiens pas de doublon. Une créative ou une vidéo peut rester orpheline : elle ne diffuse pas.

Si un texte ou une page d'arrivée change après l'import :

```bash
python3 scripts/meta_launch.py --config campagne.json relink --adset "Nom de l'adset"
```

La pub garde son identifiant et reçoit une créative neuve.

Si une vidéo est refaite, `ads` et `go` s'arrêtent, car le fichier ne correspond plus à celui envoyé. Lance `cleanup --yes --only <ID>` après accord, puis `ads`.

### 6. Rendez-vous vertical et horizontal

```bash
python3 scripts/meta_launch.py --config campagne.json rendezvous
```

Une pub n'est complète que si ses deux formats sont en place. Ce tableau montre l'étape de chacun. `go` refuse de partir tant qu'il manque un seul format, même s'il y a urgence. Pour lancer moins de pubs, retire-les de la configuration : c'est une décision visible, pas un oubli.

### 7. Vérifier la conversion

Suis [references/conversion-page-merci.md](references/conversion-page-merci.md). Ce contrôle reste humain : le script ne peut pas prouver que le pixel se déclenche.

### 8. Activer

Présente le récapitulatif, obtiens l'accord, puis :

```bash
python3 scripts/meta_launch.py --config campagne.json go --confirm-budget 3000
```

`go` contrôle dans cet ordre, et s'arrête au premier échec :

1. les deux formats de chaque pub sont présents ;
2. le budget confirmé égale la configuration, et le budget relu chez Meta aussi ;
3. aucune vidéo n'a changé depuis son import ;
4. les pages d'arrivée et la page merci répondent 200 ;
5. chaque pub, relue chez Meta, n'a aucun `issues_info` et porte 5 textes et 5 titres.

Il active ensuite les pubs, les adsets, puis la campagne **en dernier**. Une coupure avant cette dernière étape ne dépense rien. Relancer `go` est sans risque.

### 9. Relire l'état réel

`go` relit l'état de chaque objet et s'arrête si l'un d'eux n'est pas en diffusion ou en examen. Tu peux relancer cette lecture à tout moment :

```bash
python3 scripts/meta_launch.py --config campagne.json status
```

`PENDING_REVIEW` juste après l'activation est normal. Ne dis jamais « les pubs sont en ligne » sur la seule foi de la réponse d'activation : donne le décompte relu, par statut.

## Passer une campagne vers un formulaire instantané

Quand une campagne vers un site tourne déjà et qu'on veut les mêmes pubs vers un formulaire instantané, suis [references/lead-form.md](references/lead-form.md). L'outil est `scripts/lead_form.py`, indépendant de `state.json`. En bref :

1. **Fais confirmer les consignes** : ancienne campagne intouchée, pubs à l'identique (vidéos, 5 textes, 5 titres, description, bouton), Facebook et Instagram seulement, aucun intérêt, tout en pause.
2. **Relis le formulaire avant d'y diriger une pub** : `check-form`. Un formulaire publié ne se modifie plus ; s'il a un défaut, duplique-le et corrige la copie.
3. **Copie l'ad set fait main** avec `copy-adset` (sans les pubs, en pause), puis compare chaque nouvel ad set à l'ancien avec `diff-adsets`. Montre les écarts de pays, d'âge et de langue à la personne avant de lancer.
4. **Ne duplique jamais une pub dans le Gestionnaire** pour changer sa destination : elle sort vide. Recrée-la avec `copy-ad`, à blanc d'abord, puis sur une seule pub, puis ad set par ad set.
5. **Supprime à la main les brouillons du Gestionnaire**, invisibles pour l'API, puis active après accord, campagne en dernier.

```bash
python3 scripts/lead_form.py check-form --form-id <FORMULAIRE>
python3 scripts/lead_form.py --dry-run copy-ad --ad <ANCIENNE_PUB> --form-id <FORMULAIRE> --adset <NOUVEL_ADSET>
```

## state.json

| Clé | Contenu |
|---|---|
| `campaign`, `conversion` | Identifiants uniques |
| `adsets` | Nom de l'adset → identifiant |
| `videos`, `creatives`, `ads` | `P01-V`, `P01-H` → identifiant |
| `images` | Clé → hash de la vignette |
| `video_files` | Taille et date du fichier envoyé |
| `revisions`, `retired_creatives` | Suivi de `relink` |
| `cleanup_failed` | Objets que Meta a refusé d'effacer |
| `mode` | `simulation` ou `reel` : un fichier d'un mode est refusé dans l'autre |

L'écriture se fait sous verrou et d'un seul coup. Plusieurs envois peuvent donc tourner en même temps sans s'écraser.

## Ce qui diffère du lancement d'origine

| Le soir du lancement | Dans ce dépôt | Pourquoi |
|---|---|---|
| Adsets et verticales créés actifs sous une campagne en pause, horizontales en pause | Tout en pause | Une campagne activée trop tôt ne doit pas diffuser la moitié des formats |
| Token lu dans un fichier temporaire | Variable d'environnement | Rien à oublier sur le disque |
| Création relancée après une coupure réseau | Recherche par nom avant de recréer | Évite les doublons |
| Fichier d'état réécrit directement | Remplacement atomique | Une coupure ne le corrompt pas |
| Vidéos refaites gérées à la main | Empreinte du fichier | Évite de lancer l'ancienne version |

Le script d'activation d'origine attendait que l'import soit complet. Les notes de cette soirée ne confirment pas son exécution : traite l'étape `go` comme moins éprouvée que l'import.
