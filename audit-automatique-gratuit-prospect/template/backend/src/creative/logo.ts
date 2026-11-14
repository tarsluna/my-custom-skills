/**
 * Recomposition du vrai logo. Le modèle d'image ne dessine jamais le logo :
 * il laisse une zone calme, puis `applyLogo` y pose le fichier réel, à une
 * position constante, avec gestion du contraste.
 */
import { promises as fs } from 'node:fs';
import { createRequire } from 'node:module';
import opentype from 'opentype.js';
import sharp from 'sharp';
import type { OverlayOptions } from 'sharp';
import { contrast, hexToRgb, luminance } from './color.js';
import type { Rgb } from './color.js';
import { LOGO_LAYOUT, OUTPUT_SIZE } from './concepts.js';
import { safePalette } from './prompts.js';
import type { BrandProfile, CreativeFormat } from './types.js';

export type PreparedLogo = {
  /** Pixels RGBA recadrés au plus près du logo. */
  rgba: Buffer;
  width: number;
  height: number;
  mono: boolean;
  ink: Rgb;
  source: 'file' | 'typographic';
  issues: string[];
};

export type LogoMode = 'direct' | 'recolored' | 'plate';

const MIN_LOGO_SIDE = 96;
const MAX_LOGO_SIDE = 2400;

async function fontBuffer(): Promise<ArrayBuffer> {
  const require = createRequire(import.meta.url);
  const file = require.resolve('@fontsource/jost/files/jost-latin-400-normal.woff');
  const buf = await fs.readFile(file);
  return buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength) as ArrayBuffer;
}

let fontPromise: Promise<opentype.Font> | null = null;
function loadFont(): Promise<opentype.Font> {
  if (!fontPromise) fontPromise = fontBuffer().then((b) => opentype.parse(b));
  return fontPromise;
}

function splitName(text: string): string[] {
  if (text.length <= 22) return [text];
  const words = text.split(/\s+/);
  let best = [text];
  let bestDiff = Infinity;
  for (let i = 1; i < words.length; i += 1) {
    const a = words.slice(0, i).join(' ');
    const b = words.slice(i).join(' ');
    const diff = Math.abs(a.length - b.length);
    if (diff < bestDiff) {
      bestDiff = diff;
      best = [a, b];
    }
  }
  return best;
}

function layoutLine(font: opentype.Font, text: string, size: number, tracking: number): { d: string; width: number } {
  const glyphs = font.stringToGlyphs(text);
  const scale = size / font.unitsPerEm;
  let x = 0;
  const parts: string[] = [];
  glyphs.forEach((g, i) => {
    parts.push(g.getPath(x, 0, size).toPathData(2));
    const next = glyphs[i + 1];
    x += (g.advanceWidth ?? 0) * scale + tracking;
    if (next) x += font.getKerningValue(g, next) * scale;
  });
  return { d: parts.join(' '), width: Math.max(0, x - tracking) };
}

