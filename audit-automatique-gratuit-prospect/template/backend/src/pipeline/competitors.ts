import { cfg } from '../config.js';
import { searchAdsLibrary, type RawAd } from '../lib/apify.js';
import { saveImageBuffer } from '../lib/files.js';
import { geocodeCity, haversineKm } from '../lib/geo.js';
import type { Llm } from '../lib/llm.js';
import { safeFetch } from '../lib/ssrf.js';
import { collapse, hasBannedTerm, hasForbiddenAngle, normalizeForMatch, publicSafe, UNTRUSTED_RULE, untrusted } from '../lib/text.js';
import { errMsg, log } from '../log.js';
import type { SiteAnalysis } from './extract.js';
import { niche } from '../niche.js';

export type CompetitorInsights = { hooks: string[]; angles: string[]; styleNotes: string[]; saturated: string[] };

export type StoredCompetitor = {
  pageId: string;
  pageName: string;
  adArchiveId: string;
  adLibraryUrl: string;
  city: string | null;
  distanceKm: number | null;
  activeDays: number | null;
  title: string | null;
  body: string;
  why: string;
  logoFile: string | null;
  imageFile: string | null;
};

export type CompetitorResult = {
  radiusKm: number | null;
  widened: boolean;
  items: StoredCompetitor[];
  publicInsights: string[];
  insights: CompetitorInsights;
};

export const RADIUS_TIERS = [100, 200, 400] as const;

export type QueryRound = { radius: number | null; queries: string[] };

/** Plan de recherche : zone d'abord, puis élargissement. `null` = pays entier. */
export function planAdQueries(a: Pick<SiteAnalysis, 'professionLabel' | 'specialties' | 'projectTypes' | 'city' | 'department' | 'region'>): QueryRound[] {
  const metier = a.professionLabel.split(' et ')[0];
  const specialty = a.specialties.find((s) => normalizeForMatch(s).length >= 4) ?? a.projectTypes[0] ?? null;
  const rounds: QueryRound[] = [];
  const firstRound = [a.city && `${metier} ${a.city}`, a.city && specialty && `${specialty} ${a.city}`, a.department && `${metier} ${a.department}`].filter(Boolean) as string[];
  if (firstRound.length) rounds.push({ radius: 100, queries: firstRound });
  if (a.region) rounds.push({ radius: 200, queries: [`${metier} ${a.region}`] });
  if (specialty && a.region) rounds.push({ radius: 400, queries: [`${specialty} ${a.region}`] });
  else if (a.region) rounds.push({ radius: 400, queries: [] });
  rounds.push({ radius: null, queries: [metier, ...(specialty ? [`${specialty} ${metier}`] : [])] });
  return rounds;
}

/** Écarts évidents avant le LLM (audit.config.json). */
const wordsRe = (words: string[]) => (words.length ? new RegExp(`(?<![\\p{L}])(${words.join('|')})(?![\\p{L}])`, 'iu') : null);

function isObviousNonCompetitor(ad: RawAd): boolean {
  const body = ad.snapshot.body?.text ?? '';
  const name = `${ad.pageName} ${(ad.snapshot.pageCategories ?? []).join(' ')}`;
  const { excludedNameWords, excludedBodyWords } = niche().competitors;
  return Boolean(wordsRe(excludedNameWords)?.test(name) || wordsRe(excludedBodyWords)?.test(body));
}

function adText(ad: RawAd): string {
  const raw = ad.snapshot.body?.text ?? ad.snapshot.cards?.[0]?.body ?? '';
  const text = collapse(typeof raw === 'string' ? raw : '');
  return text.includes('{{') ? '' : text;
}

function adImageUrl(s: RawAd['snapshot']): string | null {
  const pick = (o: any): string | null => o?.originalImageUrl ?? o?.original_image_url ?? o?.resizedImageUrl ?? o?.resized_image_url ?? o?.videoPreviewImageUrl ?? o?.video_preview_image_url ?? null;
  for (const list of [s.images, s.cards, s.videos]) {
    for (const item of Array.isArray(list) ? list : []) {
      const url = pick(item);
      if (url) return url;
    }
  }
  return null;
}

