import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import { query } from '../src/db/pool.js';
import { ensureWatermark, getWatermark, ingestBooking, pollOnce } from '../src/poller.js';
import { parseEventCall, type ParsedBooking } from '../src/lib/iclosed.js';
import { TEST_DATABASE_URL, setupTestEnv, teardownTestEnv, truncateAll } from './helpers.js';
import { loadConfig, setConfigForTests } from '../src/config.js';
import { webhookRoutes } from '../src/routes/webhooks.js';

const EVENT = '1001';
const FUTURE = new Date(Date.now() + 5 * 86_400_000).toISOString();

const row = (over: Record<string, unknown> = {}) => ({
  id: 1001,
  callId: 1001,
  eventId: Number(EVENT),
  createdAt: new Date().toISOString(),
  dateTimeUTC: FUTURE,
  inviteeEmail: 'marie@exemple-dupont.fr',
  inviteeName: 'Marie Dupont',
  phoneNumber: '+33 2 61 91 00 00',
  cancelledBy: null,
  cancelReason: '',
  questions: [{ statement: 'First Name', answer: 'Marie' }],
  secondaryAnswers: [],
  ...over,
});

const countAudits = async () => (await query<{ n: number }>('SELECT count(*)::int AS n FROM audits')).rows[0].n;
const countJobs = async () => (await query<{ n: number }>('SELECT count(*)::int AS n FROM jobs')).rows[0].n;

beforeAll(async () => {
  await setupTestEnv({ BOOKING_EVENT_IDS: EVENT });
});
afterAll(async () => {
  await teardownTestEnv();
});
beforeEach(async () => {
  await truncateAll();
});

describe('filigrane', () => {
  it('est posé une seule fois et survit aux démarrages suivants', async () => {
    const first = await ensureWatermark(new Date('2026-11-08T10:00:00Z'));
    const second = await ensureWatermark(new Date('2026-12-01T10:00:00Z'));
    expect(second.toISOString()).toBe(first.toISOString());
    expect((await getWatermark())!.toISOString()).toBe('2026-11-08T10:00:00.000Z');
  });

  it('ignore les réservations antérieures et ne dépense rien sur l’historique', async () => {
    await ensureWatermark(new Date(Date.now() + 60_000));
    const out = await pollOnce([row({ createdAt: new Date(Date.now() - 86_400_000).toISOString() })]);
    expect(out.created).toBe(0);
    expect(await countAudits()).toBe(0);
    expect(await countJobs()).toBe(0);
  });

  it('prend les réservations postérieures', async () => {
    await ensureWatermark(new Date(Date.now() - 60_000));
    const out = await pollOnce([row()]);
    expect(out.created).toBe(1);
    expect(await countAudits()).toBe(1);
    expect(await countJobs()).toBe(1);
  });
});

describe('idempotence', () => {
  beforeEach(async () => {
    await ensureWatermark(new Date(Date.now() - 60_000));
  });

  it('rejouer la même réservation ne crée rien de plus', async () => {
    await pollOnce([row()]);
    await pollOnce([row()]);
    await pollOnce([row()]);
    expect(await countAudits()).toBe(1);
    expect(await countJobs()).toBe(1);
    const bookings = await query<{ n: number }>('SELECT count(*)::int AS n FROM bookings');
    expect(bookings.rows[0].n).toBe(1);
  });

  it('deux réservations simultanées du même domaine n’en font qu’un audit', async () => {
    await Promise.all([pollOnce([row({ id: 1, callId: 1 })]), pollOnce([row({ id: 2, callId: 2, inviteeEmail: 'paul@exemple-dupont.fr', inviteeName: 'Paul Martin' })])]);
    expect(await countAudits()).toBe(1);
    expect(await countJobs()).toBe(1);
    const outcomes = await query<{ outcome: string }>('SELECT outcome FROM bookings ORDER BY outcome');
    expect(outcomes.rows.map((r) => r.outcome).sort()).toEqual(['created', 'reused']);
  });

  it('un domaine traité il y a moins de 30 jours réutilise l’audit', async () => {
    await pollOnce([row({ id: 3, callId: 3 })]);
    await pollOnce([row({ id: 4, callId: 4, inviteeEmail: 'autre@exemple-dupont.fr', dateTimeUTC: new Date(Date.now() + 9 * 86_400_000).toISOString() })]);
    expect(await countAudits()).toBe(1);
    const audit = await query<{ meeting_at: Date }>('SELECT meeting_at FROM audits');
    expect(audit.rows[0].meeting_at.getTime()).toBeGreaterThan(Date.now() + 8 * 86_400_000);
  });

  it('au-delà de 30 jours, un nouvel audit est créé', async () => {
    await pollOnce([row({ id: 5, callId: 5 })]);
    await query(`UPDATE audits SET created_at = now() - interval '31 days'`);
    await pollOnce([row({ id: 6, callId: 6 })]);
    expect(await countAudits()).toBe(2);
  });

  it('un audit en échec ne bloque pas une nouvelle réservation', async () => {
    await pollOnce([row({ id: 7, callId: 7 })]);
    await query(`UPDATE audits SET status='failed'`);
    await pollOnce([row({ id: 8, callId: 8 })]);
    expect(await countAudits()).toBe(2);
  });
});

