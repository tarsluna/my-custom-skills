# Orchestration par sous-agents

## Le principe

Un sous-agent par source. Chacun a son CSV et son `BLOCKED.md`, et ne touche pas aux fichiers des autres. Une source qui échoue n'en bloque aucune autre.

Le nombre d'agents n'est pas le levier de volume : une dizaine suffit, ce sont les scripts parallèles qui font le volume. Lancer cent agents ajoute du bruit, pas des contacts.

## Découpage qui a tourné

| Agent | Rôle | Dépend de |
| --- | --- | --- |
| `registre` | Socle : `fetch_registry.py` | Rien, se lance d'abord |
| `sites-officiels` | Crawl des sites connus (registre, fiches ouvertes) | Registre |
| `afnic-domaines` | Croisement de la liste ouverte du .fr avec le registre, puis crawl et filtre | Registre |
| `open-data` | Jeux publics et OpenStreetMap | Rien |
| `annuaires` | Annuaires dont les conditions autorisent la réutilisation, un par un, avec citation | Rien |
| `qualite-fusion` | Tirages de contrôle, fusion, statistiques | Tous les autres |

Les agents de crawl ont besoin du socle : lance `registre` d'abord, en arrière-plan, et démarre-les quand `data/registre.csv` se remplit.

## Lancement d'un agent

Donne à chaque agent ce message, adapté :

> Lis `BRIEF.md` et `references/02-garde-fous.md`. Tu es l'agent `<nom>`. Ta source : `<décrire>`. Avant toute requête d'extraction, lis robots.txt et les conditions avec `scripts/read_terms.py`, écris `reviews/<nom>.json` avec le verdict et la citation exacte. Si c'est interdit, le script arrête la source et écrit `BLOCKED.md` : tu t'arrêtes là et tu le dis. Sinon, produis `sources/<nom>.csv` au schéma imposé. Lance les scripts longs en arrière-plan. Ne colle aucune donnée personnelle dans ton compte rendu. Compte rendu final : nombre de lignes, nombre avec prénom, sources utilisées, sources bloquées et pourquoi, chemin du fichier. N'annonce que ce que le fichier contient réellement.

## Ce que chaque agent laisse derrière lui

- `reviews/<nom>.json` : ce qui a été lu, quand, avec quel verdict.
- `sources/<nom>.csv` : ses lignes, avec `source_url` pour chacune.
- `data/raw/<nom>/BLOCKED.md` : les refus, avec la citation exacte ou le code HTTP.
- `data/raw/<nom>/statuses.tsv` et `evidence.jsonl` pour le crawl.

## Faire tenir un long passage

Un crawl dure des heures à 1 requête par seconde et par hôte. Les scripts reprennent seuls : relancer la même commande saute ce qui est fait. Une limite d'usage de l'agent ne coûte alors que du temps : relance et reprends où c'était.

Répartis un gros volume avec `--shard i/n` sur plusieurs lancements, en gardant la somme des `--workers` sous 40.
