# Le fichier de campagne

Tout ce qui dépend du métier est dans un fichier JSON. Exemple complet et fictif : [`examples/paysagistes/campagne.json`](../examples/paysagistes/campagne.json). Les identifiants de compte n'y figurent pas : ils viennent de l'environnement.

## `campaign`

| Champ | Rôle |
|---|---|
| `name` | Nom de la campagne, et préfixe des créatives |
| `objective` | Par défaut `OUTCOME_LEADS` |
| `daily_budget_minor` | Budget journalier de la campagne, en centimes. 3000 = 30,00 € |
| `currency` | Comparée à la devise du compte par `check` |
| `bid_strategy` | Par défaut `LOWEST_COST_WITHOUT_CAP` |
| `special_ad_categories` | `[]` sauf crédit, emploi, logement, politique |

Le budget est porté par la campagne. Meta le répartit entre les adsets, qui n'ont donc pas de budget propre.

## `conversion`

| Champ | Rôle |
|---|---|
| `name` | Nom de la conversion personnalisée. Réutilisée si elle existe déjà |
| `event` | Événement du pixel, par défaut `PageView` |
| `url_contains` | Fragment d'adresse, sans distinction de casse |
| `custom_event_type` | Par exemple `LEAD` ou `SCHEDULE` |
| `thank_you_url` | Page merci, contrôlée avant activation |

## `dsa`

`beneficiary` et `payor`, à renseigner si la campagne vise l'Union européenne.

## `targeting_base`

Ciblage commun à tous les adsets. Chaque adset peut le compléter avec sa propre clé `targeting`. Pour un ciblage large : pays, âge, langue, et `targeting_automation.advantage_audience` à `0`. Les identifiants de langue se trouvent avec `search?type=adlocale`, ceux d'intérêts avec `search?type=adinterest`.

## Vidéos

| Champ | Rôle |
|---|---|
| `video_dir` | Dossier, relatif au fichier de campagne |
| `video_pattern` | Par défaut `{id}-{slug}-{format}.mp4`. `format` vaut `Vertical` ou `Horizontal` |
| `thumbnail_at_seconds` | Instant de la vignette, par défaut 1,2 s |
| `url_tags` | Paramètres de suivi. `{key}` devient `P01-V` |

## `copy`

| Champ | Rôle |
|---|---|
| `offer` | Phrase ajoutée à la fin de chaque texte |
| `cta` | Dernière phrase de chaque texte |
| `cta_type` | Bouton, par défaut `LEARN_MORE` |
| `rules.first_line_max` | Longueur maximale de la première ligne, par défaut 125 |
| `rules.banned` | Expressions régulières interdites partout |

## `adsets[]`

| Champ | Rôle |
|---|---|
| `name` | Identifie l'adset |
| `link` | Page d'arrivée de toutes ses pubs |
| `titles` | Exactement 5 titres, communs |
| `variants` | Exactement 4 textes, communs (textes 2 à 5) |
| `stack` | Bloc facultatif, ajouté après le texte 1 |
| `title_must_contain` | Mot obligatoire dans chaque titre |
| `audience_forbidden` | Expressions qui appartiennent à une autre audience |
| `allowed_hook_targets`, `allowed_hook_offers` | Listes fermées pour l'accroche incrustée |
| `targeting` | Complément de ciblage, facultatif |

## `ads[]`

| Champ | Rôle |
|---|---|
| `id`, `slug` | Composent le nom du fichier vidéo |
| `adset` | Nom de l'adset |
| `body` | Texte 1, écrit depuis ce que dit la vidéo |
| `description` | Description sous le titre |
| `stack` | Remplace le bloc de l'adset pour cette pub, facultatif |
| `hook` | `target` et `offer` de l'accroche incrustée, facultatif |
