import { createHash } from 'node:crypto';
import { cfg } from '../config.js';
import { fill, niche } from '../niche.js';
import { query } from '../db/pool.js';
import { publicMediaUrl } from '../lib/files.js';
import type { SetterContent } from '../pipeline/setterContent.js';

/**
 * Option : affichée seulement si l'opérateur fournit COST_ESTIMATE_MIN et COST_ESTIMATE_MAX, tirés de ses campagnes réelles.
 * Le hachage de l'identifiant rend le chiffre stable : il ne bouge jamais d'un chargement à l'autre.
 */
export function estimatedCostEur(creativeId: string, range: { min?: number; max?: number } = { min: cfg().COST_ESTIMATE_MIN, max: cfg().COST_ESTIMATE_MAX }): number | null {
  const { min, max } = range;
  if (min === undefined || max === undefined || max < min) return null;
  return Math.round(min + (createHash('sha256').update(creativeId).digest().readUInt32BE(0) % (Math.round(max - min) + 1)));
}

const WORD = ['Zéro', 'Une', 'Deux', 'Trois', 'Quatre', 'Cinq', 'Six', 'Sept', 'Huit', 'Neuf', 'Dix'];

export function operatorView() {
  const n = niche();
  return { operator: n.operator, theme: n.theme, sections: n.page.sections };
}

/** Tous les textes de la page, remplis pour cette entreprise. Le front n'en contient aucun qui dépende du métier. */
function pageCopy(name: string, city: string | null, firstName: string | null, total: number) {
  const p = niche().page;
  const vars = { nom: name, ville: city ?? 'de chez vous', n: WORD[total] ?? total, prenom: firstName };
  const f = (t: string) => fill(t, vars);
  return {
    title: f(p.title),
    lockedSentence: p.lockedSentence,
    conceptNote: p.conceptNote,
    indexCta: p.indexCta,
    sections: p.sections,
    businessTitle: f(p.businessTitle),
    creativesTitle: f(p.creativesTitle),
    creativesLead: f(p.creativesLead).replace('autour de de chez vous', 'autour de chez vous'),
    projectsTitle: f(p.projectsTitle),
    projectsLead: f(p.projectsLead),
    assistantTitle: f(p.assistantTitle),
    assistantLead: f(p.assistantLead),
    assistantNotes: p.assistantNotes.map((x) => ({ tag: f(x.tag), text: f(x.text) })),
    nextTitle: f(p.nextTitle),
    closing: firstName ? f(p.closingWithName) : f(p.closing),
    teaser: p.teaser,
    costLabel: p.costLabel,
    costLabelShort: p.costLabelShort,
    costAverageLabel: p.costAverageLabel,
    footerLegal: p.footerLegal,
  };
}

type AuditDb = {
  id: string;
  token: string;
  status: string;
  domain: string | null;
  website_url: string | null;
  contact_first_name: string | null;
  meeting_at: Date | null;
  analysis: any | null;
  brand: any | null;
  competitors_meta: { radiusKm: number | null; widened: boolean; publicInsights: string[] } | null;
  setter: SetterContent | null;
};

type CreativeDb = { id: string; idx: number; concept: string; format: string; locked: boolean; status: string; headline: string | null; primary_text: string | null; bullets: string[]; display_file: string | null; blur_file: string | null };
type CompetitorDb = { page_name: string; city: string | null; distance_km: number | null; logo_file: string | null; active_days: number | null; ad_library_url: string; image_file: string | null; body: string; title: string | null; why: string };
type ProjectDb = { title: string; location: string | null; image_file: string; source_url: string };

export type AuditBundle = { audit: AuditDb; creatives: CreativeDb[]; competitors: CompetitorDb[]; projects: ProjectDb[] };

export type PublicAudit = {
  operator: ReturnType<typeof niche>['operator'];
  theme: ReturnType<typeof niche>['theme'];
  copy: ReturnType<typeof pageCopy>;
  token: string;
  status: 'processing' | 'ready' | 'failed';
  contact: { firstName: string | null };
  meetingAt: string | null;
  bookingUrl: string;
  business: {
    name: string;
    profession: string;
    professionLabel: string;
    city: string | null;
    region: string | null;
    domain: string;
    websiteUrl: string;
    logoUrl: string | null;
    logoIsFallback: boolean;
    palette: { primary: string; secondary: string; accent: string; background: string; text: string };
    specialties: string[];
    projectTypes: string[];
    summary: string;
  };
  competitors: { radiusKm: number | null; widened: boolean; insights: string[]; items: Array<{ pageName: string; city: string | null; distanceKm: number | null; logoUrl: string | null; activeDays: number | null; adLibraryUrl: string; imageUrl: string | null; body: string; title: string | null; why: string }> };
  creatives: Array<{ id: string; index: number; concept: string; format: '4:5' | '9:16' | '1:1'; locked: boolean; imageUrl: string; headline: string | null; primaryText: string | null; bullets: string[] | null; estimatedCostEur: number | null }>;
  projects: Array<{ title: string; location: string | null; imageUrl: string; sourceUrl: string }>;
  setter: { assistantName: string; firstProspectMessage: string; suggestedReplies: string[] };
};