/** Logotype de repli : nom exact, en capitales espacées (vectoriel, sans police système). */
export async function renderLogotype(name: string): Promise<Buffer> {
  const font = await loadFont();
  const size = 180;
  const tracking = size * 0.13;
  const lines = splitName(name.trim().toLocaleUpperCase('fr-FR'));
  const metrics = lines.map((l) => layoutLine(font, l, size, tracking));
  const width = Math.ceil(Math.max(...metrics.map((m) => m.width)));
  const lineHeight = size * 1.32;
  const ascent = size * 0.82;
  const height = Math.ceil(ascent + lineHeight * (lines.length - 1) + size * 0.12);
  const body = metrics
    .map((m, i) => `<path transform="translate(0 ${(ascent + i * lineHeight).toFixed(1)})" d="${m.d}" fill="#111111"/>`)
    .join('');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${body}</svg>`;
  return sharp(Buffer.from(svg)).png().toBuffer();
}

type RawImage = { data: Buffer; width: number; height: number };

async function loadRaw(input: string | Buffer): Promise<RawImage> {
  let img = sharp(input, { failOn: 'none' });
  const meta = await img.metadata();
  if (meta.format === 'svg') {
    const density = Math.min(2400, Math.max(72, (72 * 1400) / Math.max(meta.width ?? 300, 1)));
    img = sharp(input, { density, failOn: 'none' });
  }
  const { data, info } = await img
    .rotate()
    .resize({ width: MAX_LOGO_SIDE, height: MAX_LOGO_SIDE, fit: 'inside', withoutEnlargement: true })
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });
  return { data, width: info.width, height: info.height };
}

function dist(a: Rgb, b: Rgb): number {
  return Math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2);
}

function borderStats(img: RawImage): { mean: Rgb; uniform: number } {
  const { data, width, height } = img;
  const samples: Rgb[] = [];
  const push = (x: number, y: number) => {
    const i = (y * width + x) * 4;
    samples.push([data[i]!, data[i + 1]!, data[i + 2]!]);
  };
  for (let x = 0; x < width; x += 1) {
    push(x, 0);
    push(x, height - 1);
  }
  for (let y = 0; y < height; y += 1) {
    push(0, y);
    push(width - 1, y);
  }
  const mean: Rgb = [0, 1, 2].map((c) => samples.reduce((a, s) => a + s[c]!, 0) / samples.length) as Rgb;
  const near = samples.filter((s) => dist(s, mean) < 32).length / samples.length;
  return { mean, uniform: near };
}

/** Détoure un logo sur fond uni, calcule sa boîte englobante et sa couleur d'encre. */
function processPixels(img: RawImage): Omit<PreparedLogo, 'source' | 'issues'> | null {
  const { data, width, height } = img;
  const total = width * height;
  let transparent = 0;
  for (let i = 3; i < data.length; i += 4) if (data[i]! < 40) transparent += 1;

  if (transparent / total < 0.01) {
    const border = borderStats(img);
    if (border.uniform > 0.92) {
      for (let i = 0; i < data.length; i += 4) {
        const px: Rgb = [data[i]!, data[i + 1]!, data[i + 2]!];
        data[i + 3] = Math.max(0, Math.min(255, Math.round(((dist(px, border.mean) - 24) * 255) / 80)));
      }
    }
  }

  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      if (data[(y * width + x) * 4 + 3]! > 24) {
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }
  if (maxX < 0) return null;

  const w = maxX - minX + 1;
  const h = maxY - minY + 1;
  const out = Buffer.alloc(w * h * 4);
  let sum: Rgb = [0, 0, 0];
  let n = 0;
  const inks: Rgb[] = [];
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      const si = ((y + minY) * width + x + minX) * 4;
      const di = (y * w + x) * 4;
      out[di] = data[si]!;
      out[di + 1] = data[si + 1]!;
      out[di + 2] = data[si + 2]!;
      out[di + 3] = data[si + 3]!;
      if (data[si + 3]! > 200) {
        sum = [sum[0] + data[si]!, sum[1] + data[si + 1]!, sum[2] + data[si + 2]!];
        n += 1;
        if (n % 3 === 0) inks.push([data[si]!, data[si + 1]!, data[si + 2]!]);
      }
    }
  }
  const ink: Rgb = n ? [sum[0] / n, sum[1] / n, sum[2] / n] : [20, 20, 20];
  const spread = inks.length
    ? Math.sqrt(inks.reduce((a, p) => a + dist(p, ink) ** 2, 0) / inks.length)
    : 0;
  return { rgba: out, width: w, height: h, mono: spread < 42, ink };
}

async function prepareFrom(input: string | Buffer, source: PreparedLogo['source'], issues: string[]): Promise<PreparedLogo | null> {
  const raw = await loadRaw(input);
  if (Math.max(raw.width, raw.height) < MIN_LOGO_SIDE) return null;
  const processed = processPixels(raw);
  if (!processed) return null;
  return { ...processed, source, issues };
}

/** Prépare le logo de l’entreprise ; sans fichier exploitable, compose le logotype typographique. */
export async function prepareLogo(b: BrandProfile): Promise<PreparedLogo> {
  const issues: string[] = [];
  if (b.logoPath) {
    try {
      await fs.access(b.logoPath);
      const prepared = await prepareFrom(b.logoPath, b.logoIsFallback ? 'typographic' : 'file', issues);
      if (prepared) return prepared;
      issues.push('Logo trop petit ou vide : logotype typographique utilisé.');
    } catch {
      issues.push('Fichier logo illisible : logotype typographique utilisé.');
    }
  }
  const typo = await renderLogotype(b.businessName);
  const prepared = await prepareFrom(typo, 'typographic', issues);
  if (!prepared) throw new Error('Logotype typographique impossible à composer.');
  return prepared;
}

type Rect = { left: number; top: number; width: number; height: number };

function logoRect(format: CreativeFormat, logo: PreparedLogo): Rect {
  const { width: W, height: H } = OUTPUT_SIZE[format];
  const box = LOGO_LAYOUT[format].logo;
  const maxW = box.maxW * W;
  const maxH = box.maxH * H;
  const area = maxW * maxH * 0.62;
  const r = logo.width / logo.height;
  let w = Math.sqrt(area * r);
  let h = w / r;
  if (w > maxW) {
    w = maxW;
    h = w / r;
  }
  if (h > maxH) {
    h = maxH;
    w = h * r;
  }
  return { left: Math.round(box.x * W), top: Math.round(box.y * H), width: Math.round(w), height: Math.round(h) };
}

async function regionStats(base: Buffer, r: Rect): Promise<{ mean: Rgb; busy: number; outliers: number }> {
  const { data, info } = await sharp(base)
    .extract(r)
    .blur(0.8)
    .removeAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });
  const px = info.width * info.height;
  let sr = 0;
  let sg = 0;
  let sb = 0;
  let lumSum = 0;
  let lumSq = 0;
  for (let i = 0; i < data.length; i += info.channels) {
    const r0 = data[i]!;
    const g0 = data[i + 1]!;
    const b0 = data[i + 2]!;
    sr += r0;
    sg += g0;
    sb += b0;
    const y = 0.2126 * r0 + 0.7152 * g0 + 0.0722 * b0;
    lumSum += y;
    lumSq += y * y;
  }
  const meanY = lumSum / px;
  // Part de pixels franchement écartés du fond : capte un trait fin qu'un écart-type global ne voit pas.
  let farPixels = 0;
  for (let i = 0; i < data.length; i += info.channels) {
    const y = 0.2126 * data[i]! + 0.7152 * data[i + 1]! + 0.0722 * data[i + 2]!;
    if (Math.abs(y - meanY) > 38) farPixels += 1;
  }
  return {
    mean: [sr / px, sg / px, sb / px],
    busy: Math.sqrt(Math.max(0, lumSq / px - meanY * meanY)),
    outliers: farPixels / px,
  };
}

async function renderLogo(logo: PreparedLogo, w: number, h: number, tint?: Rgb): Promise<Buffer> {
  let raw = logo.rgba;
  if (tint) {
    raw = Buffer.from(logo.rgba);
    for (let i = 0; i < raw.length; i += 4) {
      raw[i] = tint[0];
      raw[i + 1] = tint[1];
      raw[i + 2] = tint[2];
    }
  }
  return sharp(raw, { raw: { width: logo.width, height: logo.height, channels: 4 } })
    .resize(w, h, { kernel: 'lanczos3' })
    .png()
    .toBuffer();
}

function plateSvg(w: number, h: number, fill: string, opacity: number, radius: number): Buffer {
  return Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect x="0" y="0" width="${w}" height="${h}" rx="${radius}" ry="${radius}" fill="${fill}" fill-opacity="${opacity}"/></svg>`,
  );
}

