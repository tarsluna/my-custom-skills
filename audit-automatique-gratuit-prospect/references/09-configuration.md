# Configuration : `backend/audit.config.json`

Le seul fichier à adapter. Il est validé au démarrage : un champ manquant empêche le backend de démarrer et indique lequel.

| Bloc | Rôle |
|---|---|
| `operator` | votre nom, logo (URL ou `null` pour afficher le nom), site, accroche de pied de page |
| `theme` | couleurs de la page |
| `business` | le mot qui désigne un prospect, décliné : `nom`, `le`, `du`, `un`, `au`, `ce`, `votre`. Exemple : `le` vaut « la clinique » ou « l’entreprise » |
| `sector` | description du secteur, lecteur des publicités, pays, métiers possibles |
| `competitors` | ce qu'on garde, ce qu'on écarte, mots d'exclusion immédiate |
| `assistant` | sujets de préqualification, mot pour le budget du client et pour les tarifs, réponses de secours |
| `vocabulary` | mots bannis, angles interdits, points d'exclamation autorisés ou non |
| `creatives` | nombre de créatives visibles (`visible`, 3 par défaut), voix, exemples d'accroches, CTA, puces de secours |
| `visuals` | sujet photographié, style, états avant et après, éléments de la table de travail, présence de personnes |
| `page` | titre, phrase sur les éléments floutés, tous les libellés |

## Métiers

```json
{ "key": "cuisiniste", "label": "cuisiniste", "evidence": "cuisinistes?|cuisines? sur mesure", "neverCalled": [] }
```

- `evidence` est une expression régulière : le métier n'est retenu que si le site en porte la trace.
- `neverCalled` liste les mots interdits pour ce métier. Exemple : une professionnelle dont le titre est protégé ne doit pas recevoir le titre d'une autre profession.

## Textes de la page

Variables disponibles : `{nom}`, `{ville}`, `{n}`, `{prenom}`. Les deux phrases qui portent la conversion :

- `page.title` : « Nous avons préinstallé ce système pour vous, {nom}. »
- `page.lockedSentence` : « Le reste de vos bonus vous sera présenté dans l'appel. »

## Vocabulaire et angles

`vocabulary.banned` et `vocabulary.forbiddenAngles` acceptent des expressions régulières. Mettez dans les angles interdits ce que votre métier ou votre droit national encadre. Le contrôle s'applique aux créatives, aux constats et à l'assistant.

## Variables d'environnement

Voir `backend/.env.example` et `frontend/.env.example`. Les garde-fous de dépense gardent les valeurs d'origine par défaut.

## Exemples

`references/exemples-config/paysagiste.json` et `institut-beaute.json` montrent les blocs à changer pour un autre métier.
