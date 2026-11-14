# Fournir ses propres sons

Ce dépôt ne contient **aucun son ni musique** : nous ne pouvons pas garantir la licence de ceux utilisés en production. Tu fournis les tiens.

## Où les poser

Dans `<projet>/sounds/`, avec les noms attendus par `style.json` :

```json
"sfx": {
  "dir": "sounds",
  "keyword": [
    { "file": "whoosh.mp3", "offset": -0.14, "volume": 0.15 },
    { "file": "thump.mp3",  "offset": 0,     "volume": 0.8 }
  ],
  "zoom": { "file": "flick.mp3", "offset": -0.03, "volume": 0.5, "every": 2 }
}
```

- `keyword` : joués à chaque mot-clé. `offset` en secondes par rapport au mot-clé, `volume` de 0 à 1 ou plus.
- `zoom` : joué sur un changement de zoom sur `every`, sauf à moins de 0,5 s d'un mot-clé. Retire la clé `zoom` pour ne rien entendre sur les zooms.
- Un fichier absent est ignoré, avec un message. Le montage se construit quand même.

Trois sons suffisent :

| Rôle | Ce qu'il faut | Durée |
| --- | --- | --- |
| Whoosh | Souffle court, qui précède le mot-clé | Moins de 1 s |
| Thump | Impact grave, sur le mot-clé | Moins de 1 s |
| Flick | Clic léger, sur certains zooms | Moins de 0,4 s |

## Où les trouver

Cherche une licence claire qui autorise la publicité : CC0, ou une bibliothèque sous abonnement dont la licence couvre l'usage commercial. Garde la preuve de licence avec le projet. Une pub diffusée à grande échelle attire les réclamations.

## Régler le niveau

Les volumes par défaut sont un point de départ. Selon le fichier, un même `volume` donne un résultat très différent. Monte une pub courte, écoute au casque et au téléphone, puis `rerender.py`. Le son doit se sentir sans passer devant la voix.

## Tester sans son

Pour vérifier la chaîne, génère des sons factices. Ils ne sont pas faits pour être diffusés :

```bash
ffmpeg -f lavfi -i "anoisesrc=d=0.5:c=pink:a=0.5" -af "afade=t=in:d=0.2,afade=t=out:st=0.25:d=0.25" sounds/whoosh.mp3
ffmpeg -f lavfi -i "sine=f=70:d=0.35" -af "afade=t=out:d=0.35" sounds/thump.mp3
ffmpeg -f lavfi -i "sine=f=1500:d=0.08" -af "afade=t=out:d=0.08" sounds/flick.mp3
```

## Et la musique ?

Par défaut, pas de musique. C'est un choix de montage, voir les règles du [SKILL.md](../SKILL.md).
