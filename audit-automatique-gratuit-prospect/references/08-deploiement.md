# Déploiement

Il faut un hébergeur Node 22 capable de lancer une image Docker avec Chromium, un Postgres, un **volume persistant** monté sur `DATA_DIR`, et un hébergeur Next.js. Un seul exemplaire du backend : la limite de débit est en mémoire et le volume est local.

## Backend, exemple Railway

```bash
cd template/backend
railway init
railway add --database postgres
railway up --detach
```

Puis, dans le service : volume sur `/data`, domaine public, port `8080`, contrôle de santé sur `/health`. Variables : voir `.env.example`, avec `DATABASE_URL` en référence au service Postgres.

Le `Dockerfile` installe Chromium et lance les migrations au démarrage.

## Front, exemple Vercel

```bash
cd template/frontend
vercel link
vercel env add API_URL production
vercel env add ADMIN_API_KEY production
vercel env add ADMIN_PASSWORD production
vercel deploy --prod
```

`vercel.json` fixe le préréglage Next.js : sans lui, un projet créé vide peut se déployer sans erreur et répondre 404 partout. **Vérifiez toujours l'adresse de production dans un navigateur.**

Réglez ensuite `FRONTEND_ORIGIN` et `PUBLIC_BASE_URL` côté backend avec les vraies adresses.

## Autres hébergeurs

Tout ce qui lance le `Dockerfile` convient : Fly.io, Render, un VPS. Le front est un Next.js standard. Avec un stockage objet au lieu d'un volume, adaptez `src/lib/files.ts`.

## Domaines

Deux sous-domaines suffisent, par exemple `audit.exemple.fr` pour la page et `api.exemple.fr` pour le backend.

## Brancher votre CRM

Les routes admin permettent d'afficher l'audit sur chaque fiche :

1. Votre serveur appelle `POST /admin/audits/lookup` pour relier des fiches à leurs audits, par domaine puis par e-mail.
2. Pour lancer un audit depuis une fiche : `POST /admin/audits`, ou `POST /admin/audits/:id/rerun` avec `{domain}` si l'audit attend son domaine.
3. Pour l'aperçu dans un cadre, ajoutez `FRAME_ANCESTORS=https://crm.exemple.fr` côté front, puis affichez `https://audit.exemple.fr/c/<jeton>` dans une `iframe`.

La clé admin reste sur le serveur du CRM. Une panne du service d'audits ne doit jamais empêcher d'enregistrer une fiche.

## Exploitation

- **Crédits** : surveillez `GET /admin/stats`. Sous la réserve, les audits passent en erreur lisible.
- **Admin** : statut en direct, créatives en clair, choix des visibles, régénération, relance, journal des étapes.
- **Modèles** : vérifiez de temps en temps le dernier modèle Flash sur OpenRouter et ajustez `LLM_MODEL`.
- **Sauvegardes** : Postgres et le volume. Sans le volume, les pages perdent leurs images.