/** startDate en secondes epoch ou en date ISO ; totalActiveTime en secondes si présent. */
export function activeDaysOf(ad: Pick<RawAd, 'startDate' | 'totalActiveTime'>, now: number = Date.now()): number | null {
  if (typeof ad.totalActiveTime === 'number' && ad.totalActiveTime > 0) return Math.max(1, Math.round(ad.totalActiveTime / 86_400));
  const raw = ad.startDate;
  if (raw === null || raw === undefined || raw === '') return null;
  const ms = typeof raw === 'number' ? (raw > 1e12 ? raw : raw * 1000) : Date.parse(raw);
  if (!Number.isFinite(ms)) return null;
  return Math.max(1, Math.round((now - ms) / 86_400_000));
}

function pageRepresentative(ads: RawAd[]): RawAd {
  return [...ads].sort((a, b) => {
    const aImage = adImageUrl(a.snapshot) ? 1 : 0;
    const bImage = adImageUrl(b.snapshot) ? 1 : 0;
    if (aImage !== bImage) return bImage - aImage;
    return (activeDaysOf(b) ?? 0) - (activeDaysOf(a) ?? 0);
  })[0];
}

type FilterDecision = { pageId?: string; keep?: boolean; city?: string | null; why?: string };

function filterSystem(): string {
  const n = niche();
  return `Tu tries des annonces Meta pour constituer la liste des vrais concurrents d'${n.business.un} (${n.sector.description}).
${UNTRUSTED_RULE}

Garde une page uniquement si c'est ${n.competitors.keep}.
Écarte strictement : ${n.competitors.exclude}.
En cas de doute, écarte.

Réponds en JSON : {"pages":[{"pageId":"…","keep":true|false,"city":"ville du concurrent si elle figure dans l'annonce, sinon null","why":"si gardée : une phrase courte et factuelle, en français, disant ce qui rapproche cette annonce de l'activité analysée, avec les accents, sans point d'exclamation ni emoji, sans jargon marketing"}]}.
La ville doit apparaître dans les données de l'annonce ; ne la devine jamais.`;
}

async function filterPages(pages: RawAd[], analysis: SiteAnalysis, llm: Llm): Promise<Map<string, FilterDecision>> {
  if (!pages.length) return new Map();
  const payload = pages.map((ad) => ({
    pageId: ad.pageId,
    page: ad.pageName,
    categories: ad.snapshot.pageCategories ?? [],
    titre: ad.snapshot.title ?? null,
    texte: adText(ad).slice(0, 700),
    lien: ad.snapshot.linkUrl ?? null,
  }));
  const user = `Activité analysée : ${analysis.businessName}, ${analysis.professionLabel}${analysis.city ? `, ${analysis.city}` : ''}.
Spécialités : ${analysis.specialties.join(', ') || 'non précisées'}. Types de projets : ${analysis.projectTypes.join(', ') || 'non précisés'}.

Annonces à trier :
${untrusted('ads library', JSON.stringify(payload), 40_000)}`;
  const result = await llm.json<{ pages?: FilterDecision[] }>({ system: filterSystem(), user });
  const out = new Map<string, FilterDecision>();
  for (const decision of result.pages ?? []) {
    if (decision.pageId) out.set(String(decision.pageId), decision);
  }
  return out;
}

type Candidate = { ad: RawAd; decision: FilterDecision; city: string | null; distanceKm: number | null };

/** Le rayon réellement atteint : le plus petit palier contenant assez d'annonces retenues. */
export function selectRadius<T extends { distanceKm: number | null }>(items: T[], minCount: number, hasOrigin: boolean): { radiusKm: number | null; widened: boolean; items: T[] } {
  if (hasOrigin) {
    for (const tier of RADIUS_TIERS) {
      const within = items.filter((i) => i.distanceKm !== null && i.distanceKm <= tier);
      if (within.length >= minCount) return { radiusKm: tier, widened: tier > RADIUS_TIERS[0], items: within };
    }
  }
  return { radiusKm: null, widened: true, items };
}

