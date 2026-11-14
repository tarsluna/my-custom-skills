import { niche } from '../niche.js';
import { readFile } from 'node:fs/promises';
import sharp from 'sharp';
import { cfg } from '../config.js';
import { errMsg, log } from '../log.js';
import { recordCost } from './costs.js';

/** Interface partagée avec le module créatif (contrat §Interface). */
export type Llm = {
  json<T>(a: { system: string; user: string; images?: string[] }): Promise<T>;
  text(a: { system: string; user: string; images?: string[] }): Promise<string>;
};

type Part = { type: 'text'; text: string } | { type: 'image_url'; image_url: { url: string } };

async function toImagePart(ref: string): Promise<Part | null> {
  if (ref.startsWith('http://') || ref.startsWith('https://') || ref.startsWith('data:')) return { type: 'image_url', image_url: { url: ref } };
  try {
    const raw = await readFile(ref);
    const buf = await sharp(raw).rotate().resize({ width: 1280, height: 1280, fit: 'inside', withoutEnlargement: true }).jpeg({ quality: 82 }).toBuffer();
    return { type: 'image_url', image_url: { url: `data:image/jpeg;base64,${buf.toString('base64')}` } };
  } catch (e) {
    log.warn('image illisible pour le LLM', { path: ref, error: errMsg(e) });
    return null;
  }
}

async function buildContent(user: string, images?: string[]): Promise<string | Part[]> {
  if (!images?.length) return user;
  const parts: Part[] = [{ type: 'text', text: user }];
  for (const ref of images.slice(0, 8)) {
    const part = await toImagePart(ref);
    if (part) parts.push(part);
  }
  return parts;
}

class LlmHttpError extends Error {
  constructor(message: string, readonly retryable: boolean) {
    super(message);
  }
}

async function callModel(model: string, system: string, content: string | Part[], jsonMode: boolean, auditId: string | null, signal?: AbortSignal): Promise<string> {
  const body: Record<string, unknown> = {
    model,
    temperature: 0.4,
    max_tokens: 6000,
    usage: { include: true },
    messages: [
      { role: 'system', content: system },
      { role: 'user', content },
    ],
  };
  if (jsonMode) body.response_format = { type: 'json_object' };
  const timeoutSignal = AbortSignal.timeout(120_000);
  const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${cfg().OPENROUTER_API_KEY}`,
      'content-type': 'application/json',
      'http-referer': niche().operator.websiteUrl,
      'x-title': `${niche().operator.name} Audit`,
    },
    body: JSON.stringify(body),
    signal: signal ? AbortSignal.any([signal, timeoutSignal]) : timeoutSignal,
  });
  if (!res.ok) {
    const detail = (await res.text().catch(() => '')).slice(0, 300);
    throw new LlmHttpError(`OpenRouter ${res.status} sur ${model} : ${detail}`, res.status === 429 || res.status >= 500 || res.status === 402 || res.status === 408);
  }
  const data = (await res.json()) as any;
  const usage = data?.usage;
  if (usage) void recordCost({ auditId, provider: 'openrouter', detail: model, quantity: Number(usage.total_tokens ?? 0), usd: typeof usage.cost === 'number' ? usage.cost : null });
  const out = data?.choices?.[0]?.message?.content;
  const text = Array.isArray(out) ? out.map((p: any) => p?.text ?? '').join('') : out;
  if (typeof text !== 'string' || !text.trim()) throw new LlmHttpError(`Réponse vide de ${model}`, true);
  return text;
}

/** Extrait l'objet JSON d'une réponse, y compris entourée de ```json ou de texte. */
export function parseJsonLoose<T>(text: string): T {
  const trimmed = text.trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '');
  try {
    return JSON.parse(trimmed) as T;
  } catch {
    const start = trimmed.search(/[\[{]/);
    const last = Math.max(trimmed.lastIndexOf('}'), trimmed.lastIndexOf(']'));
    if (start >= 0 && last > start) return JSON.parse(trimmed.slice(start, last + 1)) as T;
    throw new Error('JSON introuvable dans la réponse du modèle');
  }
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export function createLlm(opts: { auditId?: string | null; signal?: AbortSignal } = {}): Llm {
  const auditId = opts.auditId ?? null;

  async function complete(a: { system: string; user: string; images?: string[] }, jsonMode: boolean): Promise<string> {
    const content = await buildContent(a.user, a.images);
    const models = [cfg().LLM_MODEL, cfg().LLM_FALLBACK];
    let lastError: unknown;
    for (const model of models) {
      for (let attempt = 0; attempt < 2; attempt += 1) {
        try {
          const text = await callModel(model, a.system, content, jsonMode, auditId, opts.signal);
          if (jsonMode) parseJsonLoose(text);
          return text;
        } catch (e) {
          lastError = e;
          if (opts.signal?.aborted) throw e;
          log.warn('appel LLM en échec', { model, attempt, error: errMsg(e) });
          if (e instanceof LlmHttpError && !e.retryable) break;
          await sleep(1500 * (attempt + 1));
        }
      }
    }
    throw new Error(`LLM indisponible : ${errMsg(lastError)}`);
  }

  return {
    async json<T>(a: { system: string; user: string; images?: string[] }): Promise<T> {
      const text = await complete(a, true);
      return parseJsonLoose<T>(text);
    },
    async text(a: { system: string; user: string; images?: string[] }): Promise<string> {
      return complete(a, false);
    },
  };
}
