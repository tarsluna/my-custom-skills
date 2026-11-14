# Direction créative

## Les 10 concepts

| Clé | Concept | Format | Famille |
|---|---|---|---|
| `ba_vertical` | Avant-après, coupe verticale | 4:5 | avant-après |
| `ba_horizontal` | Avant-après, coupe horizontale | 9:16 | avant-après |
| `ba_slider` | Avant-après, curseur de comparaison | 4:5 | avant-après |
| `ba_prints` | Avant-après, tirages sur table de travail | 4:5 | avant-après |
| `ba_sketch_photo` | Avant-après, du dessin à la photo | 4:5 | avant-après |
| `photo_bullets` | Photo plein cadre avec puces | 4:5 | éditorial |
| `imessage` | Conversation iMessage | 9:16 | natif |
| `notes` | Notes iOS | 1:1 | natif |
| `advertorial` | Publireportage façon magazine | 4:5 | éditorial |
| `listicle` | Listicle d'erreurs à éviter | 9:16 | éditorial |

Le code et les briefs sont dans `backend/src/creative/concepts.ts` et `prompts.ts`.

## Moteur d'image

kie.ai, modèle `gpt-image-2-5-sunburst-image-to-image`, 2K, environ 10 crédits l'image, pool de 4. Le modèle refuse le 4:5 : on génère en 3:4 et on recadre, en gardant les bandes coupées libres de texte.

Une tâche qui semble échouer côté client est vérifiée avant toute relance : elle a pu réussir et être facturée.

## Rédaction

Le LLM écrit, le code contrôle. Chaque texte est refusé s'il contient un mot ou un angle interdit, une affirmation absente des faits (récompense, garantie, avis, expérience), un chiffre non sourcé, une formule reprise d'un concurrent, ou si le nom exact et le métier exact manquent. Une créative refusée repart une fois au modèle avec la correction, puis un texte de repli sûr prend le relais. Il y a donc toujours 10 créatives.

## Le logo, point le plus important

Ne faites jamais confiance au modèle pour un logo. Le prompt lui demande de **réserver une zone calme** à position constante, puis `sharp` recompose le vrai fichier à cet endroit, avec gestion du contraste : version claire ou plaque discrète si le logo disparaît sur le fond.

## Références visuelles

Les photos de réalisations partent au modèle sous forme d'une **planche de détails**, jamais en entier. Lors de nos essais, une photo complète a été recopiée presque à l'identique, ce qui fabriquait un faux « après ». La relecture vérifie aussi ce point.

## Relecture automatique

Chaque image est relue par le LLM avec vision : orthographe comparée au texte attendu, lettres déformées, visages et mains, zone du logo libre, même sujet entre avant et après, copie d'une référence. Un défaut bloquant déclenche **une seule** régénération, dans le plafond de 14 générations par audit. Les défauts restants sont visibles dans l'admin.

## Visibles et floutées

Le module choisit les plus fortes parmi les familles et les formats, avec au moins un avant-après. Le serveur garantit le compte réglé par `creatives.visible`, 3 par défaut.

Le dérivé flou est produit par `sharp`, aucun texte n'y reste lisible. `thumbPath` reste net : ne l'exposez jamais pour une créative verrouillée.

## Adapter à un autre métier

Réglez `visuals` : `subject`, `photoStyle`, `calmSurface`, états `defaultBefore` et `defaultAfter`, `workTable`, `workDocument`, `sketchStyle`. Les concepts photographiques sont conçus pour un sujet qui change d'état : un lieu, un jardin, une façade, un véhicule. Si votre métier n'a pas d'avant-après visible, remplacez ces concepts dans `concepts.ts` et `prompts.ts`.

Testez toujours **une image** avant le lot. La qualité varie d'une exécution à l'autre : regardez plusieurs créatives avant de transmettre une page.
