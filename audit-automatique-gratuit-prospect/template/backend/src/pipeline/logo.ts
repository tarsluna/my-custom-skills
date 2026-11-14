import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import * as cheerio from 'cheerio';
import opentype from 'opentype.js';
import sharp from 'sharp';
import { safeFetch } from '../lib/ssrf.js';
import { errMsg, log } from '../log.js';

export type LogoCandidate = { kind: 'url'; url: string; score: number; source: string } | { kind: 'svg'; svg: string; score: number; source: string };

const LOGO_HINT = /logo|brand|site-title|site-branding/i;

function pushUrl(list: LogoCandidate[], raw: string | undefined, base: URL, score: number, source: string) {
  if (!raw) return;
  try {
    const url = new URL(raw.trim().split(/\s+/)[0], base).toString();
    if (!/^https?:/i.test(url)) return;
    if (list.some((c) => c.kind === 'url' && c.url === url)) return;
    list.push({ kind: 'url', url, score, source });
  } catch {
    /* URL invalide */
  }
}

function jsonLdLogos(value: unknown, out: string[]): void {
  if (Array.isArray(value)) {
    value.forEach((v) => jsonLdLogos(v, out));
    return;
  }
  if (!value || typeof value !== 'object') return;
  const obj = value as Record<string, unknown>;
  for (const [key, inner] of Object.entries(obj)) {
    if (key.toLowerCase() === 'logo') {
      if (typeof inner === 'string') out.push(inner);
      else if (inner && typeof inner === 'object' && typeof (inner as any).url === 'string') out.push((inner as any).url);
    }
    if (inner && typeof inner === 'object') jsonLdLogos(inner, out);
  }
}

/** Candidats classés : en-tête, JSON-LD, SVG inline, apple-touch-icon, favicon. */
export function findLogoCandidates(html: string, pageUrl: string): LogoCandidate[] {
  const $ = cheerio.load(html);
  const base = new URL(pageUrl);
  const list: LogoCandidate[] = [];

  const imgScore = (el: any) => {
    const $el = $(el);
    const attrs = `${$el.attr('class') ?? ''} ${$el.attr('id') ?? ''} ${$el.attr('alt') ?? ''} ${$el.attr('src') ?? ''} ${$el.parent().attr('class') ?? ''} ${$el.parent().attr('id') ?? ''}`;
    let score = 0;
    if (LOGO_HINT.test(attrs)) score += 6;
    if ($el.closest('header, nav, [class*="header"], [id*="header"]').length) score += 3;
    const anchor = $el.closest('a');
    if (anchor.length && /^(\/|https?:\/\/[^/]+\/?)$/.test(anchor.attr('href') ?? '')) score += 3;
    return score;
  };

  $('img').each((_, el) => {
    const score = imgScore(el);
    if (score < 3) return;
    const $el = $(el);
    const src = $el.attr('src') ?? $el.attr('data-src') ?? $el.attr('data-lazy-src');
    if (src?.startsWith('data:')) return;
    pushUrl(list, src, base, score + (/\.svg(\?|$)/i.test(src ?? '') ? 2 : 0), 'img');
  });

  $('script[type="application/ld+json"]').each((_, el) => {
    try {
      const found: string[] = [];
      jsonLdLogos(JSON.parse($(el).text()), found);
      for (const url of found) pushUrl(list, url, base, 8, 'json-ld');
    } catch {
      /* JSON-LD invalide */
    }
  });

  $('header svg, nav svg, [class*="logo"] svg, [id*="logo"] svg, a[href="/"] svg').each((_, el) => {
    const $el = $(el);
    if ($el.closest('button').length) return;
    const svg = $.html(el);
    if (svg.length < 200) return;
    let score = 5;
    if (LOGO_HINT.test(`${$el.attr('class') ?? ''} ${$el.parent().attr('class') ?? ''} ${$el.closest('a').attr('class') ?? ''}`)) score += 3;
    list.push({ kind: 'svg', svg, score, source: 'svg-inline' });
  });

  pushUrl(list, $('meta[property="og:logo"]').attr('content'), base, 6, 'og:logo');
  $('link[rel="apple-touch-icon"], link[rel="apple-touch-icon-precomposed"]').each((_, el) => pushUrl(list, $(el).attr('href'), base, 3, 'apple-touch-icon'));
  $('link[rel="icon"], link[rel="shortcut icon"]').each((_, el) => {
    const href = $(el).attr('href') ?? '';
    if (/\.ico(\?|$)/i.test(href)) return;
    pushUrl(list, href, base, 1, 'icon');
  });

  return list.sort((a, b) => b.score - a.score).slice(0, 8);
}