const DEFAULT_PALETTE = { primary: '#100f0d', secondary: '#9a9386', accent: '#e9c48f', background: '#efe9dd', text: '#100f0d' };

export function publicStatus(status: string): PublicAudit['status'] {
  if (status === 'ready') return 'ready';
  if (status === 'failed' || status === 'needs_domain') return 'failed';
  return 'processing';
}

/**
 * Seule source de la réponse publique. Pour une créative verrouillée, seul le dérivé flouté et le concept sortent :
 * aucun titre, aucun texte, aucun nom de fichier d'origine.
 */
export function toPublicAudit(bundle: AuditBundle): PublicAudit {
  const { audit, creatives, competitors, projects } = bundle;
  const a = audit.analysis ?? {};
  const b = audit.brand ?? {};
  const token = audit.token;
  const media = (file: string | null | undefined) => (file ? publicMediaUrl(token, file) : null);

  const businessName = a.businessName ?? audit.domain ?? '';
  return {
    operator: niche().operator,
    theme: niche().theme,
    copy: pageCopy(businessName, a.city ?? null, audit.contact_first_name, creatives.length),
    token,
    status: publicStatus(audit.status),
    contact: { firstName: audit.contact_first_name },
    meetingAt: audit.meeting_at ? audit.meeting_at.toISOString() : null,
    bookingUrl: cfg().BOOKING_URL,
    business: {
      name: businessName,
      profession: a.profession ?? '',
      professionLabel: a.professionLabel ?? '',
      city: a.city ?? null,
      region: a.region ?? null,
      domain: audit.domain ?? '',
      websiteUrl: audit.website_url ?? (audit.domain ? `https://${audit.domain}` : ''),
      logoUrl: media(a.logoFile),
      logoIsFallback: Boolean(b.logoIsFallback),
      palette: b.palette ?? DEFAULT_PALETTE,
      specialties: a.specialties ?? [],
      projectTypes: a.projectTypes ?? [],
      summary: a.summary ?? '',
    },
    competitors: {
      radiusKm: audit.competitors_meta?.radiusKm ?? null,
      widened: Boolean(audit.competitors_meta?.widened),
      insights: audit.competitors_meta?.publicInsights ?? [],
      items: competitors.map((c) => ({
        pageName: c.page_name,
        city: c.city,
        distanceKm: c.distance_km,
        logoUrl: media(c.logo_file),
        activeDays: c.active_days,
        adLibraryUrl: c.ad_library_url,
        imageUrl: media(c.image_file),
        body: c.body,
        title: c.title,
        why: c.why,
      })),
    },
    creatives: creatives
      .filter((c) => c.status === 'ready' && (c.locked ? c.blur_file : c.display_file))
      .map((c) => ({
        id: c.id,
        index: c.idx,
        concept: c.concept,
        format: c.format as '4:5' | '9:16' | '1:1',
        locked: c.locked,
        imageUrl: media(c.locked ? c.blur_file : c.display_file)!,
        headline: c.locked ? null : c.headline,
        primaryText: c.locked ? null : c.primary_text,
        bullets: c.locked ? null : c.bullets,
        estimatedCostEur: estimatedCostEur(c.id),
      })),
    projects: projects.map((p) => ({ title: p.title, location: p.location, imageUrl: media(p.image_file)!, sourceUrl: p.source_url })),
    setter: audit.setter ?? { assistantName: '', firstProspectMessage: '', suggestedReplies: [] },
  };
}

export async function loadPublicBundle(token: string): Promise<AuditBundle | null> {
  const res = await query<AuditDb>('SELECT * FROM audits WHERE token=$1', [token]);
  const audit = res.rows[0];
  if (!audit) return null;
  const [creatives, competitors, projects] = await Promise.all([
    query<CreativeDb>('SELECT id, idx, concept, format, locked, status, headline, primary_text, bullets, display_file, blur_file FROM creatives WHERE audit_id=$1 ORDER BY idx', [audit.id]),
    query<CompetitorDb>('SELECT page_name, city, distance_km, logo_file, active_days, ad_library_url, image_file, body, title, why FROM competitors WHERE audit_id=$1 ORDER BY ordering', [audit.id]),
    query<ProjectDb>('SELECT title, location, image_file, source_url FROM projects WHERE audit_id=$1 ORDER BY ordering', [audit.id]),
  ]);
  return { audit, creatives: creatives.rows, competitors: competitors.rows, projects: projects.rows };
}
