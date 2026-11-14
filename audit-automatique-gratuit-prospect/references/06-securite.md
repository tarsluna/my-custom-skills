# Sécurité et responsabilités

## Le domaine vient d'un formulaire public : SSRF

`src/lib/ssrf.ts` : http et https seulement, ports 80 et 443, noms internes et IP privées refusés, résolution vérifiée à la connexion (pas de rebinding DNS), redirections revérifiées, délai et taille maximale. Chromium applique le même contrôle à chaque requête.

## Le contenu d'un site est une donnée, jamais une instruction

Un site ou une annonce peut contenir « ignore tes consignes ». Tout contenu tiers passe par `untrusted()`, qui l'enferme dans des balises et neutralise les balises de fin, et chaque prompt le rappelle. Le code vérifie ensuite les sorties. Tout texte extrait est échappé à l'affichage : n'utilisez jamais `dangerouslySetInnerHTML` sur ces données.

## Page privée

Jeton non devinable, `noindex` en en-tête et en métadonnée, `Referrer-Policy: no-referrer`, pas de listage des médias. Une page d'audit ne peut être affichée dans un cadre que si `FRAME_ANCESTORS` l'autorise.

## Le floutage est réel

Une créative verrouillée n'existe côté public que sous forme de dérivé flou. Originaux, dérivés nets et textes ne sortent jamais d'une route publique. Contrôle dans le plan de test.

## Plafonds de dépense

| Variable | Défaut | Effet |
|---|---|---|
| `MAX_AUDITS_PER_DAY` | 25 | au-delà, report au lendemain |
| `MAX_GENERATIONS_PER_AUDIT` | 14 | 10 créatives et 4 reprises |
| `KIE_CREDIT_RESERVE` | 150 | sous ce seuil, arrêt avec une erreur lisible |
| `REUSE_WINDOW_DAYS` | 30 | un domaine déjà traité réutilise son audit |
| `ADS_MAX_QUERIES` | 6 | requêtes Apify par audit |
| `CHAT_MAX_PER_AUDIT_PER_DAY` | 400 | messages de l'assistant |

Le filigrane ignore toute réservation antérieure au premier démarrage. Ne le remettez pas à zéro sans raison : tout l'historique serait payé.

## Clés

Dans les variables de l'hébergeur, jamais dans le dépôt ni côté navigateur. Créez des clés dédiées à ce service, avec un plafond de dépense quand le fournisseur le permet. `ADMIN_API_KEY` n'est appelée que depuis un serveur.

Derrière un proxy, le front transmet l'IP du visiteur au backend. Le backend ne doit croire cette valeur que si la requête prouve qu'elle vient de votre proxy.

## Vos responsabilités

- **Données personnelles** : nom, e-mail, téléphone et date de rendez-vous sont traités. Informez vos prospects, définissez une durée de conservation et prévoyez la suppression.
- **Conditions des services** : vérifiez celles des services que vous branchez, notamment pour la collecte de la bibliothèque publicitaire Meta.
- **Marque du prospect** : logo et images servent uniquement à lui présenter sa propre page, à titre privé.
- **Visuels générés** : la page les présente comme des concepts. Un prospect qui les publierait comme de vraies réalisations tromperait ses clients.
- **IA** : l'assistant doit se présenter comme tel, conformément aux obligations de transparence.
- **Chiffres** : tout chiffre montré à un prospect doit être fondé. Voir l'option de coût estimé dans `SKILL.md`.
- **Règles de votre métier** : certaines professions encadrent la publicité. Reportez-les dans `vocabulary.forbiddenAngles` et faites-les valider si nécessaire.
