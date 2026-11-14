import { mkdir } from 'node:fs/promises';
import sharp from 'sharp';
import { planCreatives, renderCreative, KieError, type CreativeSpec } from '../creative/index.js';
import { GenerationLedger, assertCredits } from '../lib/kie.js';
import { cfg } from '../config.js';
import { niche } from '../niche.js';
import { query, tx } from '../db/pool.js';
import { createLlm, type Llm } from '../lib/llm.js';
import { purgeAuditFiles, registerFile, removeMedia, removeMediaByKinds, workDir } from '../lib/files.js';
import { logStep, newToken, setStatus } from '../audits/service.js';
import { errMsg, log } from '../log.js';
import type { JobRow } from '../jobs/queue.js';
import { crawlSite, type CrawlResult } from './crawl.js';
import { analyzeSite, type SiteAnalysis } from './extract.js';
import { buildPalette, colorsFromScreenshot, extractFonts, type Palette } from './palette.js';
import { findLogoCandidates, resolveLogo } from './logo.js';
import { extractProjects, type ProjectItem } from './projects.js';
import { findCompetitors, type CompetitorResult } from './competitors.js';
import { generateSetterContent } from './setterContent.js';
import { FatalAuditError } from './errors.js';

export type AuditRow = {
  id: string;
  token: string | null;
  status: string;
  domain: string | null;
  analysis: (SiteAnalysis & { logoFile?: string; screenshotFile?: string | null }) | null;
  brand: BrandProfileLike | null;
  competitors_meta: { radiusKm: number | null; widened: boolean; publicInsights: string[] } | null;
  insights: CompetitorResult['insights'] | null;
  setter: unknown;
  started_at: Date | null;
  generations_used: number;
};

export type BrandProfileLike = Parameters<typeof planCreatives>[0];

export async function loadAudit(id: string): Promise<AuditRow> {
  const res = await query<AuditRow>('SELECT * FROM audits WHERE id=$1', [id]);
  if (!res.rows[0]) throw new FatalAuditError('Audit introuvable.');
  return res.rows[0];
}

/** Réserve une place dans le plafond quotidien ; un audit déjà commencé (reprise) la garde. */
export async function takeDailySlot(auditId: string): Promise<boolean> {
  return tx(async (client) => {
    await query(`SELECT pg_advisory_xact_lock(hashtext('audit-daily-cap'))`, [], client);
    const row = await query<{ started_at: Date | null }>('SELECT started_at FROM audits WHERE id=$1 FOR UPDATE', [auditId], client);
    if (!row.rows[0]) return false;
    if (row.rows[0].started_at) return true;
    const count = await query<{ n: number }>(
      `SELECT count(*)::int AS n FROM audits WHERE started_at >= (date_trunc('day', now() AT TIME ZONE 'Europe/Paris') AT TIME ZONE 'Europe/Paris')`,
      [],
      client,
    );
    if ((count.rows[0]?.n ?? 0) >= cfg().MAX_AUDITS_PER_DAY) return false;
    await query('UPDATE audits SET started_at=now() WHERE id=$1', [auditId], client);
    return true;
  });
}

export async function msUntilNextParisDay(): Promise<number> {
  const res = await query<{ ms: number }>(
    `SELECT (extract(epoch FROM ((date_trunc('day', now() AT TIME ZONE 'Europe/Paris') + interval '1 day') AT TIME ZONE 'Europe/Paris') - now()) * 1000)::float8 AS ms`,
  );
  return Math.max(60_000, Math.round(res.rows[0]?.ms ?? 3_600_000));
}

