import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import { buildApp } from '../src/app.js';
import { query } from '../src/db/pool.js';
import { clearRateLimits } from '../src/lib/rateLimit.js';
import { newToken } from '../src/audits/service.js';
import { toPublicAudit } from '../src/routes/publicView.js';
import { setupTestEnv, teardownTestEnv, truncateAll } from './helpers.js';

let dataDir = '';
const app = () => buildApp();
const ADMIN = { 'x-admin-key': 'admin-key-for-tests-0001' };

beforeAll(async () => {
  ({ dataDir } = await setupTestEnv());
});
afterAll(async () => {
  await teardownTestEnv();
});
beforeEach(async () => {
  await truncateAll();
  clearRateLimits();
});

const ANALYSIS = { businessName: 'Exemple Test', profession: 'renovation', professionLabel: 'entreprise de rénovation', city: 'Lyon', region: 'Auvergne-Rhône-Alpes', specialties: ['Rénovation'], projectTypes: ['Appartements'], summary: 'Un studio.', logoFile: 'a'.repeat(32) + '.png' };
const BRAND = { palette: { primary: '#111111', secondary: '#222222', accent: '#333333', background: '#ffffff', text: '#000000' }, logoIsFallback: false };
const SETTER = { assistantName: 'Assistant de Exemple Test', firstProspectMessage: 'Bonjour.', suggestedReplies: ['ok'] };

async function makeAudit(status = 'ready'): Promise<{ id: string; token: string }> {
  const token = newToken('Exemple Test');
  const res = await query<{ id: string }>(
    `INSERT INTO audits (token, status, domain, website_url, source, contact_first_name, analysis, brand, setter, competitors_meta)
     VALUES ($1,$2,'exemple-test.fr','https://exemple-test.fr/','admin','Marie',$3,$4,$5,$6) RETURNING id`,
    [token, status, JSON.stringify(ANALYSIS), JSON.stringify(BRAND), JSON.stringify(SETTER), JSON.stringify({ radiusKm: 100, widened: false, publicInsights: ['Constat.'] })],
  );
  return { id: res.rows[0].id, token };
}

const hexName = (c: string) => c.repeat(32);

async function addCreative(auditId: string, locked: boolean, idx: number, suffix: string): Promise<{ id: string; display: string; blur: string; original: string; thumb: string }> {
  const [original, display, blur, thumb] = [`${hexName(suffix)}.jpg`, `${hexName(String.fromCharCode(suffix.charCodeAt(0) + 1))}.webp`, `${hexName(String.fromCharCode(suffix.charCodeAt(0) + 2))}.webp`, `${hexName(String.fromCharCode(suffix.charCodeAt(0) + 3))}.webp`];
  const res = await query<{ id: string }>(
    `INSERT INTO creatives (audit_id, idx, concept, format, headline, primary_text, bullets, prompt, locked, status, original_file, display_file, blur_file, thumb_file)
     VALUES ($1,$2,'Concept','4:5','Titre secret ${idx}','Texte secret ${idx}','["puce secrète"]','prompt secret',$3,'ready',$4,$5,$6,$7) RETURNING id`,
    [auditId, idx, locked, original, display, blur, thumb],
  );
  const id = res.rows[0].id;
  const dir = path.join(dataDir, 'audits', auditId, 'media');
  await mkdir(dir, { recursive: true });
  for (const [file, kind] of [[original, 'creative_original'], [display, 'creative_display'], [blur, 'creative_blur'], [thumb, 'creative_thumb']] as const) {
    const filePath = path.join(dir, file);
    await writeFile(filePath, `contenu ${kind}`);
    await query(`INSERT INTO media (file_name, audit_id, creative_id, kind, path, content_type, bytes) VALUES ($1,$2,$3,$4,$5,'image/jpeg',10)`, [file, auditId, id, kind, filePath]);
  }
  return { id, display, blur, original, thumb };
}

