import { cfg } from '../config.js';

export type BookingAnswerEntry = { statement: string; answer: string };

export type ParsedBooking = {
  callId: string;
  eventId: string | null;
  createdAt: Date | null;
  meetingAt: Date | null;
  inviteeName: string | null;
  firstName: string | null;
  email: string | null;
  phone: string | null;
  answers: BookingAnswerEntry[];
  cancelled: boolean;
  past: boolean;
};

function text(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  if (typeof value === 'object') return null;
  const s = String(value).trim();
  return s && !/^(null|undefined)$/i.test(s) ? s : null;
}

function date(value: unknown): Date | null {
  const s = text(value);
  if (!s) return null;
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? null : d;
}

function answersOf(row: Record<string, any>): BookingAnswerEntry[] {
  const out: BookingAnswerEntry[] = [];
  for (const list of [row.questions, row.secondaryAnswers]) {
    if (!Array.isArray(list)) continue;
    for (const entry of list) {
      const statement = text(entry?.statement);
      const answer = text(entry?.answer);
      if (statement && answer) out.push({ statement, answer });
    }
  }
  return out;
}

const FIRST_NAME_STATEMENT = /^(first\s*name|pr[ée]nom)/i;

/** Une ligne de GET /v1/eventCalls. `callId`, sinon `id`, identifie la réservation. */
export function parseEventCall(row: Record<string, any>, now: Date = new Date()): ParsedBooking | null {
  const callId = text(row.callId) ?? text(row.id);
  if (!callId) return null;
  const answers = answersOf(row);
  const inviteeName = text(row.inviteeName);
  const firstFromForm = answers.find((a) => FIRST_NAME_STATEMENT.test(a.statement))?.answer ?? null;
  const firstName = firstFromForm ?? (inviteeName ? inviteeName.split(/\s+/)[0] : null);
  const cancelled = Boolean(text(row.cancelledBy) || text(row.cancelReason) || text(row.deletedAt));
  const meetingAt = date(row.dateTimeUTC);
  return {
    callId,
    eventId: text(row.eventId),
    createdAt: date(row.createdAt),
    meetingAt,
    inviteeName,
    firstName,
    email: text(row.inviteeEmail)?.toLowerCase() ?? null,
    phone: text(row.phoneNumber),
    answers,
    cancelled,
    past: meetingAt ? meetingAt.getTime() < now.getTime() : false,
  };
}

/**
 * Toutes les réservations visibles. iClosed ignore le filtre `eventId` côté serveur et ne trie pas par date de création
 * : on lit toutes les pages et l'appelant filtre sur l'identifiant d'événement.
 */
export async function fetchAllEventCalls(fetcher: typeof fetch = fetch): Promise<Array<Record<string, any>>> {
  const key = cfg().ICLOSED_API_KEY;
  if (!key) return [];
  const rows: Array<Record<string, any>> = [];
  for (let page = 0; page < 50; page += 1) {
    const query = new URLSearchParams({ limit: '100', page: String(page) });
    if (cfg().bookingEventIds.size === 1) query.set('eventId', [...cfg().bookingEventIds][0]);
    const res = await fetcher(`https://public.api.iclosed.io/v1/eventCalls?${query}`, {
      headers: { authorization: `Bearer ${key}` },
      signal: AbortSignal.timeout(30_000),
    });
    if (!res.ok) throw new Error(`iClosed : réponse ${res.status}`);
    const body = (await res.json()) as { data?: { eventCalls?: Array<Record<string, any>> } };
    const batch = body.data?.eventCalls ?? [];
    rows.push(...batch);
    if (batch.length < 100) break;
  }
  return rows;
}
