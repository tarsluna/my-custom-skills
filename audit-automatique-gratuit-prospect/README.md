# Audit automatique gratuit pour un prospect

Un skill complet, avec son code, pour offrir à chaque prospect un audit personnalisé avant son rendez-vous. Il fonctionne pour n'importe quel métier local et se déploie sur votre propre infrastructure.

À partir d'un simple nom de domaine, le système :

- analyse le site du prospect (métier, ville, spécialités, logo, palette, réalisations) ;
- trouve ses concurrents qui font déjà de la publicité près de chez lui ;
- génère 10 créatives Meta à son logo, dont 5 avant-après différents ;
- publie une page privée à son nom, avec 3 créatives visibles et 7 réellement floutées ;
- ouvre un téléphone iMessage où le visiteur joue un client face à un assistant de préqualification.

Le but est simple : donner envie de venir au rendez-vous.

## Démarrer

```bash
./scripts/install.sh
cd template/frontend && USE_FIXTURES=1 npm run dev
# puis http://localhost:4411/c/exemple-renovation-Q7vK2mXp9LsT4bYw1Zc8Rd
```

La démonstration ne demande aucune clé et ne dépense rien.

Avec Claude Code, copiez ce dossier dans `~/.claude/skills/audit-automatique-gratuit-prospect/` et demandez : « installe-moi l'audit automatique pour mon métier ». La méthode complète est dans [SKILL.md](SKILL.md).

## Ce qu'il vous faut

Des comptes OpenRouter, kie.ai et Apify, un hébergeur Node avec Postgres et un volume persistant, et un hébergeur Next.js. Un audit coûte environ 120 crédits kie.ai et 0,11 $ d'OpenRouter, plus quelques centimes d'Apify, pour 5 à 6 minutes de traitement.

## Adapter à votre métier

Un seul fichier : [`template/backend/audit.config.json`](template/backend/audit.config.json). Voir [references/09-configuration.md](references/09-configuration.md) et les exemples dans `references/exemples-config/`.

## Limites à connaître

- Les prompts et la page sont en français.
- Le géocodage utilise la Base Adresse Nationale, donc la France. Pour un autre pays, remplacez `backend/src/lib/geo.ts`.
- Vérifiez les conditions d'utilisation des services que vous branchez, notamment pour la collecte de la bibliothèque publicitaire Meta.
- Vous restez responsable de ce que vous envoyez à vos prospects et du traitement de leurs données.

## Licence

MIT. La police Jost incluse dans `template/backend/assets/fonts` est sous licence SIL Open Font.
