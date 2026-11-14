import type { CSSProperties } from 'react';
import type { Palette } from './types';

/* L’entreprise prête une teinte à la page, le thème de l'opérateur reste le fond. */

type Rgb = [number, number, number];
const DARK_GROUND: Rgb = [15, 17, 21];
const LIGHT_GROUND: Rgb = [238, 240, 243];

export function isHex(c: unknown): c is string {
  return typeof c === 'string' && /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(c);
}

function toRgb(hex: string): Rgb {
  let h = hex.slice(1);
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}
const toHex = (c: Rgb) => '#' + c.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');

function lum([r, g, b]: Rgb) {
  const f = (v: number) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
function contrast(a: Rgb, b: Rgb) {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}
function saturation([r, g, b]: Rgb) {
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  return max === 0 ? 0 : (max - min) / max;
}

function legibleOn(color: Rgb, ground: Rgb, target: number): Rgb {
  const toward: Rgb = lum(ground) < 0.3 ? [255, 255, 255] : [0, 0, 0];
  let c = color;
  for (let t = 0; t <= 1 && contrast(c, ground) < target; t += 0.05) {
    c = color.map((v, i) => v + (toward[i] - v) * t) as Rgb;
  }
  return c;
}

/** La teinte de l’entreprise, rendue lisible sur fond sombre et sur fond clair. */
export function businessVars(p: Partial<Palette> | null | undefined): CSSProperties {
  const candidates = [p?.accent, p?.primary, p?.secondary].filter(isHex).map(toRgb);
  const pick = candidates.find((c) => saturation(c) > 0.18) ?? candidates[0] ?? ([154, 147, 134] as Rgb);
  return {
    ['--biz-d' as string]: toHex(legibleOn(pick, DARK_GROUND, 5)),
    ['--biz-l' as string]: toHex(legibleOn(pick, LIGHT_GROUND, 4.2)),
    ['--biz-plate' as string]: isHex(p?.background) ? p.background : '#EEF0F3',
  };
}

export type Swatch = { key: string; label: string; hex: string };
export function swatches(p: Partial<Palette> | null | undefined): Swatch[] {
  const rows: Array<[keyof Palette, string]> = [
    ['primary', 'Principale'],
    ['secondary', 'Secondaire'],
    ['accent', 'Accent'],
    ['background', 'Fond'],
    ['text', 'Texte'],
  ];
  const out: Swatch[] = [];
  for (const [key, label] of rows) {
    const hex = p?.[key];
    if (isHex(hex)) out.push({ key, label, hex: hex.toUpperCase() });
  }
  return out;
}
