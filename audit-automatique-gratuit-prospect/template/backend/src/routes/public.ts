import { readFile } from 'node:fs/promises';
import { Hono, type Context, type MiddlewareHandler } from 'hono';
import { z } from 'zod';
import { cfg } from '../config.js';
import { query } from '../db/pool.js';
import { chatClosing, answerChat, type ChatMessage } from '../chat/assistant.js';
import { isPubliclyServable, type MediaKind } from '../lib/files.js';
import { createLlm } from '../lib/llm.js';
import { clientIp, hit } from '../lib/rateLimit.js';
import { errMsg, log } from '../log.js';
import { loadPublicBundle, operatorView, toPublicAudit } from './publicView.js';
import type { SiteAnalysis } from '../pipeline/extract.js';

const TOKEN = /^[a-z0-9-]{1,50}-[A-Za-z0-9_-]{22}$/;
const FILE = /^[a-f0-9]{32}\.(png|jpe?g|webp)$/;

const ChatBody = z.object({
  sessionId: z.string().regex(/^[A-Za-z0-9_-]{8,100}$/),
  messages: z
    .array(z.object({ role: z.enum(['user', 'assistant']), content: z.string().trim().min(1) }))
    .min(1),
});

export function rateLimit(name: string, limit: number, windowMs: number): MiddlewareHandler {
  return async (c, next) => {
    if (!hit(`${name}:${clientIp(c.req.raw.headers)}`, limit, windowMs)) return c.json({ error: 'Trop de requêtes' }, 429);
    await next();
  };
}

export const publicRoutes = new Hono();

/** Ce que le front doit savoir sans audit : nom de l'opérateur, thème, titres d'accueil. */
publicRoutes.get('/public/config', rateLimit('public-config', 300, 60_000), (c) => c.json(operatorView()));

publicRoutes.get('/public/audits/:token', rateLimit('public-read', 180, 60_000), async (c) => {
  const token = c.req.param('token');
  if (!TOKEN.test(token)) return c.json({ error: 'Audit introuvable' }, 404);
  const bundle = await loadPublicBundle(token);
  if (!bundle) return c.json({ error: 'Audit introuvable' }, 404);
  return c.json(toPublicAudit(bundle));
});

publicRoutes.post('/public/audits/:token/chat', async (c) => {
  const ip = clientIp(c.req.raw.headers);
  const conf = cfg();
  if (!hit(`chat-min:${ip}`, conf.CHAT_RATE_PER_MINUTE, 60_000) || !hit(`chat-day:${ip}`, conf.CHAT_RATE_PER_MINUTE * 40, 86_400_000)) return c.json({ error: 'Trop de messages' }, 429);

  const token = c.req.param('token');
  if (!TOKEN.test(token)) return c.json({ error: 'Audit introuvable' }, 404);
  const parsed = ChatBody.safeParse(await c.req.json().catch(() => null));
  if (!parsed.success) return c.json({ error: 'Requête invalide' }, 400);
  const { sessionId } = parsed.data;
  const messages: ChatMessage[] = parsed.data.messages;
  if (messages.length > conf.CHAT_MAX_MESSAGES_PER_SESSION || messages.some((m) => m.content.length > conf.CHAT_MAX_MESSAGE_LENGTH) || messages[messages.length - 1].role !== 'user') {
    return c.json({ error: 'Requête invalide' }, 400);
  }

  const res = await query<{ id: string; status: string; analysis: SiteAnalysis | null }>('SELECT id, status, analysis FROM audits WHERE token=$1', [token]);
  const audit = res.rows[0];
  if (!audit) return c.json({ error: 'Audit introuvable' }, 404);
  if (audit.status !== 'ready' || !audit.analysis) return c.json({ error: 'Audit indisponible' }, 409);

  // Compteurs côté serveur : la longueur envoyée par le navigateur ne suffit pas à plafonner une session.
  const session = await query(
    `INSERT INTO chat_sessions (audit_id, session_id, messages) VALUES ($1,$2,2)
     ON CONFLICT (audit_id, session_id) DO UPDATE SET messages=chat_sessions.messages+2, updated_at=now()
     WHERE chat_sessions.messages+2 <= $3 RETURNING messages`,
    [audit.id, sessionId, conf.CHAT_MAX_MESSAGES_PER_SESSION],
  );
  if ((session.rowCount ?? 0) === 0) return c.json(chatClosing());

  const daily = await query(
    `INSERT INTO chat_daily (day, audit_id, count) VALUES ((now() AT TIME ZONE 'Europe/Paris')::date, $1, 1)
     ON CONFLICT (day, audit_id) DO UPDATE SET count=chat_daily.count+1 WHERE chat_daily.count < $2 RETURNING count`,
    [audit.id, conf.CHAT_MAX_PER_AUDIT_PER_DAY],
  );
  if ((daily.rowCount ?? 0) === 0) return c.json({ error: 'Trop de messages aujourd’hui' }, 429);

  const projects = await query<{ title: string }>('SELECT title FROM projects WHERE audit_id=$1 ORDER BY ordering', [audit.id]);
  try {
    const reply = await answerChat(audit.analysis, projects.rows.map((p) => p.title), messages, createLlm({ auditId: audit.id }));
    return c.json(reply);
  } catch (e) {
    log.warn('assistant indisponible', { error: errMsg(e) });
    return c.json({ error: 'Assistant indisponible' }, 503);
  }
});

const mediaRateLimit = rateLimit('public-media', 900, 60_000);

publicRoutes.get('/media/:token/:file', mediaRateLimit, async (c) => {
  const token = c.req.param('token');
  const file = c.req.param('file');
  if (!TOKEN.test(token) || !FILE.test(file)) return c.json({ error: 'Introuvable' }, 404);
  const res = await query<{ path: string; content_type: string; kind: MediaKind; locked: boolean | null }>(
    `SELECT m.path, m.content_type, m.kind, cr.locked
     FROM media m JOIN audits a ON a.id=m.audit_id LEFT JOIN creatives cr ON cr.id=m.creative_id
     WHERE m.file_name=$1 AND a.token=$2`,
    [file, token],
  );
  const row = res.rows[0];
  if (!row || !isPubliclyServable(row.kind, row.locked)) return c.json({ error: 'Introuvable' }, 404);
  return serveFile(c, row.path, row.content_type);
});

export async function serveFile(c: Context, filePath: string, contentType: string) {
  try {
    const data = await readFile(filePath);
    return c.body(new Uint8Array(data), 200, {
      'Content-Type': contentType,
      'Cache-Control': 'private, max-age=300',
      'X-Content-Type-Options': 'nosniff',
    });
  } catch {
    return c.json({ error: 'Introuvable' }, 404);
  }
}