export async function stageAnalysis(audit: AuditRow, llm: Llm): Promise<AuditRow> {
  await setStatus(audit.id, 'analyzing');
  await logStep(audit.id, 'analyse', 'start', `Analyse de ${audit.domain}`);
  await removeMediaByKinds(audit.id, ['logo', 'screenshot', 'project']);

  const crawl = await crawlSite(audit.domain!);
  await logStep(audit.id, 'crawl', 'ok', `${crawl.pages.length} pages lues`, { pages: crawl.pages.map((p) => p.url), notes: crawl.notes });

  const analysis = await analyzeSite(crawl.pages, audit.domain!, llm);
  await logStep(audit.id, 'extraction', 'ok', `${analysis.businessName} (${analysis.professionLabel})`, { city: analysis.city, facts: analysis.facts.length });

  const capture = crawl.screenshot ? await colorsFromScreenshot(crawl.screenshot) : [];
  const palette = buildPalette({ computed: crawl.computed, cssTexts: crawl.cssTexts, capture });
  const fonts = extractFonts(crawl.computed, crawl.cssTexts, crawl.pages[0].html);

  let screenshotFile: string | null = null;
  if (crawl.screenshot) {
    const saved = await registerFile(audit.id, 'screenshot', crawl.screenshot, 'jpg');
    screenshotFile = saved.fileName;
  }

  const logo = await resolveLogo(findLogoCandidates(crawl.pages[0].html, crawl.pages[0].url), analysis.businessName, palette.text);
  const savedLogo = await registerFile(audit.id, 'logo', logo.png, 'png');
  await logStep(audit.id, 'logo', 'ok', logo.isFallback ? 'Logotype typographique généré' : `Logo extrait (${logo.source})`);

  const projects = await extractProjects(crawl.pages, audit.id, llm);
  await logStep(audit.id, 'projets', 'ok', `${projects.length} réalisations publiées recopiées`);

  const setter = await generateSetterContent(analysis, llm);
  await saveAnalysis(audit, crawl, analysis, palette, fonts, savedLogo.fileName, savedLogo.path, logo.isFallback, screenshotFile, projects, setter);
  return loadAudit(audit.id);
}

/** Relit seulement les réalisations du site : aucune image générée, donc aucun crédit. */
export async function refreshProjects(auditId: string): Promise<number> {
  const audit = await loadAudit(auditId);
  const crawl = await crawlSite(audit.domain as string);
  const projects = await extractProjects(crawl.pages, audit.id, createLlm({ auditId: audit.id }));
  await tx(async (client) => {
    await query('DELETE FROM projects WHERE audit_id=$1', [audit.id], client);
    for (const [i, p] of projects.entries()) {
      await query('INSERT INTO projects (audit_id, ordering, title, location, image_file, source_url) VALUES ($1,$2,$3,$4,$5,$6)', [audit.id, i, p.title, p.location, p.imageFile, p.sourceUrl], client);
    }
    await query(`UPDATE audits SET brand=jsonb_set(COALESCE(brand,'{}'::jsonb),'{projectImages}',$2::jsonb), updated_at=now() WHERE id=$1`, [audit.id, JSON.stringify(projects.map((p) => ({ path: p.imagePath, title: p.title })))], client);
  });
  await logStep(audit.id, 'projets', 'ok', `${projects.length} réalisations relues`);
  return projects.length;
}

async function saveAnalysis(
  audit: AuditRow,
  crawl: CrawlResult,
  analysis: SiteAnalysis,
  palette: Palette,
  fonts: string[],
  logoFile: string,
  logoPath: string,
  logoIsFallback: boolean,
  screenshotFile: string | null,
  projects: ProjectItem[],
  setter: unknown,
): Promise<void> {
  const brand: BrandProfileLike = {
    businessName: analysis.businessName,
    profession: analysis.profession,
    professionLabel: analysis.professionLabel,
    city: analysis.city,
    region: analysis.region,
    specialties: analysis.specialties,
    projectTypes: analysis.projectTypes,
    summary: analysis.summary,
    tone: analysis.tone,
    palette,
    fonts,
    logoPath,
    logoIsFallback,
    projectImages: projects.map((p) => ({ path: p.imagePath, title: p.title })),
    facts: analysis.facts,
  };
  await tx(async (client) => {
    await query('DELETE FROM projects WHERE audit_id=$1', [audit.id], client);
    for (const [i, p] of projects.entries()) {
      await query('INSERT INTO projects (audit_id, ordering, title, location, image_file, source_url) VALUES ($1,$2,$3,$4,$5,$6)', [audit.id, i, p.title, p.location, p.imageFile, p.sourceUrl], client);
    }
    await query(
      `UPDATE audits SET analysis=$2, brand=$3, setter=$4, website_url=$5, token=COALESCE(token,$6), updated_at=now() WHERE id=$1`,
      [
        audit.id,
        JSON.stringify({ ...analysis, logoFile, screenshotFile }),
        JSON.stringify(brand),
        JSON.stringify(setter),
        crawl.websiteUrl,
        newToken(analysis.businessName),
      ],
      client,
    );
  });
  await logStep(audit.id, 'analyse', 'ok', 'Analyse terminée');
}

