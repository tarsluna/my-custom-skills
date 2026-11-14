import { timingSafeEqual } from 'node:crypto';
import { Hono, type MiddlewareHandler } from 'hono';
import { z } from 'zod';
import { cfg } from '../config.js';
import { query } from '../db/pool.js';
import { createOrReuseAudit, rerunAudit } from '../audits/service.js';
import { enqueue, hasActiveJob } from '../jobs/queue.js';
import { kieCredits } from '../lib/kie.js';
import { normalizeDomain } from '../lib/domain.js';
import { adminMediaUrl } from '../lib/files.js';
import { errMsg, log } from '../log.js';
import { refreshProjects } from '../pipeline/run.js';
import { serveFile } from './public.js';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function safeEqual(a: string, b: string): boolean {
  const x = Buffer.from(a);
  const y = Buffer.from(b);
  return x.length === y.length && timingSafeEqual(x, y);
}

const requireAdmin: MiddlewareHandler = async (c, next) => {
  const key = c.req.header('x-admin-key') ?? '';
  if (!safeEqual(key, cfg().ADMIN_API_KEY)) return c.json({ error: 'Non autorisé' }, 401);
  await next();
};

export const adminRoutes = new Hono();
adminRoutes.use('/admin/*', requireAdmin);

adminRoutes.get('/admin/stats', async (c) => {
  const [today, jobs] = await Promise.all([
    query<{ started: number; created: number; ready: number }>(
      `SELECT count(*) FILTER (WHERE started_at >= d)::int AS started, count(*) FILTER (WHERE created_at >= d)::int AS created, count(*) FILTER (WHERE ready_at >= d)::int AS ready
       FROM audits, (SELECT date_trunc('day', now() AT TIME ZONE 'Europe/Paris') AT TIME ZONE 'Europe/Paris' AS d) t
       GROUP BY d`,
    ),
    query<{ queued: number; running: number }>(`SELECT count(*) FILTER (WHERE status='queued')::int AS queued, count(*) FILTER (WHERE status='running')::int AS running FROM jobs`),
  ]);
  let kieBalance: number | null = null;
  let kieError: string | null = null;
  try {
    kieBalance = await kieCredits();
  } catch (e) {
    kieError = errMsg(e);
  }
  return c.json({
    kieCredits: kieBalance,
    kieError,
    auditsToday: today.rows[0] ?? { started: 0, created: 0, ready: 0 },
    maxAuditsPerDay: cfg().MAX_AUDITS_PER_DAY,
    jobs: jobs.rows[0],
  });
});

adminRoutes.get('/admin/audits', async (c) => {
  const status = c.req.query('status');
  const q = c.req.query('q');
  const params: unknown[] = [];
  const where: string[] = [];
  if (status) {
    params.push(status);
    where.push(`status=$${params.length}`);
  }
  if (q) {
    params.push(`%${q}%`);
    where.push(`(domain ILIKE $${params.length} OR contact_name ILIKE $${params.length} OR contact_email ILIKE $${params.length} OR analysis->>'businessName' ILIKE $${params.length})`);
  }
  const res = await query(
    `SELECT id, token, status, domain, website_url, contact_name, contact_email, meeting_at, error, generations_used, source, created_at, updated_at, ready_at,
            analysis->>'businessName' AS business_name, analysis->>'logoFile' AS logo_file
     FROM audits ${where.length ? `WHERE ${where.join(' AND ')}` : ''}
     ORDER BY created_at DESC LIMIT 200`,
    params,
  );
  return c.json({ audits: res.rows });
});

const validId = (c: { req: { param: (k: string) => string } }, key = 'id') => UUID.test(c.req.param(key));

