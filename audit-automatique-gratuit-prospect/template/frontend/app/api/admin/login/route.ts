import { NextResponse } from 'next/server';
import { clientIp } from '@/lib/env';
import {
  clearLoginFailures,
  COOKIE,
  createSessionValue,
  loginAllowed,
  passwordMatches,
  recordLoginFailure,
  sessionCookieOptions,
} from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  const ip = clientIp(req.headers);
  if (!loginAllowed(ip)) return NextResponse.json({ error: 'too_many' }, { status: 429 });

  const body = (await req.json().catch(() => null)) as { password?: unknown } | null;
  const password = typeof body?.password === 'string' ? body.password.slice(0, 200) : '';

  if (!passwordMatches(password)) {
    recordLoginFailure(ip);
    await new Promise((r) => setTimeout(r, 450));
    return NextResponse.json({ error: 'invalid' }, { status: 401 });
  }
  const value = createSessionValue();
  if (!value) return NextResponse.json({ error: 'not_configured' }, { status: 500 });

  clearLoginFailures(ip);
  const res = NextResponse.json({ ok: true });
  res.cookies.set(COOKIE, value, sessionCookieOptions);
  return res;
}
