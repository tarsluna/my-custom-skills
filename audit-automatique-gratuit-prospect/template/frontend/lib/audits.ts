import 'server-only';
import { cache } from 'react';
import type { AuditLookup, ChatResponse, ChatTurn, PublicAudit } from './types';
import { apiBase, useFixtures } from './env';
import { isValidToken } from './safe';
import { fixtureAudit, fixtureChat } from './fixtures';

/** Dédupliqué par requête : la page et ses métadonnées lisent le même audit. */
export const getPublicAudit = cache(async (token: string): Promise<AuditLookup> => {
  if (!isValidToken(token)) return { kind: 'not_found' };
  if (useFixtures()) return fixtureAudit(token);
  const base = apiBase();
  if (!base) return { kind: 'unavailable' };
  try {
    const res = await fetch(`${base}/public/audits/${encodeURIComponent(token)}`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(12_000),
    });
    if (res.status === 404) return { kind: 'not_found' };
    if (!res.ok) return { kind: 'unavailable' };
    return { kind: 'ok', audit: normalize((await res.json()) as PublicAudit) };
  } catch {
    return { kind: 'unavailable' };
  }
});

/** Un audit en cours peut être partiel : la page ne doit jamais casser sur un champ absent. */
function normalize(a: PublicAudit): PublicAudit {
  return {
    ...a,
    contact: a.contact ?? { firstName: null },
    meetingAt: a.meetingAt ?? null,
    bookingUrl: a.bookingUrl ?? '',
    business: {
      ...a.business,
      specialties: a.business?.specialties ?? [],
      projectTypes: a.business?.projectTypes ?? [],
      summary: a.business?.summary ?? '',
    },
    competitors: {
      radiusKm: a.competitors?.radiusKm ?? null,
      widened: a.competitors?.widened ?? false,
      insights: a.competitors?.insights ?? [],
      items: a.competitors?.items ?? [],
    },
    creatives: a.creatives ?? [],
    projects: a.projects ?? [],
    setter: a.setter ?? { assistantName: '', firstProspectMessage: '', suggestedReplies: [] },
  };
}

export type ChatOutcome =
  | { kind: 'ok'; data: ChatResponse }
  | { kind: 'limit' }
  | { kind: 'not_found' }
  | { kind: 'error' };

export async function postChat(
  token: string,
  body: { sessionId: string; messages: ChatTurn[] },
  ip: string,
): Promise<ChatOutcome> {
  if (useFixtures()) return fixtureAudit(token).kind === 'ok' ? fixtureChat(body.messages) : { kind: 'not_found' };
  const base = apiBase();
  if (!base) return { kind: 'error' };
  try {
    const res = await fetch(`${base}/public/audits/${encodeURIComponent(token)}/chat`, {
      method: 'POST',
      cache: 'no-store',
      headers: { 'content-type': 'application/json', 'x-visitor-ip': ip, 'x-proxy-key': process.env.ADMIN_API_KEY ?? '' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(45_000),
    });
    if (res.status === 429) return { kind: 'limit' };
    if (res.status === 404) return { kind: 'not_found' };
    if (!res.ok) return { kind: 'error' };
    const json = (await res.json()) as Partial<ChatResponse>;
    const replies = Array.isArray(json.replies)
      ? json.replies.filter((r): r is string => typeof r === 'string' && r.trim().length > 0).slice(0, 2)
      : [];
    if (replies.length === 0 && !json.done) return { kind: 'error' };
    return { kind: 'ok', data: { replies, done: Boolean(json.done) } };
  } catch {
    return { kind: 'error' };
  }
}
