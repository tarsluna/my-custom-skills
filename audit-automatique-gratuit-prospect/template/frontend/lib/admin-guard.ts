import 'server-only';
import { NextResponse } from 'next/server';
import { isAdmin } from './session';

/** Toute route /api/admin passe ici : session valide, et même origine pour les écritures. */
export async function guard(req: Request): Promise<NextResponse | null> {
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    const origin = req.headers.get('origin');
    const host = req.headers.get('x-forwarded-host') ?? req.headers.get('host');
    if (origin) {
      let ok = false;
      try {
        ok = new URL(origin).host === host;
      } catch {
        ok = false;
      }
      if (!ok) return NextResponse.json({ error: 'forbidden' }, { status: 403 });
    }
  }
  if (!(await isAdmin())) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  return null;
}
