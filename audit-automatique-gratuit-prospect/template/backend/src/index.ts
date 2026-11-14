import { serve } from '@hono/node-server';
import { mkdir } from 'node:fs/promises';
import { cfg } from './config.js';
import { closePool } from './db/pool.js';
import { migrate } from './db/migrate.js';
import { buildApp } from './app.js';
import { startWorker, type WorkerHandle } from './jobs/worker.js';
import { ensureWatermark, startPoller, type PollerHandle } from './poller.js';
import { errMsg, log } from './log.js';

async function main() {
  const c = cfg();
  await mkdir(c.DATA_DIR, { recursive: true });
  await migrate();
  // Filigrane posé dès le premier démarrage, avant toute sonde ou webhook.
  const watermark = await ensureWatermark();
  log.info('filigrane des réservations', { watermark: watermark.toISOString(), provider: c.BOOKING_PROVIDER });

  let poller: PollerHandle | null = null;
  const app = buildApp({ wakePoller: () => poller?.wake() });

  const server = serve({ fetch: app.fetch, port: c.PORT }, (info) => log.info('serveur démarré', { port: info.port }));

  let worker: WorkerHandle | null = null;
  if (c.WORKER_ENABLED) worker = startWorker();
  if (c.POLLER_ENABLED && c.BOOKING_PROVIDER === 'iclosed' && c.ICLOSED_API_KEY) poller = startPoller();

  let stopping = false;
  const shutdown = async (signal: string) => {
    if (stopping) return;
    stopping = true;
    log.info('arrêt demandé', { signal });
    poller?.stop();
    await worker?.stop();
    server.close();
    await closePool().catch(() => undefined);
    process.exit(0);
  };
  process.on('SIGTERM', () => void shutdown('SIGTERM'));
  process.on('SIGINT', () => void shutdown('SIGINT'));
}

main().catch((e) => {
  log.error('démarrage impossible', { error: errMsg(e) });
  process.exit(1);
});
