import { query, tx, type Db } from '../db/pool.js';

export type JobKind = 'audit' | 'regenerate';
export type JobRow = {
  id: string;
  audit_id: string;
  kind: JobKind;
  payload: Record<string, any>;
  status: string;
  run_after: Date;
  locked_by: string | null;
  locked_until: Date | null;
  claims: number;
  attempts: number;
  last_error: string | null;
};

export const LEASE_MS = 120_000;
export const MAX_ATTEMPTS = 3;
export const MAX_CLAIMS = 12;

/** Un seul job actif par audit : la contrainte unique rend l'enqueue idempotent. */
export async function enqueue(auditId: string, kind: JobKind, payload: Record<string, unknown> = {}, db?: Db): Promise<boolean> {
  const res = await query(
    `INSERT INTO jobs (audit_id, kind, payload, status) VALUES ($1,$2,$3,'queued')
     ON CONFLICT (audit_id) WHERE status IN ('queued','running') DO NOTHING RETURNING id`,
    [auditId, kind, JSON.stringify(payload)],
    db,
  );
  return (res.rowCount ?? 0) > 0;
}

export async function hasActiveJob(auditId: string, db?: Db): Promise<boolean> {
  const res = await query(`SELECT 1 FROM jobs WHERE audit_id=$1 AND status IN ('queued','running') LIMIT 1`, [auditId], db);
  return (res.rowCount ?? 0) > 0;
}

/** Prend le prochain job disponible, y compris un job dont le bail a expiré (service redémarré). */
export async function claimNext(workerId: string): Promise<JobRow | null> {
  return tx(async (client) => {
    const pick = await query<{ id: string }>(
      `SELECT id FROM jobs
       WHERE (status='queued' AND run_after <= now()) OR (status='running' AND locked_until < now())
       ORDER BY run_after, created_at
       FOR UPDATE SKIP LOCKED LIMIT 1`,
      [],
      client,
    );
    const id = pick.rows[0]?.id;
    if (!id) return null;
    const updated = await query<JobRow>(
      `UPDATE jobs SET status='running', locked_by=$2, locked_until=now()+($3 || ' milliseconds')::interval,
              claims=claims+1, updated_at=now()
       WHERE id=$1 RETURNING *`,
      [id, workerId, String(LEASE_MS)],
      client,
    );
    return updated.rows[0] ?? null;
  });
}

/** Renouvelle le bail ; false si un autre exemplaire a repris le job. */
export async function heartbeat(jobId: string, workerId: string): Promise<boolean> {
  const res = await query(
    `UPDATE jobs SET locked_until=now()+($3 || ' milliseconds')::interval, updated_at=now()
     WHERE id=$1 AND locked_by=$2 AND status='running'`,
    [jobId, workerId, String(LEASE_MS)],
  );
  return (res.rowCount ?? 0) > 0;
}

export async function completeJob(jobId: string): Promise<void> {
  await query(`UPDATE jobs SET status='done', locked_by=NULL, locked_until=NULL, finished_at=now(), updated_at=now() WHERE id=$1`, [jobId]);
}

export async function failJob(jobId: string, error: string): Promise<void> {
  await query(
    `UPDATE jobs SET status='failed', last_error=$2, attempts=attempts+1, locked_by=NULL, locked_until=NULL, finished_at=now(), updated_at=now() WHERE id=$1`,
    [jobId, error.slice(0, 2000)],
  );
}

/** Remet le job en file pour une nouvelle tentative, avec un délai. */
export async function requeueJob(jobId: string, error: string, delayMs: number, countsAsAttempt = true): Promise<number> {
  const res = await query<{ attempts: number }>(
    `UPDATE jobs SET status='queued', last_error=$2, attempts=attempts+$4, locked_by=NULL, locked_until=NULL,
            run_after=now()+($3 || ' milliseconds')::interval, updated_at=now()
     WHERE id=$1 RETURNING attempts`,
    [jobId, error.slice(0, 2000), String(delayMs), countsAsAttempt ? 1 : 0],
  );
  return res.rows[0]?.attempts ?? 0;
}

/** Rend les jobs tenus par ce processus au moment d'un arrêt propre. */
export async function releaseWorkerJobs(workerId: string): Promise<void> {
  await query(`UPDATE jobs SET status='queued', locked_by=NULL, locked_until=NULL, updated_at=now() WHERE locked_by=$1 AND status='running'`, [workerId]);
}
