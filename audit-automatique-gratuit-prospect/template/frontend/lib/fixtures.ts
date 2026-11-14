import 'server-only';
import base from '@/fixtures/audit.json';
import admin from '@/fixtures/admin.json';
import type {
  AdminAuditDetail,
  AdminAuditRow,
  AdminCreative,
  AdminStats,
  AdminStatus,
  AuditLookup,
  ChatTurn,
  PublicAudit,
} from './types';
import type { ChatOutcome } from './audits';

/* Données de démonstration, activées uniquement par USE_FIXTURES=1. Toutes les entreprises sont fictives. */

const audit = base as unknown as PublicAudit & { _fixture?: string };

export function fixtureAudit(token: string): AuditLookup {
  if (token === audit.token) return { kind: 'ok', audit };

  if (token === 'demo-attente') {
    return { kind: 'ok', audit: { ...audit, token, status: 'processing', creatives: [], projects: [] } };
  }
  if (token === 'demo-cout') {
    return { kind: 'ok', audit: { ...audit, token, creatives: audit.creatives.map((c, i) => ({ ...c, estimatedCostEur: 20 + i })) } };
  }
  if (token === 'demo-erreur') {
    return { kind: 'ok', audit: { ...audit, token, status: 'failed' } };
  }
  if (token === 'demo-elargi') {
    return {
      kind: 'ok',
      audit: {
        ...audit,
        token,
        business: {
          ...audit.business,
          name: 'Entreprise Fictive au nom très long pour éprouver la mise en page',
          profession: 'cuisiniste',
          professionLabel: 'cuisiniste',
          city: 'Exempleville',
          palette: { primary: '#111111', secondary: '#777777', accent: '#BBBBBB', background: '#101010', text: '#EEEEEE' },
        },
        competitors: { ...audit.competitors, radiusKm: 200, widened: true },
      },
    };
  }
  if (token === 'demo-xss') {
    const evil = '<img src=x onerror="window.__xss=1"><script>window.__xss=1</script>';
    return {
      kind: 'ok',
      audit: {
        ...audit,
        token,
        business: {
          ...audit.business,
          name: `Entreprise ${evil}`,
          summary: evil,
          websiteUrl: 'javascript:window.__xss=1',
          logoUrl: 'javascript:window.__xss=1',
          palette: { primary: 'red;}body{display:none}', secondary: '#000', accent: 'url(x)', background: 'expression(1)', text: '#fff' },
          specialties: [evil],
        },
        competitors: {
          ...audit.competitors,
          items: audit.competitors.items.map((c) => ({ ...c, pageName: evil, body: evil, why: evil, adLibraryUrl: 'javascript:window.__xss=1', imageUrl: 'javascript:window.__xss=1' })),
        },
        projects: audit.projects.map((p) => ({ ...p, title: evil, sourceUrl: 'javascript:window.__xss=1' })),
        setter: { ...audit.setter, firstProspectMessage: evil, suggestedReplies: [evil] },
      },
    };
  }
  if (token === 'demo-vide') {
    return {
      kind: 'ok',
      audit: {
        ...audit,
        token,
        contact: { firstName: null },
        meetingAt: null,
        business: {
          ...audit.business,
          name: 'Exemple Fictif',
          profession: 'cuisiniste',
          professionLabel: 'cuisiniste',
          city: null,
          region: null,
          logoUrl: null,
          logoIsFallback: true,
          specialties: [],
          projectTypes: [],
        },
        competitors: { radiusKm: null, widened: true, insights: [], items: [] },
        projects: audit.projects.slice(0, 1),
      },
    };
  }
  return { kind: 'not_found' };
}

const lastUser = (m: ChatTurn[]) => [...m].reverse().find((t) => t.role === 'user')?.content.toLowerCase() ?? '';

/** Réponses simulées, sans appel au backend : suffisant pour vérifier le parcours du téléphone. */
export async function fixtureChat(messages: ChatTurn[]): Promise<ChatOutcome> {
  await new Promise((r) => setTimeout(r, 350));
  const said = messages.filter((m) => m.role === 'user').length;
  const text = lastUser(messages);
  if (said >= 8) {
    return {
      kind: 'ok',
      data: { replies: ['Parfait. Je transmets votre projet à Claire, qui vous rappelle pour fixer un rendez-vous.'], done: true },
    };
  }
  if (said === 1) {
    return {
      kind: 'ok',
      data: {
        replies: [
          'Bonjour, je suis l’assistant d’Exemple Rénovation.',
          'Un appartement à rénover, c’est exactement notre métier. Quel budget global avez-vous en tête pour les travaux ?',
        ],
        done: false,
      },
    };
  }
  if (/\b\d[\d\s]*(k|€|euros?)/.test(text) || text.includes('budget')) {
    return { kind: 'ok', data: { replies: ['Très bien, ce budget permet un beau travail sur la matière. Quand aimeriez-vous commencer ?'], done: false } };
  }
  if (text.includes('printemps') || text.includes('commencer') || text.includes('date')) {
    return { kind: 'ok', data: { replies: ['Le printemps se prépare maintenant.', 'Préférez-vous un rendez-vous en semaine, ou un samedi matin à l’atelier ?'], done: false } };
  }
  if (text.includes('rappel') || text.includes('appel')) {
    return { kind: 'ok', data: { replies: ['Bien sûr. Quel créneau vous convient le mieux, plutôt en matinée ou en fin de journée ?'], done: false } };
  }
  return { kind: 'ok', data: { replies: ['Merci. Pouvez-vous m’en dire un peu plus sur ce que vous imaginez pour cet appartement ?'], done: false } };
}

