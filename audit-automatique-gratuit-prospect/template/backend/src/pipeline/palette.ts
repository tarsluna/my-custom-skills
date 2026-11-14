import sharp from 'sharp';
import type { ComputedStyles } from './browser.js';

export type Palette = { primary: string; secondary: string; accent: string; background: string; text: string };

type Rgb = { r: number; g: number; b: number };

const hex2 = (n: number) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, '0');
const toHex = ({ r, g, b }: Rgb) => `#${hex2(r)}${hex2(g)}${hex2(b)}`;

function fromHex(hex: string): Rgb {
  return { r: parseInt(hex.slice(1, 3), 16), g: parseInt(hex.slice(3, 5), 16), b: parseInt(hex.slice(5, 7), 16) };
}

const NAMED: Record<string, string> = { white: '#ffffff', black: '#000000' };

/** Couleur CSS vers #rrggbb ; null si absente ou trop transparente. */
export function parseCssColor(input: string | null | undefined): string | null {
  if (!input) return null;
  const v = input.trim().toLowerCase();
  if (NAMED[v]) return NAMED[v];
  let m = v.match(/^#([0-9a-f]{3,4})$/);
  if (m) {
    const c = m[1];
    if (c.length === 4 && parseInt(c[3] + c[3], 16) < 128) return null;
    return `#${c[0]}${c[0]}${c[1]}${c[1]}${c[2]}${c[2]}`;
  }
  m = v.match(/^#([0-9a-f]{6})([0-9a-f]{2})?$/);
  if (m) return m[2] && parseInt(m[2], 16) < 128 ? null : `#${m[1]}`;
  m = v.match(/^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:[\s,/]+([\d.]+%?))?\s*\)$/);
  if (m) {
    const alpha = m[4] === undefined ? 1 : m[4].endsWith('%') ? parseFloat(m[4]) / 100 : parseFloat(m[4]);
    if (alpha < 0.5) return null;
    return toHex({ r: Number(m[1]), g: Number(m[2]), b: Number(m[3]) });
  }
  m = v.match(/^hsla?\(\s*([\d.]+)(?:deg)?[\s,]+([\d.]+)%[\s,]+([\d.]+)%(?:[\s,/]+([\d.]+%?))?\s*\)$/);
  if (m) {
    const alpha = m[4] === undefined ? 1 : m[4].endsWith('%') ? parseFloat(m[4]) / 100 : parseFloat(m[4]);
    if (alpha < 0.5) return null;
    const h = Number(m[1]) / 360;
    const s = Number(m[2]) / 100;
    const l = Number(m[3]) / 100;
    const hue = (p: number, q: number, t0: number) => {
      let t = t0;
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1 / 6) return p + (q - p) * 6 * t;
      if (t < 1 / 2) return q;
      if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
      return p;
    };
    if (s === 0) return toHex({ r: l * 255, g: l * 255, b: l * 255 });
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    return toHex({ r: hue(p, q, h + 1 / 3) * 255, g: hue(p, q, h) * 255, b: hue(p, q, h - 1 / 3) * 255 });
  }
  return null;
}

function hsl({ r, g, b }: Rgb) {
  const [rr, gg, bb] = [r / 255, g / 255, b / 255];
  const max = Math.max(rr, gg, bb);
  const min = Math.min(rr, gg, bb);
  const l = (max + min) / 2;
  const d = max - min;
  const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
  return { s, l };
}

const isChromatic = (hex: string) => {
  const { s, l } = hsl(fromHex(hex));
  return s > 0.22 && l > 0.12 && l < 0.8;
};
const lum = (hex: string) => {
  const c = fromHex(hex);
  const channel = (v: number) => {
    const x = v / 255;
    return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(c.r) + 0.7152 * channel(c.g) + 0.0722 * channel(c.b);
};
const contrast = (a: string, b: string) => {
  const [l1, l2] = [lum(a), lum(b)].sort((x, y) => y - x);
  return (l1 + 0.05) / (l2 + 0.05);
};
const distance = (a: string, b: string) => {
  const x = fromHex(a);
  const y = fromHex(b);
  return Math.sqrt((x.r - y.r) ** 2 + (x.g - y.g) ** 2 + (x.b - y.b) ** 2);
};

const THEME_PRESET = /--(wp--preset|wc|bs)-[\w-]*\s*:[^;}]*[;}]?/g;