adminRoutes.get('/admin/audits/:id', async (c) => {
  if (!validId(c)) return c.json({ error: 'Audit introuvable' }, 404);
  const id = c.req.param('id');
  const audit = (await query('SELECT * FROM audits WHERE id=$1', [id])).rows[0];
  if (!audit) return c.json({ error: 'Audit introuvable' }, 404);
  const [creatives, competitors, projects, steps, costs, bookings, media, jobs] = await Promise.all([
    query('SELECT * FROM creatives WHERE audit_id=$1 ORDER BY idx', [id]),
    query('SELECT * FROM competitors WHERE audit_id=$1 ORDER BY ordering', [id]),
    query('SELECT * FROM projects WHERE audit_id=$1 ORDER BY ordering', [id]),
    query('SELECT step, status, message, meta, created_at FROM audit_steps WHERE audit_id=$1 ORDER BY id', [id]),
    query(`SELECT provider, sum(quantity)::float8 AS quantity, sum(usd)::float8 AS usd, count(*)::int AS calls FROM audit_costs WHERE audit_id=$1 GROUP BY provider`, [id]),
    query('SELECT call_id, event_id, booked_at, meeting_at, invitee_name, invitee_email, domain, outcome FROM bookings WHERE audit_id=$1 ORDER BY first_seen_at DESC', [id]),
    query('SELECT file_name, kind, content_type, bytes FROM media WHERE audit_id=$1 ORDER BY created_at', [id]),
    query('SELECT id, kind, status, attempts, claims, last_error, created_at, finished_at FROM jobs WHERE audit_id=$1 ORDER BY created_at DESC LIMIT 20', [id]),
  ]);
  const fileUrl = (file: string | null) => (file ? adminMediaUrl(id, file) : null);
  return c.json({
    audit,
    creatives: creatives.rows.map((r: any) => ({ ...r, originalUrl: fileUrl(r.original_file), displayUrl: fileUrl(r.display_file), blurUrl: fileUrl(r.blur_file), thumbUrl: fileUrl(r.thumb_file) })),
    competitors: competitors.rows.map((r: any) => ({ ...r, imageUrl: fileUrl(r.image_file), logoUrl: fileUrl(r.logo_file) })),
    projects: projects.rows.map((r: any) => ({ ...r, imageUrl: fileUrl(r.image_file) })),
    steps: steps.rows,
    costs: costs.rows,
    bookings: bookings.rows,
    media: media.rows.map((r: any) => ({ ...r, url: adminMediaUrl(id, r.file_name) })),
    jobs: jobs.rows,
    publicUrl: audit.token ? `${cfg().FRONTEND_ORIGIN}/c/${audit.token}` : null,
  });
});

const CreateBody = z.object({
  domain: z.string().min(1).max(300),
  contact: z
    .object({
      name: z.string().max(200).nullish(),
      firstName: z.string().max(100).nullish(),
      email: z.string().max(200).nullish(),
      phone: z.string().max(50).nullish(),
      meetingAt: z.string().datetime().nullish(),
    })
    .optional(),
});

const LookupBody = z.object({
  items: z.array(z.object({ key: z.string().min(1).max(64), email: z.string().max(320).nullish(), domain: z.string().max(300).nullish() })).max(300),
});

/** Relie des prospects du CRM à leur audit : le domaine d'abord, l'e-mail ensuite (cas du domaine encore manquant). */
adminRoutes.post('/admin/audits/lookup', async (c) => {
  const parsed = LookupBody.safeParse(await c.req.json().catch(() => null));
  if (!parsed.success) return c.json({ error: 'Requête invalide' }, 400);
  const items = parsed.data.items.map((i) => ({ key: i.key, email: i.email?.trim().toLowerCase() || null, domain: i.domain ? normalizeDomain(i.domain) : null }));
  const domains = [...new Set(items.map((i) => i.domain).filter((d): d is string => Boolean(d)))];
  const emails = [...new Set(items.map((i) => i.email).filter((e): e is string => Boolean(e)))];
  const rows = (domains.length || emails.length)
    ? (
        await query<{ id: string; domain: string | null; email: string | null }>(
          `SELECT id, token, status, domain, lower(contact_email) AS email, error, meeting_at, ready_at, created_at, analysis->>'businessName' AS business_name
           FROM audits WHERE domain = ANY($1::text[]) OR lower(contact_email) = ANY($2::text[]) ORDER BY created_at DESC`,
          [domains, emails],
        )
      ).rows
    : [];
  const results: Record<string, unknown> = {};
  for (const item of items) {
    results[item.key] = (item.domain && rows.find((r) => r.domain === item.domain)) || (item.email && rows.find((r) => r.email === item.email)) || null;
  }
  return c.json({ results });
});