describe('masquage des créatives verrouillées', () => {
  it('la réponse publique ne contient ni texte, ni original, ni dérivé non flouté', async () => {
    const { id, token } = await makeAudit();
    const locked = await addCreative(id, true, 1, 'a');
    const open = await addCreative(id, false, 2, 'e');
    const res = await app().request(`/public/audits/${token}`);
    expect(res.status).toBe(200);
    const body = (await res.json()) as any;
    const lockedOut = body.creatives.find((c: any) => c.index === 1);
    const openOut = body.creatives.find((c: any) => c.index === 2);
    expect(lockedOut.locked).toBe(true);
    expect(lockedOut.headline).toBeNull();
    expect(lockedOut.primaryText).toBeNull();
    expect(lockedOut.bullets).toBeNull();
    expect(lockedOut.imageUrl).toContain(locked.blur);
    expect(openOut.headline).toBe('Titre secret 2');
    expect(openOut.imageUrl).toContain(open.display);

    const raw = JSON.stringify(body);
    expect(raw).not.toContain('Titre secret 1');
    expect(raw).not.toContain('Texte secret 1');
    expect(raw).not.toContain('prompt secret');
    for (const file of [locked.original, locked.display, locked.thumb, open.original]) expect(raw).not.toContain(file);
  });

  it('toPublicAudit ignore toute valeur secrète présente dans les données', () => {
    const out = toPublicAudit({
      audit: { id: 'x', token: 't-aaaaaaaaaaaaaaaaaaaaaa', status: 'ready', domain: 'a.fr', website_url: 'https://a.fr', contact_first_name: null, meeting_at: null, analysis: ANALYSIS, brand: BRAND, competitors_meta: null, setter: SETTER },
      creatives: [{ id: 'c', idx: 1, concept: 'C', format: '1:1', locked: true, status: 'ready', headline: 'SECRET', primary_text: 'SECRET', bullets: ['SECRET'], display_file: 'display.webp', blur_file: 'blur.webp' }],
      competitors: [],
      projects: [],
    });
    expect(JSON.stringify(out)).not.toContain('SECRET');
    expect(JSON.stringify(out)).not.toContain('display.webp');
    expect(out.creatives[0].imageUrl).toContain('blur.webp');
  });
});

describe('route média', () => {
  it('une créative verrouillée : seul le flou est servi', async () => {
    const { id, token } = await makeAudit();
    const c = await addCreative(id, true, 1, 'a');
    expect((await app().request(`/media/${token}/${c.blur}`)).status).toBe(200);
    expect((await app().request(`/media/${token}/${c.display}`)).status).toBe(404);
    expect((await app().request(`/media/${token}/${c.original}`)).status).toBe(404);
    expect((await app().request(`/media/${token}/${c.thumb}`)).status).toBe(404);
  });
  it('une créative ouverte : le dérivé d’affichage est servi, jamais l’original', async () => {
    const { id, token } = await makeAudit();
    const c = await addCreative(id, false, 1, 'a');
    expect((await app().request(`/media/${token}/${c.display}`)).status).toBe(200);
    expect((await app().request(`/media/${token}/${c.original}`)).status).toBe(404);
  });
  it('après verrouillage par l’admin, le dérivé n’est plus accessible', async () => {
    const { id, token } = await makeAudit();
    const c = await addCreative(id, false, 1, 'a');
    await app().request(`/admin/audits/${id}/creatives/${c.id}`, { method: 'PATCH', headers: { ...ADMIN, 'content-type': 'application/json' }, body: JSON.stringify({ locked: true }) });
    expect((await app().request(`/media/${token}/${c.display}`)).status).toBe(404);
  });
  it('un fichier d’un autre audit n’est pas servi sous ce jeton', async () => {
    const a = await makeAudit();
    const b = await makeAudit();
    const c = await addCreative(a.id, false, 1, 'a');
    expect((await app().request(`/media/${b.token}/${c.display}`)).status).toBe(404);
  });
  it('refuse les noms de fichiers mal formés', async () => {
    const { token } = await makeAudit();
    expect((await app().request(`/media/${token}/..%2F..%2Fetc%2Fpasswd`)).status).toBe(404);
  });
});

