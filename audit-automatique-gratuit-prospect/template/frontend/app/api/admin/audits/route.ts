import { NextResponse } from 'next/server';
import { adminCreate, adminList, adminStats } from '@/lib/admin';
import { guard } from '@/lib/admin-guard';
import { normalizeDomain } from '@/lib/domain';

export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  const denied = await guard(req);
  if (denied) return denied;
  const url = new URL(req.url);
  const [audits, stats] = await Promise.all([adminList(url.searchParams.get('status'), url.searchParams.get('q')), adminStats()]);
  if (!audits) return NextResponse.json({ error: 'upstream' }, { status: 502 });
  return NextResponse.json({ audits, stats });
}

export async function POST(req: Request) {
  const denied = await guard(req);
  if (denied) return denied;
  const body = (await req.json().catch(() => null)) as { domain?: unknown; contact?: { name?: unknown; email?: unknown } } | null;
  const domain = typeof body?.domain === 'string' ? normalizeDomain(body.domain) : null;
  if (!domain) return NextResponse.json({ error: 'invalid_domain' }, { status: 400 });
  const name = typeof body?.contact?.name === 'string' ? body.contact.name.trim().slice(0, 120) : '';
  const email = typeof body?.contact?.email === 'string' ? body.contact.email.trim().slice(0, 200) : '';
  const contact = name || email ? { ...(name ? { name } : {}), ...(email ? { email } : {}) } : null;
  const out = await adminCreate(domain, contact);
  return NextResponse.json(out.ok ? { ok: true, audit: out.data ?? null } : { error: out.message ?? 'upstream' }, { status: out.ok ? 200 : out.status });
}