describe('tri des réservations', () => {
  beforeEach(async () => {
    await ensureWatermark(new Date(Date.now() - 60_000));
  });

  it('ignore les autres événements', async () => {
    const out = await pollOnce([row({ eventId: 1002 })]);
    expect(out.created).toBe(0);
    expect(await countAudits()).toBe(0);
  });

  it('ignore les réservations annulées', async () => {
    await pollOnce([row({ cancelledBy: 'superadmin (Exemple)' })]);
    expect(await countAudits()).toBe(0);
    const b = await query<{ outcome: string }>('SELECT outcome FROM bookings');
    expect(b.rows[0].outcome).toBe('ignored_cancelled');
  });

  it('ignore un rendez-vous déjà passé', async () => {
    await pollOnce([row({ dateTimeUTC: new Date(Date.now() - 3600_000).toISOString() })]);
    expect(await countAudits()).toBe(0);
  });

  it('e-mail grand public sans site : needs_domain, sans job', async () => {
    await pollOnce([row({ inviteeEmail: 'marie@gmail.com' })]);
    const audits = await query<{ status: string }>('SELECT status FROM audits');
    expect(audits.rows[0].status).toBe('needs_domain');
    expect(await countJobs()).toBe(0);
  });

  it('prend le site répondu au formulaire avant l’e-mail', async () => {
    await pollOnce([row({ inviteeEmail: 'marie@gmail.com', questions: [{ statement: 'Votre site web', answer: 'https://www.exemple-b.fr/' }] })]);
    const audits = await query<{ domain: string }>('SELECT domain FROM audits');
    expect(audits.rows[0].domain).toBe('exemple-b.fr');
  });

  it('annulation avant démarrage : l’audit en file est abandonné', async () => {
    await pollOnce([row({ id: 9, callId: 9 })]);
    await pollOnce([row({ id: 9, callId: 9, cancelledBy: 'Marie' })]);
    const jobs = await query<{ status: string }>('SELECT status FROM jobs');
    expect(jobs.rows[0].status).toBe('cancelled');
    const audits = await query<{ status: string }>('SELECT status FROM audits');
    expect(audits.rows[0].status).toBe('failed');
  });

  it('un rendez-vous déplacé met à jour la date de l’audit', async () => {
    await pollOnce([row({ id: 10, callId: 10 })]);
    const moved = new Date(Date.now() + 20 * 86_400_000).toISOString();
    await pollOnce([row({ id: 10, callId: 10, dateTimeUTC: moved })]);
    const audit = await query<{ meeting_at: Date }>('SELECT meeting_at FROM audits');
    expect(audit.rows[0].meeting_at.toISOString()).toBe(new Date(moved).toISOString());
  });
});

describe('parseEventCall', () => {
  it('lit le prénom du formulaire et détecte une annulation', () => {
    const parsed = parseEventCall(row({ cancelledBy: 'superadmin (Exemple)', cancelReason: 'x' }), new Date());
    expect(parsed?.firstName).toBe('Marie');
    expect(parsed?.cancelled).toBe(true);
  });
  it('un champ vide en objet ne compte pas comme une annulation', () => {
    const parsed = parseEventCall(row({ cancelledBy: {}, cancelReason: '' }));
    expect(parsed?.cancelled).toBe(false);
  });
  it('sans identifiant, rien n’est créé', () => {
    expect(parseEventCall({ eventId: 1 })).toBeNull();
  });
  it('ingestBooking traite le callId comme clé, quelle que soit sa valeur', async () => {
    await ensureWatermark(new Date(Date.now() - 60_000));
    const parsed = parseEventCall(row({ id: 11, callId: 11 })) as ParsedBooking;
    const watermark = (await getWatermark())!;
    expect(await ingestBooking(parsed, watermark, 'poller')).toBe('created');
    expect(await ingestBooking(parsed, watermark, 'webhook')).toBe('duplicate');
  });
});

describe('adaptateur générique', () => {
  const secret = 'secret-de-webhook-de-test';
  const post = (body: unknown, key = secret) =>
    webhookRoutes(() => undefined).request('/webhooks/booking', { method: 'POST', headers: { 'content-type': 'application/json', 'x-webhook-secret': key, 'x-real-ip': '10.1.1.1' }, body: JSON.stringify(body) });
  const booking = (over: Record<string, unknown> = {}) => ({ id: 'rdv-1', meetingAt: FUTURE, name: 'Jeanne Martin', email: 'jeanne@gmail.com', website: 'https://www.exemple-c.fr/', ...over });

  beforeEach(async () => {
    setConfigForTests({ ...loadConfig({ ...process.env, NODE_ENV: 'test', DATABASE_URL: TEST_DATABASE_URL, DATA_DIR: '/tmp', ADMIN_API_KEY: 'admin-key-for-tests-0001', OPENROUTER_API_KEY: 'test', BOOKING_WEBHOOK_SECRET: secret } as NodeJS.ProcessEnv) });
    await ensureWatermark(new Date(Date.now() - 60_000));
  });

  it('refuse un secret faux', async () => {
    expect((await post(booking(), 'mauvais-secret-de-test')).status).toBe(401);
  });
  it('crée un audit depuis le champ website, une seule fois', async () => {
    const first = await post(booking());
    expect(first.status).toBe(200);
    expect(((await first.json()) as any).results).toEqual(['created']);
    const second = await post(booking());
    expect(((await second.json()) as any).results).toEqual(['duplicate']);
    const audits = await query<{ domain: string; contact_first_name: string }>('SELECT domain, contact_first_name FROM audits');
    expect(audits.rows).toEqual([{ domain: 'exemple-c.fr', contact_first_name: 'Jeanne' }]);
  });
  it('sans site ni e-mail professionnel : en attente de domaine', async () => {
    const res = await post(booking({ id: 'rdv-2', website: null }));
    expect(((await res.json()) as any).results).toEqual(['needs_domain']);
  });
  it('rejette un corps illisible', async () => {
    expect((await post({ nimporte: 'quoi' })).status).toBe(400);
  });
});