describe('API publique', () => {
  it('jeton inconnu : 404', async () => {
    expect((await app().request(`/public/audits/nimporte-quoi`)).status).toBe(404);
  });
  it('audit en cours : processing, sans créatives', async () => {
    const { token } = await makeAudit('creatives');
    const body = (await (await app().request(`/public/audits/${token}`)).json()) as any;
    expect(body.status).toBe('processing');
    expect(body.creatives).toEqual([]);
  });
  it('X-Robots-Tag partout, erreurs comprises', async () => {
    const paths = ['/health', '/public/audits/nimporte-quoi', '/inexistant', '/media/x/y'];
    for (const p of paths) {
      const res = await app().request(p);
      expect(res.headers.get('x-robots-tag')).toContain('noindex');
    }
  });
  it('CORS limité au domaine de la page', async () => {
    const { token } = await makeAudit();
    const ok = await app().request(`/public/audits/${token}`, { headers: { origin: 'https://audit.exemple.fr' } });
    expect(ok.headers.get('access-control-allow-origin')).toBe('https://audit.exemple.fr');
    const bad = await app().request(`/public/audits/${token}`, { headers: { origin: 'https://evil.example' } });
    expect(bad.headers.get('access-control-allow-origin')).toBeNull();
    const local = await app().request(`/public/audits/${token}`, { headers: { origin: 'http://localhost:3000' } });
    expect(local.headers.get('access-control-allow-origin')).toBe('http://localhost:3000');
  });
  it('limite de débit par IP', async () => {
    const { token } = await makeAudit();
    let last = 200;
    for (let i = 0; i < 185; i += 1) {
      const res = await app().request(`/public/audits/${token}`, { headers: { 'x-forwarded-for': '203.0.113.9' } });
      last = res.status;
    }
    expect(last).toBe(429);
  });
});

describe('chat', () => {
  const post = (token: string, body: unknown, ip = '198.51.100.7') => app().request(`/public/audits/${token}/chat`, { method: 'POST', headers: { 'content-type': 'application/json', 'x-forwarded-for': ip }, body: JSON.stringify(body) });

  it('refuse un message trop long, trop de messages, ou un corps invalide', async () => {
    const { token } = await makeAudit();
    expect((await post(token, { sessionId: 'session-1234', messages: [{ role: 'user', content: 'x'.repeat(501) }] })).status).toBe(400);
    expect((await post(token, { sessionId: 'session-1234', messages: Array.from({ length: 41 }, () => ({ role: 'user', content: 'x' })) })).status).toBe(400);
    expect((await post(token, { sessionId: 'x', messages: [{ role: 'user', content: 'x' }] })).status).toBe(400);
    expect((await post(token, { sessionId: 'session-1234', messages: [{ role: 'system', content: 'x' }] })).status).toBe(400);
    expect((await post(token, { sessionId: 'session-1234', messages: [{ role: 'assistant', content: 'x' }] })).status).toBe(400);
  });
  it('refuse sur un audit non prêt', async () => {
    const { token } = await makeAudit('creatives');
    expect((await post(token, { sessionId: 'session-1234', messages: [{ role: 'user', content: 'Bonjour' }] })).status).toBe(409);
  });
  it('au-delà de 40 messages par session : clôture sans appel au modèle', async () => {
    const { id, token } = await makeAudit();
    await query(`INSERT INTO chat_sessions (audit_id, session_id, messages) VALUES ($1,'session-1234',40)`, [id]);
    const res = await post(token, { sessionId: 'session-1234', messages: [{ role: 'user', content: 'Encore une question' }] });
    expect(res.status).toBe(200);
    expect(((await res.json()) as any).done).toBe(true);
  });
});

