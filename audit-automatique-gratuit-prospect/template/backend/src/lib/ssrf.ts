import dns from 'node:dns/promises';
import net from 'node:net';
import { Agent, fetch as undiciFetch } from 'undici';

export class BlockedUrlError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'BlockedUrlError';
  }
}

type Cidr = [number[], number];

function v4Bytes(ip: string): number[] {
  return ip.split('.').map((n) => Number(n));
}

/** Développe une IPv6 (y compris `::` et un IPv4 terminal) en 16 octets. */
export function v6Bytes(ip: string): number[] {
  let text = ip.split('%')[0].toLowerCase();
  const dotted = text.match(/(\d+\.\d+\.\d+\.\d+)$/);
  if (dotted) {
    const [a, b, c, d] = v4Bytes(dotted[1]);
    text = text.slice(0, -dotted[1].length) + ((a << 8) | b).toString(16) + ':' + ((c << 8) | d).toString(16);
  }
  const [left, right] = text.split('::');
  const leftGroups = left ? left.split(':') : [];
  const rightGroups = right ? right.split(':') : [];
  const missing = 8 - leftGroups.length - rightGroups.length;
  const groups = text.includes('::') ? [...leftGroups, ...Array(missing).fill('0'), ...rightGroups] : leftGroups;
  return groups.flatMap((g) => {
    const v = parseInt(g || '0', 16);
    return [(v >> 8) & 255, v & 255];
  });
}

function inCidr(bytes: number[], [net_, bits]: Cidr): boolean {
  let left = bits;
  for (let i = 0; i < net_.length && left > 0; i += 1) {
    const take = Math.min(8, left);
    const mask = take === 8 ? 255 : (0xff << (8 - take)) & 255;
    if ((bytes[i] & mask) !== (net_[i] & mask)) return false;
    left -= take;
  }
  return true;
}

const V4_BLOCK: Cidr[] = [
  [[0, 0, 0, 0], 8], [[10, 0, 0, 0], 8], [[100, 64, 0, 0], 10], [[127, 0, 0, 0], 8], [[169, 254, 0, 0], 16],
  [[172, 16, 0, 0], 12], [[192, 0, 0, 0], 24], [[192, 0, 2, 0], 24], [[192, 88, 99, 0], 24], [[192, 168, 0, 0], 16],
  [[198, 18, 0, 0], 15], [[198, 51, 100, 0], 24], [[203, 0, 113, 0], 24], [[224, 0, 0, 0], 4], [[240, 0, 0, 0], 4],
];

function hex(...groups: number[]): number[] {
  return groups.flatMap((g) => [(g >> 8) & 255, g & 255]);
}

const V6_BLOCK: Cidr[] = [
  [hex(0, 0, 0, 0, 0, 0, 0, 0), 128], [hex(0, 0, 0, 0, 0, 0, 0, 1), 128],
  [hex(0x100, 0, 0, 0), 64], [hex(0x2001, 0xdb8), 32], [hex(0x2001, 0), 32],
  [hex(0xfc00), 7], [hex(0xfe80), 10], [hex(0xfec0), 10], [hex(0xff00), 8],
];

function embeddedV4(bytes: number[]): number[] | null {
  const zeroPrefix = bytes.slice(0, 10).every((b) => b === 0);
  if (zeroPrefix && bytes[10] === 0xff && bytes[11] === 0xff) return bytes.slice(12); // ::ffff:a.b.c.d
  if (bytes.slice(0, 12).every((b) => b === 0)) return bytes.slice(12); // ::a.b.c.d (déprécié)
  if (bytes[0] === 0x00 && bytes[1] === 0x64 && bytes[2] === 0xff && bytes[3] === 0x9b && bytes.slice(4, 12).every((b) => b === 0)) return bytes.slice(12); // NAT64
  if (bytes[0] === 0x20 && bytes[1] === 0x02) return bytes.slice(2, 6); // 6to4
  return null;
}

/** Vrai seulement pour une adresse routable sur Internet. */
export function isPublicIp(ip: string): boolean {
  const family = net.isIP(ip);
  if (family === 4) return !V4_BLOCK.some((c) => inCidr(v4Bytes(ip), c));
  if (family === 6) {
    const bytes = v6Bytes(ip);
    const v4 = embeddedV4(bytes);
    if (v4) return !V4_BLOCK.some((c) => inCidr(v4, c));
    return !V6_BLOCK.some((c) => inCidr(bytes, c));
  }
  return false;
}

const BLOCKED_HOST_SUFFIXES = ['localhost', '.localhost', '.local', '.internal', '.intranet', '.lan', '.home', '.corp', '.localdomain', '.home.arpa', '.railway.internal'];

export type UrlCheckDeps = { isAllowedIp: (ip: string) => boolean; allowedPorts?: string[] };
const defaultDeps: UrlCheckDeps = { isAllowedIp: isPublicIp };

