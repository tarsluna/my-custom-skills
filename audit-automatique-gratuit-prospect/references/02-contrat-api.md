# Contrat d'API

## Publique (CORS limité à `FRONTEND_ORIGIN`, `X-Robots-Tag: noindex` partout)

### `GET /public/config`
Opérateur, thème et libellés de section.

### `GET /public/audits/:token`
```ts
type PublicAudit = {
  operator: { name: string; logoUrl: string | null; websiteUrl: string; motto: string | null };
  theme: { background: string; backgroundAlt: string; backgroundLight: string; foreground: string; foregroundSoft: string; muted: string; accent: string };
  copy: PageCopy; // tous les textes de la page, déjà remplis
  token: string;
  status: 'processing' | 'ready' | 'failed';
  contact: { firstName: string | null };
  meetingAt: string | null;
  bookingUrl: string;
  business: { name: string; profession: string; professionLabel: string; city: string | null; region: string | null; domain: string; websiteUrl: string; logoUrl: string | null; logoIsFallback: boolean; palette: Palette; specialties: string[]; projectTypes: string[]; summary: string };
  competitors: { radiusKm: number | null; widened: boolean; insights: string[]; items: Competitor[] };
  creatives: { id: string; index: number; concept: string; format: '4:5' | '9:16' | '1:1'; locked: boolean; imageUrl: string; headline: string | null; primaryText: string | null; bullets: string[] | null; estimatedCostEur: number | null }[];
  projects: { title: string; location: string | null; imageUrl: string; sourceUrl: string }[];
  setter: { assistantName: string; firstProspectMessage: string; suggestedReplies: string[] };
};
```
Pour une créative `locked`, `imageUrl` pointe vers le dérivé flouté et les textes valent `null`. `estimatedCostEur` vaut `null` sans fourchette fournie par l'opérateur.

### `POST /public/audits/:token/chat`
Corps : `{ sessionId: string, messages: { role: 'user' | 'assistant', content: string }[] }`. Réponse : `{ replies: string[], done: boolean }` (1 ou 2 bulles). Plafonds : 40 messages par session, 500 caractères par message, limite par IP et par audit.

### `GET /media/:token/:file`
Images publiques de l'audit, sans listage, noms non devinables.

## Réservation

### `POST /webhooks/booking`
Secret dans `x-webhook-secret` ou `?secret=`. Corps : un objet ou un tableau (100 au maximum).
```json
{
  "id": "identifiant-unique-de-la-reservation",
  "createdAt": "2030-01-10T09:00:00Z",
  "meetingAt": "2030-01-15T14:00:00Z",
  "eventId": "optionnel",
  "name": "Claire Exemple",
  "firstName": "Claire",
  "email": "claire@exemple.fr",
  "phone": "+33 1 23 45 67 89",
  "website": "https://exemple.fr",
  "answers": [{ "question": "Votre site web", "answer": "exemple.fr" }],
  "cancelled": false
}
```
Réponse `{ results: ["created" | "reused" | "needs_domain" | "duplicate" | "ignored_*" | "invalid"] }`. Un renvoi avec le même `id` ne crée rien.

## Admin (en-tête `x-admin-key`, à appeler uniquement depuis un serveur)

| Route | Rôle |
|---|---|
| `GET /admin/stats` | crédits kie, audits du jour, file |
| `GET /admin/audits?status=&q=` | liste |
| `GET /admin/audits/:id` | tout, originaux compris, journal, coûts |
| `POST /admin/audits` `{domain, contact?}` | lancer ou réutiliser |
| `POST /admin/audits/lookup` `{items:[{key,email,domain}]}` | relier des fiches de CRM à leur audit |
| `POST /admin/audits/:id/rerun` `{domain?}` | tout relancer, environ 120 crédits |
| `POST /admin/audits/:id/projects/refresh` | relire les réalisations, sans crédit d'image |
| `POST /admin/audits/:id/creatives/:cid/regenerate` | refaire une créative |
| `PATCH /admin/audits/:id/creatives/:cid` `{locked}` | choisir les créatives visibles |
| `GET /admin/media/:id/:file` | originaux |
