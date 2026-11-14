import { Hono } from 'hono';
import { bodyLimit } from 'hono/body-limit';
import { cors } from 'hono/cors';
import { cfg } from './config.js';
import { query } from './db/pool.js';
import { errMsg, log } from './log.js';
import { adminRoutes } from './routes/admin.js';
import { publicRoutes } from './routes/public.js';
import { webhookRoutes } from './routes/webhooks.js';

export function isAllowedOrigin(origin: string): boolean {
  if (origin === cfg().FRONTEND_ORIGIN) return true;
  return /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
}

export function buildApp(options: { wakePoller?: () => void } = {}) {
  const app = new Hono();

  app.use('*', async (c, next) => {
    await next();
    c.header('X-Robots-Tag', 'noindex, nofollow');
    c.header('X-Content-Type-Options', 'nosniff');
    c.header('Referrer-Policy', 'no-referrer');
  });

  app.use(
    '/public/*',
    cors({
      origin: (origin) => (isAllowedOrigin(origin) ? origin : null),
      allowMethods: ['GET', 'POST', 'OPTIONS'],
      allowHeaders: ['content-type'],
      maxAge: 600,
    }),
  );

  // Le front lit les pixels du logo pour choisir sa plaque de contraste.
  app.use('/media/*', cors({ origin: (origin) => (isAllowedOrigin(origin) ? origin : null), allowMethods: ['GET'], maxAge: 600 }));

  const limit = (maxSize: number) => bodyLimit({ maxSize, onError: (c) => c.json({ error: 'Corps trop volumineux' }, 413) });
  app.use('/public/*', limit(128 * 1024));
  app.use('/admin/*', limit(128 * 1024));
  app.use('/webhooks/*', limit(512 * 1024));

  app.get('/health', async (c) => {
    try {
      await query('SELECT 1');
      return c.json({ ok: true });
    } catch (e) {
      log.error('santé : base injoignable', { error: errMsg(e) });
      return c.json({ ok: false }, 503);
    }
  });

  app.route('/', publicRoutes);
  app.route('/', adminRoutes);
  app.route('/', webhookRoutes(options.wakePoller ?? (() => undefined)));

  app.notFound((c) => c.json({ error: 'Introuvable' }, 404));
  app.onError((e, c) => {
    log.error('erreur serveur', { path: c.req.path, error: errMsg(e) });
    return c.json({ error: 'Erreur serveur' }, 500);
  });

  return app;
}
