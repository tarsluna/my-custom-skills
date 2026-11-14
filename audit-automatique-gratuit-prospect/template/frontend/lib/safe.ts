/* Tout ce qui vient de l'audit est une donnée extérieure. Ici : ce qui ne peut pas être laissé au seul échappement de React. */

const TOKEN_RE = /^[a-zA-Z0-9][a-zA-Z0-9_-]{4,160}$/;
const ID_RE = /^[a-zA-Z0-9_-]{1,120}$/;
const FILE_RE = /^[a-zA-Z0-9][a-zA-Z0-9._-]{0,200}$/;

export const isValidToken = (t: unknown): t is string => typeof t === 'string' && TOKEN_RE.test(t);
export const isValidId = (t: unknown): t is string => typeof t === 'string' && ID_RE.test(t);
export const isValidFile = (t: unknown): t is string => typeof t === 'string' && FILE_RE.test(t) && !t.includes('..');

/** Lien cliquable : http(s) uniquement, jamais javascript: ni data:. */
export function safeHref(u: string | null | undefined): string | null {
  if (!u) return null;
  try {
    const x = new URL(u);
    return x.protocol === 'http:' || x.protocol === 'https:' ? x.href : null;
  } catch {
    return null;
  }
}

/** Source d'image : URL http(s) ou chemin local absolu fourni par le backend. */
export function safeImg(u: string | null | undefined): string | null {
  if (!u) return null;
  if (u.startsWith('/') && !u.startsWith('//')) return u;
  return safeHref(u);
}

export function hostOf(u: string | null | undefined): string | null {
  const s = safeHref(u);
  if (!s) return null;
  try {
    return new URL(s).hostname.replace(/^www\./, '');
  } catch {
    return null;
  }
}
