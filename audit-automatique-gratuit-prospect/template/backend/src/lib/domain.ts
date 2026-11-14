import net from 'node:net';

/** Boîtes grand public : leur domaine ne dit rien de l’entreprise. */
const FREE_EMAIL_DOMAINS = new Set([
  'gmail.com', 'googlemail.com', 'outlook.com', 'outlook.fr', 'hotmail.com', 'hotmail.fr', 'live.com', 'live.fr',
  'msn.com', 'yahoo.com', 'yahoo.fr', 'ymail.com', 'icloud.com', 'me.com', 'mac.com', 'aol.com', 'aol.fr',
  'proton.me', 'protonmail.com', 'pm.me', 'gmx.com', 'gmx.fr', 'orange.fr', 'wanadoo.fr', 'free.fr', 'sfr.fr',
  'neuf.fr', 'cegetel.net', 'laposte.net', 'bbox.fr', 'numericable.fr', 'club-internet.fr', 'voila.fr', 'tutanota.com',
  'yandex.com', 'mail.com', 'zoho.com', 'fastmail.com',
]);

/** Réseaux, annuaires et raccourcisseurs : ce n'est pas le site de l’entreprise. */
const NOT_A_SITE = [
  'facebook.com', 'fb.com', 'fb.me', 'instagram.com', 'linkedin.com', 'pinterest.com', 'pinterest.fr', 'youtube.com',
  'youtu.be', 'tiktok.com', 'twitter.com', 'x.com', 'threads.net', 'linktr.ee', 'linkin.bio', 'lnk.bio', 'beacons.ai',
  'houzz.com', 'houzz.fr', 'pagesjaunes.fr', 'wa.me', 'whatsapp.com', 't.me', 'google.com', 'goo.gl', 'g.page',
  'bit.ly', 'tinyurl.com',
];

const LOCAL_SUFFIXES = ['localhost', 'local', 'internal', 'intranet', 'lan', 'home', 'corp', 'localdomain', 'test', 'invalid', 'example', 'onion'];
const FILE_EXT = /\.(pdf|jpe?g|png|gif|webp|svg|docx?|xlsx?|pptx?|zip|mp4|mov)$/i;

function isNonSite(host: string): boolean {
  return NOT_A_SITE.some((d) => host === d || host.endsWith(`.${d}`));
}

/** Ramène une saisie libre à un nom de domaine (ASCII, sans www) ou à null. */
export function normalizeDomain(input: string | null | undefined): string | null {
  if (!input) return null;
  const raw = input.trim().replace(/^[<("'\s]+|[>)"',;.\s]+$/g, '').replace(/\s+/g, '');
  if (!raw || raw.includes('@')) return null;
  let url: URL;
  try {
    url = new URL(/^[a-z][a-z0-9+.-]*:\/\//i.test(raw) ? raw : `https://${raw}`);
  } catch {
    return null;
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return null;
  if (url.username || url.password) return null;
  let host = url.hostname.toLowerCase().replace(/\.$/, '');
  if (!host || net.isIP(host) || host.startsWith('[')) return null;
  host = host.replace(/^www\d?\./, '');
  if (host.length > 253 || !host.includes('.')) return null;
  const labels = host.split('.');
  if (!labels.every((l) => l.length >= 1 && l.length <= 63 && /^[a-z0-9-]+$/.test(l) && !l.startsWith('-') && !l.endsWith('-'))) return null;
  const tld = labels[labels.length - 1];
  if (!/^[a-z]{2,}$/.test(tld) && !tld.startsWith('xn--')) return null;
  if (LOCAL_SUFFIXES.includes(tld)) return null;
  return host;
}

export function isProfessionalEmailDomain(domain: string): boolean {
  return !FREE_EMAIL_DOMAINS.has(domain) && !isNonSite(domain);
}

export function domainFromEmail(email: string | null | undefined): string | null {
  if (!email) return null;
  const at = email.trim().toLowerCase().match(/^[^\s@]+@([^\s@]+)$/);
  if (!at) return null;
  const domain = normalizeDomain(at[1]);
  return domain && isProfessionalEmailDomain(domain) ? domain : null;
}

/** Cherche un nom de domaine dans une réponse libre (« Notre site : business-x.fr/contact »). */
export function domainFromFreeText(text: string): string | null {
  const token = /(?:https?:\/\/)?(?:[\p{L}\p{N}-]+\.)+\p{L}{2,}(?:\/[^\s,;]*)?/giu;
  for (const match of text.matchAll(token)) {
    const before = text[match.index! - 1];
    const hit = match[0].replace(/[).,;]+$/, '');
    if (before === '@') {
      if (isProfessionalEmailDomain(normalizeDomain(hit) ?? 'gmail.com')) return normalizeDomain(hit);
      continue;
    }
    const pathless = hit.replace(/^https?:\/\//i, '').split(/[/?#]/)[0];
    if (FILE_EXT.test(pathless)) continue;
    const domain = normalizeDomain(hit);
    if (domain && !isNonSite(domain)) return domain;
  }
  return null;
}

const SITE_STATEMENT = /\b(site|sites|domaine|web|url)\b|siteweb/;

function deburr(text: string): string {
  return text.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
}

export type BookingAnswer = { statement?: string | null; answer?: unknown };

export type BookingDomain = { domain: string | null; via: 'answer' | 'email' | null };

/**
 * Domaine d'une réservation : réponse dont l'intitulé parle de site ou de domaine,
 * sinon domaine de l'e-mail s'il est professionnel, sinon rien (needs_domain).
 */
export function extractBookingDomain(answers: BookingAnswer[], email: string | null | undefined): BookingDomain {
  for (const entry of answers) {
    if (!entry?.statement || typeof entry.answer !== 'string') continue;
    if (!SITE_STATEMENT.test(deburr(entry.statement))) continue;
    const domain = domainFromFreeText(entry.answer);
    if (domain) return { domain, via: 'answer' };
  }
  const domain = domainFromEmail(email);
  return domain ? { domain, via: 'email' } : { domain: null, via: null };
}

export function slugify(text: string, max = 40): string {
  const slug = deburr(text).replace(/œ/g, 'oe').replace(/æ/g, 'ae').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, max).replace(/-+$/g, '');
  return slug || 'audit';
}
