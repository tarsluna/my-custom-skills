import * as cheerio from 'cheerio';
import sharp from 'sharp';
import { cfg } from '../config.js';
import type { Llm } from '../lib/llm.js';
import { saveImageBuffer } from '../lib/files.js';
import { safeFetch } from '../lib/ssrf.js';
import { collapse, normalizeForMatch, UNTRUSTED_RULE, untrusted } from '../lib/text.js';
import { errMsg, log } from '../log.js';
import type { CrawledPage } from './crawl.js';

export type ProjectItem = { title: string; location: string | null; sourceUrl: string; imageFile: string; imagePath: string };

type Candidate = { id: number; title: string; sourceUrl: string; imageUrl: string; context: string };

function bestFromSrcset(srcset: string | undefined): string | null {
  if (!srcset) return null;
  const options = srcset
    .split(',')
    .map((part) => part.trim().split(/\s+/))
    .filter((p) => p[0])
    .map(([url, size]) => ({ url, weight: size ? parseFloat(size) : 1 }));
  options.sort((a, b) => b.weight - a.weight);
  return options[0]?.url ?? null;
}

/** Leurre des extensions de chargement différé (`blank.gif` en `src`, la vraie image dans un `data-*`). */
const PLACEHOLDER_IMAGE = /blank\.(gif|png|svg)|spacer\.|transparent\.(gif|png)|\b1x1\.(gif|png)|lazy[-_.]?(load|placeholder)|grey\.gif|pixel\.gif/i;
const IMAGE_VALUE = /\.(jpe?g|png|webp|avif)(\?|$)/i;
const FILE_LINK = /\.(jpe?g|png|webp|gif|avif|svg|pdf)(\?|$)/i;

function imageFrom($: cheerio.CheerioAPI, el: any): string | null {
  const $el = $(el);
  const attribs = (el.attribs ?? {}) as Record<string, string>;
  const lazy = Object.entries(attribs)
    .filter(([name, value]) => name.startsWith('data-') && /src|orig|lazy|image/i.test(name) && !/srcset/i.test(name) && IMAGE_VALUE.test(value))
    .map(([, value]) => value);
  const options = [bestFromSrcset($el.attr('data-srcset') ?? $el.attr('data-lazy-srcset') ?? $el.attr('srcset')), ...lazy, $el.attr('src')];
  return options.find((url) => url && !url.startsWith('data:') && !PLACEHOLDER_IMAGE.test(url)) ?? null;
}

function absolute(raw: string | null, base: string): string | null {
  if (!raw || raw.startsWith('data:')) return null;
  try {
    const url = new URL(raw, base);
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.toString() : null;
  } catch {
    return null;
  }
}

const NOT_PROJECT_IMAGE = /logo|icon|favicon|avatar|sprite|placeholder|pixel|spinner|loader/i;

export function collectCandidates(pages: CrawledPage[]): Candidate[] {
  const byUrl = new Map<string, Candidate>();
  let id = 0;
  const add = (sourceUrl: string, title: string, imageUrl: string | null, context: string, isDetail = false) => {
    if (!imageUrl || NOT_PROJECT_IMAGE.test(imageUrl) || PLACEHOLDER_IMAGE.test(imageUrl) || FILE_LINK.test(sourceUrl)) return;
    const key = sourceUrl.replace(/\/$/, '');
    const existing = byUrl.get(key);
    if (existing) {
      if (!existing.title && title) existing.title = title;
      // La page du projet connaît mieux son image que la vignette de la liste.
      if (isDetail) existing.imageUrl = imageUrl;
      return;
    }
    byUrl.set(key, { id: (id += 1), title: collapse(title).slice(0, 140), sourceUrl: key, imageUrl, context: collapse(context).slice(0, 400) });
  };

  for (const page of pages) {
    const $ = cheerio.load(page.html);
    if (page.category === 'detail' || (page.category === 'projects' && $('img').length <= 8)) {
      const h1 = collapse($('h1').first().text()) || page.title;
      const og = $('meta[property="og:image"]').attr('content') ?? null;
      const firstImg = $('main img, article img, img').toArray().find((el) => !NOT_PROJECT_IMAGE.test(imageFrom($, el) ?? ''));
      const image = absolute(og, page.url) ?? (firstImg ? absolute(imageFrom($, firstImg), page.url) : null);
      add(page.url, h1, image, `${page.description} ${page.text.slice(0, 300)}`, true);
    }
    if (page.category === 'projects' || page.category === 'home') {
      $('a[href]').each((_, a) => {
        const img = $(a).find('img').first();
        const href = absolute($(a).attr('href') ?? null, page.url);
        if (!img.length || !href) return;
        if (new URL(href).hostname.replace(/^www\./, '') !== new URL(page.url).hostname.replace(/^www\./, '')) return;
        const title = collapse($(a).text()) || collapse(img.attr('alt')) || collapse(img.attr('title'));
        add(href, title, absolute(imageFrom($, img[0]), page.url), `${title} ${$(a).parent().text().slice(0, 200)}`);
      });
    }
  }
  return [...byUrl.values()];
}