/** Retire de l'arbre SVG ce qui peut référencer l'extérieur ou exécuter du code. */
export function sanitizeSvg(svg: string): string | null {
  if (svg.length > 2 * 1024 * 1024 || !/<svg[\s>]/i.test(svg)) return null;
  const out = svg
    .replace(/<\?xml[^>]*>/gi, '')
    .replace(/<!DOCTYPE[^>[]*(\[[^\]]*\])?[^>]*>/gi, '')
    .replace(/<!ENTITY[^>]*>/gi, '')
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<foreignObject[\s\S]*?<\/foreignObject>/gi, '')
    .replace(/\son\w+\s*=\s*("[^"]*"|'[^']*')/gi, '')
    .replace(/\s(?:xlink:)?href\s*=\s*("(?!#|data:image)[^"]*"|'(?!#|data:image)[^']*')/gi, '');
  return /<svg[\s>]/i.test(out) ? out : null;
}

async function pngFromSvg(svgText: string): Promise<Buffer | null> {
  const safe = sanitizeSvg(svgText);
  if (!safe) return null;
  // Sans dimensions explicites, librsvg peut rendre très petit : on impose une densité élevée.
  const svg = safe.replace(/currentColor/gi, '#111111');
  const buf = Buffer.from(svg);
  const base = await sharp(buf, { density: 72 }).metadata();
  const longest = Math.max(base.width ?? 0, base.height ?? 0) || 300;
  const density = Math.min(1200, Math.round((72 * 1400) / longest));
  return sharp(buf, { density }).resize({ width: 1600, height: 1600, fit: 'inside', withoutEnlargement: true }).png().toBuffer();
}

function looksLikePhoto(entropy: number, width: number, opaque: boolean): boolean {
  return opaque && entropy > 7.0 && width > 700;
}

/** Vrai si l'image ne contient en réalité rien de visible. */
async function isBlank(png: Buffer): Promise<boolean> {
  const stats = await sharp(png).ensureAlpha().stats();
  const alpha = stats.channels[3];
  if (alpha.max === 0) return true;
  if (alpha.max > 0 && alpha.stdev > 2) return false;
  return stats.channels.slice(0, 3).every((c) => c.stdev < 2);
}

export async function normalizeLogoBuffer(buffer: Buffer, contentType: string): Promise<Buffer | null> {
  const head = buffer.subarray(0, 300).toString('utf8').trimStart();
  const isSvg = /svg/.test(contentType) || head.startsWith('<svg') || (head.startsWith('<?xml') && buffer.includes('<svg'));
  if (isSvg) {
    const png = await pngFromSvg(buffer.toString('utf8'));
    if (!png || (await isBlank(png))) return null;
    return trimTransparent(png);
  }
  const image = sharp(buffer, { failOn: 'error' });
  const meta = await image.metadata();
  const longest = Math.max(meta.width ?? 0, meta.height ?? 0);
  if (longest < 120) return null;
  const stats = await image.stats();
  if (looksLikePhoto(stats.entropy, meta.width ?? 0, stats.isOpaque)) return null;
  const png = await sharp(buffer).rotate().resize({ width: 1600, height: 1600, fit: 'inside', withoutEnlargement: true }).png().toBuffer();
  if (await isBlank(png)) return null;
  return trimTransparent(png);
}

async function trimTransparent(png: Buffer): Promise<Buffer> {
  try {
    return await sharp(png).trim({ threshold: 5 }).png().toBuffer();
  } catch {
    return png;
  }
}

export type ResolvedLogo = { png: Buffer; isFallback: boolean; source: string };

/** Premier candidat convertible en PNG exploitable, sinon logotype typographique marqué `logoIsFallback`. */
export async function resolveLogo(candidates: LogoCandidate[], businessName: string, color: string): Promise<ResolvedLogo> {
  for (const candidate of candidates) {
    try {
      let png: Buffer | null;
      if (candidate.kind === 'svg') {
        png = await normalizeLogoBuffer(Buffer.from(candidate.svg), 'image/svg+xml');
      } else {
        const res = await safeFetch(candidate.url, { maxBytes: 6 * 1024 * 1024, timeoutMs: 15_000 });
        if (res.status >= 400) continue;
        png = await normalizeLogoBuffer(res.body, res.contentType);
      }
      if (png) return { png, isFallback: false, source: candidate.source };
    } catch (e) {
      log.warn('logo candidat rejeté', { source: candidate.source, error: errMsg(e) });
    }
  }
  return { png: await typographicLogo(businessName, color), isFallback: true, source: 'typographie' };
}

const FONT_PATH = fileURLToPath(new URL('../../assets/fonts/Jost-400.woff', import.meta.url));
let fontCache: opentype.Font | null = null;

async function font(): Promise<opentype.Font> {
  if (!fontCache) {
    const data = await readFile(FONT_PATH);
    fontCache = opentype.parse(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength));
  }
  return fontCache;
}

/** Logotype discret en capitales espacées, sur fond transparent, à partir du nom de l’entreprise. */
export async function typographicLogo(businessName: string, color: string): Promise<Buffer> {
  const f = await font();
  const text = businessName.toLocaleUpperCase('fr-FR').replace(/\s+/g, ' ').trim().slice(0, 42);
  const fontSize = 180;
  const tracking = fontSize * 0.16;
  const glyphsFor = (t: string) => f.stringToGlyphs(t);
  const missing = glyphsFor(text).some((g) => g.index === 0 && g.name !== 'space');
  const display = missing ? text.normalize('NFD').replace(/\p{Diacritic}/gu, '') : text;

  let cursor = 0;
  const parts: string[] = [];
  for (const glyph of glyphsFor(display)) {
    const path = glyph.getPath(cursor, fontSize * 1.1, fontSize);
    parts.push(path.toPathData(2));
    cursor += ((glyph.advanceWidth ?? fontSize * 0.5) * fontSize) / f.unitsPerEm + tracking;
  }
  const width = Math.ceil(cursor - tracking + fontSize * 0.2);
  const height = Math.ceil(fontSize * 1.5);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><path d="${parts.join('')}" fill="${color}"/></svg>`;
  const raster = await sharp(Buffer.from(svg)).resize({ width: Math.min(width, 1600), withoutEnlargement: true }).png().toBuffer();
  return trimTransparent(raster);
}
