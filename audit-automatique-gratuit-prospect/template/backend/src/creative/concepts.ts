import { niche } from '../niche.js';
import type { BrandProfile, ConceptFamily, ConceptKey, CopyDraft, CreativeFormat } from './types.js';

export type Zone = { x: number; y: number; w: number; h: number };

export const OUTPUT_SIZE: Record<CreativeFormat, { width: number; height: number; pixels: string }> = {
  '4:5': { width: 1440, height: 1800, pixels: '1440 x 1800' },
  '9:16': { width: 1440, height: 2560, pixels: '1440 x 2560' },
  '1:1': { width: 1440, height: 1440, pixels: '1440 x 1440' },
};

/**
 * Position constante du logo, par format, en fractions de l'image.
 * `zone` est la zone que le modèle doit laisser calme ; `logo` est la boîte réelle
 * de recomposition. En 9:16, le logo reste sous la zone d'interface des stories.
 */
export const LOGO_LAYOUT: Record<CreativeFormat, { zone: Zone; logo: { x: number; y: number; maxW: number; maxH: number } }> = {
  '4:5': { zone: { x: 0, y: 0, w: 0.38, h: 0.13 }, logo: { x: 0.055, y: 0.045, maxW: 0.26, maxH: 0.062 } },
  '1:1': { zone: { x: 0, y: 0, w: 0.38, h: 0.14 }, logo: { x: 0.055, y: 0.05, maxW: 0.26, maxH: 0.075 } },
  '9:16': { zone: { x: 0, y: 0.1, w: 0.4, h: 0.11 }, logo: { x: 0.055, y: 0.135, maxW: 0.28, maxH: 0.05 } },
};

/** Le modèle n'accepte pas le 4:5 (rejet vérifié le 2026-11-08) : génération en 3:4, puis recadrage centré. */
export const GENERATION_ASPECT: Record<CreativeFormat, string> = { '4:5': '3:4', '9:16': '9:16', '1:1': '1:1' };

/** Fraction de hauteur perdue en haut et en bas par le recadrage final. */
export function cropMargin(format: CreativeFormat): number {
  return format === '4:5' ? 0.03125 : 0;
}

/** Zone contrôlée par la relecture : la place réelle du logo, avec une petite marge. */
export function logoCheckRect(format: CreativeFormat): Zone {
  const { logo } = LOGO_LAYOUT[format];
  return {
    x: 0,
    y: Math.max(0, logo.y - 0.025),
    w: Math.min(1, logo.x + logo.maxW + 0.025),
    h: logo.maxH + 0.05,
  };
}

export type FallbackContext = {
  cityIn: string;
  cityLabel: string;
  label: string;
  name: string;
  bullets: string[];
};

export type Concept = {
  key: ConceptKey;
  label: string;
  family: ConceptFamily;
  format: CreativeFormat;
  bullets: { min: number; max: number; maxWords: number };
  headlineMaxWords: number;
  /** Textes fixes rendus sur l'image (étiquettes), en plus du titre, des puces et du CTA. */
  staticTexts: string[];
  /** Brief créatif donné au rédacteur. */
  brief: string;
  fallback: (c: FallbackContext) => Omit<CopyDraft, 'strength' | 'angle' | 'before' | 'after' | 'scene'> & { angle: string };
};

const generic = (c: FallbackContext, s: string) => `${c.name}, ${c.label.toLowerCase()}${c.cityIn ? ` ${c.cityIn}` : ''}. ${s}`;

