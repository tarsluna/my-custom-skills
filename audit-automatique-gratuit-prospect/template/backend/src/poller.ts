import { cfg } from './config.js';
import { query, tx, type Db } from './db/pool.js';
import { extractBookingDomain } from './lib/domain.js';
import { fetchAllEventCalls, parseEventCall, type ParsedBooking } from './lib/iclosed.js';
import { createNeedsDomainAudit, createOrReuseAudit } from './audits/service.js';
import { errMsg, log } from './log.js';

const WATERMARK_KEY = 'booking_watermark';

export type IngestSource = 'poller' | 'webhook';

export async function getWatermark(db?: Db): Promise<Date | null> {
  const res = await query<{ value: string }>('SELECT value FROM settings WHERE key=$1', [WATERMARK_KEY], db);
  return res.rows[0] ? new Date(res.rows[0].value) : null;
}

/** Fixe le filigrane au premier démarrage seulement : il survit aux redémarrages. */
export async function ensureWatermark(now: Date = new Date()): Promise<Date> {
  await query(`INSERT INTO settings (key, value) VALUES ($1, $2) ON CONFLICT (key) DO NOTHING`, [WATERMARK_KEY, JSON.stringify(now.toISOString())]);
  return (await getWatermark())!;
}

export type IngestOutcome = 'created' | 'reused' | 'needs_domain' | 'ignored_event' | 'ignored_watermark' | 'ignored_cancelled' | 'ignored_past' | 'duplicate';

/** Une réservation, une seule décision : la clé `call_id` rend l'opération rejouable sans effet. */
export async function ingestBooking(b: ParsedBooking, watermark: Date, source: IngestSource): Promise<IngestOutcome> {
  const events = cfg().bookingEventIds;
  if (b.eventId && events.size && !events.has(b.eventId)) return 'ignored_event';
  if (!b.createdAt || b.createdAt.getTime() < watermark.getTime()) return 'ignored_watermark';

  return tx(async (client) => {
    await query(`SELECT pg_advisory_xact_lock(hashtext($1))`, [`booking:${b.callId}`], client);

    const existing = await query<{ audit_id: string | null; outcome: string }>('SELECT audit_id, outcome FROM bookings WHERE call_id=$1', [b.callId], client);
    if (existing.rows[0]) {
      await query('UPDATE bookings SET last_seen_at=now(), meeting_at=$2 WHERE call_id=$1', [b.callId, b.meetingAt], client);
      const row = existing.rows[0];
      if (row.audit_id) await applyBookingUpdate(client, row.audit_id, b);
      return 'duplicate';
    }

    if (b.cancelled) return insertBooking(client, b, null, null, 'ignored_cancelled', source);
    if (b.past) return insertBooking(client, b, null, null, 'ignored_past', source);

    const { domain } = extractBookingDomain(b.answers, b.email);
    const contact = { name: b.inviteeName, firstName: b.firstName, email: b.email, phone: b.phone, meetingAt: b.meetingAt };
    if (!domain) {
      const auditId = await createNeedsDomainAudit({ source, contact }, client);
      return insertBooking(client, b, auditId, null, 'needs_domain', source);
    }
    const { auditId, reused } = await createOrReuseAudit({ domain, source, contact }, client);
    return insertBooking(client, b, auditId, domain, reused ? 'reused' : 'created', source);
  });
}

async function insertBooking(c: Db, b: ParsedBooking, auditId: string | null, domain: string | null, outcome: IngestOutcome, source: IngestSource): Promise<IngestOutcome> {
  await query(
    `INSERT INTO bookings (call_id, event_id, audit_id, booked_at, meeting_at, invitee_name, invitee_email, invitee_phone, answers, domain, outcome, source)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)`,
    [b.callId, b.eventId, auditId, b.createdAt, b.meetingAt, b.inviteeName, b.email, b.phone, JSON.stringify(b.answers), domain, outcome, source],
    c,
  );
  return outcome;
}

/** Une réservation annulée avant son démarrage libère l'audit ; un rendez-vous déplacé met à jour la date. */
async function applyBookingUpdate(c: Db, auditId: string, b: ParsedBooking): Promise<void> {
  if (b.cancelled) {
    await query(`UPDATE jobs SET status='cancelled', finished_at=now(), updated_at=now() WHERE audit_id=$1 AND status='queued' AND claims=0`, [auditId], c);
    await query(`UPDATE audits SET status='failed', error='Réservation annulée avant le démarrage', updated_at=now() WHERE id=$1 AND status='queued' AND started_at IS NULL`, [auditId], c);
    return;
  }
  if (b.meetingAt) await query('UPDATE audits SET meeting_at=$2, updated_at=now() WHERE id=$1', [auditId, b.meetingAt], c);
}

export async function pollOnce(rows?: Array<Record<string, any>>): Promise<{ seen: number; created: number }> {
  const watermark = await getWatermark();
  if (!watermark) return { seen: 0, created: 0 };
  const list = rows ?? (await fetchAllEventCalls());
  let created = 0;
  for (const row of list) {
    const parsed = parseEventCall(row);
    if (!parsed) continue;
    try {
      const outcome = await ingestBooking(parsed, watermark, 'poller');
      if (outcome === 'created' || outcome === 'reused' || outcome === 'needs_domain') {
        created += 1;
        log.info('réservation prise en compte', { callId: parsed.callId, outcome });
      }
    } catch (e) {
      log.error('réservation non traitée', { callId: parsed.callId, error: errMsg(e) });
    }
  }
  return { seen: list.length, created };
}

export type PollerHandle = { stop: () => void; wake: () => void };

/** Adaptateur iClosed : sonde toutes les 2 minutes, le webhook ne fait que la déclencher. */
export function startPoller(): PollerHandle {
  let timer: NodeJS.Timeout | null = null;
  let busy = false;
  let pendingWake = false;
  let stopped = false;

  const run = async () => {
    if (busy) {
      pendingWake = true;
      return;
    }
    busy = true;
    try {
      const out = await pollOnce();
      if (out.created) log.info('sonde iClosed', out);
    } catch (e) {
      log.warn('sonde iClosed en échec', { error: errMsg(e) });
    } finally {
      busy = false;
      if (pendingWake && !stopped) {
        pendingWake = false;
        void run();
      }
    }
  };

  const schedule = () => {
    if (stopped) return;
    timer = setTimeout(async () => {
      await run();
      schedule();
    }, cfg().POLLER_INTERVAL_MS);
  };

  void run();
  schedule();

  return {
    stop: () => {
      stopped = true;
      if (timer) clearTimeout(timer);
    },
    wake: () => {
      void run();
    },
  };
}
