# Passer une campagne vers un formulaire instantané

Le cas vécu : une campagne vidéo dirigée vers un site dépense déjà. On veut les mêmes pubs, dans une nouvelle campagne, mais vers un formulaire instantané (lead form). L'ancienne campagne continue de tourner, on n'y touche pas.

Ce document décrit le chemin qui a fonctionné ce jour-là. [`scripts/lead_form.py`](../scripts/lead_form.py) l'outille : relecture du formulaire, copie des ad sets, recréation des pubs, contrôle champ par champ.

## Les consignes à faire confirmer avant de commencer

| Consigne | Conséquence |
|---|---|
| Ne pas toucher l'ancienne campagne | Lecture seule sur ses objets. Aucune mise en pause, aucun renommage, aucune modification |
| Pubs à l'identique | Mêmes vidéos, 5 textes, 5 titres, description, bouton. Seule la destination change |
| Facebook et Instagram seulement | `publisher_platforms` vaut `["facebook", "instagram"]`. Pas d'Audience Network |
| Ciblage large | Aucun intérêt, aucun comportement |
| Tout en pause | L'activation suit l'accord humain, comme pour `go` |

Fais-les confirmer par la personne avant la première écriture.

## Le déroulé

Toutes les commandes acceptent `--dry-run`, qui n'écrit rien chez Meta. Avec `--file` ou `--files`, elles tournent sans réseau ni token, sur des objets tels que Meta les renvoie.

### 1. Relire le formulaire, avant d'y diriger la moindre pub

**Un formulaire publié ne se modifie plus.** Le jour du cas réel, il avait des libellés en anglais et des tranches de chiffre d'affaires qui se chevauchaient. Il a fallu le dupliquer et corriger la copie, après coup.

```bash
python3 scripts/lead_form.py check-form --form-id <FORMULAIRE> --locale fr_FR
```

La commande s'arrête si :

- la langue du formulaire n'est pas celle attendue. C'est elle qui fixe les libellés des champs préremplis : nom, e-mail, téléphone ;
- un libellé ou un choix contient des mots anglais courants ;
- deux tranches d'une même question se chevauchent. `0 - 50 000 €` et `50 000 - 100 000 €` comptent comme un chevauchement : une entreprise à 50 000 € ne sait pas quoi cocher. `Moins de 50 000 €` puis `50 000 € à 100 000 €` passe.

Elle ne lit pas l'intro, l'écran de fin ni le lien de politique de confidentialité. Fais-les relire par la personne.

En cas de problème : duplique le formulaire dans le Gestionnaire, corrige la copie, relis-la avec la même commande, puis note son identifiant. C'est vers elle que les pubs iront.

### 2. La campagne et un premier ad set

Dans le cas réel, la nouvelle campagne existait déjà, avec un premier ad set créé à la main dans le Gestionnaire, destination formulaire instantané. **Publie-les.** Un brouillon non publié est invisible pour l'API.

### 3. Les autres ad sets : copier, renommer, comparer

```bash
python3 scripts/lead_form.py copy-adset --adset <ADSET_FAIT_MAIN> --name "Entreprises d'espaces verts | formulaire"
```

La commande appelle `POST /<adset_id>/copies` avec `deep_copy` à `false` (sans les pubs) et `status_option` à `PAUSED`, puis renomme la copie. Si un ad set porte déjà ce nom dans la campagne, elle ne fait rien : tu peux la relancer.

Compare ensuite chaque nouvel ad set à son équivalent dans l'ancienne campagne :

```bash
python3 scripts/lead_form.py diff-adsets --adsets <ANCIEN_ADSET> <NOUVEL_ADSET>
```

**Les réglages hérités d'un ad set créé à la main peuvent différer de l'ancienne campagne.** Dans le cas réel, les pays, la tranche d'âge et les langues des copies venaient de l'ad set fait main, pas de l'ancienne campagne. Ils ont été signalés avant le lancement.

| Niveau | Exemple | Que faire |
|---|---|---|
| `ECART` | Placements automatiques, donc Audience Network possible. Intérêts présents | Corriger avant de lancer |
| `A SIGNALER` | Pays, âges, langues, genres différents | Montrer à la personne, qui tranche |
| `INFO` | `optimization_goal`, `destination_type` | Attendu en passant au formulaire |

Pour corriger le ciblage, renvoie l'objet `targeting` complet : il remplace l'ancien en entier.

### 4. Les pubs : recréer par l'API, jamais dupliquer dans le Gestionnaire

**Dupliquer une pub dans le Gestionnaire, puis passer sa destination au formulaire, a donné des pubs vides** : ni vidéo, ni texte. Elles ont été mises en pause et renommées, puis les pubs ont été recréées par l'API.

```bash
# À blanc, sur une pub : affiche la charge utile complète
python3 scripts/lead_form.py --dry-run copy-ad --ad <ANCIENNE_PUB> --form-id <FORMULAIRE> --adset <NOUVEL_ADSET>

# Une seule pub en réel, à regarder dans le Gestionnaire
python3 scripts/lead_form.py copy-ad --ad <ANCIENNE_PUB> --form-id <FORMULAIRE> --adset <NOUVEL_ADSET>

# Le reste, ad set par ad set
python3 scripts/lead_form.py copy-ad --from-adset <ANCIEN_ADSET> --form-id <FORMULAIRE> --adset <NOUVEL_ADSET>
```

Pour chaque pub, la commande :

