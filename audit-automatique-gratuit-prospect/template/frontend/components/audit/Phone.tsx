'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { initials } from '@/lib/format';
import { usePlate } from './usePlate';

type Msg = { id: number; role: 'user' | 'assistant'; text: string; failed?: boolean };
type Ended = null | 'done' | 'limit';

const MAX_MESSAGES = 40;
const MAX_CHARS = 500;

const wait = (ms: number) => new Promise<void>((r) => window.setTimeout(r, ms));
const typingFor = (text: string) => Math.min(3000, 750 + text.length * 22);

function useReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const q = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(q.matches);
    const on = () => setReduced(q.matches);
    q.addEventListener('change', on);
    return () => q.removeEventListener('change', on);
  }, []);
  return reduced;
}

function nowLabel() {
  return new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit' }).format(new Date());
}

function newSessionId() {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `s-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

type Props = {
  token: string;
  businessName: string;
  logoUrl: string | null;
  firstMessage: string;
  suggested: string[];
};

export function Phone({ token, businessName, logoUrl, firstMessage, suggested }: Props) {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [draft, setDraft] = useState('');
  const [typing, setTyping] = useState(false);
  const [busy, setBusy] = useState(false);
  const [ended, setEnded] = useState<Ended>(null);
  const [chips, setChips] = useState<string[]>(() => suggested.filter(Boolean));
  const [clock, setClock] = useState('9:41');

  const root = useRef<HTMLDivElement>(null);
  const list = useRef<HTMLDivElement>(null);
  const history = useRef<Msg[]>([]);
  const ids = useRef(0);
  const epoch = useRef(0);
  const session = useRef('');
  const started = useRef(false);
  const reduced = useReducedMotion();
  const plate = usePlate(logoUrl);

  const commit = useCallback((next: Msg[]) => {
    history.current = next;
    setMsgs(next);
  }, []);

  useEffect(() => {
    session.current = newSessionId();
    setClock(nowLabel());
    const t = window.setInterval(() => setClock(nowLabel()), 20_000);
    return () => {
      window.clearInterval(t);
      epoch.current += 1;
    };
  }, []);

  useEffect(() => {
    const el = list.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: reduced ? 'auto' : 'smooth' });
  }, [msgs, typing, chips, ended, reduced]);

  const deliver = useCallback(async () => {
    const run = epoch.current;
    const alive = () => run === epoch.current;
    setBusy(true);
    await wait(reduced ? 150 : 700);
    if (!alive()) return;
    setTyping(true);

    const fail = () => {
      if (!alive()) return;
      setTyping(false);
      setBusy(false);
      const copy = [...history.current];
      for (let i = copy.length - 1; i >= 0; i--) {
        if (copy[i].role === 'user') {
          copy[i] = { ...copy[i], failed: true };
          break;
        }
      }
      commit(copy);
    };

    let response: Response;
    const started = performance.now();
    try {
      response = await fetch(`/api/chat/${encodeURIComponent(token)}`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          sessionId: session.current,
          messages: history.current.filter((m) => !m.failed).map((m) => ({ role: m.role, content: m.text })),
        }),
      });
    } catch {
      fail();
      return;
    }
    if (!alive()) return;

    if (response.status === 429) {
      setTyping(false);
      setBusy(false);
      setEnded('limit');
      return;
    }
    if (!response.ok) {
      fail();
      return;
    }

    let data: { replies?: unknown; done?: unknown };
    try {
      data = await response.json();
    } catch {
      fail();
      return;
    }
    if (!alive()) return;

    const replies = Array.isArray(data.replies) ? data.replies.filter((r): r is string => typeof r === 'string' && r.trim() !== '').slice(0, 2) : [];
    const elapsed = performance.now() - started;

    for (let i = 0; i < replies.length; i++) {
      const text = replies[i];
      if (i > 0) {
        await wait(reduced ? 120 : 480);
        if (!alive()) return;
        setTyping(true);
      }
      const hold = reduced ? 200 : Math.max(280, typingFor(text) - (i === 0 ? elapsed : 0));
      await wait(hold);
      if (!alive()) return;
      setTyping(false);
      ids.current += 1;
      commit([...history.current, { id: ids.current, role: 'assistant', text }]);
    }

    setTyping(false);
    setBusy(false);
    if (data.done === true) setEnded('done');
    else if (history.current.length >= MAX_MESSAGES) setEnded('limit');
  }, [commit, reduced, token]);

  const send = useCallback(
    (raw: string) => {
      const text = raw.trim().slice(0, MAX_CHARS);
      if (!text || busy || ended) return;
      setDraft('');
      setChips((c) => c.filter((x) => x !== text));
      ids.current += 1;
      commit([...history.current, { id: ids.current, role: 'user', text }]);
      void deliver();
    },
    [busy, commit, deliver, ended],
  );

  const retry = useCallback(() => {
    if (busy) return;
    commit(history.current.map((m) => (m.failed ? { ...m, failed: false } : m)));
    void deliver();
  }, [busy, commit, deliver]);

  const begin = useCallback(async () => {
    const run = epoch.current;
    if (!firstMessage) return;
    if (!reduced) {
      await wait(450);
      if (run !== epoch.current) return;
      setDraft(firstMessage);
      await wait(1300);
      if (run !== epoch.current) return;
    }
    setDraft('');
    ids.current += 1;
    commit([{ id: ids.current, role: 'user', text: firstMessage }]);
    void deliver();
  }, [commit, deliver, firstMessage, reduced]);

  /* Le téléphone arrive à l'écran : le prospect envoie son premier message. */
  useEffect(() => {
    const el = root.current;
    if (!el || started.current) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true;
          io.disconnect();
          void begin();
        }
      },
      { threshold: 0.5 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [begin]);

  const restart = () => {
    epoch.current += 1;
    session.current = newSessionId();
    setTyping(false);
    setBusy(false);
    setEnded(null);
    setDraft('');
    setChips(suggested.filter(Boolean));
    commit([]);
    void begin();
  };

  const lastUserId = [...msgs].reverse().find((m) => m.role === 'user')?.id;
  const canType = !busy && !ended;

  return (
    <div className="iph-wrap" data-m="phone" data-m-from="1" data-m-to=".5">
      <div className="iph" ref={root}>
        <span className="iph__btn iph__btn--silent" aria-hidden="true" />
        <span className="iph__btn iph__btn--up" aria-hidden="true" />
        <span className="iph__btn iph__btn--down" aria-hidden="true" />
        <span className="iph__btn iph__btn--side" aria-hidden="true" />

        <div className="iph__screen">
          <div className="iph__island" aria-hidden="true" />

          <div className="iph__status" aria-hidden="true">
            <span className="iph__time">{clock}</span>
            <span className="iph__icons">
              <svg width="18" height="12" viewBox="0 0 18 12">
                <rect x="0" y="8" width="3" height="4" rx=".8" />
                <rect x="5" y="5.5" width="3" height="6.5" rx=".8" />
                <rect x="10" y="3" width="3" height="9" rx=".8" />
                <rect x="15" y="0" width="3" height="12" rx=".8" />
              </svg>
              <svg width="17" height="12" viewBox="0 0 17 12">
                <path d="M8.5 2.4c2.4 0 4.6.9 6.3 2.5l1.2-1.3A10.8 10.8 0 0 0 8.5.6C5.6.6 3 1.7 1 3.6l1.2 1.3a9.1 9.1 0 0 1 6.3-2.5Z" />
                <path d="M8.5 6.3c1.4 0 2.6.5 3.6 1.4l1.3-1.3a7 7 0 0 0-9.8 0l1.3 1.3a5.2 5.2 0 0 1 3.6-1.4Z" />
                <path d="M8.5 8.4c-.8 0-1.5.3-2 .8l2 2.2 2-2.2c-.5-.5-1.2-.8-2-.8Z" />
              </svg>
              <svg width="27" height="13" viewBox="0 0 27 13">
                <rect x=".5" y=".5" width="23" height="12" rx="3.6" fill="none" stroke="currentColor" opacity=".4" />
                <rect x="2" y="2" width="20" height="9" rx="2.2" />
                <path d="M25 4.5c.9.3 1.5 1.1 1.5 2s-.6 1.7-1.5 2Z" opacity=".5" />
              </svg>
            </span>
          </div>

          <header className="iph__head">
            <span className="iph__back" aria-hidden="true">
              <svg width="11" height="19" viewBox="0 0 11 19">
                <path d="M9.5 1.5 2 9.5l7.5 8" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
            <div className="iph__contact">
              <span className="iph__avatar" style={plate ? { background: plate } : undefined}>
                {logoUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={logoUrl} alt="" />
                ) : (
                  <span>{initials(businessName)}</span>
                )}
              </span>
              <span className="iph__name">
                {businessName}
                <svg width="6" height="10" viewBox="0 0 6 10" aria-hidden="true">
                  <path d="m1 1 4 4-4 4" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
            </div>
            <span className="iph__video" aria-hidden="true">
              <svg width="26" height="18" viewBox="0 0 26 18">
                <rect x="0" y="1" width="18" height="16" rx="4" fill="currentColor" />
                <path d="M20 7.2 25.2 3v12L20 10.8Z" fill="currentColor" />
              </svg>
            </span>
          </header>

          <div className="iph__list" ref={list} role="log" aria-live="polite" aria-label={`Conversation avec ${businessName}`}>
            <p className="iph__stamp">
              <b>Aujourd’hui</b> {clock}
            </p>

            {msgs.map((m, i) => {
              const next = msgs[i + 1];
              const tail = !next || next.role !== m.role;
              return (
                <div key={m.id} className={`msg msg--${m.role === 'user' ? 'me' : 'them'}${tail ? ' msg--tail' : ''}`}>
                  <p className="msg__bubble">{m.text}</p>
                  {m.failed ? (
                    <button type="button" className="msg__failed" onClick={retry} disabled={busy}>
                      Non distribué. Toucher pour réessayer.
                    </button>
                  ) : m.id === lastUserId && !next && !typing && !busy ? (
                    <span className="msg__status">Distribué</span>
                  ) : null}
                </div>
              );
            })}

            {typing ? (
              <div className="msg msg--them msg--tail" aria-label="L’entreprise écrit">
                <p className="msg__bubble msg__typing">
                  <i />
                  <i />
                  <i />
                </p>
              </div>
            ) : null}

            {ended ? (
              <p className="iph__end">
                {ended === 'done'
                  ? 'La conversation s’arrête ici. La suite se passe à votre rendez-vous.'
                  : 'Cet essai s’arrête ici. Nous le reprendrons avec vous à votre rendez-vous.'}
              </p>
            ) : null}
          </div>

          {chips.length > 0 && !ended ? (
            <div className="iph__chips">
              {chips.map((c) => (
                <button key={c} type="button" onClick={() => send(c)} disabled={!canType}>
                  {c}
                </button>
              ))}
            </div>
          ) : null}

          <form
            className="iph__compose"
            onSubmit={(e) => {
              e.preventDefault();
              send(draft);
            }}
          >
            <span className="iph__plus" aria-hidden="true">
              <svg width="14" height="14" viewBox="0 0 14 14">
                <path d="M7 1v12M1 7h12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
            </span>
            <div className="iph__field">
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                maxLength={MAX_CHARS}
                placeholder={ended ? 'Conversation terminée' : 'iMessage'}
                aria-label="Votre message"
                disabled={Boolean(ended)}
                enterKeyHint="send"
                autoComplete="off"
              />
              <button type="submit" className="iph__send" disabled={!draft.trim() || !canType} aria-label="Envoyer">
                <svg width="14" height="16" viewBox="0 0 14 16" aria-hidden="true">
                  <path d="M7 14.5V2M2 6.5 7 1.5l5 5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </form>
          <div className="iph__homebar" aria-hidden="true" />
        </div>
      </div>

      <button type="button" className="iph__restart" onClick={restart}>
        Recommencer la conversation
      </button>
    </div>
  );
}
