import 'server-only';
import crypto from 'node:crypto';
import { cookies } from 'next/headers';
import { adminKey } from './env';

export const COOKIE = 'lv_admin';
const TTL_S = 12 * 60 * 60;

function signingKey(): Buffer | null {
  const secret = process.env.ADMIN_SESSION_SECRET?.trim() || adminKey();
  if (!secret) return null;
  return crypto.createHmac('sha256', secret).update('audit-admin-session-v1').digest();
}

function sign(payload: string, key: Buffer) {
  return crypto.createHmac('sha256', key).update(payload).digest('base64url');
}

export function createSessionValue(): string | null {
  const key = signingKey();
  if (!key) return null;
  const payload = `${Math.floor(Date.now() / 1000) + TTL_S}.${crypto.randomBytes(9).toString('base64url')}`;
  return `${payload}.${sign(payload, key)}`;
}

export function verifySessionValue(v: string | undefined): boolean {
  const key = signingKey();
  if (!key || !v) return false;
  const i = v.lastIndexOf('.');
  if (i < 1) return false;
  const payload = v.slice(0, i);
  const given = Buffer.from(v.slice(i + 1));
  const want = Buffer.from(sign(payload, key));
  if (given.length !== want.length || !crypto.timingSafeEqual(given, want)) return false;
  const exp = Number(payload.split('.')[0]);
  return Number.isFinite(exp) && exp * 1000 > Date.now();
}

export const sessionCookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict' as const,
  path: '/',
  maxAge: TTL_S,
};

export async function isAdmin(): Promise<boolean> {
  const jar = await cookies();
  return verifySessionValue(jar.get(COOKIE)?.value);
}

/** Comparaison à temps constant : les deux empreintes ont toujours la même longueur. */
export function passwordMatches(input: string): boolean {
  const expected = process.env.ADMIN_PASSWORD;
  if (!expected) return false;
  const a = crypto.createHash('sha256').update(input).digest();
  const b = crypto.createHash('sha256').update(expected).digest();
  return crypto.timingSafeEqual(a, b);
}

/* Limitation des essais : par adresse et globale. La mémoire est celle de l'instance,
   d'où le plafond global qui reste efficace même si une adresse change à chaque essai. */
type Bucket = { count: number; resetAt: number };
const WINDOW_MS = 15 * 60 * 1000;
const MAX_PER_IP = 6;
const MAX_GLOBAL = 40;
const g = globalThis as unknown as { __lvLogin?: { ips: Map<string, Bucket>; all: Bucket } };
const state = (g.__lvLogin ??= { ips: new Map(), all: { count: 0, resetAt: 0 } });

function hit(b: Bucket, now: number) {
  if (b.resetAt <= now) {
    b.count = 0;
    b.resetAt = now + WINDOW_MS;
  }
  b.count += 1;
}

export function loginAllowed(ip: string): boolean {
  const now = Date.now();
  const b = state.ips.get(ip);
  const ipBlocked = b && b.resetAt > now && b.count >= MAX_PER_IP;
  const allBlocked = state.all.resetAt > now && state.all.count >= MAX_GLOBAL;
  return !ipBlocked && !allBlocked;
}

export function recordLoginFailure(ip: string) {
  const now = Date.now();
  if (state.ips.size > 5000) state.ips.clear();
  const b = state.ips.get(ip) ?? { count: 0, resetAt: 0 };
  hit(b, now);
  state.ips.set(ip, b);
  hit(state.all, now);
}

export function clearLoginFailures(ip: string) {
  state.ips.delete(ip);
}
