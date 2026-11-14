import { niche } from '../niche.js';
import { GENERATION_ASPECT, LOGO_LAYOUT, cropMargin } from './concepts.js';
import type { Concept } from './concepts.js';
import { contrast, hexToRgb, isHex, luminance, rgbToHex } from './color.js';
import type { BrandProfile, CopyDraft, CreativeFormat } from './types.js';

export function safePalette(b: BrandProfile) {
  const p = b.palette;
  return {
    primary: isHex(p.primary) ? p.primary : '#1f1f1f',
    secondary: isHex(p.secondary) ? p.secondary : '#8a8a8a',
    accent: isHex(p.accent) ? p.accent : '#b08d57',
    background: isHex(p.background) ? p.background : '#f4efe6',
    text: isHex(p.text) ? p.text : '#1a1a1a',
  };
}

function darkest(hexes: string[]): string {
  return [...hexes].sort((a, b) => luminance(hexToRgb(a)) - luminance(hexToRgb(b)))[0]!;
}
function lightest(hexes: string[]): string {
  return [...hexes].sort((a, b) => luminance(hexToRgb(b)) - luminance(hexToRgb(a)))[0]!;
}

function labelOn(fill: string): string {
  const candidates = ['#ffffff', '#141414'];
  const best = candidates.sort((a, b) => contrast(hexToRgb(b), hexToRgb(fill)) - contrast(hexToRgb(a), hexToRgb(fill)));
  return best[0]!;
}

