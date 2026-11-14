import { timingSafeEqual } from 'node:crypto';
import { Hono } from 'hono';
import { parseGenericBooking } from '../booking.js';
import { cfg } from '../config.js';
import { errMsg, log } from '../log.js';
import { ensureWatermark, ingestBooking } from '../poller.js';
import { rateLimit } from './public.js';

function matches(given: string, expected: string): boolean {
  const a = Buffer.from(given);
  const b = Buffer.from(expected);
  return a.length === b.length && timingSafeEqual(a, b);
}

/**
 * Point d'entrée unique des réservations. En mode `generic`, le corps porte la réservation.
 * En mode `iclosed`, le webhook déclenche seulement une sonde de l'API, seule source lue.
 * Mêmes filtres, même filigrane, même idempotence dans les deux cas.
 */
export function webhookRoutes(wake: () => void) {
  const app = new Hono();
  app.post('/webhooks/booking', rateLimit('webhook', 120, 60_000), async (c) => {
    const secret = cfg().BOOKING_WEBHOOK_SECRET;
    const given = c.req.query('secret') ?? c.req.header('x-webhook-secret') ?? '';
    if (!secret || !matches(given, secret)) return c.json({ error: 'Non autorisé' }, 401);

    if (cfg().BOOKING_PROVIDER === 'iclosed') {
      wake();
      return c.json({ ok: true }, 202);
    }

    const body = await c.req.json().catch(() => null);
    const items: unknown[] = Array.isArray(body) ? body : [body];
    const watermark = await ensureWatermark();
    const results: string[] = [];
    let failed = false;
    for (const item of items.slice(0, 100)) {
      const booking = parseGenericBooking(item);
      if (!booking) {
        results.push('invalid');
        continue;
      }
      try {
        results.push(await ingestBooking(booking, watermark, 'webhook'));
      } catch (e) {
        failed = true;
        results.push('error');
        log.error('réservation non traitée', { callId: booking.callId, error: errMsg(e) });
      }
    }
    // Une erreur demande à l'outil d'origine de renvoyer : l'identifiant évite tout doublon.
    return c.json({ results }, failed ? 500 : results.every((r) => r === 'invalid') ? 400 : 200);
  });
  return app;
}
