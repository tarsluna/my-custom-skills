import { NextResponse } from 'next/server';
import { adminRerun } from '@/lib/admin';
import { guard } from '@/lib/admin-guard';
import { normalizeDomain } from '@/lib/domain';

export const dynamic = 'force-dynamic';

export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const denied = await guard(req);
  if (denied) return denied;
  const { id } = await ctx.params;
  const body = (await req.json().catch(() => null)) as { domain?: unknown } | null;
  let domain: string | null = null;
  if (typeof body?.domain === 'string') {
    domain = normalizeDomain(body.domain);
    if (!domain) return NextResponse.json({ error: 'Domaine invalide' }, { status: 400 });
  }
  const out = await adminRerun(id, domain);
  return NextResponse.json(out.ok ? { ok: true } : { error: out.message ?? 'upstream' }, { status: out.ok ? 200 : out.status });
}