adminRoutes.post('/admin/audits', async (c) => {
  const parsed = CreateBody.safeParse(await c.req.json().catch(() => null));
  if (!parsed.success) return c.json({ error: 'Requête invalide' }, 400);
  const domain = normalizeDomain(parsed.data.domain);
  if (!domain) return c.json({ error: 'Domaine invalide' }, 400);
  const contact = parsed.data.contact;
  const out = await createOrReuseAudit({
    domain,
    source: 'admin',
    contact: contact ? { name: contact.name, firstName: contact.firstName ?? contact.name?.split(/\s+/)[0] ?? null, email: contact.email, phone: contact.phone, meetingAt: contact.meetingAt ? new Date(contact.meetingAt) : null } : undefined,
  });
  return c.json(out, 201);
});

const RerunBody = z.object({ domain: z.string().min(1).max(300).optional() }).optional();

adminRoutes.post('/admin/audits/:id/rerun', async (c) => {
  if (!validId(c)) return c.json({ error: 'Audit introuvable' }, 404);
  const body = RerunBody.safeParse(await c.req.json().catch(() => undefined));
  if (!body.success) return c.json({ error: 'Requête invalide' }, 400);
  let domain: string | null = null;
  if (body.data?.domain) {
    domain = normalizeDomain(body.data.domain);
    if (!domain) return c.json({ error: 'Domaine invalide' }, 400);
  }
  const out = await rerunAudit(c.req.param('id'), domain);
  if (out === 'not_found') return c.json({ error: 'Audit introuvable' }, 404);
  if (out === 'active') return c.json({ error: 'Un traitement est déjà en cours' }, 409);
  if (out === 'missing_domain') return c.json({ error: 'Indiquez un domaine pour relancer cet audit' }, 400);
  return c.json({ ok: true }, 202);
});

adminRoutes.post('/admin/audits/:id/projects/refresh', async (c) => {
  if (!validId(c)) return c.json({ error: 'Audit introuvable' }, 404);
  const id = c.req.param('id');
  const exists = await query('SELECT 1 FROM audits WHERE id=$1 AND domain IS NOT NULL', [id]);
  if ((exists.rowCount ?? 0) === 0) return c.json({ error: 'Audit introuvable' }, 404);
  if (await hasActiveJob(id)) return c.json({ error: 'Un traitement est déjà en cours' }, 409);
  void refreshProjects(id).catch((e) => log.error('relecture des projets en échec', { auditId: id, error: errMsg(e) }));
  return c.json({ ok: true }, 202);
});

adminRoutes.post('/admin/audits/:id/creatives/:cid/regenerate', async (c) => {
  if (!validId(c) || !validId(c, 'cid')) return c.json({ error: 'Créative introuvable' }, 404);
  const id = c.req.param('id');
  const cid = c.req.param('cid');
  const exists = await query('SELECT 1 FROM creatives WHERE id=$1 AND audit_id=$2', [cid, id]);
  if ((exists.rowCount ?? 0) === 0) return c.json({ error: 'Créative introuvable' }, 404);
  if (await hasActiveJob(id)) return c.json({ error: 'Un traitement est déjà en cours' }, 409);
  const queued = await enqueue(id, 'regenerate', { creativeId: cid });
  if (!queued) return c.json({ error: 'Un traitement est déjà en cours' }, 409);
  return c.json({ ok: true }, 202);
});

const LockBody = z.object({ locked: z.boolean() });

adminRoutes.patch('/admin/audits/:id/creatives/:cid', async (c) => {
  if (!validId(c) || !validId(c, 'cid')) return c.json({ error: 'Créative introuvable' }, 404);
  const parsed = LockBody.safeParse(await c.req.json().catch(() => null));
  if (!parsed.success) return c.json({ error: 'Requête invalide' }, 400);
  const res = await query(`UPDATE creatives SET locked=$3, updated_at=now() WHERE id=$1 AND audit_id=$2 RETURNING id, idx, locked`, [c.req.param('cid'), c.req.param('id'), parsed.data.locked]);
  if (!res.rows[0]) return c.json({ error: 'Créative introuvable' }, 404);
  return c.json(res.rows[0]);
});

adminRoutes.get('/admin/media/:id/:file', async (c) => {
  if (!validId(c)) return c.json({ error: 'Introuvable' }, 404);
  const res = await query<{ path: string; content_type: string }>('SELECT path, content_type FROM media WHERE audit_id=$1 AND file_name=$2', [c.req.param('id'), c.req.param('file')]);
  const row = res.rows[0];
  if (!row) return c.json({ error: 'Introuvable' }, 404);
  return serveFile(c, row.path, row.content_type);
});
