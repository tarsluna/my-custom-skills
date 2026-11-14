import 'server-only';
import type { AdminAuditDetail, AdminAuditRow, AdminCosts, AdminCreative, AdminStats, AdminStatus, AdminStep } from './types';
import { adminKey, apiBase, useFixtures } from './env';
import * as fx from './fixtures';
import { isValidFile, isValidId } from './safe';

/* Le serveur Next est le seul à connaître ADMIN_API_KEY. */

type Json = Record<string, unknown>;
const STATUSES: AdminStatus[] = ['queued', 'analyzing', 'ads', 'creatives', 'ready', 'failed', 'needs_domain'];

const str = (v: unknown): string | null => (typeof v === 'string' && v.trim() ? v : null);
const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);
const obj = (v: unknown): Json => (v && typeof v === 'object' ? (v as Json) : {});

async function call(path: string, init?: RequestInit): Promise<Response | null> {
  const base = apiBase();
  const key = adminKey();
  if (!base || !key) return null;
  try {
    return await fetch(`${base}${path}`, {
      ...init,
      cache: 'no-store',
      headers: { 'x-admin-key': key, ...(init?.body ? { 'content-type': 'application/json' } : {}) },
      signal: AbortSignal.timeout(20_000),
    });
  } catch {
    return null;
  }
}

function toRow(raw: unknown): AdminAuditRow {
  const r = obj(raw);
  const biz = obj(r.business);
  const analysis = obj(r.analysis);
  const contact = obj(r.contact);
  const id = String(r.id ?? '');
  const logoFile = str(analysis.logoFile) ?? str(r.logo_file);
  const status = STATUSES.includes(r.status as AdminStatus) ? (r.status as AdminStatus) : 'queued';
  return {
    id,
    token: str(r.token),
    status,
    domain: str(r.domain) ?? str(biz.domain),
    businessName: str(biz.name) ?? str(r.businessName) ?? str(r.business_name) ?? str(analysis.businessName) ?? str(r.domain),
    professionLabel: str(biz.professionLabel) ?? str(r.professionLabel) ?? str(analysis.professionLabel),
    city: str(biz.city) ?? str(r.city) ?? str(analysis.city),
    logoUrl: logoFile ? `/api/admin/media/${encodeURIComponent(id)}/${encodeURIComponent(logoFile)}` : (str(biz.logoUrl) ?? str(r.logoUrl) ?? str(r.logo_url)),
    contactName: str(contact.name) ?? str(r.contactName) ?? str(r.contact_name),
    contactEmail: str(contact.email) ?? str(r.contactEmail) ?? str(r.contact_email),
    meetingAt: str(r.meetingAt) ?? str(r.meeting_at),
    createdAt: str(r.createdAt) ?? str(r.created_at),
    error: str(r.error),
  };
}

function toCreative(raw: unknown, auditId: string): AdminCreative {
  const c = obj(raw);
  const file = str(c.originalFile) ?? str(c.original_file);
  const original = str(c.originalUrl) ?? str(c.original_url) ?? str(c.imageUrl);
  const fmt = c.format === '9:16' || c.format === '1:1' ? c.format : '4:5';
  return {
    id: String(c.id ?? ''),
    index: num(c.index) ?? num(c.idx) ?? 0,
    concept: str(c.concept) ?? '',
    format: fmt,
    locked: Boolean(c.locked),
    imageUrl: rewriteMedia(file ? `/admin/media/${auditId}/${file}` : original, auditId),
    headline: str(c.headline),
    primaryText: str(c.primaryText) ?? str(c.primary_text),
    bullets: Array.isArray(c.bullets) ? (c.bullets as unknown[]).filter((b): b is string => typeof b === 'string') : [],
    cta: str(c.cta),
    angle: str(c.angle),
    status: str(c.status),
  };
}