/** Contrôle statique de l'URL : schéma, identifiants, port, noms internes, IP littérale. */
export function assertPublicUrlShape(raw: string, deps: UrlCheckDeps = defaultDeps): URL {
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw new BlockedUrlError('URL invalide');
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') throw new BlockedUrlError(`Schéma interdit : ${url.protocol}`);
  if (url.username || url.password) throw new BlockedUrlError('Identifiants interdits dans l’URL');
  if (url.port && !(deps.allowedPorts ?? ['80', '443']).includes(url.port)) throw new BlockedUrlError(`Port interdit : ${url.port}`);
  const host = url.hostname.toLowerCase().replace(/^\[|\]$/g, '').replace(/\.$/, '');
  if (!host || BLOCKED_HOST_SUFFIXES.some((s) => (s.startsWith('.') ? host.endsWith(s) : host === s))) throw new BlockedUrlError(`Hôte interdit : ${host}`);
  if (net.isIP(host) && !deps.isAllowedIp(host)) throw new BlockedUrlError(`Adresse interdite : ${host}`);
  return url;
}

/** Résolution suivie du refus de toute adresse non publique. */
export async function assertResolvesPublic(host: string, deps: UrlCheckDeps = defaultDeps): Promise<void> {
  if (net.isIP(host)) {
    if (!deps.isAllowedIp(host)) throw new BlockedUrlError(`Adresse interdite : ${host}`);
    return;
  }
  const addrs = await dns.lookup(host, { all: true, verbatim: true });
  if (!addrs.length) throw new BlockedUrlError(`Nom introuvable : ${host}`);
  for (const a of addrs) if (!deps.isAllowedIp(a.address)) throw new BlockedUrlError(`${host} pointe vers une adresse interdite`);
}

/** Vérification complète avant une requête d'un navigateur (Playwright). */
export async function isUrlAllowed(raw: string): Promise<boolean> {
  try {
    if (raw.startsWith('data:') || raw.startsWith('blob:')) return true;
    const url = assertPublicUrlShape(raw);
    await assertResolvesPublic(url.hostname.replace(/^\[|\]$/g, ''));
    return true;
  } catch {
    return false;
  }
}

/**
 * Le contrôle se fait au moment de la connexion : le résolveur rend l'adresse qu'il vient de vérifier,
 * ce qui ferme la fenêtre de DNS rebinding entre la vérification et le connect.
 */
function pinnedAgent(deps: UrlCheckDeps): Agent {
  const lookup = (hostname: string, options: any, cb: any) => {
    dns.lookup(hostname, { all: true, verbatim: true }).then(
      (addrs) => {
        const bad = addrs.find((a) => !deps.isAllowedIp(a.address));
        if (bad || !addrs.length) {
          cb(new BlockedUrlError(`${hostname} pointe vers une adresse interdite`));
          return;
        }
        if (options?.all) cb(null, addrs);
        else cb(null, addrs[0].address, addrs[0].family);
      },
      (err) => cb(err),
    );
  };
  return new Agent({ connect: { lookup: lookup as any, timeout: 10_000 } });
}

const sharedAgent = pinnedAgent(defaultDeps);

export type SafeFetchOptions = {
  headers?: Record<string, string>;
  maxBytes?: number;
  timeoutMs?: number;
  maxRedirects?: number;
};

export type SafeResponse = { url: string; status: number; contentType: string; body: Buffer };

export const DEFAULT_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36';

/** GET protégé : schéma, résolution, redirections revérifiées, délai total, taille maximale. */
export async function safeFetch(raw: string, options: SafeFetchOptions = {}, deps: UrlCheckDeps = defaultDeps, agent: Agent = sharedAgent): Promise<SafeResponse> {
  const maxBytes = options.maxBytes ?? 5 * 1024 * 1024;
  const maxRedirects = options.maxRedirects ?? 5;
  const signal = AbortSignal.timeout(options.timeoutMs ?? 20_000);
  let current = raw;
  for (let hop = 0; ; hop += 1) {
    const url = assertPublicUrlShape(current, deps);
    const res = await undiciFetch(url, {
      method: 'GET',
      redirect: 'manual',
      dispatcher: agent,
      signal,
      headers: { 'user-agent': DEFAULT_UA, accept: '*/*', 'accept-language': 'fr-FR,fr;q=0.9', ...options.headers },
    });
    if (res.status >= 300 && res.status < 400) {
      const location = res.headers.get('location');
      await res.body?.cancel().catch(() => undefined);
      if (!location) throw new BlockedUrlError(`Redirection sans destination depuis ${current}`);
      if (hop >= maxRedirects) throw new BlockedUrlError('Trop de redirections');
      current = new URL(location, url).toString();
      continue;
    }
    const contentType = (res.headers.get('content-type') ?? '').toLowerCase();
    const declared = Number(res.headers.get('content-length') ?? 0);
    if (declared > maxBytes) {
      await res.body?.cancel().catch(() => undefined);
      throw new BlockedUrlError(`Réponse trop volumineuse (${declared} octets)`);
    }
    const chunks: Uint8Array[] = [];
    let total = 0;
    if (res.body) {
      for await (const chunk of res.body as unknown as AsyncIterable<Uint8Array>) {
        total += chunk.byteLength;
        if (total > maxBytes) {
          await res.body.cancel().catch(() => undefined);
          throw new BlockedUrlError(`Réponse trop volumineuse (plus de ${maxBytes} octets)`);
        }
        chunks.push(chunk);
      }
    }
    return { url: url.toString(), status: res.status, contentType, body: Buffer.concat(chunks) };
  }
}
