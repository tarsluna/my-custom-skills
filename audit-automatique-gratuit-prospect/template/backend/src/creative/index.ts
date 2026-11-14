import { niche } from '../niche.js';
/**
 * Moteur de création : 10 créatives Meta statiques à l'identité d’une entreprise.
 * Interface publique (voir docs/CONTRACT.md) : planCreatives et renderCreative.
 */
import { createHash } from 'node:crypto';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';
import { GenerationLedger, KieError, generateImage, MAX_GENERATIONS_PER_AUDIT } from '../lib/kie.js';
import { GENERATION_ASPECT, conceptByLabel } from './concepts.js';
import type { Concept } from './concepts.js';
import { writeCopy } from './copy.js';
import type { CopyPlan } from './copy.js';
import { applyLogo, prepareLogo } from './logo.js';
import { normalizeImage, writeFinal } from './output.js';
import { buildPrompt, correctionsBlock } from './prompts.js';
import { reviewImage } from './qa.js';
import type { QaResult } from './qa.js';
import type {
  BrandProfile,
  CompetitorInsights,
  ConceptFamily,
  CopyDraft,
  CreativeSpec,
  Llm,
  RenderOptions,
  RenderResult,
} from './types.js';

export type {
  BrandProfile,
  CompetitorInsights,
  CreativeSpec,
  Llm,
  RenderOptions,
  RenderResult,
} from './types.js';
export { KieError } from '../lib/kie.js';


function fallbackScene(concept: Concept, b: BrandProfile): Pick<CopyDraft, 'before' | 'after' | 'scene'> {
  const place = (b.projectTypes[0] ?? b.specialties[0] ?? 'French home').slice(0, 80);
  const dated: Record<string, string> = {
    ba_vertical: `a dated French ${place} from the 1980s: brown floor tiles, faded flowered wallpaper, low false ceiling with a fluorescent tube, melamine units, stained paint`,
    ba_horizontal: `the same ${place} as a raw building site: bare plaster walls, exposed cables, capped pipes, rubble and stacked plasterboard on a concrete floor`,
    ba_slider: `a tired French ${place} of the 1970s: yellowed paint, worn lino floor, dark varnished wood, a low cramped layout`,
    ba_prints: `a dated French ${place}: worn carpet, heavy curtains, tired paint`,
    ba_sketch_photo: `a French ${place} in its original state`,
  };
  const finished = `the same ${place} redesigned in the style of the reference projects: pale oak, warm plaster, tailored joinery, soft daylight, a calm and precise layout`;
  return {
    before: dated[concept.key],
    after: finished,
    scene: `a finished ${place} in the style of the reference projects: pale oak, warm plaster, tailored joinery, soft daylight`,
  };
}

function referencesFor(concept: Concept, b: BrandProfile, slot: number): string[] {
  const images = b.projectImages.filter((p) => p.path);
  if (!images.length) return [];
  if (concept.key === 'imessage' || concept.key === 'notes') return [];
  const count = concept.family === 'before_after' || concept.key === 'photo_bullets' || concept.key === 'advertorial' ? 2 : 1;
  const out: string[] = [];
  for (let i = 0; i < count && i < images.length; i += 1) {
    out.push(images[(slot + i) % images.length]!.path);
  }
  return out;
}

/** Trois créatives ouvertes : une par famille, les plus fortes, au moins un avant-après. */
export function chooseUnlocked(plans: { family: ConceptFamily; strength: number; format: string; index: number }[]): Set<number> {
  const families: ConceptFamily[] = ['before_after', 'native', 'editorial'];
  const chosen: typeof plans = [];
  for (const family of families) {
    const best = plans.filter((p) => p.family === family).sort((a, b) => b.strength - a.strength || a.index - b.index)[0];
    if (best) chosen.push(best);
  }
  // Variété de formats : remplace le plus faible si tout est au même format.
  const formats = new Set(chosen.map((c) => c.format));
  if (chosen.length === 3 && formats.size === 1) {
    const weakest = [...chosen].sort((a, b) => a.strength - b.strength)[0]!;
    const replacement = plans
      .filter((p) => p.family === weakest.family && p.format !== weakest.format)
      .sort((a, b) => b.strength - a.strength)[0];
    if (replacement) chosen.splice(chosen.indexOf(weakest), 1, replacement);
  }
  const visible = niche().creatives.visible;
  for (const p of [...plans].sort((a, b) => b.strength - a.strength)) {
    if (chosen.length >= visible) break;
    if (!chosen.includes(p)) chosen.push(p);
  }
  return new Set(chosen.slice(0, visible).map((c) => c.index));
}

/** Planifie les 10 créatives : concept, texte, prompt, références et verrouillage. */
export async function planCreatives(b: BrandProfile, i: CompetitorInsights, llm: Llm): Promise<CreativeSpec[]> {
  const plans: CopyPlan[] = await writeCopy(b, i, llm);
  const specs = plans.map((plan, idx): CreativeSpec => {
    const concept = plan.concept;
    const draft: CopyDraft = { ...fallbackScene(concept, b), ...stripUndefined(plan.draft) };
    const refs = referencesFor(concept, b, idx);
    return {
      index: idx + 1,
      concept: concept.label,
      format: concept.format,
      angle: draft.angle,
      headline: draft.headline,
      primaryText: draft.primaryText,
      bullets: draft.bullets,
      cta: draft.cta,
      prompt: buildPrompt(concept, draft, b, refs.length > 0),
      referencePaths: refs,
      locked: true,
    };
  });
  const unlocked = chooseUnlocked(
    plans.map((plan, idx) => ({ family: plan.concept.family, strength: plan.draft.strength, format: plan.concept.format, index: idx + 1 })),
  );
  for (const s of specs) s.locked = !unlocked.has(s.index);
  return specs;
}

