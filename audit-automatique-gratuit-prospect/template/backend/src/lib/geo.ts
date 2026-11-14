import { errMsg, log } from '../log.js';

export type GeoPoint = { lat: number; lon: number; city: string; postcode: string | null; department: string | null; region: string | null };

const cache = new Map<string, GeoPoint | null>();

/** Géocodage d'une commune par la Base Adresse Nationale (sans clé). */
export async function geocodeCity(q: string | null | undefined): Promise<GeoPoint | null> {
  const term = (q ?? '').trim();
  if (term.length < 2) return null;
  if (cache.has(term)) return cache.get(term) ?? null;
  const url = new URL('https://api-adresse.data.gouv.fr/search/');
  url.searchParams.set('q', term);
  url.searchParams.set('type', 'municipality');
  url.searchParams.set('limit', '1');
  let data: { features?: any[] };
  try {
    data = await lookupWithRetry(url);
  } catch (e) {
    // Une panne ne se met pas en cache : la prochaine tentative repart de zéro.
    log.warn('géocodage en échec', { error: errMsg(e) });
    return null;
  }
  try {
    const feature = data.features?.[0];
    const [lon, lat] = feature?.geometry?.coordinates ?? [];
    const score = Number(feature?.properties?.score ?? 0);
    if (!feature || typeof lat !== 'number' || score < 0.4) {
      cache.set(term, null);
      return null;
    }
    const context = String(feature.properties?.context ?? '').split(',').map((s: string) => s.trim());
    const point: GeoPoint = {
      lat,
      lon,
      city: String(feature.properties?.city ?? feature.properties?.label ?? term),
      postcode: feature.properties?.postcode ?? null,
      department: context[1] ?? null,
      region: context[2] ?? null,
    };
    cache.set(term, point);
    return point;
  } catch (e) {
    log.warn('géocodage en échec', { error: errMsg(e) });
    return null;
  }
}

/** Distance à vol d'oiseau en kilomètres. */
export function haversineKm(a: { lat: number; lon: number }, b: { lat: number; lon: number }): number {
  const R = 6371;
  const rad = (d: number) => (d * Math.PI) / 180;
  const dLat = rad(b.lat - a.lat);
  const dLon = rad(b.lon - a.lon);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

async function lookupWithRetry(url: URL): Promise<{ features?: any[] }> {
  let last: unknown;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(12_000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return (await res.json()) as { features?: any[] };
    } catch (e) {
      last = e;
    }
  }
  throw last instanceof Error ? last : new Error(String(last));
}

export function resetGeoCache() {
  cache.clear();
}
