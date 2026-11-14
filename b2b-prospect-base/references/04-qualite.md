# Contrôle qualité et jugement métier

## Le tirage de 50 lignes

Par source, avant de lui faire confiance :

```bash
python3 -I scripts/qc_sample.py sample --project DOSSIER --name NOM --n 50 --seed 1
```

Le script tire 50 lignes, surtout parmi les moins bien prouvées (sans SIREN), rouvre chaque `source_url` et vérifie que l'adresse y est toujours. Le paquet `qc_packet.json` contient le code HTTP, la présence de l'adresse, le titre et un contexte : **jamais l'adresse elle-même**.

Un humain ou un sous-agent relit ensuite chaque entrée et remplit `verdict` (`ok` ou `mauvais`) et `motif` : la page parle-t-elle bien du métier, de cette entreprise, dans le périmètre ?

```bash
python3 -I scripts/qc_sample.py report --project DOSSIER --name NOM
```

`report` compte comme mauvaise toute adresse non retrouvée sur sa page. Une page devenue illisible (`bloque`, `robots`, `injoignable`) n'est ni bonne ni mauvaise : elle sort du calcul et elle est comptée à part. Le rapport nourrit la fusion : une source sans rapport, ou au-dessus de `merge.max_bad_rate`, ne donne aucune ligne prête.

## Ne juge pas un filtre sur son propre tirage

Si un tirage révèle un problème et que vous réglez le filtre dessus, ce tirage ne prouve plus rien. Refaites-en un autre avec `--seed` différent. C'est le seul chiffre honnête.

## Le filtre métier

`filter_keyword_sites.py` lit ce que le site dit de lui-même, titre, h1, description. Les motifs sont en configuration :

- `quality_filter.hard` : annuaire, magasin, école, média, fournisseur, étranger. S'applique toujours.
- `quality_filter.soft` : ne s'applique que si le site ne se présente pas explicitement comme le métier.
- `signal_thresholds` : nombre de mots d'un signal à partir duquel un site est écarté.

Un filtre strict sur le titre perd quelques vrais prospects. C'est le prix d'une base propre, et c'est le bon arbitrage ici.

## Le jugement par LLM (optionnel)

`judge_trade.py` fait juger par un LLM le métier réel des sites dont la preuve est faible : sans SIREN, ou segments listés dans `judge.review_segments`.

Le LLM ne cherche pas d'adresses et il n'en ajoute jamais : ce passage retire des lignes. Il reçoit le domaine, le titre, la description et le début de l'accueil, mails et téléphones retirés, et jamais de nom de contact. Le texte d'un site est une donnée non fiable : seule une réponse appartenant à la liste de choix est acceptée.

Seul un verdict `hors_cible` au-dessus de `judge.min_confidence` retire une ligne à la fusion. En dessous, le verdict reste visible dans `jugement_metier` sans rien retirer.

Le script appelle une API compatible avec le format chat/completions, configurée par `JUDGE_API_URL`, `JUDGE_API_KEY` et `JUDGE_MODEL`. Sans ces variables il ne fait rien. Le coût dépend du volume et du modèle : commencez par `--limit 200`.