export async function stageCompetitors(audit: AuditRow, llm: Llm): Promise<AuditRow> {
  await setStatus(audit.id, 'ads');
  await logStep(audit.id, 'concurrents', 'start', 'Recherche dans la bibliothèque publicitaire');
  await removeMediaByKinds(audit.id, ['competitor_image', 'competitor_logo']);
  const result = await findCompetitors(audit.analysis!, audit.id, llm);
  await tx(async (client) => {
    await query('DELETE FROM competitors WHERE audit_id=$1', [audit.id], client);
    for (const [i, c] of result.items.entries()) {
      await query(
        `INSERT INTO competitors (audit_id, ordering, page_id, page_name, ad_archive_id, ad_library_url, city, distance_km, active_days, title, body, why, logo_file, image_file)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)`,
        [audit.id, i, c.pageId, c.pageName, c.adArchiveId, c.adLibraryUrl, c.city, c.distanceKm, c.activeDays, c.title, c.body, c.why, c.logoFile, c.imageFile],
        client,
      );
    }
    await query(`UPDATE audits SET competitors_meta=$2, insights=$3, updated_at=now() WHERE id=$1`, [
      audit.id,
      JSON.stringify({ radiusKm: result.radiusKm, widened: result.widened, publicInsights: result.publicInsights }),
      JSON.stringify(result.insights),
    ], client);
  });
  await logStep(audit.id, 'concurrents', 'ok', `${result.items.length} concurrents retenus`, { radiusKm: result.radiusKm, widened: result.widened });
  return loadAudit(audit.id);
}

type CreativeRow = {
  id: string;
  audit_id: string;
  idx: number;
  concept: string;
  format: '4:5' | '9:16' | '1:1';
  angle: string | null;
  headline: string | null;
  primary_text: string | null;
  bullets: string[];
  cta: string | null;
  prompt: string;
  reference_paths: string[];
  locked: boolean;
  status: string;
  original_file: string | null;
  display_file: string | null;
  blur_file: string | null;
  thumb_file: string | null;
};

function specFromRow(row: CreativeRow): CreativeSpec {
  return {
    index: row.idx,
    concept: row.concept,
    format: row.format,
    angle: row.angle ?? '',
    headline: row.headline ?? '',
    primaryText: row.primary_text ?? '',
    bullets: row.bullets,
    cta: row.cta ?? '',
    prompt: row.prompt,
    referencePaths: row.reference_paths,
    locked: row.locked,
  };
}

/** Les meilleures restent nettes : le module les désigne, le serveur garantit le compte. */
export function enforceLockSplit(specs: CreativeSpec[]): CreativeSpec[] {
  const visible = niche().creatives.visible;
  const unlocked = specs.filter((s) => !s.locked).length;
  if (unlocked === visible) return specs;
  return specs.map((s, i) => ({ ...s, locked: i >= visible }));
}

