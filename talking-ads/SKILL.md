---
name: talking-ads
description: Transforme un dossier de prises face caméra en une série de pubs montées, chacune livrée en vertical plein cadre et en horizontal 16:9 sur fond flouté. Montage volontairement simple, du texte et rien d'autre (sous-titres, mots-clés en gros au centre, hook sur l'horizontal), zooms réguliers, effets sonores, vidéo complète de A à Z. Un sous-agent par pub, à partir d'un brief unique. Utilise ce skill pour « monter mes pubs », « talking ads », « talking head ads », « pubs face caméra », « monter une série de prises », « batch facecam ads », « faire mes pubs en vertical et horizontal », ou pour corriger et re-rendre une série déjà montée, même si l'utilisateur ne nomme pas le skill. Pas pour un short très animé à partir d'une seule prise.
---

# Talking ads

D'un dossier de prises face caméra à N pubs montées, chacune en deux formats. La langue par défaut est le français, elle se change dans `project.json`.

`<skill>` est le dossier qui contient ce `SKILL.md`. Tous les outils prennent le dossier du projet en premier argument. `init_project.py` et `show.py` mis à part, tous acceptent `--dry-run`.

| Fichier | À lire pour |
| --- | --- |
| [references/01-sous-agents.md](references/01-sous-agents.md) | Le casting, la mission type, le lancement et le retour des sous-agents |
| [references/02-fichiers.md](references/02-fichiers.md) | `project.json`, `style.json`, `edit.json`, `captions.json`, `plan.json` |
| [references/03-sons.md](references/03-sons.md) | Fournir ses propres effets sonores |
| [references/04-pieges.md](references/04-pieges.md) | Ce qui a cassé en production et comment l'éviter |
| [template/BRIEF.md](template/BRIEF.md) | Le brief unique que reçoit chaque sous-agent |

## Règles par défaut

Elles viennent des retours reçus pendant une vraie série. Ne les change que si l'utilisateur le demande.

1. **Du texte, rien d'autre.** Le visage, les sous-titres, les mots-clés, le hook, des effets sonores. Pas d'animation de début ou de fin, pas de carte, de logo, d'image, de b-roll, de motion design, de musique.
2. **Vidéo complète de A à Z.** Du premier au dernier mot, y compris le mot d'ouverture et la dernière phrase. On ne retire que le déchet évident : faux départs, phrases recommencées, rires, apartés.
3. **Zooms réguliers.** Coupe de zoom à chaque raccord et toutes les 3 à 4 s sur un début de groupe, plus une légère poussée continue, dans les deux formats. C'est `gen.py` qui les place.
4. **Le sous-titre et les mots-clés dans la même police**, serrée, sans fond ni ombre.
5. **Le vertical ne porte pas de hook.** L'horizontal affiche la cible et l'offre au-dessus de la vidéo, pendant toute la durée.
6. **Rien d'inventé à l'écran.** Un mot-clé reprend ce qui est dit dans la prise. Une offre du hook vient de la liste du brief.
7. **Local par défaut.** On monte et on livre sur la machine. Publier ou lancer une campagne demande une consigne à part.

## Ce que tu livres

```text
<projet>/
├── BRIEF.md, project.json, style.json
├── work/takes.json, faces.json     Inventaire et position du visage
├── ads/A01/
│   ├── edit.json, captions.json, plan.json
│   ├── hf-v/, hf-h/                Compositions HyperFrames
│   └── qa/Vertical.jpg, Horizontal.jpg
└── out/<nom>-A01-<slug>-Vertical.mp4, <nom>-A01-<slug>-Horizontal.mp4
```

Les deux fichiers sont en 1080×1920. Vertical : le visage recadré plein cadre. Horizontal : la vidéo 16:9 au milieu, fond = la même vidéo floutée.

## Déroulé

### 1. Créer le projet

```bash
python3 <skill>/scripts/init_project.py <projet> --rushes <dossier-des-prises> --name MaMarque
```

