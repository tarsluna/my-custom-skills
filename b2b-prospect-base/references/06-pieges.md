# Les pièges rencontrés

Tout ce qui suit est arrivé pendant un vrai passage.

## Le réseau sature bien avant les limites des sites

Au-delà de 30 à 40 connexions simultanées sur une ligne partagée, la connexion sature et une part importante des sites devient « injoignable ». Pire, un échec réseau ressemble alors à « ce site n'existe pas », et ces entreprises disparaissent en silence.

Plafond dans le code : 40 connexions, défaut 30. Relancez les injoignables en faible concurrence, une fois le crawl principal fini :

```bash
python3 -I scripts/crawl_sites.py --project DOSSIER --input X.csv --name NOM --retry-unreachable --workers 8
```

Une bonne part revient vivante. `injoignable` n'est jamais marqué comme fait, pour rester à reprendre.

## Deviner le domaine rapporte très peu

Essayer `nom-entreprise.fr` à partir du registre donne peu de sites vérifiés, et beaucoup de domaines qui appartiennent à quelqu'un d'autre. Le croisement avec la liste ouverte du .fr rapporte nettement plus pour le même nombre de requêtes, parce qu'on ne visite que des domaines qui existent.

C'est pour cela que le crawl de ce dépôt prend toujours un domaine en entrée.

## Une part importante des adresses publiées sont des boîtes personnelles

Beaucoup de petites structures n'ont qu'une adresse gmail ou orange. Elles gonflent vite le compte brut. Ne les comptez pas comme des contacts professionnels : elles sont exclues par défaut, et mises de côté au mieux pour arbitrage.

## Les domaines à mots-clés sont sales avant filtre

Un domaine contenant un mot du métier peut être une boutique, une école, un média, un annuaire ou une entreprise à l'étranger. Le premier tirage sur ces domaines revient typiquement avec plusieurs lignes mauvaises sur dix. C'est le signal qu'il faut filtrer, pas qu'il faut arrêter.

## Vérifier l'identité, pas seulement le métier

Un domaine deviné ou un homonyme peut appartenir à quelqu'un d'autre. Sans vérification par SIREN ou nom + lieu + métier, on attribue l'adresse d'un inconnu à une entreprise. Quand plusieurs SIREN correspondent au même nom et au même lieu, le SIREN reste vide.

## Les robots.txt des services publics surprennent

Sur le terrain, une instance publique d'Overpass interdisait son API dans son robots.txt : il a fallu passer par une autre instance. Sur data.gouv.fr, des URL de téléchargement directes étaient interdites par robots.txt alors que l'API tabulaire était permise. Lisez le fichier avant de choisir l'URL.

Certaines zones Overpass manquent ou sont incomplètes selon l'instance : préférez une requête par zone et contrôlez les résultats par région.

## Les adresses qui ne sont pas des contacts

`x@2x.png`, `votre@email.fr`, adresses de DPO ou de webmaster, `no-reply@`, signatures de services techniques : tout cela passe un regex d'email. La fusion les retire, et certaines surprennent, comme un numéro de portable en partie locale.

## Les agents et les limites d'usage

Un sous-agent peut s'arrêter en plein travail à cause d'une limite d'usage. Les scripts reprennent seuls : relancez la même commande. Ne relancez pas un agent en lui faisant tout refaire.

## Un chiffre brut n'est pas une base

Le nombre brut d'adresses uniques à un instant T comprend des boîtes personnelles, des lignes pas filtrées, des lignes à arbitrer. Annoncez le nombre de lignes `pret_campagne=oui`, et dites ce qui reste à arbitrer.

## Du MX à la délivrabilité, il y a un monde

Le contrôle MX dit seulement que le domaine reçoit du courrier. Il ne dit pas que la boîte existe et aucune sonde SMTP ne doit servir à le savoir. Prévoyez des rebonds et surveillez-les à l'envoi.