export const SYSTEM = `Tu repères, parmi des éléments extraits du site d’une entreprise, ceux qui sont de vraies réalisations publiées : un projet précis, avec un titre et une image.
${UNTRUSTED_RULE}
Écarte les articles de blog, pages de services, logos, membres de l'équipe, mentions, éléments de navigation, fiches produits.
Pour chaque vraie réalisation retenue, renvoie son identifiant, son titre propre, et son lieu seulement s'il figure dans les données.
Réponds en JSON : {"projects":[{"id":1,"title":"…","location":"…" ou null}]}. Maximum 12. Pas d'invention : un titre ou un lieu absent des données vaut null, et le titre doit reprendre les mots du site.`;

async function downloadProjectImage(auditId: string, imageUrl: string): Promise<{ fileName: string; path: string } | null> {
  try {
    const res = await safeFetch(imageUrl, { maxBytes: 15 * 1024 * 1024, timeoutMs: 20_000, headers: { accept: 'image/*' } });
    if (res.status >= 400) return null;
    const meta = await sharp(res.body, { failOn: 'none' }).metadata();
    const w = meta.width ?? 0;
    const h = meta.height ?? 0;
    if (Math.max(w, h) < 600 || Math.min(w, h) < 280) return null;
    const stats = await sharp(res.body, { failOn: 'none' }).stats();
    if (stats.entropy < 3.5) return null;
    return await saveImageBuffer(auditId, 'project', res.body, { maxSide: 1800 });
  } catch (e) {
    log.warn('image de projet ignorée', { url: imageUrl, error: errMsg(e) });
    return null;
  }
}

/** Réalisations publiées, avec image recopiée sur le volume et lien vers la source. */
export async function extractProjects(pages: CrawledPage[], auditId: string, llm: Llm): Promise<ProjectItem[]> {
  const candidates = collectCandidates(pages);
  if (!candidates.length) return [];
  const payload = candidates.slice(0, 40).map((c) => ({ id: c.id, titre: c.title, url: c.sourceUrl, contexte: c.context }));
  const out = await llm.json<{ projects?: Array<{ id?: number; title?: string | null; location?: string | null }> }>({
    system: SYSTEM,
    user: `Éléments extraits :\n${untrusted('site de l’entreprise', JSON.stringify(payload))}`,
  });

  const items: ProjectItem[] = [];
  for (const entry of out.projects ?? []) {
    if (items.length >= cfg().PROJECTS_MAX) break;
    const candidate = candidates.find((c) => c.id === entry.id);
    if (!candidate) continue;
    const contextNorm = normalizeForMatch(`${candidate.title} ${candidate.context} ${decodeURIComponent(candidate.sourceUrl).replace(/[-_/]/g, ' ')}`);
    const llmTitle = collapse(entry.title);
    const titleOk = llmTitle && normalizeForMatch(llmTitle).split(' ').every((word) => word.length < 3 || contextNorm.includes(word));
    const title = titleOk ? llmTitle : candidate.title;
    if (!title) continue;
    const location = collapse(entry.location);
    const locationOk = location && contextNorm.includes(normalizeForMatch(location));
    const saved = await downloadProjectImage(auditId, candidate.imageUrl);
    if (!saved) continue;
    items.push({ title, location: locationOk ? location : null, sourceUrl: candidate.sourceUrl, imageFile: saved.fileName, imagePath: saved.path });
  }
  return items;
}
