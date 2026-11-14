# Architecture

Deux applications déployées séparément :

- **backend** : un seul service Node 22 (Hono, worker et sonde dans le même processus), Postgres, volume persistant pour les images.
- **frontend** : Next.js 15, page publique `/c/<jeton>` et admin `/admin`. Le navigateur ne voit jamais la clé admin : tout passe par des routes serveur.

```
Réservation ─► /webhooks/booking ─┐
Sonde iClosed (option) ───────────┼─► ingestBooking ─► file `jobs` ─► worker
Admin : POST /admin/audits ───────┘                                     │
                                                                        ▼
     analyzing ─► ads ─► creatives ─► ready        Volume : logos, projets, créatives
                                                                        │
Front /c/<jeton> ◄── GET /public/audits/:token ◄── Postgres ◄───────────┘
```

## Tables

`audits` (état, `analysis`, `brand`, `competitors_meta`, `insights`, `setter`) · `bookings` (`call_id` unique) · `jobs` · `creatives` · `competitors` · `projects` · `media` (un fichier, une ligne, un `kind`) · `audit_steps` (journal) · `audit_costs` · `settings` (filigrane).

## Décisions

- **File en base** : `FOR UPDATE SKIP LOCKED`, bail renouvelé. Un job dont le bail expire est repris, et les étapes déjà enregistrées ne sont pas rejouées. Pas de Redis à gérer.
- **Filigrane** : posé au premier démarrage, jamais réécrit. Toute réservation créée avant est ignorée : on ne dépense rien sur l'historique.
- **Idempotence** : `call_id` unique pour une réservation, verrou consultatif par domaine, audit de moins de 30 jours réutilisé pour un même domaine.
- **Média public** : seuls les noms inscrits en base sont servis, et une seule fonction décide lesquels. L'original d'une créative n'est jamais public, même déverrouillée : on sert un dérivé.
- **Configuration unique** : `audit.config.json`, lu par le backend. Le front reçoit opérateur, thème et textes dans la réponse de l'API.
- **Exécution** : `tsx` en production plutôt qu'une compilation, pour garder une seule chaîne d'import.

## Arborescence du backend

```
src/niche.ts           lecture de audit.config.json
src/booking.ts         adaptateur de réservation générique
src/poller.ts          ingestion, filigrane, sonde
src/pipeline/          crawl, extract, logo, palette, projects, competitors, run
src/creative/          concepts, copy, prompts, logo, qa
src/chat/assistant.ts  assistant de premier contact
src/routes/            public, publicView, admin, webhooks
src/lib/               ssrf, kie, apify, llm, geo, domain, files, iclosed
```
