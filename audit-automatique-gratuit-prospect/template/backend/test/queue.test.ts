import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import { query } from '../src/db/pool.js';
import { claimNext, completeJob, enqueue, heartbeat, releaseWorkerJobs, requeueJob } from '../src/jobs/queue.js';
import { takeDailySlot } from '../src/pipeline/run.js';
import { rerunAudit } from '../src/audits/service.js';
import { setupTestEnv, teardownTestEnv, truncateAll } from './helpers.js';

async function audit(domain = 'a.fr'): Promise<string> {
  const res = await query<{ id: string }>(`INSERT INTO audits (status, domain, source) VALUES ('queued',$1,'admin') RETURNING id`, [domain]);
  return res.rows[0].id;
}

beforeAll(async () => {
  await setupTestEnv({ MAX_AUDITS_PER_DAY: '2' });
});
afterAll(teardownTestEnv);
beforeEach(truncateAll);

describe('file d’attente', () => {
  it('un seul job actif par audit', async () => {
    const id = await audit();
    expect(await enqueue(id, 'audit')).toBe(true);
    expect(await enqueue(id, 'audit')).toBe(false);
  });

  it('deux consommateurs ne prennent jamais le même job', async () => {
    const [a, b] = [await audit('a.fr'), await audit('b.fr')];
    await enqueue(a, 'audit');
    await enqueue(b, 'audit');
    const [x, y] = await Promise.all([claimNext('w1'), claimNext('w2')]);
    expect(x?.id).toBeTruthy();
    expect(y?.id).toBeTruthy();
    expect(x?.id).not.toBe(y?.id);
    expect(await claimNext('w3')).toBeNull();
  });

  it('reprend un job dont le bail a expiré (redémarrage)', async () => {
    const id = await audit();
    await enqueue(id, 'audit');
    const job = (await claimNext('w1'))!;
    expect(await claimNext('w2')).toBeNull();
    await query(`UPDATE jobs SET locked_until = now() - interval '1 second' WHERE id=$1`, [job.id]);
    const resumed = (await claimNext('w2'))!;
    expect(resumed.id).toBe(job.id);
    expect(resumed.claims).toBe(2);
    expect(await heartbeat(job.id, 'w1')).toBe(false);
    expect(await heartbeat(job.id, 'w2')).toBe(true);
  });

  it('un arrêt propre rend le job immédiatement disponible', async () => {
    const id = await audit();
    await enqueue(id, 'audit');
    await claimNext('w1');
    await releaseWorkerJobs('w1');
    const job = await claimNext('w2');
    expect(job?.audit_id).toBe(id);
  });

  it('respecte le délai d’une nouvelle tentative et compte les essais', async () => {
    const id = await audit();
    await enqueue(id, 'audit');
    const job = (await claimNext('w1'))!;
    expect(await requeueJob(job.id, 'boom', 60_000)).toBe(1);
    expect(await claimNext('w1')).toBeNull();
    await query(`UPDATE jobs SET run_after = now() WHERE id=$1`, [job.id]);
    expect((await claimNext('w1'))?.id).toBe(job.id);
    await completeJob(job.id);
    expect(await claimNext('w1')).toBeNull();
  });
});

describe('plafond quotidien', () => {
  it('s’arrête à MAX_AUDITS_PER_DAY mais laisse une reprise continuer', async () => {
    const [a, b, c] = [await audit('a.fr'), await audit('b.fr'), await audit('c.fr')];
    expect(await takeDailySlot(a)).toBe(true);
    expect(await takeDailySlot(b)).toBe(true);
    expect(await takeDailySlot(c)).toBe(false);
    expect(await takeDailySlot(a)).toBe(true);
  });
});

describe('relance', () => {
  it('efface les résultats, garde le jeton, repart à zéro de génération', async () => {
    const id = await audit();
    await query(`UPDATE audits SET token='tok-aaaaaaaaaaaaaaaaaaaaaa', status='ready', analysis='{}', generations_used=7 WHERE id=$1`, [id]);
    await query(`INSERT INTO creatives (audit_id, idx, concept, format, prompt, locked) VALUES ($1,1,'C','1:1','p',false)`, [id]);
    expect(await rerunAudit(id)).toBe('ok');
    const row = (await query('SELECT * FROM audits WHERE id=$1', [id])).rows[0];
    expect(row.status).toBe('queued');
    expect(row.token).toBe('tok-aaaaaaaaaaaaaaaaaaaaaa');
    expect(row.analysis).toBeNull();
    expect(row.generations_used).toBe(0);
    expect((await query('SELECT count(*)::int AS n FROM creatives')).rows[0].n).toBe(0);
    const job = (await query(`SELECT payload FROM jobs WHERE audit_id=$1`, [id])).rows[0];
    expect(job.payload.purge).toBe(true);
    expect(await rerunAudit(id)).toBe('active');
  });
});