function dataString(s: string, max = 300): string {
  return s
    // eslint-disable-next-line no-control-regex
    .replace(/[\u0000-\u001f\u007f<>`]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}

function pct(v: number): string {
  return `${Math.round(v * 100)}%`;
}

/** Convertit une fraction de hauteur de l'image finale en fraction du canevas généré. */
function toCanvasY(format: CreativeFormat, v: number): number {
  const m = cropMargin(format);
  return m + v * (1 - 2 * m);
}

function canvasLine(format: CreativeFormat): string {
  const m = cropMargin(format);
  if (!m) return `Canvas aspect ratio ${format}.`;
  return `Canvas aspect ratio ${GENERATION_ASPECT[format]}. The image will afterwards be cropped to ${format}: the top ${pct(m)} and the bottom ${pct(m)} of the height are cut off, so keep those two thin bands free of text and of any important detail.`;
}

function reservedZone(format: CreativeFormat, surface: string): string {
  const { zone } = LOGO_LAYOUT[format];
  return `RESERVED LOGO AREA (critical): the rectangle from the left edge of the image to ${pct(zone.x + zone.w)} of the image width, between ${pct(toCanvasY(format, zone.y))} and ${pct(toCanvasY(format, zone.y + zone.h))} of the image height, must stay completely empty and visually quiet: only ${surface}. Absolutely no text, no letters, no logo, no monogram, no icon, no object, no sharp edge and no frame line inside that rectangle. A real logo file will be placed there afterwards. Therefore do not draw any logo, company name, monogram or signature anywhere in the image.`;
}

function quality(extra = ''): string {
  return `QUALITY: ${extra} Ultra-realistic, sharp, high end. No distorted letters, no extra letters, no misspelled or invented words, no lorem ipsum, no watermark, no signature, no real brand or magazine name. Do not render colour codes or font names as text. sRGB.`.replace(/\s+/g, ' ').trim();
}

function exactText(lines: string[], fontFeel: string): string {
  return `TEXT TO TYPESET IN THE IMAGE (in French, exactly as written below, character for character, with every accent, apostrophe and capital letter. Typeface in the spirit of ${fontFeel}: clean, refined, sharp, evenly spaced letters. Do not add, translate, rephrase, repeat or invent any other text, word or number anywhere in the image. Each quoted line appears exactly once):\n${lines.map((l) => `- ${l}`).join('\n')}`;
}

function brandBlock(b: BrandProfile, fontFeel: string, ctaFill: string, ctaLabel: string): string {
  const p = safePalette(b);
  const tone = dataString(b.tone, 160);
  const summary = dataString(b.summary, 300);
  return `BRAND (colour and mood only, never rendered as text): primary ${p.primary}, secondary ${p.secondary}, background ${p.background}, text ${p.text}, accent ${ctaFill} used only for the call-to-action button and one tiny focal detail, button label colour ${ctaLabel}. Typography feel: ${fontFeel}. Mood: ${tone}. The business's real style, as data: ${summary}. Avoid: stock-photo clichés, generic AI staging, over-saturated colours, luxury kitsch.`;
}

function refsLine(hasRefs: boolean): string {
  return hasRefs
    ? `REFERENCE IMAGE: the single attached image is a moodboard of close-up details from this business's real work. Borrow only its materials, colours, craftsmanship and light. Invent a completely different ${niche().visuals.subject}: never reproduce the layout, the arrangement, the composition or any recognisable piece of anything shown in the moodboard, and never show the moodboard itself. Never copy any text, logo or person from it.`
    : '';
}

function ctaLine(cta: string): string {
  return `Call-to-action button label: «${cta}» (all capitals, one single button)`;
}

function bulletLines(bullets: string[]): string[] {
  return bullets.map((b, i) => `Bullet ${i + 1}: «${b}»`);
}

export function buildPrompt(concept: Concept, copy: CopyDraft, b: BrandProfile, hasRefs: boolean): string {
  const p = safePalette(b);
  const format = concept.format;
  const fontFeel = b.fonts.length ? b.fonts.slice(0, 2).map((f) => dataString(f, 40)).join(', ') : 'a refined contemporary sans-serif';
  const dark = darkest([p.primary, p.text, p.secondary]);
  const light = lightest([p.background, p.secondary, '#f5f1ea']);
  const ctaFill = p.accent;
  const ctaLabel = labelOn(ctaFill);
  const textOnPhoto = luminance(hexToRgb(light)) > 0.55 ? light : '#FFFFFF';
  const scrim = rgbToHex(hexToRgb(dark).map((v) => v * 0.55) as [number, number, number]);

  const role = `Meta advertising creative. ${canvasLine(format)} Edge-to-edge composition filling the whole frame. No white margins, no white header or footer bar, no mock-up border around the whole image.`;
  const brand = brandBlock(b, fontFeel, ctaFill, ctaLabel);
  const v = niche().visuals;
  const S = v.subject;
  const PHOTO = v.photoStyle;
  const NO_PEOPLE = v.noPeople ? 'No people, no faces, no hands, no body parts, no animals.' : 'No recognisable real person.';
  const before = copy.before ?? v.defaultBefore;
  const after = copy.after ?? v.defaultAfter;
  const scene = copy.scene ?? v.defaultScene;

  const bottomScrim = (fromPct: number) =>
    `A soft gradient scrim rises from the bottom of the image up to ${fromPct}% of its height (fully transparent at the top of the scrim, about 85% opaque ${scrim} at the bottom edge), and all the text sits on it.`;

  const textLeftColumn = (extra = '') =>
    `TEXT PLACEMENT: left-aligned column starting at 6% of the image width, headline dominant, bullets below it, each bullet on its own line with a small ${ctaFill} square bullet, then the button directly below the bullets in the same column. ${extra} Headline and bullets in ${textOnPhoto}. Pill-shaped button filled ${ctaFill} with label in ${ctaLabel}. The button ends above 91% of the image height: nothing touches the bottom edge.`;

  let style: string;
  let layout: string;
  let surface: string;
  let lines: string[];
  let hierarchy: string;
  let qualityExtra = NO_PEOPLE;

  const baseLines = [`Headline: «${copy.headline}»`, ...bulletLines(copy.bullets), ctaLine(copy.cta)];

  switch (concept.key) {
    case 'ba_vertical':
      style = `STYLE: high-end before/after split-screen advertising photograph. ${PHOTO}`;
      surface = v.calmSurface;
      layout = `COMPOSITION: one single ${S}, photographed once from one fixed tripod position, shown in two states side by side and split by a perfectly vertical, perfectly straight hard cut exactly at 50% of the image width, marked by a crisp 3-pixel ${light} line that stops at 58% of the image height, so that no line ever crosses the text below. No blending across the cut. All the main lines, edges and fixed elements align exactly across the cut, so it reads as the same ${S} with the same camera.\nLEFT HALF (BEFORE): ${before}. Flat, unflattering light, ordinary and dated, tired surfaces, believable real state, no people.\nRIGHT HALF (AFTER): ${after}. Warm, generous natural light, finished, desirable.\nThe labels «AVANT» and «APRÈS» sit just left and right of the cut, at 22% of the image height, below the reserved logo area, small letter-spaced capitals in ${textOnPhoto}, one on each side of the line.\n${bottomScrim(40)}\n${textLeftColumn()}`;
      lines = [`Label on the left half: «AVANT»`, `Label on the right half: «APRÈS»`, ...baseLines];
      hierarchy = 'HIERARCHY: headline about 9% of the image height per line, bold enough to read on a phone at 375 pixels wide; bullets clearly smaller; button high contrast, clearly a button.';
      break;
    case 'ba_horizontal':
      style = `STYLE: high-end before/after advertising photograph for a vertical story. ${PHOTO}`;
      surface = `${v.calmSurface}, in the BEFORE photograph`;
      layout = `COMPOSITION: one single ${S}, photographed once from one fixed tripod position, shown in two states stacked vertically and split by a perfectly horizontal, perfectly straight hard cut across the whole width at exactly 46% of the image height, marked by a crisp 3-pixel ${light} line. Same camera, same perspective, same ${S} above and below the line.\nTOP (BEFORE): ${before}. Raw, tired or unfinished, plain working light, no people, no tools with brand names.\nBOTTOM (AFTER): ${after}. Warm natural light, finished, desirable.\nThe label «AVANT» sits just above the cut line at the right edge; the label «APRÈS» sits just below the cut line at the right edge; both small letter-spaced capitals in ${textOnPhoto}.\nText arrangement (story safe zones): the headline sits in the BEFORE photograph, directly below the reserved logo area, left-aligned at 6% of the width, between 22% and 36% of the image height, on a soft dark gradient that keeps it legible. The three bullets and the button sit in the AFTER photograph on a soft dark gradient, left-aligned at 6% of the width, between 60% and 80% of the image height. The top 10% and the bottom 18% of the image contain no text at all.`;
      lines = [`Label above the cut: «AVANT»`, `Label below the cut: «APRÈS»`, ...baseLines];
      hierarchy = `HIERARCHY: headline large, about 5% of the image height per line, in ${textOnPhoto}; bullets smaller in ${textOnPhoto}, each with a small ${ctaFill} square bullet; pill-shaped button filled ${ctaFill} with label in ${ctaLabel}.`;
      break;
    case 'ba_slider':
      style = `STYLE: before/after comparison slider, as a clean product interface over one photograph. ${PHOTO}`;
      surface = `${v.calmSurface}, on the BEFORE side`;
      layout = `COMPOSITION: one single ${S}, photographed once from one fixed tripod position. A thin ${light} vertical divider line runs the full height of the image at exactly 36% of the image width. On that line, centred at 42% of the image height, a circular white slider handle with a diameter of 9% of the image width, with a soft shadow, containing two small dark chevrons, one pointing left and one pointing right. Left of the divider: BEFORE, ${before}, flat unflattering light, ordinary and dated, believable real state. Right of the divider: AFTER, ${after}, warm generous natural light, finished, desirable. All the main lines and edges continue exactly across the divider.\nA small pill label «AVANT» sits at 20% of the image height, near the left edge, and a small pill label «APRÈS» sits at the same height near the right edge, semi-transparent ${scrim} background with ${textOnPhoto} letters.\n${bottomScrim(36)}\n${textLeftColumn()}`;
      lines = [`Pill label on the left side: «AVANT»`, `Pill label on the right side: «APRÈS»`, ...baseLines];
      hierarchy = 'HIERARCHY: headline about 9% of the image height per line; bullets clearly smaller; the slider handle is the only interface element; the button is high contrast.';
      break;
    case 'ba_prints':
      style = `STYLE: overhead flat-lay photograph of ${v.workTable}, photorealistic, natural daylight from one side, soft shadows, real paper and photographic print textures, shot straight down.`;
      surface = 'the bare, empty surface of the table, one uniform plain material';
      layout = `COMPOSITION: seen from directly above, ${v.workTable} in a material from the reference projects. Two matte photographic prints lie side by side in the upper-middle of the frame, on top of ${v.workDocument}: the left print is the BEFORE, ${before}; the right print is the AFTER, ${after}. Both prints show exactly the same ${S} from the same camera position: same framing, same proportions, only the state of the ${S} changes. Each print is about 38% of the image width, slightly rotated by about two degrees for realism. A small white paper tab is taped to the top edge of each print: the left tab reads «AVANT» and the right tab reads «APRÈS», in neat small capitals. A steel ruler and a pencil lie on the table. The prints sit between 16% and 62% of the image height. Bottom area: a sheet of thick cream paper lies flat on the table from 64% to 96% of the image height, spanning 88% of the width. Headline, bullets and button are set directly on that sheet, left-aligned at 10% of the image width, in ${p.text}, the button filled ${ctaFill} with label in ${ctaLabel}. The table surface stays empty everywhere else.`;
      lines = [`Paper tab on the left print: «AVANT»`, `Paper tab on the right print: «APRÈS»`, ...baseLines];
      hierarchy = 'HIERARCHY: headline about 6.5% of the image height per line; bullets clearly smaller, each with a small square bullet; button flat, clean, high contrast.';
      break;
    case 'ba_sketch_photo':
      style = `STYLE: one continuous image in which a hand-drawn sketch becomes a real photograph. Sketch side: fine black ink and soft graphite pencil on cream paper. Photograph side: ${PHOTO}`;
      surface = 'the empty cream paper of the sketch, with no lines on it';
      layout = `COMPOSITION: one single ${S} from one single fixed viewpoint. The image transitions along a diagonal from the bottom-left corner to the top-right corner. Upper-left triangle: ${v.sketchStyle} of the ${S}, confident lines, construction lines, soft hatching. Lower-right triangle: the finished ${S} as a real photograph: ${after}. The ink lines continue exactly into the real edges of the ${S}: same camera, same framing, same positions. Along the diagonal, the drawing dissolves into the photograph through graphite hatching, with no hard line. The drawing fades out to empty blank paper before reaching the top-left corner: the reserved logo rectangle is bare paper, with not a single pencil line, or edge in it. The drawing shows no measurements, no annotations and no words.\nText sits in the lower part of the image over the photograph: ${bottomScrim(42)}\n${textLeftColumn()}`;
      lines = [...baseLines];
      hierarchy = 'HIERARCHY: headline about 9% of the image height per line; bullets clearly smaller; button high contrast.';
      break;
    case 'photo_bullets':
      style = `STYLE: full-frame editorial photograph, the ${S} is the hero. ${PHOTO}`;
      surface = v.calmSurface;
      layout = `COMPOSITION: ${scene}. Warm, generous natural light. One wide view of the whole ${S}, deep composition with foreground, middle ground and background.\n${bottomScrim(38)}\n${textLeftColumn()}`;
      lines = [...baseLines];
      hierarchy = 'HIERARCHY: headline about 9% of the image height per line; bullets clearly smaller; button high contrast.';
      break;
    case 'imessage':
      style = `STYLE: native iOS Messages screenshot presented as a clean card on a solid brand-coloured background, flat graphic, pixel-accurate iOS typography.`;
      surface = `the plain solid ${p.primary} background`;
      layout = `COMPOSITION: solid ${p.primary} background over the whole image, with a very subtle paper grain. A rounded rectangular iOS Messages conversation card (corner radius about 4% of the width, soft shadow, white interior) spans 88% of the image width, centred horizontally, from 31% to 74% of the image height. Inside the card: only the message bubbles, no status bar, no clock, no battery, no signal icons, no contact name, no header, no date, no input field. Bubble 1 on the right, blue iOS bubble (#0B84FF) with white text. Bubble 2 on the left, light grey iOS bubble (#E9E9EB) with black text. Bubble 3 on the right, blue. Bubble 4 on the left, grey. Natural iOS bubble tails, generous line spacing, the bubble text is large and easy to read.\nAbove the card, between 22% and 30% of the image height, the headline, left-aligned at 6% of the image width, in ${luminance(hexToRgb(p.primary)) > 0.4 ? p.text : '#FFFFFF'}.\nBelow the card, between 76% and 81% of the image height, the pill-shaped button, left-aligned at 6% of the image width, filled ${ctaFill}, label in ${ctaLabel}. The top 10% and the bottom 18% of the image contain only the plain background.`;
      lines = [`Headline above the card: «${copy.headline}»`, ...copy.bullets.map((t, n) => `Bubble ${n + 1}: «${t}»`), ctaLine(copy.cta)];
      hierarchy = 'HIERARCHY: conversation first, headline second, button third. No other interface elements anywhere.';
      qualityExtra = `${NO_PEOPLE} Flat graphic, sharp text, perfect iOS bubble geometry.`;
      break;
    case 'notes':
      style = `STYLE: native iOS Notes app note, presented as a clean card on a solid brand-coloured background, flat graphic, pixel-accurate iOS typography.`;
      surface = `the plain solid ${p.primary} background`;
      layout = `COMPOSITION: solid ${p.primary} background over the whole image, with a very subtle paper grain. A rounded rectangular iOS Notes card with warm white paper interior, soft shadow, spans 84% of the image width, centred horizontally, from 18% to 84% of the image height. Inside the card: no toolbar, no status bar, no date, no icons, no back arrow. The note title is bold black, then each line of the list below it with an iOS dash, generous line spacing.\nBelow the card, the pill-shaped button sits between 87% and 94% of the image height, centred horizontally, filled ${ctaFill}, label in ${ctaLabel}.`;
      lines = [`Note title (bold): «${copy.headline}»`, ...copy.bullets.map((t, n) => `Note line ${n + 1}: «${t}»`), ctaLine(copy.cta)];
      hierarchy = 'HIERARCHY: note title largest, lines large enough to read on a phone, button third.';
      qualityExtra = `${NO_PEOPLE} Flat graphic, sharp text.`;
      break;
    case 'advertorial':
      style = `STYLE: a printed page of a high-end French lifestyle magazine, photographed flat, refined editorial layout, matte paper texture. The photograph on the page: ${PHOTO}`;
      surface = `the plain matte paper of the page, colour ${p.background}`;
      layout = `COMPOSITION: full-bleed magazine page with a matte paper background in ${p.background}. Top band from 0% to 18% of the image height is empty paper except for the kicker «PUBLIREPORTAGE», small letter-spaced capitals at the top right, right-aligned at 94% of the width, vertically centred in that band. The reserved logo area lies entirely on this paper band, so the photograph must not start before 18% of the image height. A large photograph spans the full width of the page from 18% to 56% of the image height: ${scene}. Under the photograph, on the paper: the headline in a high-contrast editorial serif, large, left-aligned at 6% of the width in ${p.text}, on at most two lines; below it the two short standfirst sentences, left-aligned, in a smaller refined serif; then the pill-shaped button, left-aligned, filled ${ctaFill}, label in ${ctaLabel}. The whole button must end above 90% of the image height, with empty paper below it down to the bottom edge. No masthead, no magazine name, no page number, no date, no other columns of text.`;
      lines = [`Kicker, top right: «PUBLIREPORTAGE»`, `Headline: «${copy.headline}»`, ...copy.bullets.map((t, n) => `Standfirst sentence ${n + 1}: «${t}»`), ctaLine(copy.cta)];
      hierarchy = 'HIERARCHY: headline about 7% of the image height per line, standfirst clearly smaller, kicker small and discreet, button last.';
      break;
    case 'listicle':
      style = `STYLE: elegant editorial numbered list over a darkened photograph, vertical story format. Photograph: ${PHOTO}`;
      surface = v.calmSurface;
      layout = `COMPOSITION: ${scene}, lit softly, darkened evenly with a ${scrim} overlay at about 62% opacity so the white text reads perfectly while the ${S} stays visible. Text arrangement (story safe zones): the headline left-aligned at 6% of the width, between 22% and 33% of the image height, in ${textOnPhoto}. Below it, between 36% and 72% of the image height, a numbered list of three rows, each row with a large thin numeral (1, 2, 3) on the left, in ${ctaFill}, the error text beside it in ${textOnPhoto}, rows separated by thin ${textOnPhoto} hairlines. Below, between 75% and 81% of the image height, the pill-shaped button, left-aligned at 6% of the width, filled ${ctaFill}, label in ${ctaLabel}. The top 10% and the bottom 18% of the image contain no text.`;
      lines = [`Headline: «${copy.headline}»`, ...copy.bullets.map((t, n) => `Row ${n + 1}: «${t}», numbered ${n + 1}`), ctaLine(copy.cta)];
      hierarchy = 'HIERARCHY: headline about 5% of the image height per line, numerals large, row text clearly readable on a phone, button last.';
      break;
    default:
      throw new Error(`Concept inconnu : ${concept.key}`);
  }

  return [
    role,
    style,
    brand,
    reservedZone(format, surface),
    layout,
    refsLine(hasRefs),
    exactText(lines, fontFeel),
    hierarchy,
    quality(qualityExtra),
  ]
    .filter(Boolean)
    .join('\n\n');
}

export function correctionsBlock(corrections: string[]): string {
  if (!corrections.length) return '';
  return `\n\nCORRECTIONS REQUIRED (a previous render had these defects; fix them precisely, keep everything else):\n${corrections.map((c) => `- ${c}`).join('\n')}`;
}
