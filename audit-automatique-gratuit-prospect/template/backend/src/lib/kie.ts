/**
 * Client kie.ai (GPT Image 2.5 Sunburst) et garde-fous de dépense.
 *
 * Règles du contrat :
 * - MAX_GENERATIONS_PER_AUDIT (14 par défaut) par dossier d'audit, compté sur disque ;
 * - réserve de 150 crédits : au-dessous, on arrête et l'erreur reste lisible ;
 * - pool de 4 tâches simultanées au maximum, partagé par tout le processus ;
 * - une tâche qui semble échouer côté client est vérifiée avant toute relance :
 *   chaque taskId est journalisé avant l'attente, et un nouvel appel reprend ce
 *   même taskId au lieu de relancer (et de repayer) une génération.
 */
import { createHash } from 'node:crypto';
import { promises as fs } from 'node:fs';
import path from 'node:path';

const API = 'https://api.kie.ai/api/v1';
const UPLOAD_URL = 'https://kieai.redpandaai.co/api/file-stream-upload';

export const KIE_I2I = 'gpt-image-2-5-sunburst-image-to-image';
export const KIE_T2I = 'gpt-image-2-5-sunburst-text-to-image';
export const IMAGE_COST = 10;
export const CREDIT_RESERVE = Number(process.env.KIE_CREDIT_RESERVE ?? 150);
export const MAX_GENERATIONS_PER_AUDIT = Number(process.env.MAX_GENERATIONS_PER_AUDIT ?? 14);
const POOL_SIZE = 4;
const POLL_MS = Number(process.env.KIE_POLL_MS ?? 5000);
const WAIT_TIMEOUT_MS = Number(process.env.KIE_WAIT_TIMEOUT_MS ?? 8 * 60 * 1000);
const UPLOAD_TTL_MS = 36 * 3600 * 1000;

export type KieErrorKind = 'budget' | 'rejected' | 'task_failed' | 'timeout' | 'network' | 'config';

export class KieError extends Error {
  readonly kind: KieErrorKind;
  readonly detail?: string;
  constructor(kind: KieErrorKind, message: string, detail?: string) {
    super(message);
    this.name = 'KieError';
    this.kind = kind;
    this.detail = detail;
  }
}