export const CONCEPTS: Concept[] = [
  {
    key: 'ba_vertical',
    label: 'Avant-après, coupe verticale',
    family: 'before_after',
    format: '4:5',
    bullets: { min: 3, max: 3, maxWords: 4 },
    headlineMaxWords: 7,
    staticTexts: ['AVANT', 'APRÈS'],
    brief:
      'Photo coupée en deux à la verticale : le même sujet, état de départ à gauche, résultat à droite. Accroche courte qui vend le contraste. Trois puces très courtes sur ce qui change.',
    fallback: (c) => ({
      headline: 'Le même point de départ. Un autre résultat.',
      bullets: c.bullets.slice(0, 3),
      cta: 'PARLER DE MON PROJET',
      angle: 'projection désirée',
      primaryText: generic(c, 'Vous avez déjà tout ce qu’il faut. Il manque seulement le bon regard.'),
    }),
  },
  {
    key: 'ba_horizontal',
    label: 'Avant-après, coupe horizontale',
    family: 'before_after',
    format: '9:16',
    bullets: { min: 3, max: 3, maxWords: 4 },
    headlineMaxWords: 7,
    staticTexts: ['AVANT', 'APRÈS'],
    brief:
      'Story en deux étages : en haut l’état de départ, en bas le résultat. Accroche courte sur le passage de l’un à l’autre. Trois puces très courtes.',
    fallback: (c) => ({
      headline: 'Du point de départ à votre quotidien.',
      bullets: c.bullets.slice(0, 3),
      cta: 'DÉMARRER MON PROJET',
      angle: 'du départ au quotidien',
      primaryText: generic(c, 'Un projet fait peur tant qu’on ne sait pas où il mène. Commençons par voir où il mène.'),
    }),
  },
  {
    key: 'ba_slider',
    label: 'Avant-après, curseur de comparaison',
    family: 'before_after',
    format: '4:5',
    bullets: { min: 3, max: 3, maxWords: 4 },
    headlineMaxWords: 7,
    staticTexts: ['AVANT', 'APRÈS'],
    brief:
      'Visuel de comparaison avec curseur et poignée, façon interface. Accroche qui invite à regarder la différence. L’image est statique : le texte ne demande jamais de glisser, cliquer ou faire défiler. Trois puces très courtes.',
    fallback: (c) => ({
      headline: 'Regardez. C’est le même point de départ.',
      bullets: c.bullets.slice(0, 3),
      cta: 'VOIR CE QUE ÇA CHANGE',
      angle: 'preuve visuelle',
      primaryText: generic(c, 'La différence tient souvent à une seule bonne décision.'),
    }),
  },
  {
    key: 'ba_prints',
    label: 'Avant-après, tirages sur table de travail',
    family: 'before_after',
    format: '4:5',
    bullets: { min: 3, max: 3, maxWords: 4 },
    headlineMaxWords: 7,
    staticTexts: ['AVANT', 'APRÈS'],
    brief:
      'Vue de dessus d’une table de travail : deux tirages photo posés sur un document de travail, avant et après. Accroche sur le travail de préparation. Trois puces très courtes.',
    fallback: (c) => ({
      headline: 'Tout se décide sur cette table.',
      bullets: c.bullets.slice(0, 3),
      cta: 'PRENDRE RENDEZ-VOUS',
      angle: 'méthode et préparation',
      primaryText: generic(c, 'Un beau résultat commence sur une table, bien avant le premier geste.'),
    }),
  },
  {
    key: 'ba_sketch_photo',
    label: 'Avant-après, du dessin à la photo',
    family: 'before_after',
    format: '4:5',
    bullets: { min: 3, max: 3, maxWords: 4 },
    headlineMaxWords: 7,
    staticTexts: [],
    brief:
      'Le même cadrage passe d’un dessin à la main à la photo du résultat. Accroche sur l’idée qui devient réalité. Trois puces très courtes.',
    fallback: (c) => ({
      headline: 'Dessiné avant d’être réalisé.',
      bullets: c.bullets.slice(0, 3),
      cta: 'DÉCRIRE MON PROJET',
      angle: 'de l’idée à la réalité',
      primaryText: generic(c, 'Chaque détail prévu devient un geste du quotidien.'),
    }),
  },
  {
    key: 'photo_bullets',
    label: 'Photo plein cadre avec puces',
    family: 'editorial',
    format: '4:5',
    bullets: { min: 3, max: 3, maxWords: 5 },
    headlineMaxWords: 7,
    staticTexts: [],
    brief:
      'Grande photo d’un résultat terminé, très désirable. Accroche qui fait rêver, ancrée dans la ville ou le type de projet. Trois puces sur ce que cela apporte au quotidien.',
    fallback: (c) => ({
      headline: 'Un résultat pensé pour votre vie.',
      bullets: c.bullets.slice(0, 3),
      cta: 'PARLER DE MON PROJET',
      angle: 'désir et art de vivre',
      primaryText: generic(c, 'Votre projet peut vous ressembler, jusque dans les détails.'),
    }),
  },
  {
    key: 'imessage',
    label: 'Conversation iMessage',
    family: 'native',
    format: '9:16',
    bullets: { min: 4, max: 4, maxWords: 12 },
    headlineMaxWords: 6,
    staticTexts: [],
    brief:
      'Vraie capture d’une conversation iMessage entre un futur client (bulles 1 et 3, bleues) et l’entreprise (bulles 2 et 4, grises). Les puces sont les quatre bulles, dans l’ordre. Pas un témoignage : une question de départ et une réponse de métier. Aucun remerciement, aucun résultat, aucun avis.',
    fallback: (c) => ({
      headline: 'Vous hésitez encore à commencer ?',
      bullets: [
        'Bonjour, on hésite à lancer notre projet.',
        'Bonjour. Qu’est-ce qui vous retient aujourd’hui ?',
        'Le budget, et ne pas savoir par où commencer.',
        'Commençons par votre façon de vivre. Le reste suit.',
      ],
      cta: 'POSER MA QUESTION',
      angle: 'première conversation',
      primaryText: generic(c, 'Une bonne conversation évite bien des mauvaises décisions.'),
    }),
  },
  {
    key: 'notes',
    label: 'Notes iOS',
    family: 'native',
    format: '1:1',
    bullets: { min: 3, max: 4, maxWords: 7 },
    headlineMaxWords: 6,
    staticTexts: [],
    brief:
      'Capture de l’application Notes d’iPhone : une liste de points à vérifier avant de lancer un projet dans sa ville, écrite simplement, comme pour soi.',
    fallback: (c) => ({
      headline: 'Avant de lancer votre projet',
      bullets: ['Regarder ce qui marche déjà', 'Définir le résultat avant les détails', 'Fixer le budget, puis s’y tenir'],
      cta: 'PRÉPARER MON PROJET',
      angle: 'liste utile',
      primaryText: generic(c, 'Les bonnes décisions se prennent avant le premier devis.'),
    }),
  },
  {
    key: 'advertorial',
    label: 'Publireportage façon magazine',
    family: 'editorial',
    format: '4:5',
    bullets: { min: 2, max: 2, maxWords: 11 },
    headlineMaxWords: 9,
    staticTexts: ['PUBLIREPORTAGE'],
    brief:
      'Page de magazine : grande photo, titre de presse, deux phrases de chapô. Ton de journaliste qui parle d’un type de projet et de sa ville, jamais d’un cas précis (pas de récit d’un client particulier). Aucun nom de vrai magazine.',
    fallback: (c) => ({
      headline: 'Ces projets qui changent tout sans tout recommencer',
      bullets: ['Tout commence par un échange et un plan.', 'Le reste est une affaire de détails et de méthode.'],
      cta: 'LIRE LA SUITE',
      angle: 'récit éditorial',
      primaryText: generic(c, 'Changer de quotidien sans tout recommencer, c’est souvent une question de méthode.'),
    }),
  },
  {
    key: 'listicle',
    label: 'Listicle d’erreurs à éviter',
    family: 'editorial',
    format: '9:16',
    bullets: { min: 3, max: 3, maxWords: 6 },
    headlineMaxWords: 8,
    staticTexts: ['1', '2', '3'],
    brief:
      'Liste numérotée de trois erreurs concrètes à éviter sur un projet comme ceux de l’entreprise. L’accroche est une phrase entière qui contient « 3 erreurs » (forme : « 3 erreurs qui ... »). Les puces sont les trois erreurs, sans numéro (le visuel les numérote).',
    fallback: (c) => ({
      headline: '3 erreurs avant de lancer votre projet',
      bullets: ['Commencer sans plan d’ensemble', 'Choisir les détails en premier', 'Oublier le quotidien'],
      cta: 'ÉVITER CES ERREURS',
      angle: 'peur de mal faire',
      primaryText: generic(c, 'Les erreurs les plus chères se décident avant de commencer.'),
    }),
  },
];