Renseigne `project.json` : `language`, `mirror` si la caméra enregistre l'image retournée, `takes.exclude` si des captures d'écran traînent dans le dossier. Pose les effets sonores dans `<projet>/sounds/` ([03-sons.md](references/03-sons.md)). Sans son, le montage se construit quand même, en silence d'effets.

**Ne prends jamais une capture d'écran ou une sortie programme comme source.** Elles peuvent montrer des fenêtres privées. Vérifie la liste affichée par l'étape 2.

### 2. Inventorier et transcrire

```bash
python3 <skill>/scripts/extract_audio.py <projet>   # numérote T01, T02... et extrait l'audio
python3 <skill>/scripts/transcribe.py <projet>      # temps mot à mot
python3 <skill>/scripts/text_pass.py <projet>       # texte fidèle
python3 <skill>/scripts/faces.py <projet>           # position médiane du visage
```

### 3. Faire le casting

Lis tous les textes de `transcripts/text/`. Regroupe : quelle prise fait quelle pub, laquelle est ratée ou doublon, quelles prises se complètent. Une pub peut coller deux prises. Écris `work/casting.md`, une ligne par pub : identifiant, prise(s), slug, cible, offre. Ne demande à l'utilisateur que ce que le texte ne permet pas de trancher.

### 4. Figer le brief

Remplis ce qui est entre crochets dans `<projet>/BRIEF.md`, règle `style.json` (police, couleurs, tailles). C'est ce fichier unique qui garde une série cohérente.

### 5. Monter une pilote, et la faire valider

Prends la pub la plus courte et fais-la entièrement toi-même. Montre-la. **Ne lance rien d'autre avant le retour sur cette pilote.** Une série réelle a changé de format trois fois après le premier rendu, avec plusieurs montages déjà partis : chaque changement a coûté un rendu complet.

### 6. Lancer un sous-agent par pub

Une pub égale un sous-agent. Chacun reçoit `BRIEF.md` et sa ligne de casting, ne touche que `ads/<ID>/`, et rend un rapport de six lignes. Mission type, taille des vagues et gestion des retours : [01-sous-agents.md](references/01-sous-agents.md).

Si le runtime n'a pas de sous-agents, enchaîne les pubs une à une avec le même brief.

### 7. Contrôler et corriger

Regarde toutes les planches `qa/`. Reprends chaque doute des rapports. Selon ce qui change :

| Changement | À relancer |
| --- | --- |
| Style, police, couleurs, zooms, effets sonores | `rerender.py <projet>` |
| Hook, mots-clés | `plan.json`, puis `rerender.py <projet> A01` |
| Plusieurs mots-clés à ajouter | `topup.py <projet> ajouts.json`, puis `rerender.py` |
| Texte d'un sous-titre | `captions.json`, puis `rerender.py <projet> A01` |
| Une coupe | `edit.json`, puis `cut.py`, `seams.py`, `caps.py`, relecture, `gen.py`, `finish.py` |
| Cadrage du début | `track.py`, puis `cut.py`, et la suite comme une coupe |

### 8. Livrer

Donne le dossier, le nombre de pubs, la durée de chacune, et la liste de ce qui reste douteux. **Dis clairement que personne n'a écouté les films en continu** si c'est le cas : les outils lisent des transcriptions et des niveaux, ils n'entendent pas une voix qui remonte à un raccord.

Pour ouvrir les vidéos ailleurs : `finish.py <projet> A01 <slug> --deliver <dossier>` ou `rerender.py <projet> --deliver <dossier>`.

## Pièges à garder en tête

Détail dans [04-pieges.md](references/04-pieges.md). Les trois qui coûtent le plus cher :

- Un sous-agent qui coupe trop tôt. La dernière phrase disparaît et personne ne le voit sur une planche. Le texte retranscrit de `voice.wav` doit finir sur le dernier mot.
- Les temps mot à mot ont plusieurs dixièmes d'écart. Une coupe posée sur eux tombe dans un mot. `seams.py` le signale par « A REVOIR ».
- Lancer la série avant d'avoir validé une pilote.

## Hors périmètre

Pour un short très animé à partir d'une seule prise, ce skill n'est pas le bon outil : le dépôt public `autonomous-shortform-facecam-editing` couvre ce cas en motion design.