async function planIfNeeded(audit: AuditRow, llm: Llm): Promise<void> {
  const existing = await query<{ n: number }>('SELECT count(*)::int AS n FROM creatives WHERE audit_id=$1', [audit.id]);
  if ((existing.rows[0]?.n ?? 0) > 0) return;
  const brand = audit.brand!;
  const insights = audit.insights ?? { hooks: [], angles: [], styleNotes: [], saturated: [] };
  const specs = enforceLockSplit(await planCreatives(brand, insights, llm));
  if (specs.length !== 10) throw new Error(`Le module créatif a planifié ${specs.length} créatives au lieu de 10.`);
  await tx(async (client) => {
    await query('DELETE FROM creatives WHERE audit_id=$1', [audit.id], client);
    for (const s of specs) {
      await query(
        `INSERT INTO creatives (audit_id, idx, concept, format, angle, headline, primary_text, bullets, cta, prompt, reference_paths, locked)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)`,
        [audit.id, s.index, s.concept, s.format, s.angle, s.headline, s.primaryText, JSON.stringify(s.bullets), s.cta, s.prompt, JSON.stringify(s.referencePaths), s.locked],
        client,
      );
    }
  });
  await logStep(audit.id, 'planification', 'ok', `${specs.length} créatives planifiées`);
}

function ledgerFor(auditId: string): GenerationLedger {
  return new GenerationLedger(creativesDir(auditId), cfg().MAX_GENERATIONS_PER_AUDIT);
}

/** Un seul dossier par audit : c'est lui qui porte le plafond de générations du module créatif. */
export function creativesDir(auditId: string): string {
  return workDir(auditId, 'creatives');
}

async function syncGenerationCount(auditId: string): Promise<void> {
  await query('UPDATE audits SET generations_used=$2, updated_at=now() WHERE id=$1', [auditId, await ledgerFor(auditId).used()]);
}

async function storeRender(row: CreativeRow, render: { imagePath: string; blurPath: string; thumbPath: string; attempts: number; issues: string[] }): Promise<void> {
  const original = await registerFile(row.audit_id, 'creative_original', { path: render.imagePath, move: true }, 'jpg', { creativeId: row.id });
  const displayBuf = await sharp(original.path).resize({ width: 1600, height: 1600, fit: 'inside', withoutEnlargement: true }).webp({ quality: 88 }).toBuffer();
  const display = await registerFile(row.audit_id, 'creative_display', displayBuf, 'webp', { creativeId: row.id });
  const blur = await registerFile(row.audit_id, 'creative_blur', { path: render.blurPath, move: true }, 'webp', { creativeId: row.id });
  const thumb = await registerFile(row.audit_id, 'creative_thumb', { path: render.thumbPath, move: true }, 'webp', { creativeId: row.id });
  await query(
    `UPDATE creatives SET status='ready', original_file=$2, display_file=$3, blur_file=$4, thumb_file=$5, attempts=$6, issues=$7, last_error=NULL, updated_at=now() WHERE id=$1`,
    [row.id, original.fileName, display.fileName, blur.fileName, thumb.fileName, render.attempts, JSON.stringify(render.issues)],
  );
}

/** Erreur budget (plafond ou crédits) : arrêt net, message lisible. */
function fatalIfBudget(error: unknown): void {
  if (error instanceof KieError && (error.kind === 'budget' || error.kind === 'config')) throw new FatalAuditError(error.message);
}

const RENDER_CONCURRENCY = 4;

async function stageCreatives(audit: AuditRow, llm: Llm, signal: AbortSignal): Promise<void> {
  await setStatus(audit.id, 'creatives');
  await logStep(audit.id, 'creatives', 'start', 'Génération des créatives');
  await planIfNeeded(audit, llm);
  await mkdir(creativesDir(audit.id), { recursive: true });

  try {
    await assertCredits();
  } catch (e) {
    fatalIfBudget(e);
    throw e;
  }

  const pending = (await query<CreativeRow>(`SELECT * FROM creatives WHERE audit_id=$1 AND status<>'ready' ORDER BY idx`, [audit.id])).rows;
  let failed = 0;
  let cursor = 0;

  const worker = async () => {
    while (cursor < pending.length && !signal.aborted) {
      const row = pending[cursor];
      cursor += 1;
      try {
        const render = await renderCreative(specFromRow(row), audit.brand!, creativesDir(audit.id), llm, { maxGenerations: cfg().MAX_GENERATIONS_PER_AUDIT });
        await storeRender(row, render);
        await logStep(audit.id, 'creatives', 'info', `Créative ${row.idx} prête`, { attempts: render.attempts, issues: render.issues });
      } catch (e) {
        await syncGenerationCount(audit.id);
        fatalIfBudget(e);
        failed += 1;
        await query(`UPDATE creatives SET status='failed', last_error=$2, updated_at=now() WHERE id=$1`, [row.id, errMsg(e).slice(0, 1000)]);
        await logStep(audit.id, 'creatives', 'error', `Créative ${row.idx} en échec : ${errMsg(e)}`);
      }
    }
  };
  try {
    await Promise.all(Array.from({ length: Math.min(RENDER_CONCURRENCY, pending.length) }, worker));
  } finally {
    await syncGenerationCount(audit.id).catch(() => undefined);
  }

  if (failed > 0) throw new Error(`${failed} créatives n'ont pas pu être générées.`);
  const remaining = await query<{ n: number }>(`SELECT count(*)::int AS n FROM creatives WHERE audit_id=$1 AND status<>'ready'`, [audit.id]);
  if ((remaining.rows[0]?.n ?? 0) > 0) throw new Error('Des créatives restent à générer.');
  await logStep(audit.id, 'creatives', 'ok', '10 créatives prêtes');
}