function sortCandidates(list: Candidate[]): Candidate[] {
  return [...list].sort((a, b) => {
    const da = a.distanceKm ?? Number.POSITIVE_INFINITY;
    const db = b.distanceKm ?? Number.POSITIVE_INFINITY;
    if (da !== db) return da - db;
    return (activeDaysOf(b.ad) ?? 0) - (activeDaysOf(a.ad) ?? 0);
  });
}

async function downloadAdImage(url: string | null | undefined, auditId: string, kind: 'competitor_image' | 'competitor_logo'): Promise<string | null> {
  if (!url) return null;
  try {
    const res = await safeFetch(url, { maxBytes: 12 * 1024 * 1024, timeoutMs: 20_000, headers: { accept: 'image/*' } });
    if (res.status >= 400) return null;
    const saved = await saveImageBuffer(auditId, kind, res.body, { maxSide: kind === 'competitor_logo' ? 240 : 1400 });
    return saved?.fileName ?? null;
  } catch (e) {
    log.warn('image concurrente ignorée', { kind, error: errMsg(e) });
    return null;
  }
}

const INSIGHTS_SYSTEM = `À partir d'annonces Meta de concurrents, tu dégages ce qui marche dans le secteur pour alimenter de nouvelles créatives.
${UNTRUSTED_RULE}
Réponds en JSON :
{
 "hooks": ["accroches ou tournures qui reviennent, reformulées, 6 max"],
 "angles": ["angles de communication employés, 6 max"],
 "styleNotes": ["remarques sur le style visuel et rédactionnel, 5 max"],
 "saturated": ["ce qui est déjà trop vu et qu'il faut éviter, 5 max"],
 "publicInsights": ["3 à 5 constats courts écrits pour le dirigeant : une idée par phrase, factuelle, vouvoiement si besoin"]
}
Écris en français correct, avec tous les accents et les apostrophes. Vocabulaire interdit partout : ${niche().vocabulary.banned.join(', ')}. Aucun emoji. N'invente aucun chiffre.`;

const EMPTY_INSIGHTS: CompetitorInsights = { hooks: [], angles: [], styleNotes: [], saturated: [] };

function cleanList(list: unknown, max: number): string[] {
  if (!Array.isArray(list)) return [];
  return list
    .filter((v): v is string => typeof v === 'string')
    .map((v) => collapse(v))
    .filter((v) => v && !hasBannedTerm(v) && !hasForbiddenAngle(v))
    .slice(0, max);
}

async function buildInsights(chosen: Candidate[], analysis: SiteAnalysis, llm: Llm): Promise<{ insights: CompetitorInsights; publicInsights: string[] }> {
  if (!chosen.length) return { insights: EMPTY_INSIGHTS, publicInsights: [] };
  const payload = chosen.map((c) => ({ page: c.ad.pageName, ville: c.city, joursActifs: activeDaysOf(c.ad), titre: c.ad.snapshot.title ?? null, texte: adText(c.ad).slice(0, 900) }));
  const raw = await llm.json<Record<string, unknown>>({
    system: INSIGHTS_SYSTEM,
    user: `Activité : ${analysis.professionLabel}${analysis.city ? `, ${analysis.city}` : ''}.\nAnnonces concurrentes retenues :\n${untrusted('ads library', JSON.stringify(payload), 30_000)}`,
  });
  return {
    insights: {
      hooks: cleanList(raw.hooks, 6),
      angles: cleanList(raw.angles, 6),
      styleNotes: cleanList(raw.styleNotes, 5),
      saturated: cleanList(raw.saturated, 5),
    },
    publicInsights: cleanList(raw.publicInsights, 5).map((s) => publicSafe(s) ?? '').filter(Boolean),
  };
}

export type FindCompetitorsDeps = {
  search: (query: string, limit: number) => Promise<RawAd[]>;
};