/* ---------- Admin ---------- */

type Store = {
  started: number;
  rows: AdminAuditRow[];
  creatives: Map<string, AdminCreative[]>;
  regenerating: Set<string>;
};
const g = globalThis as unknown as { __auditFixtureStore?: Store };

const ORIGINAL_TEXT: Record<number, { headline: string; primaryText: string; bullets: string[] }> = Object.fromEntries(
  [2, 3, 4, 5, 8, 9, 10].map((i) => [i, { headline: `Accroche fictive ${i}.`, primaryText: 'Texte fictif, visible seulement dans l’admin.', bullets: ['Puce fictive'] }]),
);

function makeCreatives(auditId: string): AdminCreative[] {
  return audit.creatives.map((c) => ({
    id: c.id,
    index: c.index,
    concept: c.concept,
    format: c.format,
    locked: c.locked,
    imageUrl: `/api/admin/media/${auditId}/crea-${String(c.index).padStart(2, '0')}.svg`,
    headline: c.headline ?? ORIGINAL_TEXT[c.index]?.headline ?? null,
    primaryText: c.primaryText ?? ORIGINAL_TEXT[c.index]?.primaryText ?? null,
    bullets: c.bullets ?? ORIGINAL_TEXT[c.index]?.bullets ?? [],
    cta: c.index % 2 ? 'Prendre rendez-vous' : 'Voir le projet',
    angle: c.index <= 3 ? 'Matière et lumière' : 'Projet entier',
    status: 'ready',
  }));
}

function store(): Store {
  if (!g.__auditFixtureStore) {
    g.__auditFixtureStore = {
      started: Date.now(),
      rows: (admin.audits as Array<Partial<AdminAuditRow>>).map((r) => ({
        id: r.id ?? '',
        token: r.token ?? null,
        status: (r.status ?? 'queued') as AdminStatus,
        domain: r.domain ?? null,
        businessName: r.businessName ?? null,
        professionLabel: r.professionLabel ?? null,
        city: r.city ?? null,
        logoUrl: r.logoUrl ?? null,
        contactName: r.contactName ?? null,
        contactEmail: r.contactEmail ?? null,
        meetingAt: r.meetingAt ?? null,
        createdAt: r.createdAt ?? null,
        error: r.error ?? null,
      })),
      creatives: new Map(),
      regenerating: new Set(),
    };
  }
  return g.__auditFixtureStore;
}

/** Fait avancer les audits en cours pour vérifier le statut en direct. */
function advance(s: Store) {
  const order: AdminStatus[] = ['queued', 'analyzing', 'ads', 'creatives', 'ready'];
  const steps = Math.floor((Date.now() - s.started) / 14_000);
  const startFor: Record<string, number> = { 'a-1002': 3, 'a-1003': 1, 'a-1006': 0 };
  for (const r of s.rows) {
    const start = startFor[r.id];
    if (start === undefined) continue;
    r.status = order[Math.min(order.length - 1, start + steps)];
  }
}

export function fixtureStats(): AdminStats {
  return admin.stats as AdminStats;
}

export function fixtureList(status: string | null, q: string | null): AdminAuditRow[] {
  const s = store();
  advance(s);
  const needle = q?.trim().toLowerCase();
  return s.rows.filter((r) => {
    if (status && r.status !== status) return false;
    if (!needle) return true;
    return [r.businessName, r.domain, r.contactName, r.contactEmail].some((v) => v?.toLowerCase().includes(needle));
  });
}

export function fixtureCreate(domain: string, contact?: { name?: string; email?: string } | null): AdminAuditRow {
  const s = store();
  const slug = domain.replace(/\W+/g, '-');
  const row: AdminAuditRow = {
    id: `a-${Date.now()}`,
    token: `${slug}-Fx0000000000000000000000`,
    status: 'queued',
    domain,
    businessName: domain,
    professionLabel: null,
    city: null,
    logoUrl: null,
    contactName: contact?.name ?? null,
    contactEmail: contact?.email ?? null,
    meetingAt: null,
    createdAt: new Date().toISOString(),
    error: null,
  };
  s.rows.unshift(row);
  return row;
}

export function fixtureDetail(id: string): AdminAuditDetail | null {
  const s = store();
  advance(s);
  const row = s.rows.find((r) => r.id === id);
  if (!row) return null;
  if (!s.creatives.has(id)) s.creatives.set(id, makeCreatives(id));
  const ready = row.status === 'ready';
  return {
    ...row,
    creatives: ready ? (s.creatives.get(id) ?? []) : [],
    steps: ready
      ? admin.steps
      : admin.steps.slice(0, Math.max(1, ['queued', 'analyzing', 'ads', 'creatives'].indexOf(row.status))).map((x) => ({ ...x })),
    costs: admin.costs,
  };
}

export function fixtureLock(id: string, cid: string, locked: boolean): boolean {
  const s = store();
  const list = s.creatives.get(id) ?? makeCreatives(id);
  s.creatives.set(id, list);
  const c = list.find((x) => x.id === cid);
  if (!c) return false;
  c.locked = locked;
  return true;
}

export function fixtureRerun(id: string, domain?: string | null): boolean {
  const r = store().rows.find((x) => x.id === id);
  if (!r) return false;
  if (domain) {
    r.domain = domain;
    r.businessName = domain;
    r.token = r.token ?? `${domain.replace(/\W+/g, '-')}-Fx0000000000000000000000`;
  }
  r.status = 'queued';
  r.error = null;
  return true;
}
