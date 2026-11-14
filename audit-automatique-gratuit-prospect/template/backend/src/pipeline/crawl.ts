import * as cheerio from 'cheerio';
import { safeFetch } from '../lib/ssrf.js';
import { deburr } from '../lib/text.js';
import { cfg } from '../config.js';
import { errMsg, log } from '../log.js';
import { renderPage, withBrowser, type ComputedStyles, type RenderedPage } from './browser.js';
import { FatalAuditError } from './errors.js';

export type PageLink = { href: string; text: string; hasImage: boolean };

export type CrawledPage = {
  url: string;
  title: string;
  description: string;
  headings: string[];
  text: string;
  html: string;
  links: PageLink[];
  rendered: boolean;
  category: LinkCategory | 'home' | 'detail';
};

export type CrawlResult = {
  websiteUrl: string;
  host: string;
  pages: CrawledPage[];
  screenshot: Buffer | null;
  computed: ComputedStyles | null;
  cssTexts: string[];
  notes: string[];
};

export type LinkCategory = 'projects' | 'about' | 'contact' | 'services' | 'legal';

const CATEGORY_RULES: Array<[LinkCategory, RegExp, number]> = [
  ['projects', /projets?|projects?|realisations?|portfolio|portefolio|travaux|references?|galerie|gallery|works?\b/, 10],
  ['about', /a-?propos|about|agence|entreprise|societe|cabinet|atelier|studio|equipe|qui-sommes|philosophie|presentation|portrait/, 6],
  ['services', /services?|prestations?|expertises?|savoir-faire|approche|missions?|competences/, 4],
  ['contact', /contact|coordonnees|nous-trouver/, 5],
  ['legal', /mentions?-?legales?|legal/, 3],
];
const CATEGORY_QUOTA: Record<LinkCategory, number> = { projects: 2, about: 1, services: 1, contact: 1, legal: 1 };

const SKIP_EXT = /\.(pdf|jpe?g|png|gif|webp|svg|mp4|mov|zip|docx?|xlsx?|pptx?|ics)(\?|$)/i;
const SKIP_PATH = /\/(tag|tags|category|categorie|blog|actualites?|news|feed|wp-json|wp-admin|wp-login|panier|cart|checkout|compte|account|search|recherche|privacy|cgv|cookies?)(\/|$)/i;

function sameSite(a: string, b: string): boolean {
  const strip = (h: string) => h.toLowerCase().replace(/^www\./, '');
  return strip(a) === strip(b);
}

function parsePage(url: string, html: string, rendered: boolean, category: CrawledPage['category']): CrawledPage {
  const $ = cheerio.load(html);
  const base = new URL(url);
  const links: PageLink[] = [];
  const seen = new Set<string>();
  $('a[href]').each((_, el) => {
    const raw = ($(el).attr('href') ?? '').trim();
    if (!raw || raw.startsWith('#') || /^(mailto|tel|javascript):/i.test(raw)) return;
    let href: URL;
    try {
      href = new URL(raw, base);
    } catch {
      return;
    }
    if (href.protocol !== 'http:' && href.protocol !== 'https:') return;
    if (!sameSite(href.hostname, base.hostname)) return;
    href.hash = '';
    const clean = href.toString().replace(/\/$/, '');
    if (seen.has(clean) || clean === url.replace(/\/$/, '') || SKIP_EXT.test(href.pathname) || SKIP_PATH.test(href.pathname)) return;
    seen.add(clean);
    links.push({ href: clean, text: $(el).text().replace(/\s+/g, ' ').trim().slice(0, 120), hasImage: $(el).find('img').length > 0 });
  });
  const title = $('title').first().text().replace(/\s+/g, ' ').trim();
  const description = ($('meta[name="description"]').attr('content') ?? $('meta[property="og:description"]').attr('content') ?? '').trim();
  const headings = $('h1, h2, h3')
    .map((_, el) => $(el).text().replace(/\s+/g, ' ').trim())
    .get()
    .filter(Boolean)
    .slice(0, 40);
  $('script, style, noscript, svg, template').remove();
  const text = $('body').text().replace(/\s+/g, ' ').trim();
  return { url, title, description, headings, text, html, links, rendered, category };
}

