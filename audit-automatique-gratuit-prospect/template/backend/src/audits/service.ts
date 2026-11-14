import { randomBytes } from 'node:crypto';
import { cfg } from '../config.js';
import { query, tx, type Db } from '../db/pool.js';
import { slugify } from '../lib/domain.js';
import { enqueue, hasActiveJob } from '../jobs/queue.js';

export type AuditStatus = 'queued' | 'analyzing' | 'ads' | 'creatives' | 'ready' | 'failed' | 'needs_domain';

export type ContactInfo = { name?: string | null; firstName?: string | null; email?: string | null; phone?: string | null; meetingAt?: Date | null };

/** 22 caractères base64url, soit 128 bits : le jeton n'est pas devinable. */
export function newToken(businessName: string): string {
  return `${slugify(businessName)}-${randomBytes(16).toString('base64url')}`;
}

export async function logStep(auditId: string, step: string, status: 'start' | 'ok' | 'error' | 'info', message?: string, meta?: Record<string, unknown>, db?: Db): Promise<void> {
  await query('INSERT INTO audit_steps (audit_id, step, status, message, meta) VALUES ($1,$2,$3,$4,$5)', [auditId, step, status, message ?? null, meta ? JSON.stringify(meta) : null], db);
}

export async function setStatus(auditId: string, status: AuditStatus, extra: { error?: string | null } = {}, db?: Db): Promise<void> {
  await query(`UPDATE audits SET status=$2, error=COALESCE($3, error), updated_at=now() WHERE id=$1`, [auditId, status, extra.error ?? null], db);
}

/** Audit encore valable pour ce domaine (dernier non échoué de moins de 30 jours). */
export async function findReusableAudit(domain: string, db?: Db): Promise<{ id: string; status: AuditStatus } | null> {
  const res = await query<{ id: string; status: AuditStatus }>(
    `SELECT id, status FROM audits
     WHERE domain=$1 AND status NOT IN ('failed','needs_domain') AND created_at >= now() - ($2 || ' days')::interval
     ORDER BY created_at DESC LIMIT 1`,
    [domain, String(cfg().REUSE_WINDOW_DAYS)],
    db,
  );
  return res.rows[0] ?? null;
}

async function insertAudit(c: Db, args: { domain: string | null; status: AuditStatus; source: string; contact?: ContactInfo }): Promise<string> {
  const contact = args.contact ?? {};
  const res = await query<{ id: string }>(
    `INSERT INTO audits (status, domain, source, contact_name, contact_first_name, contact_email, contact_phone, meeting_at)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id`,
    [args.status, args.domain, args.source, contact.name ?? null, contact.firstName ?? null, contact.email ?? null, contact.phone ?? null, contact.meetingAt ?? null],
    c,
  );
  return res.rows[0].id;
}

async function lockDomain(client: Db, domain: string): Promise<void> {
  await query(`SELECT pg_advisory_xact_lock(hashtext($1))`, [`audit-domain:${domain}`], client);
}

export type CreateAuditResult = { auditId: string; reused: boolean };

/**
 * Point d'entrée commun : réutilise l'audit récent du domaine, sinon en crée un et le met en file.
 * Le verrou par domaine évite deux audits concurrents pour le même business.
 */
export async function createOrReuseAudit(args: { domain: string; source: 'poller' | 'webhook' | 'admin'; contact?: ContactInfo }, db?: Db): Promise<CreateAuditResult> {
  const run = async (client: Db): Promise<CreateAuditResult> => {
    await lockDomain(client, args.domain);
    const existing = await findReusableAudit(args.domain, client);
    if (existing) {
      if (args.contact && (args.contact.meetingAt || args.contact.firstName)) {
        await query(
          `UPDATE audits SET contact_name=COALESCE($2,contact_name), contact_first_name=COALESCE($3,contact_first_name),
                  contact_email=COALESCE($4,contact_email), contact_phone=COALESCE($5,contact_phone), meeting_at=COALESCE($6,meeting_at), updated_at=now()
           WHERE id=$1`,
          [existing.id, args.contact.name ?? null, args.contact.firstName ?? null, args.contact.email ?? null, args.contact.phone ?? null, args.contact.meetingAt ?? null],
          client,
        );
      }
      return { auditId: existing.id, reused: true };
    }
    const auditId = await insertAudit(client, { domain: args.domain, status: 'queued', source: args.source, contact: args.contact });
    await enqueue(auditId, 'audit', {}, client);
    return { auditId, reused: false };
  };
  if (db) return run(db);
  return tx(run);
}

export async function createNeedsDomainAudit(args: { source: 'poller' | 'webhook' | 'admin'; contact?: ContactInfo }, db?: Db): Promise<string> {
  const run = (client: Db) => insertAudit(client, { domain: null, status: 'needs_domain', source: args.source, contact: args.contact });
  if (db) return run(db);
  return tx(run);
}

/** Relance complète : efface les résultats, conserve le jeton, repart de zéro sur le plafond de générations. */
export async function rerunAudit(auditId: string, domain?: string | null): Promise<'ok' | 'active' | 'not_found' | 'missing_domain'> {
  return tx(async (client) => {
    const row = await query<{ domain: string | null }>('SELECT domain FROM audits WHERE id=$1 FOR UPDATE', [auditId], client);
    if (!row.rows[0]) return 'not_found';
    if (await hasActiveJob(auditId, client)) return 'active';
    const nextDomain = domain ?? row.rows[0].domain;
    if (!nextDomain) return 'missing_domain';
    for (const table of ['creatives', 'competitors', 'projects', 'audit_steps']) {
      await query(`DELETE FROM ${table} WHERE audit_id=$1`, [auditId], client);
    }
    await query(
      `UPDATE audits SET status='queued', domain=$2, analysis=NULL, brand=NULL, competitors_meta=NULL, insights=NULL, setter=NULL,
              error=NULL, generations_used=0, started_at=NULL, ready_at=NULL, updated_at=now() WHERE id=$1`,
      [auditId, nextDomain],
      client,
    );
    await enqueue(auditId, 'audit', { purge: true }, client);
    return 'ok';
  });
}