/** Exécute ou reprend un audit : chaque étape enregistrée n'est jamais refaite. */
export async function runAudit(job: JobRow, signal: AbortSignal): Promise<'done' | 'deferred'> {
  const auditId = job.audit_id;
  const llm = createLlm({ auditId, signal });

  if (job.payload.purge) {
    await purgeAuditFiles(auditId);
    await query(`UPDATE jobs SET payload = payload - 'purge' WHERE id=$1`, [job.id]);
  }

  let audit = await loadAudit(auditId);
  if (!audit.domain) {
    await setStatus(auditId, 'needs_domain');
    return 'done';
  }
  if (!(await takeDailySlot(auditId))) {
    await logStep(auditId, 'plafond', 'info', `Plafond de ${cfg().MAX_AUDITS_PER_DAY} audits par jour atteint : reporté au lendemain`);
    return 'deferred';
  }

  if (!audit.analysis) audit = await stageAnalysis(audit, llm);
  if (!audit.competitors_meta) audit = await stageCompetitors(audit, llm);

  await stageCreatives(audit, llm, signal);

  await query(`UPDATE audits SET status='ready', ready_at=COALESCE(ready_at, now()), error=NULL, updated_at=now() WHERE id=$1`, [auditId]);
  await logStep(auditId, 'pret', 'ok', 'Audit prêt');
  log.info('audit prêt', { auditId });
  return 'done';
}

/** Régénère une créative à la demande de l'admin, sur le même plafond de générations. */
export async function regenerateCreative(job: JobRow, signal: AbortSignal): Promise<void> {
  const auditId = job.audit_id;
  const creativeId = String(job.payload.creativeId ?? '');
  const llm = createLlm({ auditId, signal });
  const audit = await loadAudit(auditId);
  if (!audit.brand) throw new FatalAuditError('Audit non analysé : régénération impossible.');
  const res = await query<CreativeRow>('SELECT * FROM creatives WHERE id=$1 AND audit_id=$2', [creativeId, auditId]);
  const row = res.rows[0];
  if (!row) throw new FatalAuditError('Créative introuvable.');
  try {
    await assertCredits();
  } catch (e) {
    fatalIfBudget(e);
    throw e;
  }
  await mkdir(creativesDir(auditId), { recursive: true });
  let render;
  try {
    render = await renderCreative(specFromRow(row), audit.brand, creativesDir(auditId), llm, { force: true, maxGenerations: cfg().MAX_GENERATIONS_PER_AUDIT });
  } catch (e) {
    fatalIfBudget(e);
    throw e;
  } finally {
    await syncGenerationCount(auditId).catch(() => undefined);
  }
  const oldFiles = [row.original_file, row.display_file, row.blur_file, row.thumb_file].filter((f): f is string => Boolean(f));
  await storeRender(row, render);
  await removeMedia(oldFiles);
  await logStep(auditId, 'regeneration', 'ok', `Créative ${row.idx} régénérée`, { attempts: render.attempts, issues: render.issues });
}
