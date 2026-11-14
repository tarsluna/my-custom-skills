# La conversion sur page merci

Les adsets optimisent sur les personnes qui ont réellement terminé l'action, pas sur les visites. Le principe : une conversion personnalisée compte chaque `PageView` dont l'adresse contient un fragment propre à la page merci.

## Mise en place

1. Crée une page merci, atteinte uniquement après l'action : réservation, demande, achat.
2. Installe le pixel sur cette page et sur les pages d'arrivée.
3. Renseigne `conversion` dans le fichier de campagne.
4. Lance `structure`. La conversion est créée, ou réutilisée si le nom existe déjà.

La règle envoyée est de cette forme :

```json
{"and": [{"event": {"eq": "PageView"}}, {"url": {"i_contains": "merci"}}]}
```

`url_contains` n'est pas sensible à la casse. Chaque compte publicitaire est limité à 100 conversions personnalisées.

## Choisir le fragment

- Il doit figurer dans l'adresse de la page merci, et nulle part ailleurs. `copy` s'arrête si une page d'arrivée le contient, car chaque visite compterait alors comme une conversion.
- Évite un mot trop courant. Le filtre porte sur toute l'adresse, paramètres compris : un lien avec `?source=merci` compterait aussi.

## Vérifier, à la main

Le script contrôle que la page répond 200 et que son adresse correspond à la règle. Il ne peut pas prouver que le pixel se déclenche.

1. Ouvre la page merci, avec l'extension Meta Pixel Helper ou l'outil de test des événements du Gestionnaire d'événements.
2. Vérifie que `PageView` part bien, sur le bon pixel.
3. Vérifie que la conversion personnalisée reçoit l'événement.
4. **Si possible, fais une vraie réservation de bout en bout.** Une page merci qui charge ne prouve pas que le parcours y mène.

Chaque test compte pour une conversion. Note-les, pour ne pas les confondre avec les premiers résultats.

## À trancher avant de créer les adsets

Décide de la conversion avant `structure`. Lors du lancement d'origine, elle a été ajoutée après coup, et une seconde génération d'adsets a été créée.

Si le parcours ajoute une étape après la page merci, garde la conversion sur l'action qui compte le plus pour l'entreprise.