export function colorsFromCss(css: string): Map<string, number> {
  const out = new Map<string, number>();
  const tokens = css.match(/#[0-9a-f]{3,8}\b|rgba?\([^)]+\)|hsla?\([^)]+\)/gi) ?? [];
  for (const token of tokens) {
    const hex = parseCssColor(token);
    if (hex) out.set(hex, (out.get(hex) ?? 0) + 1);
  }
  return out;
}

/** Couleurs dominantes d'une capture : réduction, regroupement grossier, part de pixels. */
export async function colorsFromScreenshot(image: Buffer): Promise<Array<{ hex: string; share: number }>> {
  const { data, info } = await sharp(image).resize(120, 120, { fit: 'inside' }).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const buckets = new Map<string, { r: number; g: number; b: number; n: number }>();
  const pixels = info.width * info.height;
  for (let i = 0; i < data.length; i += info.channels) {
    const key = `${data[i] >> 4}-${data[i + 1] >> 4}-${data[i + 2] >> 4}`;
    const b = buckets.get(key) ?? { r: 0, g: 0, b: 0, n: 0 };
    b.r += data[i];
    b.g += data[i + 1];
    b.b += data[i + 2];
    b.n += 1;
    buckets.set(key, b);
  }
  return [...buckets.values()]
    .sort((a, b) => b.n - a.n)
    .slice(0, 24)
    .map((b) => ({ hex: toHex({ r: b.r / b.n, g: b.g / b.n, b: b.b / b.n }), share: b.n / pixels }));
}

export type PaletteInputs = {
  computed: ComputedStyles | null;
  cssTexts: string[];
  capture: Array<{ hex: string; share: number }>;
};

/** Palette à partir de couleurs réellement observées (rendu, CSS, capture), jamais inventée. */
export function buildPalette({ computed, cssTexts, capture }: PaletteInputs): Palette {
  // Les préréglages de thème (WordPress, WooCommerce, Bootstrap) ne disent rien de la marque.
  const css = new Map<string, number>();
  for (const sheet of cssTexts) {
    for (const [hex, n] of colorsFromCss(sheet.replace(THEME_PRESET, ''))) css.set(hex, (css.get(hex) ?? 0) + n);
  }
  // Une couleur du CSS ne compte que si on la voit vraiment à l'écran ; sans capture, le CSS est tout ce qu'on a.
  const visible = (hex: string) => !capture.length || capture.some((c) => c.share >= 0.002 && distance(c.hex, hex) < 45);
  const read = (el: { color: string; backgroundColor: string } | null | undefined, key: 'color' | 'backgroundColor') => parseCssColor(el?.[key]);

  const background =
    read(computed?.body, 'backgroundColor') ?? read(computed?.header, 'backgroundColor') ?? [...capture].sort((a, b) => b.share - a.share)[0]?.hex ?? '#ffffff';

  const textCandidates = [read(computed?.p, 'color'), read(computed?.body, 'color'), read(computed?.h1, 'color')].filter((c): c is string => Boolean(c) && contrast(c!, background) >= 2);
  const cssDark = [...css.entries()].sort((a, b) => b[1] - a[1]).map(([h]) => h).find((h) => contrast(h, background) >= 4 && !isChromatic(h));
  const text = textCandidates[0] ?? cssDark ?? (lum(background) > 0.5 ? '#111111' : '#f5f5f5');

  const scores = new Map<string, number>();
  const vote = (hex: string | null | undefined, weight: number) => {
    if (!hex || !isChromatic(hex)) return;
    for (const [known, score] of scores) {
      if (distance(known, hex) < 28) {
        scores.set(known, score + weight);
        return;
      }
    }
    scores.set(hex, weight);
  };
  vote(read(computed?.button, 'backgroundColor'), 40);
  vote(read(computed?.a, 'color'), 30);
  vote(read(computed?.h1, 'color'), 24);
  vote(read(computed?.h2, 'color'), 18);
  vote(read(computed?.header, 'backgroundColor'), 20);
  vote(read(computed?.footer, 'backgroundColor'), 16);
  for (const [hex, n] of css) if (n >= 2 && visible(hex)) vote(hex, Math.min(n, 12));

  const chromatic = [...scores.entries()].sort((a, b) => b[1] - a[1]).map(([h]) => h);
  const primary = chromatic[0] ?? text;
  const accent = chromatic.find((h) => distance(h, primary) >= 60) ?? chromatic[1] ?? primary;

  const midNeutrals = [...capture]
    .sort((a, b) => b.share - a.share)
    .map((c) => c.hex)
    .filter((h) => distance(h, background) > 40 && distance(h, text) > 40);
  const secondary = chromatic.find((h) => h !== primary && h !== accent) ?? midNeutrals[0] ?? [...css.keys()].find((h) => distance(h, background) > 40 && distance(h, text) > 40) ?? text;

  return { primary, secondary, accent, background, text };
}

const GENERIC_FONTS = /^(sans-serif|serif|monospace|cursive|fantasy|system-ui|ui-sans-serif|ui-serif|ui-monospace|-apple-system|blinkmacsystemfont|inherit|initial|unset|helvetica neue|segoe ui|roboto|arial|helvetica|times new roman|times|georgia|verdana|tahoma|apple color emoji|segoe ui emoji|noto color emoji|segoe ui symbol)$/i;

function firstFamilies(fontFamily: string | null | undefined): string[] {
  if (!fontFamily) return [];
  return fontFamily.split(',').map((f) => f.trim().replace(/^["']|["']$/g, '')).filter(Boolean);
}

/** Polices réellement utilisées : styles calculés, @font-face, Google Fonts. */
export function extractFonts(computed: ComputedStyles | null, cssTexts: string[], html: string): string[] {
  const ordered: string[] = [];
  const add = (name: string) => {
    if (name && !ordered.some((f) => f.toLowerCase() === name.toLowerCase())) ordered.push(name);
  };
  for (const el of [computed?.h1, computed?.h2, computed?.body, computed?.p, computed?.a]) {
    for (const family of firstFamilies(el?.fontFamily).slice(0, 1)) if (!GENERIC_FONTS.test(family)) add(family);
  }
  for (const m of html.matchAll(/fonts\.googleapis\.com\/css2?\?family=([^"'&\s]+)/gi)) {
    add(decodeURIComponent(m[1]).split(':')[0].replace(/\+/g, ' '));
  }
  for (const css of cssTexts) {
    for (const m of css.matchAll(/@font-face\s*{[^}]*font-family\s*:\s*["']?([^;"'}]+)/gi)) add(m[1].trim());
  }
  const WEIGHT_SUFFIX = /[-\s]?(thin|hairline|extra-?light|ultra-?light|light|regular|book|roman|medium|semi-?bold|demi-?bold|extra-?bold|ultra-?bold|bold|black|heavy)?[-\s]?(italic|oblique)?$/i;
  const families = [...new Set(ordered.map((f) => f.replace(WEIGHT_SUFFIX, '').trim() || f))];
  const filtered = families.filter((f) => !GENERIC_FONTS.test(f) && !/icon|awesome|material|glyph|fontello|swiper|slick|woocommerce|dashicons|eicons|elementskit|star|tabler|remixicon/i.test(f));
  if (filtered.length) return filtered.slice(0, 4);
  const fallback = firstFamilies(computed?.body?.fontFamily)[0];
  return fallback ? [fallback] : [];
}