const MIN_CONTRAST = 3.5;
const BUSY_DIRECT = 26;
const MAX_OUTLIERS = 0.006;

/**
 * Pose le logo à sa place constante. Décision :
 * 1. tel quel si le contraste suffit sur un fond calme ;
 * 2. logo monochrome : version claire ou sombre si le fond reste calme ;
 * 3. sinon, plaque discrète de la couleur la plus proche du fond qui garde le logo lisible.
 */
export async function applyLogo(
  base: Buffer,
  format: CreativeFormat,
  logo: PreparedLogo,
  b: BrandProfile,
): Promise<{ image: Buffer; mode: LogoMode }> {
  const { width: W, height: H } = OUTPUT_SIZE[format];
  const rect = logoRect(format, logo);
  const pad = Math.max(14, Math.round(rect.height * 0.35));
  const probe: Rect = {
    left: Math.max(0, rect.left - pad),
    top: Math.max(0, rect.top - pad),
    width: Math.min(W - Math.max(0, rect.left - pad), rect.width + pad * 2),
    height: Math.min(H - Math.max(0, rect.top - pad), rect.height + pad * 2),
  };
  const stats = await regionStats(base, probe);
  const palette = safePalette(b);

  const overlays: OverlayOptions[] = [];
  let mode: LogoMode;

  const calm = stats.outliers <= MAX_OUTLIERS;

  if (contrast(logo.ink, stats.mean) >= MIN_CONTRAST && stats.busy <= BUSY_DIRECT && calm) {
    mode = 'direct';
    overlays.push({ input: await renderLogo(logo, rect.width, rect.height), left: rect.left, top: rect.top });
  } else {
    const tintChoices: Rgb[] = [[255, 255, 255], [16, 16, 16], hexToRgb(palette.background), hexToRgb(palette.text)];
    const bestTint = logo.mono
      ? tintChoices.reduce((best, c) => (contrast(c, stats.mean) > contrast(best, stats.mean) ? c : best), tintChoices[0]!)
      : null;

    if (bestTint && contrast(bestTint, stats.mean) >= MIN_CONTRAST && stats.busy <= BUSY_DIRECT + 14 && calm) {
      mode = 'recolored';
      overlays.push({ input: await renderLogo(logo, rect.width, rect.height, bestTint), left: rect.left, top: rect.top });
    } else {
      mode = 'plate';
      const plateFills = [palette.background, '#FFFFFF', palette.text, '#111111'];
      const bgLum = luminance(stats.mean);
      const inkFor = (fillHex: string): Rgb | null => {
        const fill = hexToRgb(fillHex);
        if (contrast(logo.ink, fill) >= 4.5) return logo.ink;
        if (logo.mono) return contrast([255, 255, 255], fill) >= contrast([16, 16, 16], fill) ? [255, 255, 255] : [16, 16, 16];
        return null;
      };
      const usable = plateFills.filter((f) => inkFor(f) !== null);
      const fill = (usable.length ? usable : ['#FFFFFF']).reduce((best, f) => {
        return Math.abs(luminance(hexToRgb(f)) - bgLum) < Math.abs(luminance(hexToRgb(best)) - bgLum) ? f : best;
      });
      const ink = inkFor(fill) ?? logo.ink;
      const padX = Math.round(Math.max(18, rect.height * 0.55));
      const padY = Math.round(Math.max(12, rect.height * 0.38));
      const plateW = rect.width + padX * 2;
      const plateH = rect.height + padY * 2;
      overlays.push({
        input: plateSvg(plateW, plateH, fill, 0.93, Math.round(Math.min(plateH * 0.22, 18))),
        left: Math.max(8, rect.left - padX),
        top: Math.max(8, rect.top - padY),
      });
      overlays.push({
        input: await renderLogo(logo, rect.width, rect.height, ink === logo.ink ? undefined : ink),
        left: rect.left,
        top: rect.top,
      });
    }
  }

  const image = await sharp(base).composite(overlays).png().toBuffer();
  return { image, mode };
}
