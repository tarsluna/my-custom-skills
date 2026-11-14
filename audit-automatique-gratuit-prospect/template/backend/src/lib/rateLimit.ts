import { timingSafeEqual } from 'node:crypto';

/** Fenêtre glissante simple en mémoire : le service tourne en un seul exemplaire. */
const buckets = new Map<string, number[]>();
let lastSweep = 0;

export function hit(key: string, limit: number, windowMs: number, now: number = Date.now()): boolean {
  const start = now - windowMs;
  const list = (buckets.get(key) ?? []).filter((t) => t > start);
  const allowed = list.length < limit;
  if (allowed) list.push(now);
  buckets.set(key, list);
  if (now - lastSweep > 60_000) {
    lastSweep = now;
    for (const [k, v] of buckets) if (!v.some((t) => t > now - 3_600_000)) buckets.delete(k);
  }
  return allowed;
}

export function clearRateLimits() {
  buckets.clear();
}

/** Derrière le proxy Next, l'IP vue ici est celle de Vercel : la vraie n'est crue que si le proxy présente la clé partagée. */
function trustedVisitorIp(headers: { get(name: string): string | null | undefined }): string | null {
  const ip = headers.get('x-visitor-ip')?.trim();
  const given = headers.get('x-proxy-key');
  const expected = process.env.ADMIN_API_KEY;
  if (!ip || !given || !expected) return null;
  const a = Buffer.from(given), b = Buffer.from(expected);
  return a.length === b.length && timingSafeEqual(a, b) ? ip.slice(0, 64) : null;
}

export function clientIp(headers: { get(name: string): string | null | undefined }): string {
  const visitor = trustedVisitorIp(headers);
  if (visitor) return visitor;
  const real = headers.get('x-real-ip');
  if (real) return real.trim();
  const forwarded = headers.get('x-forwarded-for');
  if (forwarded) {
    const parts = forwarded.split(',').map((s) => s.trim()).filter(Boolean);
    return parts[parts.length - 1] ?? 'unknown';
  }
  return 'unknown';
}
