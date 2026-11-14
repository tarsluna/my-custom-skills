import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest';
import type { RawAd } from '../src/lib/apify.js';
import type { Llm } from '../src/lib/llm.js';
import type { SiteAnalysis } from '../src/pipeline/extract.js';

vi.mock('../src/lib/geo.js', async (importActual) => {
  const actual = await importActual<typeof import('../src/lib/geo.js')>();
  const POINTS: Record<string, { lat: number; lon: number }> = { Lyon: { lat: 45.76, lon: 4.84 }, Grenoble: { lat: 45.19, lon: 5.72 }, Marseille: { lat: 43.3, lon: 5.37 }, Paris: { lat: 48.85, lon: 2.35 } };
  return { ...actual, geocodeCity: async (q: string) => (POINTS[q] ? { ...POINTS[q], city: q, postcode: null, department: null, region: null } : null) };
});

const { setupTestEnv, teardownTestEnv } = await import('./helpers.js');
const { findCompetitors } = await import('../src/pipeline/competitors.js');

const analysis: SiteAnalysis = {
  businessName: 'Studio Test',
  profession: 'renovation',
  professionLabel: 'entreprise de rénovation',
  city: 'Lyon',
  department: 'Rhône',
  region: 'Auvergne-Rhône-Alpes',
  geo: { lat: 45.76, lon: 4.84 },
  specialties: ['Appartements'],
  projectTypes: ['Rénovation complète'],
  tone: 'sobre',
  summary: 'Un studio.',
  leader: null,
  facts: [],
};

const ad = (pageId: string, pageName: string, text: string): RawAd => ({
  pageId,
  pageName,
  adArchiveId: `ar-${pageId}`,
  startDate: Math.round(Date.now() / 1000) - 20 * 86_400,
  snapshot: { body: { text }, images: [], cards: [], videos: [], pageCategories: [] },
});

function fakeLlm(decide: (pageId: string, text: string) => { keep: boolean; city?: string | null; why?: string }): Llm {
  return {
    async text() {
      return '';
    },
    async json<T>(a: { system: string; user: string }): Promise<T> {
      if (a.system.includes('tries des annonces')) {
        const payload = JSON.parse(a.user.split('source="ads library">\n')[1].split('\n</donnees')[0]) as Array<{ pageId: string; texte: string }>;
        return { pages: payload.map((p) => ({ pageId: p.pageId, ...decide(p.pageId, p.texte) })) } as T;
      }
      return { hooks: ['Accroche'], angles: ['Angle'], styleNotes: ['Style'], saturated: ['Vu'], publicInsights: ['Un constat utile.'] } as T;
    },
  };
}

beforeAll(async () => {
  await setupTestEnv({ ADS_MAX_QUERIES: '6', ADS_MIN_COMPETITORS: '2' });
});
afterAll(teardownTestEnv);

describe('findCompetitors', () => {
  it('écarte écoles et bruit, garde les concurrents, géolocalise et classe par distance', async () => {
    const ads = [
      ad('school', 'École Exemple', 'Devenez artisan : formation diplômante, portes ouvertes en janvier.'),
      ad('realty', 'Agence immobilière du Centre', 'Trouvez votre appartement à Lyon.'),
      ad('near', 'Atelier Rive Gauche', 'Rénovation à Lyon, nous transformons vos appartements.'),
      ad('far', 'Maison Sud', 'Conception et rénovation haut de gamme à Marseille.'),
      ad('reject', 'Blog Déco', 'Dix idées déco pour votre salon cet hiver.'),
    ];
    const llm = fakeLlm((pageId) => {
      if (pageId === 'near') return { keep: true, city: 'Lyon', why: 'Même métier, appartements à Lyon.' };
      if (pageId === 'far') return { keep: true, city: 'Marseille', why: 'Rénovation haut de gamme.' };
      return { keep: false };
    });
    const result = await findCompetitors(analysis, '00000000-0000-0000-0000-000000000000', llm, { search: async () => ads });
    expect(result.items.map((i) => i.pageId)).toEqual(['near', 'far']);
    expect(result.items[0].city).toBe('Lyon');
    expect(result.items[0].distanceKm).toBe(0);
    expect(result.items[1].distanceKm).toBeGreaterThan(250);
    expect(result.items[0].adLibraryUrl).toBe('https://www.facebook.com/ads/library/?id=ar-near');
    expect(result.items[0].activeDays).toBe(20);
    expect(result.publicInsights).toEqual(['Un constat utile.']);
  });

  it('élargit le rayon quand la zone ne suffit pas, et le déclare', async () => {
    const ads = [ad('a', 'Atelier A', 'Rénovation à Lyon pour vos appartements.'), ad('b', 'Atelier B', 'Conception intérieure à Grenoble, projets soignés.'), ad('c', 'Atelier C', 'Projets intérieurs à Marseille.')];
    const llm = fakeLlm((pageId, text) => ({ keep: true, city: /Lyon/.test(text) ? 'Lyon' : /Grenoble/.test(text) ? 'Grenoble' : 'Marseille', why: 'Même métier.' }));
    const result = await findCompetitors(analysis, '00000000-0000-0000-0000-000000000000', llm, { search: async () => ads });
    // Lyon + Grenoble (≈ 90 km) atteignent le minimum dès 100 km : Marseille n'est pas retenue.
    expect(result.radiusKm).toBe(100);
    expect(result.widened).toBe(false);
    expect(result.items.map((i) => i.pageId).sort()).toEqual(['a', 'b']);
  });

  it('ne garde pas une ville qui n’apparaît pas dans l’annonce', async () => {
    const ads = [ad('x', 'Atelier X', 'Conception intérieure sur mesure, partout en France.'), ad('y', 'Atelier Y', 'Rénovation à Lyon.')];
    const llm = fakeLlm((pageId) => (pageId === 'x' ? { keep: true, city: 'Paris', why: 'Conception intérieure.' } : { keep: true, city: 'Lyon', why: 'Même métier.' }));
    const result = await findCompetitors(analysis, '00000000-0000-0000-0000-000000000000', llm, { search: async () => ads });
    const x = result.items.find((i) => i.pageId === 'x')!;
    expect(x.city).toBeNull();
    expect(x.distanceKm).toBeNull();
    expect(result.radiusKm).toBeNull();
  });

  it('une panne totale de la recherche est une erreur, pas une liste vide', async () => {
    await expect(findCompetitors(analysis, '00000000-0000-0000-0000-000000000000', fakeLlm(() => ({ keep: false })), { search: async () => { throw new Error('apify en panne'); } })).rejects.toThrow(/aucune recherche/);
  });
});