function stripUndefined<T extends object>(o: T): T {
  return Object.fromEntries(Object.entries(o).filter(([, v]) => v !== undefined && v !== '')) as T;
}

type Candidate = { rawPath: string; normalized: Buffer; qa: QaResult };

/**
 * Les références partent au modèle sous forme d'une image de détails : deux recadrages
 * serrés par projet, jamais la photo entière. Le modèle reprend ainsi les matières et la
 * lumière de l’entreprise sans pouvoir recopier une réalisation réelle pour en faire un faux « après ».
 */
async function buildMoodboard(paths: string[], dir: string): Promise<string[]> {
  if (!paths.length) return [];
  const refDir = path.join(dir, '.kie', 'refs');
  await fs.mkdir(refDir, { recursive: true });
  const digests: string[] = [];
  const tiles: Buffer[] = [];
  const tileW = 640;
  const tileH = 427;
  for (const p of paths.slice(0, 3)) {
    try {
      const buf = await fs.readFile(p);
      digests.push(createHash('sha256').update(buf).digest('hex').slice(0, 12));
      const img = sharp(buf, { failOn: 'none' }).rotate();
      const { data, info } = await img.jpeg({ quality: 92 }).toBuffer({ resolveWithObject: true });
      const cropW = Math.round(info.width * 0.5);
      const cropH = Math.min(Math.round((cropW * tileH) / tileW), Math.round(info.height * 0.8));
      for (const fx of [0.06, 0.44]) {
        const left = Math.min(info.width - cropW, Math.round(info.width * fx));
        const top = Math.min(info.height - cropH, Math.round((info.height - cropH) * (fx < 0.2 ? 0.25 : 0.6)));
        tiles.push(
          await sharp(data).extract({ left, top, width: cropW, height: cropH }).resize(tileW, tileH, { fit: 'cover' }).jpeg({ quality: 90 }).toBuffer(),
        );
      }
    } catch {
      /* référence illisible : ignorée */
    }
  }
  if (!tiles.length) return [];
  const file = path.join(refDir, `board-${createHash('sha256').update(digests.join('-')).digest('hex').slice(0, 20)}.jpg`);
  const exists = await fs.access(file).then(() => true).catch(() => false);
  if (!exists) {
    const columns = 2;
    const rows = Math.ceil(tiles.length / columns);
    const gap = 10;
    await sharp({
      create: { width: columns * tileW + (columns - 1) * gap, height: rows * tileH + (rows - 1) * gap, channels: 3, background: { r: 245, g: 241, b: 234 } },
    })
      .composite(tiles.map((input, i) => ({ input, left: (i % columns) * (tileW + gap), top: Math.floor(i / columns) * (tileH + gap) })))
      .jpeg({ quality: 88 })
      .toFile(file);
  }
  return [file];
}

/** Génère une créative, la relit, régénère une fois au besoin, puis pose le vrai logo. */
export async function renderCreative(
  s: CreativeSpec,
  b: BrandProfile,
  dir: string,
  llm: Llm,
  opts: RenderOptions = {},
): Promise<RenderResult> {
  const concept = conceptByLabel(s.concept);
  if (!concept) throw new Error(`Concept inconnu : ${s.concept}`);

  const ledger = new GenerationLedger(dir, opts.maxGenerations ?? MAX_GENERATIONS_PER_AUDIT);
  const maxAttempts = Math.max(1, opts.maxAttempts ?? 2);
  const logo = await prepareLogo(b);
  const issues: string[] = [...logo.issues];
  const refs = await buildMoodboard(s.referencePaths, dir);

  let best: Candidate | null = null;
  let attempts = 0;
  let corrections: string[] = [];

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const basePrompt = refs.length ? s.prompt : s.prompt.replace(/\n\nREFERENCE IMAGE:[^\n]*/, '');
    const prompt = `${basePrompt}${correctionsBlock(corrections)}`;
    let generated;
    try {
      generated = await generateImage({
        prompt,
        refs,
        aspectRatio: GENERATION_ASPECT[s.format],
        resolution: '2K',
        workDir: dir,
        ledger,
        nonce: opts.force ? `${Date.now()}-${attempt}` : attempt > 1 ? `regen-${attempt}` : undefined,
      });
    } catch (e) {
      if (e instanceof KieError && best) {
        // Plus de budget ou de fournisseur pour la régénération : on garde la meilleure image.
        issues.push(`Régénération impossible : ${e.message}`);
        break;
      }
      throw e;
    }
    attempts = attempt;

    const normalized = await normalizeImage(generated.path, s.format);
    const qa = await reviewImage(normalized, s, llm);
    const candidate: Candidate = { rawPath: generated.path, normalized, qa };
    if (!best || qa.blocking.length <= best.qa.blocking.length) best = candidate;
    if (!qa.blocking.length) break;
    corrections = qa.corrections;
    if ((await ledger.remaining()) <= 0) {
      issues.push(`Plafond de ${ledger.max} générations atteint : pas de régénération possible.`);
      break;
    }
  }

  if (!best) throw new Error('Aucune image n’a pu être générée.');

  const { image } = await applyLogo(best.normalized, s.format, logo, b);
  const files = await writeFinal(image, path.resolve(dir), s.index);
  return {
    ...files,
    attempts,
    issues: [...issues, ...best.qa.blocking, ...best.qa.minor],
  };
}

