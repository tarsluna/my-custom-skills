import { readFileSync } from 'node:fs';
import path from 'node:path';
import { z } from 'zod';

/**
 * Le seul fichier à adapter pour changer de métier : audit.config.json.
 * Tout ce qui parle d'un secteur, d'un opérateur ou d'un vocabulaire vient d'ici.
 */
const text = z.string().min(1);
const color = z.string().regex(/^#[0-9a-fA-F]{6}$/);

const Schema = z.object({
  operator: z.object({ name: text, logoUrl: z.string().min(1).nullable(), websiteUrl: z.string().url(), motto: z.string().nullable() }),
  theme: z.object({ background: color, backgroundAlt: color, backgroundLight: color, foreground: color, foregroundSoft: color, muted: color, accent: color }),
  business: z.object({ nom: text, le: text, du: text, un: text, au: text, ce: text, votre: text }),
  sector: z.object({
    description: text,
    reader: text,
    country: z.string().length(2),
    projectWord: text,
    portfolioWord: text,
    professions: z.array(z.object({ key: text, label: text, evidence: text, neverCalled: z.array(text) })).min(1),
    defaultProfession: text,
  }),
  competitors: z.object({ keep: text, exclude: text, excludedNameWords: z.array(text), excludedBodyWords: z.array(text) }),
  assistant: z.object({
    topics: z.array(text).min(1),
    budgetLabel: text,
    priceLabel: text,
    pricePattern: text,
    replyPrice: text,
    replyAngle: text,
    replyAi: text,
    replyDeflect: text,
    replyClosing: text,
    fallbackProject: text,
    fallbackReplies: z.array(text).min(2),
  }),
  vocabulary: z.object({ banned: z.array(text), forbiddenAngles: z.array(text), noExclamation: z.boolean() }),
  creatives: z.object({
    visible: z.number().int().min(1).max(10),
    directorOf: text,
    voice: text,
    headlineExamples: z.array(text).min(1),
    bulletExample: text,
    ctaExamples: z.array(text).min(1),
    fallbackBullets: z.array(text).min(6),
  }),
  visuals: z.object({
    subject: text,
    subjectFr: text,
    photoStyle: text,
    calmSurface: text,
    defaultBefore: text,
    defaultAfter: text,
    defaultScene: text,
    workTable: text,
    workDocument: text,
    sketchStyle: text,
    noPeople: z.boolean(),
  }),
  page: z.object({
    title: text,
    lockedSentence: text,
    conceptNote: text,
    indexCta: text,
    sections: z.object({ business: text, competitors: text, creatives: text, projects: text, assistant: text, next: text }),
    businessTitle: text,
    creativesTitle: text,
    creativesLead: text,
    projectsTitle: text,
    projectsLead: text,
    assistantTitle: text,
    assistantLead: text,
    assistantNotes: z.array(z.object({ tag: text, text })).min(1),
    nextTitle: text,
    closing: text,
    closingWithName: text,
    teaser: z.array(z.object({ title: text, sub: text })).min(1),
    costLabel: text,
    costLabelShort: text,
    costAverageLabel: text,
    footerLegal: text,
  }),
});

export type Niche = z.infer<typeof Schema>;

let cached: Niche | null = null;

export function loadNiche(file: string = process.env.AUDIT_CONFIG_PATH ?? path.resolve('audit.config.json')): Niche {
  let raw: unknown;
  try {
    raw = JSON.parse(readFileSync(file, 'utf8'));
  } catch (e) {
    throw new Error(`audit.config.json illisible (${file}) : ${e instanceof Error ? e.message : String(e)}`);
  }
  const parsed = Schema.safeParse(raw);
  if (!parsed.success) throw new Error(`audit.config.json invalide : ${parsed.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join(' ; ')}`);
  if (!parsed.data.sector.professions.some((p) => p.key === parsed.data.sector.defaultProfession)) throw new Error('audit.config.json : sector.defaultProfession doit être une clé de sector.professions');
  return parsed.data;
}

export function niche(): Niche {
  if (!cached) cached = loadNiche();
  return cached;
}

export function setNicheForTests(n: Niche | null) {
  cached = n;
}

/** Remplace {cle} dans un texte de configuration ; une clé inconnue reste visible pour être repérée. */
export function fill(template: string, vars: Record<string, string | number | null | undefined>): string {
  return template.replace(/\{(\w+)\}/g, (all, key: string) => {
    const value = vars[key];
    return value === null || value === undefined ? all : String(value);
  });
}

export const capitalize = (s: string) => (s ? s.charAt(0).toLocaleUpperCase('fr-FR') + s.slice(1) : s);

/** Les formes grammaticales du nom de l'activité, pour les réponses de l'assistant. */
export function businessVars(n: Niche = niche()) {
  const b = n.business;
  return { nom_activite: b.nom, le: b.le, le_maj: capitalize(b.le), du: b.du, un: b.un, au: b.au, ce: b.ce, votre: b.votre };
}