/** Les originaux passent par le proxy authentifié ; le navigateur ne parle jamais à l'API admin. */
function rewriteMedia(u: string | null, auditId: string): string {
  if (!u) return '';
  const m = u.match(/\/admin\/media\/[^/]+\/([^/?#]+)/);
  if (m) return `/api/admin/media/${encodeURIComponent(auditId)}/${encodeURIComponent(m[1])}`;
  return u;
}

const STEP_LABEL: Record<string, string> = {
  analyzing: 'Analyse du site',
  ads: 'Concurrents',
  creatives: 'Créatives',
  ready: 'Page en ligne',
  failed: 'Erreur',
  queued: 'Mise en file',
  needs_domain: 'Domaine manquant',
};

function toStep(raw: unknown, i: number): AdminStep {
  const s = obj(raw);
  const name = str(s.name) ?? str(s.step) ?? `step-${i}`;
  return {
    name,
    label: str(s.label) ?? STEP_LABEL[name] ?? name,
    status: str(s.status) ?? '',
    at: str(s.at) ?? str(s.created_at) ?? str(s.createdAt),
    detail: str(s.detail) ?? str(s.message),
  };
}

function toCosts(raw: unknown): AdminCosts {
  if (Array.isArray(raw)) {
    const rows = raw.map(obj);
    const by = (re: RegExp) => rows.filter((r) => re.test(String(r.provider ?? '')));
    const usd = (list: Json[]) => (list.length ? list.reduce((t, r) => t + (num(r.usd) ?? 0), 0) : null);
    const kie = by(/kie/i);
    return {
      kieCredits: kie.length ? kie.reduce((t, r) => t + (num(r.quantity) ?? 0), 0) : null,
      generations: kie.length ? kie.reduce((t, r) => t + (num(r.calls) ?? 0), 0) : null,
      llmUsd: usd(by(/openrouter|llm/i)),
      apifyUsd: usd(by(/apify/i)),
    };
  }
  const c = obj(raw);
  return {
    kieCredits: num(c.kieCredits) ?? num(c.kie_credits) ?? num(c.credits),
    generations: num(c.generations),
    llmUsd: num(c.llmUsd) ?? num(c.llm_usd),
    apifyUsd: num(c.apifyUsd) ?? num(c.apify_usd),
  };
}

function toDetail(raw: unknown): AdminAuditDetail {
  const r = obj(raw);
  const a = r.audit ? obj(r.audit) : r;
  const row = toRow(a);
  const crea = (r.creatives ?? a.creatives) as unknown;
  const steps = (r.steps ?? a.steps ?? r.events ?? a.events ?? r.log ?? a.log) as unknown;
  return {
    ...row,
    creatives: Array.isArray(crea) ? crea.map((c) => toCreative(c, row.id)).sort((x, y) => x.index - y.index) : [],
    steps: Array.isArray(steps) ? steps.map(toStep) : [],
    costs: { ...toCosts(r.costs ?? a.costs), generations: toCosts(r.costs ?? a.costs).generations ?? num(a.generations_used) },
  };
}

export async function adminStats(): Promise<AdminStats | null> {
  if (useFixtures()) return fx.fixtureStats();
  const res = await call('/admin/stats');
  if (!res?.ok) return null;
  const r = obj(await res.json().catch(() => null));
  const today = obj(r.auditsToday);
  return {
    kieCredits: num(r.kieCredits),
    auditsToday: num(r.auditsToday) ?? num(today.started) ?? num(today.created),
    maxAuditsPerDay: num(r.maxAuditsPerDay),
  };
}

export async function adminList(status: string | null, q: string | null): Promise<AdminAuditRow[] | null> {
  if (useFixtures()) return fx.fixtureList(status, q);
  const params = new URLSearchParams();
  if (status && STATUSES.includes(status as AdminStatus)) params.set('status', status);
  if (q) params.set('q', q.slice(0, 120));
  const qs = params.toString();
  const res = await call(`/admin/audits${qs ? `?${qs}` : ''}`);
  if (!res?.ok) return null;
  const j = (await res.json().catch(() => null)) as unknown;
  const list = Array.isArray(j) ? j : obj(j).audits;
  return Array.isArray(list) ? list.map(toRow) : null;
}

export async function adminDetail(id: string): Promise<AdminAuditDetail | null> {
  if (!isValidId(id)) return null;
  if (useFixtures()) return fx.fixtureDetail(id);
  const res = await call(`/admin/audits/${encodeURIComponent(id)}`);
  if (!res?.ok) return null;
  return toDetail(await res.json().catch(() => null));
}

export type AdminResult = { ok: boolean; status: number; data?: unknown; message?: string };

async function outcome(res: Response | null): Promise<AdminResult> {
  if (!res) return { ok: false, status: 502 };
  const data = await res.json().catch(() => null);
  return { ok: res.ok, status: res.status, data, message: str(obj(data).error) ?? undefined };
}

export async function adminCreate(domain: string, contact?: { name?: string; email?: string } | null): Promise<AdminResult> {
  if (useFixtures()) return { ok: true, status: 200, data: fx.fixtureCreate(domain, contact) };
  return outcome(await call('/admin/audits', { method: 'POST', body: JSON.stringify({ domain, ...(contact ? { contact } : {}) }) }));
}

/** Avec un domaine, complète un audit `needs_domain` en gardant son rendez-vous et son contact. */
export async function adminRerun(id: string, domain?: string | null): Promise<AdminResult> {
  if (!isValidId(id)) return { ok: false, status: 400 };
  if (useFixtures()) return { ok: fx.fixtureRerun(id, domain), status: 200 };
  return outcome(await call(`/admin/audits/${encodeURIComponent(id)}/rerun`, { method: 'POST', body: JSON.stringify(domain ? { domain } : {}) }));
}

export async function adminRegenerate(id: string, cid: string): Promise<AdminResult> {
  if (!isValidId(id) || !isValidId(cid)) return { ok: false, status: 400 };
  if (useFixtures()) return { ok: true, status: 200 };
  return outcome(await call(`/admin/audits/${encodeURIComponent(id)}/creatives/${encodeURIComponent(cid)}/regenerate`, { method: 'POST' }));
}

export async function adminLock(id: string, cid: string, locked: boolean): Promise<AdminResult> {
  if (!isValidId(id) || !isValidId(cid)) return { ok: false, status: 400 };
  if (useFixtures()) return { ok: fx.fixtureLock(id, cid, locked), status: 200 };
  return outcome(
    await call(`/admin/audits/${encodeURIComponent(id)}/creatives/${encodeURIComponent(cid)}`, {
      method: 'PATCH',
      body: JSON.stringify({ locked }),
    }),
  );
}

/** Flux d'un original, réservé aux sessions admin. */
export async function adminMedia(id: string, file: string): Promise<Response | null> {
  if (!isValidId(id) || !isValidFile(file)) return null;
  return call(`/admin/media/${encodeURIComponent(id)}/${encodeURIComponent(file)}`);
}