async function fetchHtml(url: string): Promise<{ finalUrl: string; html: string } | null> {
  try {
    const res = await safeFetch(url, { maxBytes: 4 * 1024 * 1024, timeoutMs: 15_000, headers: { accept: 'text/html,application/xhtml+xml' } });
    if (res.status >= 400 || !/text\/html|application\/xhtml/.test(res.contentType)) return null;
    return { finalUrl: res.url, html: res.body.toString('utf8') };
  } catch (e) {
    log.warn('page non récupérée', { url, error: errMsg(e) });
    return null;
  }
}

function scoreLink(link: PageLink): { category: LinkCategory; score: number } | null {
  const hay = deburr(`${new URL(link.href).pathname} ${link.text}`).toLowerCase();
  if (/\/en\/|\/en$|\/de\/|\/es\/|\/it\//.test(hay)) return null;
  for (const [category, pattern, score] of CATEGORY_RULES) {
    if (pattern.test(hay)) return { category, score };
  }
  return null;
}

function selectInternalLinks(links: PageLink[]): Array<{ link: PageLink; category: LinkCategory }> {
  const scored = links
    .map((link) => ({ link, match: scoreLink(link) }))
    .filter((x): x is { link: PageLink; match: { category: LinkCategory; score: number } } => x.match !== null)
    .sort((a, b) => b.match.score - a.match.score);
  const quota: Record<string, number> = {};
  const out: Array<{ link: PageLink; category: LinkCategory }> = [];
  for (const { link, match } of scored) {
    quota[match.category] = (quota[match.category] ?? 0) + 1;
    if (quota[match.category] <= CATEGORY_QUOTA[match.category]) out.push({ link, category: match.category });
  }
  return out;
}

async function mapLimit<T, R>(items: T[], limit: number, fn: (item: T) => Promise<R>): Promise<R[]> {
  const out: R[] = new Array(items.length);
  let next = 0;
  await Promise.all(
    Array.from({ length: Math.min(limit, items.length) }, async () => {
      while (next < items.length) {
        const i = next;
        next += 1;
        out[i] = await fn(items[i]);
      }
    }),
  );
  return out;
}

async function collectCss(pages: CrawledPage[]): Promise<string[]> {
  const out: string[] = [];
  const urls = new Set<string>();
  for (const page of pages.slice(0, 3)) {
    const $ = cheerio.load(page.html);
    $('style').each((_, el) => {
      out.push($(el).text());
    });
    $('link[rel="stylesheet"]').each((_, el) => {
      const href = $(el).attr('href');
      if (href && urls.size < 8) {
        try {
          urls.add(new URL(href, page.url).toString());
        } catch {
          /* lien invalide */
        }
      }
    });
  }
  let total = 0;
  for (const url of urls) {
    if (total > 2 * 1024 * 1024) break;
    try {
      const res = await safeFetch(url, { maxBytes: 1024 * 1024, timeoutMs: 10_000 });
      if (res.status < 400) {
        const css = res.body.toString('utf8');
        out.push(css);
        total += css.length;
      }
    } catch {
      /* feuille de style ignorée */
    }
  }
  return out;
}

const MIN_HOME_TEXT = 200;
const MIN_PAGE_TEXT = 120;
const MAX_RENDERS = 5;

function candidates(domain: string): string[] {
  return [`https://${domain}/`, `https://www.${domain}/`, `http://${domain}/`, `http://www.${domain}/`];
}

/** Page d'accueil + pages internes utiles, requête simple d'abord, Chromium si le rendu est vide et pour la capture. */
export async function crawlSite(domain: string): Promise<CrawlResult> {
  const maxInternal = cfg().CRAWL_MAX_INTERNAL_PAGES;
  const notes: string[] = [];

  let fetched: { finalUrl: string; html: string } | null = null;
  for (const url of candidates(domain)) {
    fetched = await fetchHtml(url);
    if (fetched) break;
  }

  const result = await withBrowser(async (context) => {
    let renders = 0;
    const renderedHomeUrl = fetched?.finalUrl ?? `https://${domain}/`;
    const homeRender = await renderPage(context, renderedHomeUrl, { screenshot: true });
    renders += homeRender ? 1 : 0;
    if (!homeRender) notes.push('capture Chromium impossible');

    let home: CrawledPage;
    const staticHome = fetched ? parsePage(fetched.finalUrl, fetched.html, false, 'home') : null;
    if (staticHome && staticHome.text.length >= MIN_HOME_TEXT) home = staticHome;
    else if (homeRender) home = parsePage(homeRender.url, homeRender.html, true, 'home');
    else if (staticHome) home = staticHome;
    else throw new FatalAuditError(`Le site ${domain} est injoignable.`);

    const pages: CrawledPage[] = [home];
    const fetchedUrls = new Set([home.url.replace(/\/$/, '')]);

    const fetchPage = async (link: PageLink, category: CrawledPage['category']): Promise<CrawledPage | null> => {
      const res = await fetchHtml(link.href);
      let page = res ? parsePage(res.finalUrl, res.html, false, category) : null;
      if ((!page || page.text.length < MIN_PAGE_TEXT) && renders < MAX_RENDERS) {
        renders += 1;
        const r: RenderedPage | null = await renderPage(context, link.href, { screenshot: false, timeoutMs: 18_000 });
        if (r) page = parsePage(r.url, r.html, true, category);
      }
      return page;
    };

    const selected = selectInternalLinks(home.links).slice(0, maxInternal);
    const firstBatch = await mapLimit(selected, 3, ({ link, category }) => fetchPage(link, category));
    for (const page of firstBatch) {
      if (page && !fetchedUrls.has(page.url.replace(/\/$/, ''))) {
        pages.push(page);
        fetchedUrls.add(page.url.replace(/\/$/, ''));
      }
    }

    // Pages de projets individuelles, liées depuis les pages de réalisations.
    const remaining = maxInternal - (pages.length - 1);
    if (remaining > 0) {
      const detailLinks: PageLink[] = [];
      for (const page of pages.filter((p) => p.category === 'projects')) {
        const prefix = new URL(page.url).pathname.replace(/\/$/, '');
        for (const link of page.links) {
          if (fetchedUrls.has(link.href)) continue;
          const path_ = new URL(link.href).pathname;
          if ((prefix && path_.startsWith(`${prefix}/`)) || link.hasImage) detailLinks.push(link);
        }
      }
      detailLinks.sort((a, b) => Number(b.hasImage) - Number(a.hasImage));
      const detailBatch = await mapLimit(
        detailLinks.filter((l, i, arr) => arr.findIndex((x) => x.href === l.href) === i).slice(0, remaining),
        3,
        (link) => fetchPage(link, 'detail'),
      );
      for (const page of detailBatch) {
        if (page && !fetchedUrls.has(page.url.replace(/\/$/, ''))) {
          pages.push(page);
          fetchedUrls.add(page.url.replace(/\/$/, ''));
        }
      }
    }

    return { pages, screenshot: homeRender?.screenshot ?? null, computed: homeRender?.computed ?? null, renderedHtml: homeRender?.html ?? null };
  });

  if (result) {
    // Le DOM rendu sert aussi à la détection du logo et du CSS.
    if (result.renderedHtml) result.pages[0].html = result.renderedHtml;
    const cssTexts = await collectCss(result.pages);
    return { websiteUrl: result.pages[0].url, host: new URL(result.pages[0].url).hostname, pages: result.pages, screenshot: result.screenshot, computed: result.computed, cssTexts, notes };
  }

  // Chromium absent : requête simple seule.
  if (!fetched) throw new FatalAuditError(`Le site ${domain} est injoignable.`);
  notes.push('analyse sans Chromium');
  const home = parsePage(fetched.finalUrl, fetched.html, false, 'home');
  const pages: CrawledPage[] = [home];
  const selected = selectInternalLinks(home.links).slice(0, maxInternal);
  const firstBatch = await mapLimit(selected, 3, async ({ link, category }) => {
    const res = await fetchHtml(link.href);
    return res ? parsePage(res.finalUrl, res.html, false, category) : null;
  });
  for (const page of firstBatch) if (page) pages.push(page);
  const cssTexts = await collectCss(pages);
  return { websiteUrl: home.url, host: new URL(home.url).hostname, pages, screenshot: null, computed: null, cssTexts, notes };
}
