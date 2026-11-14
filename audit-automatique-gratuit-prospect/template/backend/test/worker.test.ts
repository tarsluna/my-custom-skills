import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../src/pipeline/crawl.js', () => ({ crawlSite: vi.fn() }));

const { crawlSite } = await import('../src/pipeline/crawl.js');
const { FatalAuditError } = await import('../src/pipeline/errors.js');
const { query } = await import('../src/db/pool.js');
const { enqueue } = await import('../src/jobs/queue.js');
const { startWorker } = await import('../src/jobs/worker.js');
const { setupTestEnv, teardownTestEnv, truncateAll } = await import('./helpers.js');

const crawl = vi.mocked(crawlSite);

async function waitFor<T>(fn: () => Promise<T | null | false>, timeoutMs = 8000): Promise<T> {
  const start = Date.now();
  for (;;) {
    const value = await fn();
    if (value) return value;
    if (Date.now() - start > timeoutMs) throw new Error('délai dépassé');
    await new Promise((r) => setTimeout(r, 100));
  }
}

async function newAudit(): Promise<string> {
  const res = await query<{ id: string }>(`INSERT INTO audits (status, domain, source) VALUES ('queued','exemple-test.fr','admin') RETURNING id`);
  await enqueue(res.rows[0].id, 'audit');
  return res.rows[0].id;
}

beforeAll(async () => {
  await setupTestEnv({ WORKER_CONCURRENCY: '1' });
});
afterAll(teardownTestEnv);
beforeEach(async () => {
  await truncateAll();
  crawl.mockReset();
});

describe('worker', () => {
  it('erreur définitive : audit en échec au message lisible, sans nouvelle tentative', async () => {
    crawl.mockRejectedValue(new FatalAuditError('Le site exemple-test.fr est injoignable.'));
    const id = await newAudit();
    const worker = startWorker();
    const audit = await waitFor(async () => {
      const row = (await query<{ status: string; error: string }>('SELECT status, error FROM audits WHERE id=$1', [id])).rows[0];
      return row.status === 'failed' ? row : null;
    });
    await worker.stop();
    expect(audit.error).toBe('Le site exemple-test.fr est injoignable.');
    const job = (await query<{ status: string; attempts: number }>('SELECT status, attempts FROM jobs WHERE audit_id=$1', [id])).rows[0];
    expect(job.status).toBe('failed');
  });

  it('erreur passagère : le job est repoussé, l’audit n’échoue pas', async () => {
    crawl.mockRejectedValue(new Error('coupure réseau'));
    const id = await newAudit();
    const worker = startWorker();
    const job = await waitFor(async () => {
      const row = (await query<{ status: string; attempts: number; run_after: Date }>('SELECT status, attempts, run_after FROM jobs WHERE audit_id=$1', [id])).rows[0];
      return row.attempts >= 1 ? row : null;
    });
    await worker.stop();
    expect(job.status).toBe('queued');
    expect(job.run_after.getTime()).toBeGreaterThan(Date.now());
    const audit = (await query<{ status: string }>('SELECT status FROM audits WHERE id=$1', [id])).rows[0];
    expect(audit.status).not.toBe('failed');
  });

  it('au troisième échec, l’audit passe en erreur', async () => {
    crawl.mockRejectedValue(new Error('toujours en panne'));
    const id = await newAudit();
    await query(`UPDATE jobs SET attempts=2 WHERE audit_id=$1`, [id]);
    const worker = startWorker();
    const audit = await waitFor(async () => {
      const row = (await query<{ status: string; error: string }>('SELECT status, error FROM audits WHERE id=$1', [id])).rows[0];
      return row.status === 'failed' ? row : null;
    });
    await worker.stop();
    expect(audit.error).toContain('toujours en panne');
  });

  it('plafond quotidien : le job est reporté au lendemain sans démarrer', async () => {
    await query(`INSERT INTO audits (status, domain, source, started_at) SELECT 'ready', 'autre-'||i||'.fr', 'admin', now() FROM generate_series(1,25) i`);
    const id = await newAudit();
    const worker = startWorker();
    const job = await waitFor(async () => {
      const row = (await query<{ status: string; run_after: Date; last_error: string }>('SELECT status, run_after, last_error FROM jobs WHERE audit_id=$1', [id])).rows[0];
      return row.status === 'queued' && row.last_error ? row : null;
    });
    await worker.stop();
    expect(crawl).not.toHaveBeenCalled();
    expect(job.run_after.getTime()).toBeGreaterThan(Date.now() + 60_000);
  });
});
