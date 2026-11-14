import { niche } from '../niche.js';
import { cfg } from '../config.js';
import { recordCost } from './costs.js';

export type AdSnapshot = {
  body?: { text?: string } | null;
  title?: string | null;
  images?: any[];
  cards?: any[];
  videos?: any[];
  displayFormat?: string | null;
  linkUrl?: string | null;
  ctaText?: string | null;
  pageProfilePictureUrl?: string | null;
  pageProfileUri?: string | null;
  pageCategories?: string[] | null;
};

export type RawAd = {
  pageName: string;
  pageId: string;
  adArchiveId: string;
  startDate?: number | string | null;
  endDate?: number | string | null;
  totalActiveTime?: number | null;
  snapshot: AdSnapshot;
};

const ACTOR = 'https://api.apify.com/v2/acts/apify~facebook-ads-scraper/run-sync-get-dataset-items?timeout=180&memory=1024';

/** Recherche Ads Library par mots-clés. Les réponses d'erreur et les éléments incomplets sont écartés. */
export async function searchAdsLibrary(query: string, limit: number, auditId: string | null = null): Promise<RawAd[]> {
  const token = cfg().APIFY_TOKEN;
  if (!token) throw new Error('APIFY_TOKEN absent');
  const adUrl = `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=${niche().sector.country}&media_type=all&q=${encodeURIComponent(query)}&search_type=keyword_unordered`;
  let lastError: unknown;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const res = await fetch(ACTOR, {
        method: 'POST',
        headers: { authorization: `Bearer ${token}`, 'content-type': 'application/json' },
        body: JSON.stringify({ startUrls: [{ url: adUrl }], resultsLimit: limit }),
        signal: AbortSignal.timeout(200_000),
      });
      if (!res.ok) throw new Error(`Apify ${res.status} : ${(await res.text().catch(() => '')).slice(0, 200)}`);
      const data = (await res.json()) as any[];
      const ads = data.filter((item): item is RawAd => Boolean(item?.pageId && item?.adArchiveId && item?.snapshot && item?.pageName));
      void recordCost({ auditId, provider: 'apify', detail: query, quantity: ads.length });
      return ads;
    } catch (e) {
      lastError = e;
      await new Promise((r) => setTimeout(r, 3000));
    }
  }
  throw lastError instanceof Error ? lastError : new Error(String(lastError));
}
