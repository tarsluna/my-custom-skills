import { chromium, type Browser, type BrowserContext } from 'playwright';
import { DEFAULT_UA, isUrlAllowed } from '../lib/ssrf.js';
import { errMsg, log } from '../log.js';

export type ComputedElement = { color: string; backgroundColor: string; fontFamily: string } | null;
export type ComputedStyles = { body: ComputedElement; h1: ComputedElement; h2: ComputedElement; p: ComputedElement; a: ComputedElement; button: ComputedElement; header: ComputedElement; footer: ComputedElement };

export type RenderedPage = { url: string; html: string; screenshot: Buffer | null; computed: ComputedStyles | null };

async function launch(): Promise<Browser | null> {
  try {
    return await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--force-webrtc-ip-handling-policy=disable_non_proxied_udp', '--deny-permission-prompts'],
    });
  } catch (e) {
    log.warn('Chromium indisponible, analyse sans rendu', { error: errMsg(e) });
    return null;
  }
}

async function guardedContext(browser: Browser): Promise<BrowserContext> {
  const context = await browser.newContext({
    userAgent: DEFAULT_UA,
    viewport: { width: 1440, height: 900 },
    locale: 'fr-FR',
    acceptDownloads: false,
    serviceWorkers: 'block',
    javaScriptEnabled: true,
  });
  const decisions = new Map<string, boolean>();
  // Chaque requête du navigateur passe par le même contrôle SSRF que le fetch serveur.
  await context.route('**/*', async (route) => {
    const request = route.request();
    if (request.resourceType() === 'media') return route.abort();
    const url = request.url();
    let key = url;
    try {
      const parsed = new URL(url);
      key = `${parsed.protocol}//${parsed.host}`;
    } catch {
      return route.abort();
    }
    const allowed = decisions.get(key) ?? (await isUrlAllowed(url));
    decisions.set(key, allowed);
    if (!allowed) {
      log.warn('requête navigateur bloquée', { url: key });
      return route.abort();
    }
    return route.continue();
  });
  await context.routeWebSocket(/.*/, (ws) => ws.close());
  return context;
}

export async function withBrowser<T>(fn: (context: BrowserContext) => Promise<T>): Promise<T | null> {
  const browser = await launch();
  if (!browser) return null;
  try {
    const context = await guardedContext(browser);
    return await fn(context);
  } finally {
    await browser.close().catch(() => undefined);
  }
}

const SCROLL_SCRIPT = `new Promise((resolve) => {
  let y = 0;
  const timer = setInterval(() => {
    window.scrollBy(0, 700);
    y += 700;
    if (y > 4200 || window.innerHeight + window.scrollY >= document.body.scrollHeight) {
      clearInterval(timer);
      window.scrollTo(0, 0);
      resolve(true);
    }
  }, 120);
})`;

const COMPUTED_SCRIPT = `(() => {
  const pick = (selector) => {
    const el = document.querySelector(selector);
    if (!el) return null;
    const s = getComputedStyle(el);
    return { color: s.color, backgroundColor: s.backgroundColor, fontFamily: s.fontFamily };
  };
  return {
    body: pick('body'),
    h1: pick('h1'),
    h2: pick('h2'),
    p: pick('main p, article p, p'),
    a: pick('main a, nav a, a'),
    button: pick('button, .button, .btn, [class*="btn"], a[class*="button"]'),
    header: pick('header, nav'),
    footer: pick('footer'),
  };
})()`;

export async function renderPage(context: BrowserContext, url: string, options: { screenshot: boolean; timeoutMs?: number }): Promise<RenderedPage | null> {
  const page = await context.newPage();
  page.setDefaultTimeout(options.timeoutMs ?? 25_000);
  try {
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: options.timeoutMs ?? 25_000 });
    if (!response || response.status() >= 400) return null;
    await page.waitForLoadState('networkidle', { timeout: 6_000 }).catch(() => undefined);
    // Scripts passés en texte : tsx réécrit les fonctions et un `__name` injecté n'existe pas dans la page.
    await page.evaluate(SCROLL_SCRIPT).catch(() => undefined);
    await page.waitForTimeout(500);

    const computed = (await page.evaluate(COMPUTED_SCRIPT)) as ComputedStyles;

    const screenshot = options.screenshot ? await page.screenshot({ type: 'jpeg', quality: 80, fullPage: false }) : null;
    return { url: page.url(), html: await page.content(), screenshot, computed };
  } catch (e) {
    log.warn('rendu Chromium en échec', { url, error: errMsg(e) });
    return null;
  } finally {
    await page.close().catch(() => undefined);
  }
}
