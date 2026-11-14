import { query } from '../db/pool.js';
import { errMsg, log } from '../log.js';

export async function recordCost(c: { auditId: string | null; provider: string; detail?: string; quantity: number; usd?: number | null }): Promise<void> {
  try {
    await query('INSERT INTO audit_costs (audit_id, provider, detail, quantity, usd) VALUES ($1,$2,$3,$4,$5)', [c.auditId, c.provider, c.detail ?? null, c.quantity, c.usd ?? null]);
  } catch (e) {
    log.warn('coût non enregistré', { error: errMsg(e) });
  }
}
