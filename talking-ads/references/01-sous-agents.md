# Le déroulé avec des sous-agents

Principe : **un brief unique, un sous-agent par pub**. Le brief porte tout ce qui doit être identique sur la série. La mission de chaque sous-agent ne porte que ce qui change.

## Avant de lancer

- `work/takes.json`, `work/faces.json`, `transcripts/` et `transcripts/text/` existent.
- `BRIEF.md` est rempli, plus aucun crochet.
- `style.json` est réglé et une pub pilote a été validée.
- `work/casting.md` liste les pubs.

Exemple fictif de casting :

| Pub | Prise(s) | Slug | Cible | Offre |
| --- | --- | --- | --- | --- |
| A01 | T01 | essai-14-jours | Salle de sport | 14 jours d'essai offerts |
| A02 | T03+T04 | reprise-apres-pause | Reprise du sport | Premier cours offert |
| A03 | T07 | sans-engagement | | 14 jours d'essai offerts |

Une case cible vide affiche l'offre seule sur l'horizontal.

## La mission type

Un sous-agent ne voit que ce que tu lui donnes. Donne-lui ceci, et rien d'autre à interpréter :

```text
Lis <projet>/BRIEF.md et applique-le entièrement.

Ta pub : A02.
Prises : T03 puis T04, la pub colle les deux.
Slug : reprise-apres-pause.
Hook : h_target « Reprise du sport », h_goal « Premier cours offert ».
Ne touche qu'à <projet>/ads/A02/.
```

Préviens le sous-agent de ce que le casting sait déjà : une prise où la personne parle encore après la fin, une phrase ratée à retirer, une prise qui démarre pendant que la personne s'installe.

## Lancer

- Fais partir les sous-agents **dans le même message**, pour qu'ils tournent en parallèle.
- Commence par une vague de 6. Monte à 12 si la machine suit. Chaque sous-agent lance des décodages 4K et des transcriptions, c'est là que la charge se joue.
- **Un seul rendu à la fois** : HyperFrames attend tout seul qu'un autre rendu soit fini. Ne contourne pas cette attente, deux rendus côte à côte s'affament.
- Les étapes `cut.py` et `caps.py` restent parallèles. Pour tenir la charge, `caps.py` et `seams.py` utilisent Whisper `medium` : `large-v3` a pris plus de 5 minutes pour 8 secondes de voix quand plusieurs montages tournaient.

## À la réception des rapports

Chaque rapport tient en six lignes et finit par ce qui reste douteux. Ouvre les planches, puis :

- Une erreur propre à une pub : relance son sous-agent avec la correction, ou corrige toi-même si c'est un mot.
- Une erreur qui se répète sur plusieurs pubs : c'est un défaut du brief ou d'un outil. Corrige la source, puis relance ce qui est touché. Ne laisse jamais chaque sous-agent contourner le problème dans son coin.
- Un outil corrigé en cours de série : les pubs déjà montées gardent l'ancien comportement. Liste-les et relance `rerender.py`, ou `cut.py` si la découpe est concernée.

## Ce qu'un sous-agent ne doit pas faire

- Modifier `style.json`, `BRIEF.md`, les outils ou une autre pub.
- Publier quoi que ce soit.
- Écrire « vérifié » pour ce qu'il n'a pas vérifié. Il lit des transcriptions et regarde des planches. Il n'écoute pas le film.
