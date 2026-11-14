import { z } from 'zod';
import type { ParsedBooking } from './lib/iclosed.js';

/**
 * Adaptateur générique : tout outil de prise de rendez-vous (Calendly, Cal.com, formulaire maison, Zapier, Make)
 * envoie ce format à POST /webhooks/booking. Le champ `id` rend l'envoi rejouable sans effet.
 */
const GenericBooking = z.object({
  id: z.union([z.string().min(1).max(200), z.number()]).transform(String),
  eventId: z.union([z.string(), z.number()]).transform(String).nullish(),
  createdAt: z.string().datetime({ offset: true }).nullish(),
  meetingAt: z.string().datetime({ offset: true }).nullish(),
  name: z.string().max(200).nullish(),
  firstName: z.string().max(100).nullish(),
  email: z.string().max(320).nullish(),
  phone: z.string().max(50).nullish(),
  /** Le site du prospect, s'il est connu. Sinon il est cherché dans `answers`, puis dans le domaine de l'e-mail. */
  website: z.string().max(500).nullish(),
  answers: z.array(z.object({ question: z.string().max(300), answer: z.string().max(2000) })).max(50).nullish(),
  cancelled: z.boolean().nullish(),
});

export function parseGenericBooking(input: unknown, now: Date = new Date()): ParsedBooking | null {
  const parsed = GenericBooking.safeParse(input);
  if (!parsed.success) return null;
  const b = parsed.data;
  const meetingAt = b.meetingAt ? new Date(b.meetingAt) : null;
  const answers = (b.answers ?? []).map((a) => ({ statement: a.question, answer: a.answer }));
  if (b.website) answers.unshift({ statement: 'Site web', answer: b.website });
  return {
    callId: b.id,
    eventId: b.eventId ?? null,
    createdAt: b.createdAt ? new Date(b.createdAt) : now,
    meetingAt,
    inviteeName: b.name ?? null,
    firstName: b.firstName ?? (b.name ? b.name.split(/\s+/)[0] : null),
    email: b.email?.toLowerCase() ?? null,
    phone: b.phone ?? null,
    answers,
    cancelled: Boolean(b.cancelled),
    past: meetingAt ? meetingAt.getTime() < now.getTime() : false,
  };
}
