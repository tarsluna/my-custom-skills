# Textes corrélés par adset

Chaque pub porte 5 textes principaux et 5 titres. Meta les combine. Le risque, avec des dizaines de pubs et plusieurs audiences, c'est qu'un texte destiné à une audience atterrisse sur une autre. La structure ci-dessous l'empêche.

## Qui dépend de quoi

| Élément | Dépend de | Écrit à partir de |
|---|---|---|
| Texte 1 | La vidéo | Sa transcription |
| Textes 2 à 5 | L'adset | L'angle propre à cette audience |
| Les 5 titres | L'adset | La promesse pour cette audience |
| Description | La vidéo | Son idée principale |
| Page d'arrivée | L'adset | Une page par audience si le discours diffère |
| Accroche incrustée | L'adset et la voix | Une liste fermée |

Le texte 1 reprend ce que la personne dit dans la vidéo : celui qui lit retrouve ce qu'il vient d'entendre. Écris-le depuis la transcription, pas de mémoire.

L'offre et l'appel à l'action terminent chaque texte. Le script les ajoute, pour qu'aucune variante ne les oublie.

## L'ordre de travail

1. Liste les audiences. Une audience = un adset = une page d'arrivée si le discours change.
2. Range chaque vidéo dans un adset, selon ce qui y est dit.
3. Écris les 5 titres et les 4 variantes de chaque adset.
4. Écris le texte 1 et la description de chaque pub, depuis sa transcription.
5. Renseigne les interdits : mots bannis, et termes réservés à l'autre audience.
6. Lance `copy`, corrige, fais relire `textes-a-relire.txt`.

## Ce que `copy` contrôle

- Exactement 5 textes et 5 titres par pub.
- Première ligne de 125 caractères au plus, car le reste est replié derrière « Voir plus ».
- L'offre et l'appel à l'action présents dans chaque texte.
- Le mot obligatoire présent dans chaque titre.
- Aucun mot interdit, dans les textes, les titres ou la description.
- Aucun terme réservé à l'autre audience.
- Une accroche incrustée prise dans la liste fermée de l'adset.
- Une page d'arrivée qui ne contient pas le fragment de la conversion.

Ces contrôles ne jugent pas la qualité du texte, ni la véracité d'une promesse. Une garantie ou un chiffre annoncé doit être vérifié par la personne qui en répond.

## L'accroche incrustée

L'accroche écrite sur la vidéo horizontale fait partie de la corrélation. Deux règles viennent du terrain :

- **Liste fermée.** L'accroche contient la cible, l'offre, ou les deux, et rien d'autre.
- **Elle ne contredit pas la voix.** Si la vidéo annonce une autre promesse à l'oral, garde une accroche compatible avec ce qui est dit, même si elle diffère du reste de l'adset.

## Côté API

Le lien et le bouton vont dans `object_story_spec.video_data`. Les variantes vont dans `asset_feed_spec`, avec `optimization_type` à `DEGREES_OF_FREEDOM`.

```json
{
  "object_story_spec": {
    "page_id": "PAGE",
    "video_data": {
      "video_id": "VIDEO",
      "image_hash": "HASH",
      "call_to_action": {"type": "LEARN_MORE", "value": {"link": "https://exemple.test/"}}
    }
  },
  "asset_feed_spec": {
    "bodies": [{"text": "Texte 1"}],
    "titles": [{"text": "Titre 1"}],
    "descriptions": [{"text": "Description"}],
    "optimization_type": "DEGREES_OF_FREEDOM"
  }
}
```

Cette combinaison a fonctionné en v23.0. La documentation de Meta montre `DEGREES_OF_FREEDOM` avec 5 textes et 5 titres, mais ne décrit pas son association avec `video_data` : teste une pub de bout en bout avant d'importer le reste, surtout sur une version plus récente de l'API.

Une créative publiée ne se modifie pas : `relink` en crée une neuve et y rattache la pub.
