# Le design

Le cadre (quelles diapos, dans quel ordre, avec quel contenu) est fixe. L'habillage appartient à celui qui envoie la proposition : elle doit ressembler à son site et à ses autres documents, pas à ce skill.

## Trouver la charte

Dans cet ordre : une charte ou un fichier de marque dans les dossiers de l'utilisateur, les variables CSS de son site (`--couleur`, `font-family`), son logo en SVG. Reprends ce qui existe ; n'invente pas une identité. Sans rien de tout cela, garde le thème neutre.

## `theme.json`

Placé à côté de `proposition.json`, il est lu automatiquement. Chaque clé absente garde sa valeur par défaut.

| Clé | Rôle |
|---|---|
| `couleurs.fond` | Fond des diapos claires. Sert aussi de couleur de texte sur les diapos sombres |
| `couleurs.carte` | Fond des cartes et de la page du devis, légèrement plus clair que le fond |
| `couleurs.encre` | Texte, filets, cartes noires |
| `couleurs.discret` | Texte secondaire, libellés |
| `couleurs.sombre` | Fond des diapos sombres : couverture, témoignages, garantie, suite |
| `couleurs.accent` | Les passages `**en accent**` sur fond sombre (diapos sombres, cartes noires, bandeaux). Sur fond clair, ces passages passent en gras : l'accent n'a donc à être lisible que sur le sombre |
| `polices.titres`, `.texte`, `.mono` | `famille`, `secours` (pile de repli), et `fichier` pour charger une police locale (chemin relatif au thème, `.ttf`, `.otf` ou `.woff2`). Pour les polices du système : `"famille": "system-ui"` avec `"secours": "sans-serif"`, et `"ui-monospace"` avec `"monospace"` |
| `titres.graisse`, `.graisse_couverture` | Graisse des titres. Une police fine demande 300, une police large 500 |
| `logo.svg` ou `logo.texte` | Un fichier SVG (il prend la couleur du texte) ou le nom en lettres espacées |
| `rayon` | Arrondi des cartes et des photos, en pixels. 0 pour un style strict |
| `page.largeur`, `.hauteur` | 1280 × 720 par défaut (16:9). Les limites de densité sont calées sur ce format |

## Garder le rythme

- Quatre diapos sombres ponctuent la lecture : l'ouverture, les témoignages, la garantie, la fermeture. Si la charte de l'utilisateur est sombre, inverse `fond` et `sombre` plutôt que de tout assombrir.
- Une seule couleur d'accent. Elle marque ce qui doit rester : le nom du prospect, le chiffre de la garantie, le renvoi vers elle.
- Les libellés en petites capitales espacées (`mono`) portent la structure : numéro de section, pagination, légendes.
- Les photos sont celles du prospect, recadrées par le gabarit. Trois ou quatre, de même orientation si possible.

## Quand une page déborde

Le rendu le dit, page par page. Dans l'ordre : raccourcir la phrase la plus longue, retirer une ligne ou une carte, puis seulement toucher au thème. Repères : trois ou quatre lignes par colonne en page 3, six objectifs, quatre cas, six résultats, six témoignages de trois lignes, cinq étapes, quatre briques dans l'offre, cinq lignes de devis avant le total (garantie comprise).

## Aller plus loin

Le gabarit est dans `scripts/build.py` (une fonction par diapo, une feuille de style). Un utilisateur qui veut une mise en page vraiment différente peut modifier une fonction : tant que chaque diapo reste une `section.slide` avec son `.foot`, le rendu et ses contrôles continuent de fonctionner.