/** Recherche, filtre, géolocalise, élargit le rayon et recopie les images des annonces retenues. */
export async function findCompetitors(analysis: SiteAnalysis, auditId: string, llm: Llm, deps?: FindCompetitorsDeps): Promise<CompetitorResult> {
  const search = deps?.search ?? ((q: string, limit: number) => searchAdsLibrary(q, limit, auditId));
  const rounds = planAdQueries(analysis);
  const c = cfg();
  // Le géocodage de l'analyse a pu échouer ponctuellement : on retente avant de renoncer au rayon.
  const origin = analysis.geo ?? (await geocodeCity(analysis.city));
  const hasOrigin = Boolean(origin);
  const seenPages = new Set<string>();
  const accepted: Candidate[] = [];
  let queriesUsed = 0;
  let queriesFailed = 0;

  for (const round of rounds) {
    const room = c.ADS_MAX_QUERIES - queriesUsed;
    if (room <= 0) break;
    const queries = round.queries.slice(0, room);
    queriesUsed += queries.length;
    if (queries.length) {
      const results = await Promise.all(queries.map((q) => search(q, c.ADS_RESULTS_LIMIT).catch((e) => {
        log.warn('recherche Ads Library en échec', { query: q, error: errMsg(e) });
        queriesFailed += 1;
        return [] as RawAd[];
      })));
      const byPage = new Map<string, RawAd[]>();
      for (const ad of results.flat()) {
        if (seenPages.has(ad.pageId)) continue;
        byPage.set(ad.pageId, [...(byPage.get(ad.pageId) ?? []), ad]);
      }
      for (const pageId of byPage.keys()) seenPages.add(pageId);

      const candidates = [...byPage.values()]
        .map(pageRepresentative)
        .filter((ad) => !isObviousNonCompetitor(ad) && adText(ad).length >= 20);
      for (let i = 0; i < candidates.length; i += 30) {
        const batch = candidates.slice(i, i + 30);
        const decisions = await filterPages(batch, analysis, llm);
        for (const ad of batch) {
          const decision = decisions.get(ad.pageId);
          if (!decision?.keep) continue;
          const adHaystack = normalizeForMatch(`${ad.pageName} ${adText(ad)} ${ad.snapshot.title ?? ''} ${ad.snapshot.linkUrl ?? ''}`);
          const declaredCity = collapse(decision.city) || null;
          const city = declaredCity && adHaystack.includes(normalizeForMatch(declaredCity)) ? declaredCity : null;
          const point = city ? await geocodeCity(city) : null;
          const distanceKm = point && origin ? Math.round(haversineKm(origin, point)) : null;
          accepted.push({ ad, decision, city: point?.city ?? city, distanceKm });
        }
      }
    }
    const pick = selectRadius(accepted, c.ADS_MIN_COMPETITORS, hasOrigin);
    if (round.radius !== null && pick.radiusKm !== null && pick.radiusKm <= round.radius) break;
    if (round.radius === null && accepted.length >= c.ADS_MIN_COMPETITORS) break;
  }

  if (queriesUsed > 0 && queriesFailed === queriesUsed) throw new Error('Bibliothèque publicitaire indisponible : aucune recherche n’a abouti.');

  const final = selectRadius(accepted, c.ADS_MIN_COMPETITORS, hasOrigin);
  const chosen = sortCandidates(final.items).slice(0, c.ADS_MAX_COMPETITORS);

  const items: StoredCompetitor[] = [];
  for (const candidate of chosen) {
    const { ad, decision, city, distanceKm } = candidate;
    const [imageFile, logoFile] = await Promise.all([
      downloadAdImage(adImageUrl(ad.snapshot), auditId, 'competitor_image'),
      downloadAdImage(ad.snapshot.pageProfilePictureUrl, auditId, 'competitor_logo'),
    ]);
    const why = publicSafe(decision.why) ?? `Annonce d'un ${analysis.professionLabel.split(' et ')[0]} active sur Meta.`;
    items.push({
      pageId: ad.pageId,
      pageName: ad.pageName,
      adArchiveId: ad.adArchiveId,
      adLibraryUrl: `https://www.facebook.com/ads/library/?id=${ad.adArchiveId}`,
      city,
      distanceKm,
      activeDays: activeDaysOf(ad),
      title: collapse(ad.snapshot.title) || null,
      body: adText(ad),
      why,
      imageFile,
      logoFile,
    });
  }

  const { insights, publicInsights } = await buildInsights(chosen, analysis, llm);
  return { radiusKm: final.radiusKm, widened: final.widened, items, publicInsights, insights };
}