1. lit l'ancienne pub et sa créative, sans rien y écrire ;
2. saute les pubs refusées par Meta (`DISAPPROVED`) et les liste ;
3. saute les pubs dont le nom existe déjà dans l'ad set cible ;
4. construit la nouvelle créative, la crée, puis crée la pub **en pause**, sous le même nom ;
5. relit la pub créée et la compare champ par champ à l'ancienne.

Elle affiche le statut de la pub d'origine : une pub en pause dans l'ancienne campagne doit le rester dans la nouvelle.

### 5. La charge utile

**Vidéo simple.** Le formulaire va dans le bouton de `video_data`. Les 5 textes, 5 titres et la description restent dans `asset_feed_spec`, tels quels, comme `degrees_of_freedom_spec` et `url_tags`. Le lien `http://fb.me/` est celui que Meta attend à côté d'un formulaire.

```json
{
  "object_story_spec": {
    "page_id": "PAGE",
    "video_data": {
      "video_id": "VIDEO",
      "image_hash": "HASH",
      "call_to_action": {
        "type": "LEARN_MORE",
        "value": {"lead_gen_form_id": "FORMULAIRE", "link": "http://fb.me/"}
      }
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

**Vidéo par emplacement** (un format pour les stories, un pour le fil, etc.). Tout passe par `asset_feed_spec` :

| Champ lu | Champ envoyé |
|---|---|
| `videos[].adlabels` avec `id` et `name` | `adlabels` avec `name` seulement |
| `asset_customization_rules[].video_label` avec `id` et `name` | `video_label` avec `name` seulement |
| `call_to_action_types` | `call_to_actions`, chacun avec `{"lead_gen_form_id": "FORMULAIRE"}` |
| `link_urls` vers le site | `[{"website_url": "http://fb.me/"}]` |
| `additional_data`, `reasons_to_shop`, `shops_bundle` | Retirés, comme dans le cas réel : ils viennent de la lecture |

Les libellés se citent par nom : les identifiants appartiennent à l'ancienne créative.

### 6. Contrôler la copie

`copy-ad` compare déjà chaque pub après création. Pour revérifier plus tard :

```bash
python3 scripts/lead_form.py diff --ads <ANCIENNE_PUB> <NOUVELLE_PUB> --form-id <FORMULAIRE>
```

Sont comparés : Page, compte Instagram, vidéos, vignette, textes, titres, description, bouton, règles d'emplacement, paramètres de suivi. La destination doit être le formulaire.

**Un écart d'identifiant vidéo peut être un faux positif.** La même vidéo, réimportée, change d'identifiant. Le script le classe en `A VERIFIER` : compare les vignettes ou la durée dans le Gestionnaire avant de conclure.

### 7. Faire le ménage, puis activer

- **Supprime à la main les brouillons du Gestionnaire.** Ils sont invisibles pour l'API, et chaque publication en ferait des doublons.
- Laisse en pause, ou supprime, les pubs vides nées d'une duplication.
- `go` ne connaît que les objets de `state.json`. Active donc dans le Gestionnaire, après accord : les pubs, les ad sets, puis la campagne en dernier. Annonce le budget et le nombre de pubs avant.

## Les pièges, dans l'ordre où ils sont apparus

| Piège | Ce qui s'est passé | La parade |
|---|---|---|
| Duplication dans le Gestionnaire | Pubs vides après passage au formulaire | Mises en pause, renommées, recréées par `copy-ad` |
| Bouton vers le formulaire | La forme diffère entre vidéo simple et vidéo par emplacement | Voir la charge utile ci-dessus |
| Ad set identique | `/copies` sans les pubs fonctionne, mais hérite des réglages de l'ad set fait main | `copy-adset`, puis `diff-adsets` avant de lancer |
| Brouillons | Invisibles par l'API | Suppression à la main |
| Limite de débit | Code 17 après une cinquantaine d'écritures d'affilée | Attendre 40 secondes, puis relire avant de réessayer. `copy-ad` relit l'ad set cible et saute ce qui existe |
| Pubs refusées | Les pubs refusées par Meta dans l'ancienne campagne n'ont pas été recopiées | Sautées et listées en fin de commande. À réécrire avant de les reproposer |
| Formulaire publié | Libellés en anglais, tranches qui se chevauchent, plus modifiable | `check-form` avant d'y diriger les pubs, sinon duplication et correction |
| Contrôle après copie | Identifiant vidéo différent pour la même vidéo | Classé `A VERIFIER`, pas `ECART` |

## Permissions

Le token du cas réel avait, en plus des permissions de [token-meta-computer-use.md](token-meta-computer-use.md), `leads_retrieval`, pour lire le formulaire et ses réponses.

## Ce qui n'a pas été vérifié

- **`lead_form.py` généralise des scripts ponctuels.** Ceux-ci ont réellement recopié une campagne entière vers un formulaire. La version publiée a été testée à blanc et contre un faux client en mémoire, pas contre l'API. Commence par une seule pub.
- **La relecture d'une créative par emplacement** peut ne pas renvoyer l'identifiant du formulaire. Le script le signale en `A VERIFIER` : regarde la destination dans le Gestionnaire.
- **Les pubs image** et les règles d'emplacement qui portent des libellés d'image ou de lien ne sont pas couvertes.
- **Une coupure entre la copie d'un ad set et son renommage** laisse une copie au nom donné par Meta. Supprime-la avant de relancer, sinon tu en auras deux.
- **Au-delà de 200 pubs par ad set**, seules les 200 premières sont lues : passe-les par lots avec `--ad`.
