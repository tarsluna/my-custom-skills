# Les sources, dans l'ordre où elles rapportent

Toute cette page suppose la France. Pour un autre pays, gardez la logique et remplacez les registres.

## 1. Registre des entreprises (socle)

`fetch_registry.py` interroge l'API publique `recherche-entreprises.api.gouv.fr`, code NAF par code NAF, département par département, jusqu'au plafond de pagination de 10 000 résultats (Paris est redécoupé par code postal). Le filtre `etat_administratif=A` ne garde que les entreprises actives.

Ce socle ne contient **aucun email**. Il sert à vérifier qu'un site appartient bien à l'entreprise et à compléter le prénom à la fusion.

Sont écartées les entités en diffusion partielle (opposition au répertoire). Le siège d'un entrepreneur individuel est souvent son domicile : seuls le code postal et la commune sont gardés.

## 2. Sites officiels

`crawl_sites.py` lit au plus 5 pages par site : page légale, accueil, contact. Il ne garde une adresse que sur le domaine du site ou une boîte personnelle affichée.

Un site n'est retenu que s'il est vérifié :

- par son SIREN lu sur la page ;
- sinon par le nom, le lieu et un mot du métier ensemble ;
- sinon, pour une fiche open data qui donne déjà le site, par la fiche (`level_hint=fiche_ouverte`).

Un site qui n'a que des mots du métier passe en niveau `mots_cles` : c'est le niveau qui exige le filtre et le tirage.

## 3. Liste ouverte des domaines .fr (Afnic)

L'Afnic publie une liste ouverte des noms de domaine en `.fr`. C'est le meilleur levier quand on part d'un registre sans sites : au lieu de deviner, on confronte des noms plausibles à des domaines qui existent.

`build_domains.py` produit deux entrées pour le crawl :

- `input_a.csv` : domaines qui correspondent exactement au nom d'une entreprise du registre ;
- `input_b.csv` : autres domaines contenant un mot du métier, à filtrer sévèrement ensuite.

Téléchargez vous-même le fichier sur le site de l'Afnic après avoir lu sa licence, et notez-la dans `reviews/afnic-domaines.json`. Le script ne télécharge rien et n'envoie aucune requête.

## 4. Open data

`open_data.py search` liste les jeux de données publics susceptibles de citer le métier. `dataset` télécharge ceux que vous déclarez dans la configuration, en ne gardant que les champs utiles.

OpenStreetMap (`overpass`) donne des fiches classées par tags. Licence ODbL : citez la source et lisez ses conditions.

Regardez la licence de chaque jeu. Un jeu public peut interdire une réutilisation commerciale ou imposer une attribution, et une URL de téléchargement peut être interdite par robots.txt alors qu'une API du même service est permise.

## 5. Annuaires

Un par un, à la main de l'agent : lecture de robots.txt et des CGU d'abord. La plupart des annuaires professionnels interdisent la collecte ou la réutilisation. Ils ne figurent alors dans aucune sortie : verdict `interdit`, citation exacte, et on n'y retourne pas sans accord écrit.

Déclarez leurs domaines dans `excluded_hosts` pour que le crawl ne les visite jamais par erreur.

## Ce qui ne rapporte pas

Deviner un site à partir du nom d'entreprise : voir [06-pieges.md](06-pieges.md).
