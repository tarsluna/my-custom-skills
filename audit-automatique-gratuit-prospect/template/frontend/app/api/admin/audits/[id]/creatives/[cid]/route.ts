import { NextResponse } from 'next/server';
import { adminLock } from '@/lib/admin';
import { guard } from '@/lib/admin-guard';

export const dynamic = 'force-dynamic';

export async function PATCH(req: Request, ctx: { params: Promise<{ id: string; cid: string }> }) {
  const denied = await guard(req);
  if (denied) return denied;
  const { id, cid } = await ctx.params;
  const body = (await req.json().catch(() => null)) as { locked?: unknown } | null;
  if (typeof body?.locked !== 'boolean') return NextResponse.json({ error: 'invalid' }, { status: 400 });
  const out = await adminLock(id, cid, body.locked);
  return NextResponse.json(out.ok ? { ok: true } : { error: out.message ?? 'upstream' }, { status: out.ok ? 200 : out.status });
}