export function conceptByLabel(label: string): Concept | undefined {
  return CONCEPTS.find((c) => c.label === label);
}

export function cityIn(city: string | null): string {
  if (!city) return '';
  const c = city.trim();
  if (/^le\s/i.test(c)) return `au ${c.slice(3)}`;
  if (/^les\s/i.test(c)) return `aux ${c.slice(4)}`;
  return `à ${c}`;
}


function shortPhrase(s: string, maxWords: number): string | null {
  const t = s.trim();
  if (!t) return null;
  const words = t.split(/\s+/);
  if (words.length > maxWords) return null;
  return t.charAt(0).toLocaleUpperCase('fr-FR') + t.slice(1);
}

export function fallbackContext(b: BrandProfile, maxWords = 4): FallbackContext {
  const bullets: string[] = [];
  for (const s of [...b.specialties, ...b.projectTypes]) {
    const p = shortPhrase(s, maxWords);
    if (p && !bullets.includes(p)) bullets.push(p);
    if (bullets.length >= 2) break;
  }
  for (const p of niche().creatives.fallbackBullets) {
    if (bullets.length >= 6) break;
    if (!bullets.includes(p)) bullets.push(p);
  }
  return {
    cityIn: cityIn(b.city),
    cityLabel: b.city ?? '',
    label: b.professionLabel,
    name: b.businessName,
    bullets,
  };
}