function apiKey(): string {
  const k = process.env.KIE_API_KEY;
  if (!k) throw new KieError('config', 'KIE_API_KEY manquante dans l’environnement.');
  return k;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/* ---------- Pool du processus ---------- */

class Semaphore {
  private active = 0;
  private readonly waiting: Array<() => void> = [];
  constructor(private readonly max: number) {}
  async run<T>(fn: () => Promise<T>): Promise<T> {
    if (this.active >= this.max) await new Promise<void>((r) => this.waiting.push(r));
    this.active += 1;
    try {
      return await fn();
    } finally {
      this.active -= 1;
      this.waiting.shift()?.();
    }
  }
}
const pool = new Semaphore(POOL_SIZE);

/* ---------- Mutex par fichier (écritures atomiques du journal) ---------- */

const chains = new Map<string, Promise<unknown>>();
function serialize<T>(key: string, fn: () => Promise<T>): Promise<T> {
  const prev = chains.get(key) ?? Promise.resolve();
  const next = prev.catch(() => undefined).then(fn);
  chains.set(key, next.catch(() => undefined));
  return next;
}

async function readJson<T>(file: string, fallback: T): Promise<T> {
  try {
    return JSON.parse(await fs.readFile(file, 'utf8')) as T;
  } catch {
    return fallback;
  }
}

async function writeJson(file: string, value: unknown): Promise<void> {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const tmp = `${file}.${process.pid}.${Date.now()}.tmp`;
  await fs.writeFile(tmp, JSON.stringify(value, null, 1));
  await fs.rename(tmp, file);
}

/* ---------- Plafond de générations par audit ---------- */

type LedgerState = { count: number; events: { at: string; what: string; key?: string }[] };

export class GenerationLedger {
  private readonly file: string;
  readonly max: number;
  constructor(workDir: string, max: number = MAX_GENERATIONS_PER_AUDIT) {
    this.file = path.join(workDir, '.kie', 'ledger.json');
    this.max = max;
  }
  async used(): Promise<number> {
    return (await readJson<LedgerState>(this.file, { count: 0, events: [] })).count;
  }
  async remaining(): Promise<number> {
    return Math.max(0, this.max - (await this.used()));
  }
  /** Réserve une génération ; lève une erreur lisible si le plafond est atteint. */
  async reserve(key: string): Promise<void> {
    await serialize(this.file, async () => {
      const s = await readJson<LedgerState>(this.file, { count: 0, events: [] });
      if (s.count >= this.max) {
        throw new KieError(
          'budget',
          `Plafond de ${this.max} générations atteint pour cet audit : création arrêtée.`,
        );
      }
      s.count += 1;
      s.events.push({ at: new Date().toISOString(), what: 'reserve', key });
      await writeJson(this.file, s);
    });
  }
  /** Rend une génération non facturée (rejet API, tâche échouée côté fournisseur). */
  async release(key: string): Promise<void> {
    await serialize(this.file, async () => {
      const s = await readJson<LedgerState>(this.file, { count: 0, events: [] });
      s.count = Math.max(0, s.count - 1);
      s.events.push({ at: new Date().toISOString(), what: 'release', key });
      await writeJson(this.file, s);
    });
  }
}

/* ---------- Appels HTTP ---------- */

type ApiEnvelope<T> = { code: number; msg?: string; data: T };

async function apiCall<T>(url: string, init: RequestInit, timeoutMs = 60_000): Promise<ApiEnvelope<T>> {
  const res = await fetch(url, {
    ...init,
    headers: { Authorization: `Bearer ${apiKey()}`, ...(init.headers ?? {}) },
    signal: AbortSignal.timeout(timeoutMs),
  });
  const text = await res.text();
  let parsed: ApiEnvelope<T>;
  try {
    parsed = JSON.parse(text) as ApiEnvelope<T>;
  } catch {
    throw new KieError('network', `Réponse illisible de kie.ai (HTTP ${res.status}).`, text.slice(0, 200));
  }
  if (res.status === 401 || res.status === 403) {
    throw new KieError('config', 'Clé kie.ai refusée.');
  }
  return parsed;
}

export async function kieCredits(): Promise<number> {
  const r = await apiCall<number>(`${API}/chat/credit`, { method: 'GET' });
  if (r.code !== 200 || typeof r.data !== 'number') {
    throw new KieError('network', `Solde kie.ai illisible (${r.code}).`, r.msg);
  }
  return r.data;
}

/** Lève une erreur « budget » lisible si le solde passerait sous la réserve. */
export async function assertCredits(cost = IMAGE_COST): Promise<number> {
  const balance = await kieCredits();
  if (balance - cost < CREDIT_RESERVE) {
    throw new KieError(
      'budget',
      `Crédits kie.ai insuffisants : solde ${Math.floor(balance)}, réserve de ${CREDIT_RESERVE} à conserver. Rechargez le compte avant de relancer l’audit.`,
    );
  }
  return balance;
}

/* ---------- Tâches ---------- */

export type KieTask =
  | { state: 'pending'; raw: string }
  | { state: 'success'; urls: string[] }
  | { state: 'fail'; code: string; message: string };

export async function kieGetTask(taskId: string): Promise<KieTask> {
  const r = await apiCall<{
    state: string;
    resultJson?: string;
    failCode?: string;
    failMsg?: string;
  }>(`${API}/jobs/recordInfo?taskId=${encodeURIComponent(taskId)}`, { method: 'GET' });
  if (r.code !== 200 || !r.data) {
    throw new KieError('network', `Suivi de tâche kie.ai illisible (${r.code}).`, r.msg);
  }
  const d = r.data;
  if (d.state === 'success') {
    const urls: string[] = (JSON.parse(d.resultJson ?? '{}') as { resultUrls?: string[] }).resultUrls ?? [];
    if (!urls.length) return { state: 'fail', code: 'no_output', message: 'Tâche réussie sans image.' };
    return { state: 'success', urls };
  }
  if (d.state === 'fail') {
    return { state: 'fail', code: String(d.failCode ?? ''), message: String(d.failMsg ?? 'échec du modèle') };
  }
  return { state: 'pending', raw: d.state };
}

/** Attend la fin d'une tâche connue. Les erreurs réseau du suivi ne font jamais relancer. */
export async function kieWaitTask(taskId: string, deadlineMs = WAIT_TIMEOUT_MS): Promise<KieTask> {
  const end = Date.now() + deadlineMs;
  let last: KieTask = { state: 'pending', raw: 'init' };
  while (Date.now() < end) {
    try {
      last = await kieGetTask(taskId);
    } catch (e) {
      if (e instanceof KieError && e.kind === 'config') throw e;
      // réseau instable : on continue à interroger la même tâche.
      await sleep(POLL_MS * 2);
      continue;
    }
    if (last.state !== 'pending') return last;
    await sleep(POLL_MS);
  }
  return last;
}

const ASPECT_FALLBACK: Record<string, string> = { '4:5': '3:4' };
const rejectedAspects = new Set<string>();

function normalizeModelError(msg?: string): string {
  return (msg ?? '').toLowerCase();
}

/**
 * Crée une tâche d'image. Ne relance jamais après une réponse ambiguë : seul un
 * rejet explicite de l'API (aucune tâche créée, rien de facturé) permet de réessayer.
 * Retourne aussi le ratio réellement demandé.
 */
async function createImageTask(args: {
  prompt: string;
  urls: string[];
  aspectRatio: string;
  resolution: string;
}): Promise<{ taskId: string; aspectUsed: string }> {
  let aspect = args.aspectRatio;
  if (rejectedAspects.has(aspect) && ASPECT_FALLBACK[aspect]) aspect = ASPECT_FALLBACK[aspect]!;

  for (let attempt = 0; attempt < 4; attempt += 1) {
    const model = args.urls.length ? KIE_I2I : KIE_T2I;
    const input: Record<string, unknown> = {
      prompt: args.prompt,
      aspect_ratio: aspect,
      resolution: args.resolution,
    };
    if (args.urls.length) input.input_urls = args.urls;

    let res: ApiEnvelope<{ taskId?: string }>;
    try {
      res = await apiCall<{ taskId?: string }>(
        `${API}/jobs/createTask`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model, input }),
        },
        90_000,
      );
    } catch (e) {
      if (e instanceof KieError) throw e;
      // On ne peut pas savoir si la requête a abouti : ne pas relancer.
      throw new KieError('network', 'Création de tâche kie.ai sans réponse : pas de relance automatique.');
    }

    if (res.code === 200 && res.data?.taskId) return { taskId: res.data.taskId, aspectUsed: aspect };

    const msg = normalizeModelError(res.msg);
    if (msg.includes('aspect') && ASPECT_FALLBACK[aspect]) {
      rejectedAspects.add(aspect);
      aspect = ASPECT_FALLBACK[aspect]!;
      continue;
    }
    if (res.code === 402 || msg.includes('insufficient') || msg.includes('credit')) {
      throw new KieError('budget', 'Crédits kie.ai insuffisants : rechargez le compte avant de relancer l’audit.', res.msg);
    }
    if (res.code === 429 || msg.includes('rate limit')) {
      await sleep(4000 * (attempt + 1));
      continue;
    }
    throw new KieError('rejected', `Génération refusée par kie.ai (${res.code}).`, res.msg);
  }
  throw new KieError('rejected', 'Génération refusée par kie.ai après plusieurs essais.');
}

