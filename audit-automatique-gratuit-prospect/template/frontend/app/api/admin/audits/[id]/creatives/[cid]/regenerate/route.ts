import { NextResponse } from 'next/server';
import { adminRegenerate } from '@/lib/admin';
import { guard } from '@/lib/admin-guard';

export const dynamic = 'force-dynamic';

export async function POST(req: Request, ctx: { params: Promise<{ id: string; cid: string }> }) {
  const denied = await guard(req);
  if (denied) return denied;
  const { id, cid } = await ctx.params;
  const out = await adminRegenerate(id, cid);
  return NextResponse.json(out.ok ? { ok: true } : { error: out.message ?? 'upstream' }, { status: out.ok ? 200 : out.status });
}
