import http from 'node:http';
import type { AddressInfo } from 'node:net';
import { Agent } from 'undici';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { assertPublicUrlShape, assertResolvesPublic, BlockedUrlError, isPublicIp, isUrlAllowed, safeFetch, v6Bytes, type UrlCheckDeps } from '../src/lib/ssrf.js';

describe('isPublicIp', () => {
  it.each(['8.8.8.8', '1.1.1.1', '93.184.216.34', '2606:4700:4700::1111', '2001:4860:4860::8888'])('accepte %s', (ip) => expect(isPublicIp(ip)).toBe(true));
  it.each([
    '127.0.0.1', '10.0.0.1', '172.16.0.1', '172.31.255.254', '192.168.1.1', '169.254.169.254', '100.64.0.1', '0.0.0.0', '198.18.0.1', '224.0.0.1', '255.255.255.255',
    '::1', '::', 'fe80::1', 'fc00::1', 'fd12:3456::1', 'ff02::1', '::ffff:127.0.0.1', '::ffff:10.0.0.1', '64:ff9b::a00:1', '2002:7f00:1::', '2001:db8::1',
  ])('refuse %s', (ip) => expect(isPublicIp(ip)).toBe(false));
  it('refuse ce qui n’est pas une adresse', () => expect(isPublicIp('pas-une-ip')).toBe(false));
  it('développe une IPv6 mixte', () => expect(v6Bytes('::ffff:1.2.3.4').slice(-4)).toEqual([1, 2, 3, 4]));
});

describe('assertPublicUrlShape', () => {
  it.each(['http://localhost/', 'http://x.localhost/', 'http://db.railway.internal/', 'http://printer.local/', 'file:///etc/passwd', 'ftp://x.fr/', 'gopher://x.fr/', 'http://user:pw@x.fr/', 'http://x.fr:8080/', 'http://[::1]/', 'http://127.0.0.1/', 'http://2130706433/', 'http://0x7f.0.0.1/', 'http://169.254.169.254/latest/meta-data/'])(
    'refuse %s',
    (url) => expect(() => assertPublicUrlShape(url)).toThrow(BlockedUrlError),
  );
  it('accepte un site public', () => expect(assertPublicUrlShape('https://www.example.com/page').hostname).toBe('www.example.com'));
});

describe('résolution', () => {
  it('refuse un nom qui résout vers une IP privée', async () => {
    const deps: UrlCheckDeps = { isAllowedIp: () => false };
    await expect(assertResolvesPublic('example.com', deps)).rejects.toThrow(BlockedUrlError);
  });
  it('isUrlAllowed bloque le privé et laisse passer data:', async () => {
    expect(await isUrlAllowed('http://127.0.0.1/')).toBe(false);
    expect(await isUrlAllowed('data:image/png;base64,AAAA')).toBe(true);
  });
});

describe('safeFetch', () => {
  let server: http.Server;
  let port: number;
  beforeAll(async () => {
    server = http.createServer((req, res) => {
      if (req.url === '/redirect-metadata') {
        res.writeHead(302, { location: 'http://169.254.169.254/latest/meta-data/' });
        res.end();
      } else if (req.url === '/redirect-local') {
        res.writeHead(302, { location: 'http://localhost/secret' });
        res.end();
      } else if (req.url === '/redirect-ok') {
        res.writeHead(301, { location: '/final' });
        res.end();
      } else if (req.url === '/final') {
        res.writeHead(200, { 'content-type': 'text/html' });
        res.end('<html>ok</html>');
      } else if (req.url === '/big') {
        res.writeHead(200, { 'content-type': 'text/plain' });
        res.end(Buffer.alloc(200_000, 97));
      } else if (req.url === '/loop') {
        res.writeHead(302, { location: '/loop' });
        res.end();
      } else {
        res.writeHead(404);
        res.end();
      }
    });
    await new Promise<void>((r) => server.listen(0, '127.0.0.1', r));
    port = (server.address() as AddressInfo).port;
  });
  afterAll(() => new Promise<void>((r) => server.close(() => r())));

  // Le premier saut est autorisé vers le serveur de test ; la protection doit agir sur le suivant.
  const deps = (): UrlCheckDeps => ({ isAllowedIp: (ip) => ip === '127.0.0.1', allowedPorts: [String(port)] });
  const agent = new Agent();
  const base = () => `http://127.0.0.1:${port}`;

  it('suit une redirection interne', async () => {
    const res = await safeFetch(`${base()}/redirect-ok`, {}, deps(), agent);
    expect(res.status).toBe(200);
    expect(res.body.toString()).toContain('ok');
    expect(res.url).toContain('/final');
  });
  it('revérifie chaque redirection (IP de métadonnées)', async () => {
    await expect(safeFetch(`${base()}/redirect-metadata`, {}, deps(), agent)).rejects.toThrow(BlockedUrlError);
  });
  it('revérifie chaque redirection (nom local)', async () => {
    await expect(safeFetch(`${base()}/redirect-local`, {}, deps(), agent)).rejects.toThrow(BlockedUrlError);
  });
  it('coupe au-delà de la taille maximale', async () => {
    await expect(safeFetch(`${base()}/big`, { maxBytes: 1000 }, deps(), agent)).rejects.toThrow(BlockedUrlError);
  });
  it('coupe les boucles de redirection', async () => {
    await expect(safeFetch(`${base()}/loop`, { maxRedirects: 3 }, deps(), agent)).rejects.toThrow(BlockedUrlError);
  });
  it('refuse un port non standard par défaut', async () => {
    await expect(safeFetch(`${base()}/final`)).rejects.toThrow(BlockedUrlError);
  });
});