describe('coût estimé', () => {
  it('absent sans fourchette fournie par l’opérateur', async () => {
    const { estimatedCostEur } = await import('../src/routes/publicView.js');
    expect(estimatedCostEur('creative-1', {})).toBeNull();
    expect(estimatedCostEur('creative-1', { min: 40, max: 20 })).toBeNull();
  });
  it('reste dans la fourchette et ne change pas pour une même créative', async () => {
    const { estimatedCostEur } = await import('../src/routes/publicView.js');
    const range = { min: 20, max: 30 };
    const values = Array.from({ length: 500 }, (_, i) => estimatedCostEur(`creative-${i}`, range)!);
    expect(Math.min(...values)).toBe(20);
    expect(Math.max(...values)).toBe(30);
    expect(estimatedCostEur('creative-7', range)).toBe(estimatedCostEur('creative-7', range));
  });
});

describe('admin', () => {
  it('relie un prospect à son audit : domaine d\'abord, e-mail ensuite', async () => {
    const byDomain = await makeAudit();
    const waiting = await query<{ id: string }>(`INSERT INTO audits (status, source, contact_email) VALUES ('needs_domain','poller','Anne@Exemple.fr') RETURNING id`);
    const res = await app().request('/admin/audits/lookup', {
      method: 'POST',
      headers: { ...ADMIN, 'content-type': 'application/json' },
      body: JSON.stringify({ items: [
        { key: 'a', domain: 'https://www.exemple-test.fr/', email: 'anne@exemple.fr' },
        { key: 'b', email: 'anne@exemple.fr' },
        { key: 'c', email: 'inconnu@exemple.fr', domain: 'inconnu.fr' },
      ] }),
    });
    expect(res.status).toBe(200);
    const { results } = (await res.json()) as any;
    expect(results.a.id).toBe(byDomain.id);
    expect(results.b.id).toBe(waiting.rows[0].id);
    expect(results.b.status).toBe('needs_domain');
    expect(results.c).toBeNull();
    expect((await app().request('/admin/audits/lookup', { method: 'POST', body: '{}' })).status).toBe(401);
  });
  it('sans clé : 401', async () => {
    expect((await app().request('/admin/audits')).status).toBe(401);
    expect((await app().request('/admin/audits', { headers: { 'x-admin-key': 'mauvaise-cle-0000000000' } })).status).toBe(401);
  });
  it('crée un audit, puis réutilise le même domaine', async () => {
    const create = () => app().request('/admin/audits', { method: 'POST', headers: { ...ADMIN, 'content-type': 'application/json' }, body: JSON.stringify({ domain: 'https://www.business-admin.fr/', contact: { name: 'Jean Dupont' } }) });
    const first = (await (await create()).json()) as any;
    const second = (await (await create()).json()) as any;
    expect(first.reused).toBe(false);
    expect(second.reused).toBe(true);
    expect(second.auditId).toBe(first.auditId);
    const list = (await (await app().request('/admin/audits?q=business-admin', { headers: ADMIN })).json()) as any;
    expect(list.audits).toHaveLength(1);
    expect(list.audits[0].domain).toBe('business-admin.fr');
  });
  it('refuse un domaine privé ou invalide', async () => {
    const res = await app().request('/admin/audits', { method: 'POST', headers: { ...ADMIN, 'content-type': 'application/json' }, body: JSON.stringify({ domain: 'http://127.0.0.1/' }) });
    expect(res.status).toBe(400);
  });
  it('le détail expose les originaux, derrière la clé', async () => {
    const { id } = await makeAudit();
    const c = await addCreative(id, true, 1, 'a');
    const body = (await (await app().request(`/admin/audits/${id}`, { headers: ADMIN })).json()) as any;
    expect(body.creatives[0].originalUrl).toContain(c.original);
    const media = await app().request(`/admin/media/${id}/${c.original}`, { headers: ADMIN });
    expect(media.status).toBe(200);
    expect((await app().request(`/admin/media/${id}/${c.original}`)).status).toBe(401);
  });
});
