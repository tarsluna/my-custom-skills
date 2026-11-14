import { NextResponse } from 'next/server';
import { postChat } from '@/lib/audits';
import { clientIp } from '@/lib/env';
import { isValidToken } from '@/lib/safe';
import type { ChatTurn } from '@/lib/types';

export const dynamic = 'force-dynamic';

const MAX_MESSAGES = 40;
const MAX_CHARS = 500;

function parse(body: unknown): { sessionId: string; messages: ChatTurn[] } | null {
  if (!body || typeof body !== 'object') return null;
  const { sessionId, messages } = body as Record<string, unknown>;
  if (typeof sessionId !== 'string' || !/^[A-Za-z0-9_-]{8,100}$/.test(sessionId)) return null;
  if (!Array.isArray(messages) || messages.length === 0 || messages.length > MAX_MESSAGES) return null;
  const clean: ChatTurn[] = [];
  for (const m of messages) {
    if (!m || typeof m !== 'object') return null;
    const { role, content } = m as Record<string, unknown>;
    if ((role !== 'user' && role !== 'assistant') || typeof content !== 'string') return null;
    const text = content.trim();
    if (!text || text.length > MAX_CHARS) return null;
    clean.push({ role, content: text });
  }
  return { sessionId, messages: clean };
}

export async function POST(req: Request, ctx: { params: Promise<{ token: string }> }) {
  const { token } = await ctx.params;
  if (!isValidToken(token)) return NextResponse.json({ error: 'not_found' }, { status: 404 });

  const body = parse(await req.json().catch(() => null));
  if (!body) return NextResponse.json({ error: 'invalid' }, { status: 400 });
  if (body.messages[body.messages.length - 1].role !== 'user') return NextResponse.json({ error: 'invalid' }, { status: 400 });

  const out = await postChat(token, body, clientIp(req.headers));
  switch (out.kind) {
    case 'ok':
      return NextResponse.json(out.data, { headers: { 'cache-control': 'no-store' } });
    case 'limit':
      return NextResponse.json({ error: 'limit' }, { status: 429 });
    case 'not_found':
      return NextResponse.json({ error: 'not_found' }, { status: 404 });
    default:
      return NextResponse.json({ error: 'upstream' }, { status: 502 });
  }
}