/* ---------- Téléversement des références ---------- */

type UploadCache = Record<string, { url: string; at: number }>;

async function urlAlive(url: string): Promise<boolean> {
  try {
    const r = await fetch(url, { method: 'HEAD', signal: AbortSignal.timeout(15_000) });
    return r.ok;
  } catch {
    return false;
  }
}

const CONTENT_TYPES: Record<string, string> = {
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.webp': 'image/webp',
};

export async function kieUpload(filePath: string, workDir: string): Promise<string> {
  const buf = await fs.readFile(filePath);
  const digest = createHash('sha256').update(buf).digest('hex').slice(0, 20);
  const cacheFile = path.join(workDir, '.kie', 'uploads.json');
  const cached = (await readJson<UploadCache>(cacheFile, {}))[digest];
  if (cached && Date.now() - cached.at < UPLOAD_TTL_MS && (await urlAlive(cached.url))) return cached.url;

  const ext = path.extname(filePath).toLowerCase();
  const name = `${digest}${ext || '.jpg'}`;
  const form = new FormData();
  form.set('uploadPath', 'audit');
  form.set('fileName', name);
  form.set('file', new Blob([new Uint8Array(buf)], { type: CONTENT_TYPES[ext] ?? 'application/octet-stream' }), name);

  let res: ApiEnvelope<{ downloadUrl?: string }> | null = null;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      res = await apiCall<{ downloadUrl?: string }>(UPLOAD_URL, { method: 'POST', body: form }, 120_000);
      if (res.data?.downloadUrl) break;
    } catch (e) {
      if (e instanceof KieError && e.kind === 'config') throw e;
    }
    await sleep(2500 * (attempt + 1));
  }
  const url = res?.data?.downloadUrl;
  if (!url) throw new KieError('network', 'Téléversement d’une image de référence impossible.', res?.msg);

  await serialize(cacheFile, async () => {
    const cache = await readJson<UploadCache>(cacheFile, {});
    cache[digest] = { url, at: Date.now() };
    await writeJson(cacheFile, cache);
  });
  return url;
}

/* ---------- Génération avec journal, cache et plafond ---------- */

export type GenerateRequest = {
  prompt: string;
  refs: string[];
  aspectRatio: string;
  resolution?: '1K' | '2K' | '4K';
  workDir: string;
  ledger: GenerationLedger;
  /** Change la clé de cache pour forcer une nouvelle génération. */
  nonce?: string;
};

export type GenerateResult = {
  path: string;
  fromCache: boolean;
  taskId?: string;
  aspectUsed: string;
};

type Journal = { taskId: string; aspectUsed: string; at: string };

