export type Llm = {
  json<T>(a: { system: string; user: string; images?: string[] }): Promise<T>;
  text(a: { system: string; user: string; images?: string[] }): Promise<string>;
};

export type BrandProfile = {
  businessName: string;
  profession: string;
  professionLabel: string;
  city: string | null;
  region: string | null;
  specialties: string[];
  projectTypes: string[];
  summary: string;
  tone: string;
  palette: { primary: string; secondary: string; accent: string; background: string; text: string };
  fonts: string[];
  logoPath: string | null;
  logoIsFallback: boolean;
  projectImages: { path: string; title?: string }[];
  facts: string[];
};

export type CompetitorInsights = { hooks: string[]; angles: string[]; styleNotes: string[]; saturated: string[] };

export type CreativeFormat = '4:5' | '9:16' | '1:1';

export type CreativeSpec = {
  index: number;
  concept: string;
  format: CreativeFormat;
  angle: string;
  headline: string;
  primaryText: string;
  bullets: string[];
  cta: string;
  prompt: string;
  referencePaths: string[];
  locked: boolean;
};

export type RenderResult = {
  imagePath: string;
  blurPath: string;
  thumbPath: string;
  attempts: number;
  issues: string[];
};

export type RenderOptions = {
  /** Plafond de générations pour ce dossier ; 14 par défaut (contrat). */
  maxGenerations?: number;
  /** Nombre maximal de passes par créative : 2 par défaut (une régénération). */
  maxAttempts?: number;
  /** Ignore le cache pour obtenir une nouvelle image (régénération admin). */
  force?: boolean;
};

export type ConceptKey =
  | 'ba_vertical'
  | 'ba_horizontal'
  | 'ba_slider'
  | 'ba_prints'
  | 'ba_sketch_photo'
  | 'photo_bullets'
  | 'imessage'
  | 'notes'
  | 'advertorial'
  | 'listicle';

export type ConceptFamily = 'before_after' | 'native' | 'editorial';

export type CopyDraft = {
  headline: string;
  primaryText: string;
  bullets: string[];
  cta: string;
  angle: string;
  strength: number;
  /** État avant, en anglais, pour les avant-après. */
  before?: string;
  /** État après, en anglais, pour les avant-après. */
  after?: string;
  /** Scène, en anglais, pour les photos et le publireportage. */
  scene?: string;
};
