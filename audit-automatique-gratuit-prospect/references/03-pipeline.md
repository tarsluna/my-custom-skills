# Le pipeline, étape par étape

Statuts : `queued`, `analyzing`, `ads`, `creatives`, `ready`, `failed`, `needs_domain`.

## 1. Déclencheur

Le système accepte trois entrées, qui convergent vers la même fonction.

**Webhook générique (par défaut).** `BOOKING_PROVIDER=generic`. Votre outil appelle `POST /webhooks/booking` (voir [02-contrat-api.md](02-contrat-api.md)). Avec Calendly, Cal.com ou un formulaire maison, un scénario Zapier ou Make suffit à traduire la charge.

**iClosed (exemple fourni).** `BOOKING_PROVIDER=iclosed` et `ICLOSED_API_KEY`. Le backend sonde `GET https://public.api.iclosed.io/v1/eventCalls` toutes les 2 minutes. `BOOKING_EVENT_IDS` limite aux événements voulus : l'API ignore le filtre `eventId`, le tri se fait donc de notre côté. Un webhook iClosed vers `/webhooks/booking` déclenche simplement une sonde immédiate. Attention : un même rendez-vous peut exister sous deux identifiants d'événement, vérifiez où arrivent vos vraies réservations.

**Manuel.** Depuis l'admin ou `POST /admin/audits`.

Trouver le domaine, dans l'ordre : le champ `website`, une réponse dont l'intitulé contient site, domaine, web ou url, puis le domaine de l'e-mail s'il n'est pas grand public. Sinon l'audit attend en `needs_domain` et l'équipe saisit le site dans l'admin. **Ajoutez une question « Site web » à votre formulaire.**

Une réservation annulée avant le démarrage libère l'audit, et un rendez-vous déplacé met à jour la date.

## 2. Analyse du site

Page d'accueil et 10 pages internes au maximum, en priorité réalisations, à propos, contact. Requête simple d'abord, Chromium si le rendu est vide et pour la capture d'écran.

Le LLM extrait le nom, le métier parmi `sector.professions`, la ville, les spécialités et les faits. Les garde-fous sont du code, pas de la confiance :

- le métier n'est retenu que si son expression régulière `evidence` trouve une trace sur le site ;
- un fait n'est gardé que si sa citation exacte se retrouve dans le texte ;
- une phrase générée qui contient un chiffre absent du site est retirée ;
- ville, nom et dirigeant doivent figurer dans le contenu.

**Marque.** Palette tirée du CSS et de la capture, polices, logo (en-tête, SVG, JSON-LD, icônes). Sans logo exploitable, un logotype typographique est composé à partir du nom.

**Réalisations.** Candidats trouvés sur les pages de projets, images différées comprises (attributs `data-*`, leurres de type `blank.gif` ignorés), tri par le LLM, images recopiées sur le volume.

## 3. Concurrents

Requêtes par paliers, métier et spécialité croisés avec la ville, le département, la région, puis le pays. Le résultat brut est très bruité (écoles, publireportages, annuaires), donc :

1. exclusion par mots (`competitors.excludedNameWords`, `excludedBodyWords`) ;
2. tri par le LLM (`competitors.keep`, `competitors.exclude`), en cas de doute on écarte ;
3. géolocalisation et distance à vol d'oiseau ;
4. rayon : le plus petit palier qui atteint `ADS_MIN_COMPETITORS`. La page affiche le rayon réellement atteint.

Les images Meta expirent : chaque image retenue est recopiée sur le volume. Un résumé des accroches et angles sert d'inspiration de style aux créatives, jamais de texte à reprendre.

## 4. Créatives

Voir [04-direction-creative.md](04-direction-creative.md).

## 5. Page

Le jeton `<slug>-<22 caractères aléatoires>` est créé après l'analyse, ce qui permet d'afficher une page d'attente. Le statut passe à `ready` quand les créatives sont prêtes.

## Reprise après panne

Chaque étape est enregistrée avant la suivante. Un redémarrage reprend l'audit là où il en était, sans repayer ce qui est fait. Le plafond quotidien reporte au lendemain au lieu d'échouer.