async function fileHash(file: string): Promise<string> {
  return createHash('sha256').update(await fs.readFile(file)).digest('hex').slice(0, 20);
}

async function downloadResult(url: string, keyPath: string): Promise<string> {
  let lastErr = '';
  for (let attempt = 0; attempt < 5; attempt += 1) {
    try {
      const r = await fetch(url, { signal: AbortSignal.timeout(120_000) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const buf = Buffer.from(await r.arrayBuffer());
      if (buf.length < 2000) throw new Error('fichier trop petit');
      const ext = (url.split('?')[0]!.match(/\.(png|jpe?g|webp)$/i)?.[1] ?? 'png').toLowerCase();
      const out = `${keyPath}.${ext}`;
      await fs.writeFile(out, buf);
      return out;
    } catch (e) {
      lastErr = e instanceof Error ? e.message : String(e);
      await sleep(3000 * (attempt + 1));
    }
  }
  throw new KieError('network', 'Téléchargement de l’image générée impossible.', lastErr);
}

async function findRaw(keyPath: string): Promise<string | null> {
  for (const ext of ['png', 'jpg', 'jpeg', 'webp']) {
    const p = `${keyPath}.${ext}`;
    try {
      await fs.access(p);
      return p;
    } catch {
      /* suivant */
    }
  }
  return null;
}

/**
 * Génère une image ou reprend ce qui existe déjà pour la même clé
 * (prompt, modèle, ratio, résolution, références) : fichier en cache, sinon
 * tâche déjà lancée dont on vérifie l'état avant toute nouvelle dépense.
 */
export async function generateImage(req: GenerateRequest): Promise<GenerateResult> {
  const resolution = req.resolution ?? '2K';
  const refHashes = await Promise.all(req.refs.map(fileHash));
  const model = req.refs.length ? KIE_I2I : KIE_T2I;
  const key = createHash('sha256')
    .update(JSON.stringify({ v: 1, model, prompt: req.prompt, ratio: req.aspectRatio, resolution, refHashes, nonce: req.nonce ?? '' }))
    .digest('hex')
    .slice(0, 32);
  const rawBase = path.join(req.workDir, '.kie', 'raw', key);
  const journalFile = path.join(req.workDir, '.kie', 'journal', `${key}.json`);
  await fs.mkdir(path.dirname(rawBase), { recursive: true });

  const hit = await findRaw(rawBase);
  if (hit) return { path: hit, fromCache: true, aspectUsed: req.aspectRatio };

  return pool.run(async () => {
    const again = await findRaw(rawBase);
    if (again) return { path: again, fromCache: true, aspectUsed: req.aspectRatio };

    const previous = await readJson<Journal | null>(journalFile, null);
    if (previous?.taskId) {
      const state = await kieWaitTask(previous.taskId, WAIT_TIMEOUT_MS);
      if (state.state === 'success') {
        const out = await downloadResult(state.urls[0]!, rawBase);
        return { path: out, fromCache: true, taskId: previous.taskId, aspectUsed: previous.aspectUsed };
      }
      if (state.state === 'pending') {
        throw new KieError('timeout', `Tâche ${previous.taskId} toujours en cours : attente prolongée, nouvelle tentative plus tard.`);
      }
      // Échec confirmé côté fournisseur : la relance devient légitime.
      await fs.rm(journalFile, { force: true });
    }

    await assertCredits();
    await req.ledger.reserve(key);

    let taskId: string;
    let aspectUsed: string;
    try {
      const urls: string[] = [];
      for (const ref of req.refs) urls.push(await kieUpload(ref, req.workDir));
      ({ taskId, aspectUsed } = await createImageTask({
        prompt: req.prompt,
        urls,
        aspectRatio: req.aspectRatio,
        resolution,
      }));
    } catch (e) {
      // Rejet API explicite : rien n'a été lancé ni facturé.
      if (e instanceof KieError && (e.kind === 'rejected' || e.kind === 'budget' || e.kind === 'config')) {
        await req.ledger.release(key);
      }
      throw e;
    }

    await writeJson(journalFile, { taskId, aspectUsed, at: new Date().toISOString() } satisfies Journal);

    const state = await kieWaitTask(taskId);
    if (state.state === 'pending') {
      // Le journal est conservé : un prochain appel reprend cette tâche sans repayer.
      throw new KieError('timeout', `Tâche ${taskId} non terminée dans le délai : elle sera reprise, pas relancée.`);
    }
    if (state.state === 'fail') {
      await fs.rm(journalFile, { force: true });
      await req.ledger.release(key);
      throw new KieError('task_failed', 'La génération a échoué chez le fournisseur.', `${state.code} ${state.message}`);
    }
    const out = await downloadResult(state.urls[0]!, rawBase);
    return { path: out, fromCache: false, taskId, aspectUsed };
  });
}
