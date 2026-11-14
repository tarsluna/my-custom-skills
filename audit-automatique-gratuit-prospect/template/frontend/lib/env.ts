import 'server-only';

export const useFixtures = () => process.env.USE_FIXTURES === '1';

export function apiBase(): string | null {
  const v = process.env.API_URL?.trim();
  return v ? v.replace(/\/+$/, '') : null;
}

export function adminKey(): string | null {
  return process.env.ADMIN_API_KEY?.trim() || null;
}

/** L'adresse réelle du visiteur, relayée au backend pour sa limite par IP. */
export function clientIp(h: Headers): string {
  return h.get('x-real-ip') ?? h.get('x-forwarded-for')?.split(',')[0]?.trim() ?? '0.0.0.0';
}
