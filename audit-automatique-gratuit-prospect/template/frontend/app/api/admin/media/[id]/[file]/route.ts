import { promises as fs } from 'node:fs';
import path from 'node:path';
import { adminMedia } from '@/lib/admin';
import { guard } from '@/lib/admin-guard';
import { useFixtures } from '@/lib/env';
import { isValidFile, isValidId } from '@/lib/safe';

export const dynamic = 'force-dynamic';

export async function GET(req: Request, ctx: { params: Promise<{ id: string; file: string }> }) {
  const denied = await guard(req);
  if (denied) return denied;
  const { id, file } = await ctx.params;
  if (!isValidId(id) || !isValidFile(file)) return new Response('Not found', { status: 404 });

  if (useFixtures()) {
    const data = await fs.readFile(path.join(process.cwd(), 'fixtures', 'media', 'originals', path.basename(file))).catch(() => null);
    if (!data) return new Response('Not found', { status: 404 });
    return new Response(new Uint8Array(data), { headers: { 'content-type': 'image/svg+xml', 'cache-control': 'private, no-store' } });
  }

  const res = await adminMedia(id, file);
  if (!res?.ok || !res.body) return new Response('Not found', { status: 404 });
  return new Response(res.body, {
    headers: {
      'content-type': res.headers.get('content-type') ?? 'application/octet-stream',
      'cache-control': 'private, no-store',
    },
  });
}
