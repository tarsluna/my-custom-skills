import { randomUUID } from 'node:crypto';
import { cfg } from '../config.js';
import { query } from '../db/pool.js';
import { logStep, setStatus } from '../audits/service.js';
import { errMsg, log } from '../log.js';
import { FatalAuditError } from '../pipeline/errors.js';
import { msUntilNextParisDay, regenerateCreative, runAudit } from '../pipeline/run.js';
import { claimNext, completeJob, failJob, heartbeat, LEASE_MS, MAX_ATTEMPTS, MAX_CLAIMS, releaseWorkerJobs, requeueJob, type JobRow } from './queue.js';

const IDLE_POLL_MS = 3_000;
const RETRY_DELAY_MS = 60_000;

export type WorkerHandle = { stop: () => Promise<void>; id: string };

const NOT_RETRYABLE_MESSAGE = 'Génération interrompue : audit relançable depuis l’admin.';

async function markFailed(job: JobRow, message: string): Promise<void> {
  await failJob(job.id, message);
  // Une régénération ratée ne fait pas tomber un audit déjà prêt.
  if (job.kind === 'audit') {
    await setStatus(job.audit_id, 'failed', { error: message });
    await logStep(job.audit_id, 'audit', 'error', message);
  } else {
    await logStep(job.audit_id, 'regeneration', 'error', message);
  }
}

async function runJob(job: JobRow, workerId: string, parent: AbortController): Promise<void> {
  const controller = new AbortController();
  const onParentAbort = () => controller.abort();
  parent.signal.addEventListener('abort', onParentAbort, { once: true });

  const beat = setInterval(() => {
    heartbeat(job.id, workerId)
      .then((held) => {
        if (!held) {
          log.warn('bail perdu, job abandonné', { jobId: job.id });
          controller.abort();
        }
      })
      .catch((e) => log.warn('battement impossible', { error: errMsg(e) }));
  }, LEASE_MS / 4);

  try {
    if (job.claims > MAX_CLAIMS) {
      await markFailed(job, 'Trop de reprises consécutives, audit interrompu.');
      return;
    }
    if (job.kind === 'regenerate') {
      await regenerateCreative(job, controller.signal);
      await completeJob(job.id);
      return;
    }
    const outcome = await runAudit(job, controller.signal);
    if (outcome === 'deferred') {
      await requeueJob(job.id, 'Plafond journalier', await msUntilNextParisDay(), false);
      return;
    }
    await completeJob(job.id);
  } catch (e) {
    if (controller.signal.aborted) {
      log.info('job interrompu', { jobId: job.id });
      return;
    }
    if (e instanceof FatalAuditError) {
      await markFailed(job, e.message);
      return;
    }
    const message = errMsg(e);
    log.error('job en erreur', { jobId: job.id, kind: job.kind, error: message });
    await logStep(job.audit_id, 'erreur', 'error', message).catch(() => undefined);
    const attempts = await requeueJob(job.id, message, RETRY_DELAY_MS);
    if (attempts >= MAX_ATTEMPTS) {
      await markFailed(job, `${NOT_RETRYABLE_MESSAGE} Dernière erreur : ${message}`);
    }
  } finally {
    clearInterval(beat);
    parent.signal.removeEventListener('abort', onParentAbort);
  }
}

/** Boucle de consommation : reprend aussi les jobs dont le bail a expiré après un redémarrage. */
export function startWorker(): WorkerHandle {
  const workerId = `w-${randomUUID()}`;
  const controller = new AbortController();
  let running = 0;
  let stopped = false;
  let timer: NodeJS.Timeout | null = null;

  const tick = async () => {
    if (stopped) return;
    try {
      while (!stopped && running < cfg().WORKER_CONCURRENCY) {
        const job = await claimNext(workerId);
        if (!job) break;
        running += 1;
        runJob(job, workerId, controller)
          .catch((e) => log.error('job en échec inattendu', { jobId: job.id, error: errMsg(e) }))
          .finally(() => {
            running -= 1;
            schedule(100);
          });
      }
    } catch (e) {
      log.error('boucle du worker', { error: errMsg(e) });
    }
    schedule(IDLE_POLL_MS);
  };

  const schedule = (ms: number) => {
    if (stopped) return;
    if (timer) clearTimeout(timer);
    timer = setTimeout(tick, ms);
  };

  schedule(500);

  return {
    id: workerId,
    stop: async () => {
      stopped = true;
      if (timer) clearTimeout(timer);
      controller.abort();
      await releaseWorkerJobs(workerId).catch((e) => log.warn('libération impossible', { error: errMsg(e) }));
    },
  };
}

export async function workerStats(): Promise<{ queued: number; running: number }> {
  const res = await query<{ status: string; n: number }>(`SELECT status, count(*)::int AS n FROM jobs WHERE status IN ('queued','running') GROUP BY status`);
  const find = (status: string) => res.rows.find((r) => r.status === status)?.n ?? 0;
  return { queued: find('queued'), running: find('running') };
}
