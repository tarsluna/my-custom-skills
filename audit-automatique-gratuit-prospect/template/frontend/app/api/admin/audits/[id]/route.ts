import { NextResponse } from 'next/server';
import { adminDetail } from '@/lib/admin';
import { guard } from '@/lib/admin-guard';

export const dynamic = 'force-dynamic';

export async function GET(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const denied = await guard(req);
  if (denied) return denied;
  const { id } = await ctx.params;
  const audit = await adminDetail(id);
  if (!audit) return NextResponse.json({ error: 'not_found' }, { status: 404 });
  return NextResponse.json({ audit });
}
