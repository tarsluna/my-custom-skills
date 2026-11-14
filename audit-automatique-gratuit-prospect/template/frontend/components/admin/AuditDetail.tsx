'use client';

import { useCallback, useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import type { AdminAuditDetail, AdminCreative, Format } from '@/lib/types';
import { meetingShort } from '@/lib/format';
import { AdminBar, AdminLogo, CopyLink, isRunning, StatusChip } from './shared';

const MAX_VISIBLE = 3;
const RATIO: Record<Format, number> = { '4:5': 0.8, '9:16': 0.5625, '1:1': 1 };
const dateTime = (iso: string | null) => (iso ? meetingShort(iso) : '—');
const STEP_STATUS: Record<string, string> = { done: 'Fait', ok: 'Fait', success: 'Fait', running: 'En cours', started: 'En cours', pending: 'En attente', failed: 'Erreur', error: 'Erreur' };

async function errorText(res: Response | null, fallback: string): Promise<string> {
  const data = (await res?.json().catch(() => null)) as { error?: string } | null;
  return data?.error && data.error !== 'upstream' ? data.error : fallback;
}

function TwoStep({
  label,
  confirm,
  onConfirm,
  disabled,
  className,
}: {
  label: string;
  confirm: string;
  onConfirm: () => void;
  disabled?: boolean;
  className?: string;
}) {
  const [armed, setArmed] = useState(false);
  useEffect(() => {
    if (!armed) return;
    const t = window.setTimeout(() => setArmed(false), 4000);
    return () => window.clearTimeout(t);
  }, [armed]);
  return (
    <button
      type="button"
      disabled={disabled}
      className={`${className ?? 'adm-btn'}${armed ? ' is-armed' : ''}`}
      onClick={() => {
        if (armed) {
          setArmed(false);
          onConfirm();
        } else setArmed(true);
      }}
    >
      {armed ? confirm : label}
    </button>
  );
}

export function AuditDetail({ initial }: { initial: AdminAuditDetail }) {
  const [audit, setAudit] = useState(initial);
  const [regen, setRegen] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const id = encodeURIComponent(audit.id);

  const refresh = useCallback(async () => {
    const res = await fetch(`/api/admin/audits/${id}`, { cache: 'no-store' }).catch(() => null);
    if (res?.status === 401) {
      window.location.href = '/admin/login';
      return;
    }
    if (!res?.ok) return;
    const data = (await res.json()) as { audit: AdminAuditDetail };
    setAudit(data.audit);
    setRegen((prev) => {
      const next = { ...prev };
      for (const c of data.audit.creatives) {
        if (next[c.id] && next[c.id] !== c.imageUrl) delete next[c.id];
      }
      return next;
    });
  }, [id]);

  const pending = isRunning(audit.status) || Object.keys(regen).length > 0;
  useEffect(() => {
    if (!pending) return;
    const t = window.setInterval(() => void refresh(), 4000);
    return () => window.clearInterval(t);
  }, [pending, refresh]);

  const visible = audit.creatives.filter((c) => !c.locked).length;

  const toggle = async (c: AdminCreative) => {
    if (c.locked && visible >= MAX_VISIBLE) {
      setMsg({ ok: false, text: `${MAX_VISIBLE} créatives visibles au maximum. Verrouillez-en d’abord une autre.` });
      return;
    }
    setBusyId(c.id);
    setMsg(null);
    const res = await fetch(`/api/admin/audits/${id}/creatives/${encodeURIComponent(c.id)}`, {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ locked: !c.locked }),
    }).catch(() => null);
    setBusyId(null);
    if (!res?.ok) {
      setMsg({ ok: false, text: await errorText(res, 'Modification impossible. Réessayez.') });
      return;
    }
    setAudit((a) => ({ ...a, creatives: a.creatives.map((x) => (x.id === c.id ? { ...x, locked: !c.locked } : x)) }));
  };

  const regenerate = async (c: AdminCreative) => {
    setMsg(null);
    const res = await fetch(`/api/admin/audits/${id}/creatives/${encodeURIComponent(c.id)}/regenerate`, { method: 'POST' }).catch(() => null);
    if (!res?.ok) {
      setMsg({ ok: false, text: await errorText(res, 'Régénération impossible. Réessayez.') });
      return;
    }
    setRegen((p) => ({ ...p, [c.id]: c.imageUrl }));
    setMsg({ ok: true, text: `Créative ${c.index} en cours de régénération.` });
    window.setTimeout(() => {
      setRegen((p) => {
        const n = { ...p };
        delete n[c.id];
        return n;
      });
    }, 300_000);
  };

  const rerun = async () => {
    setMsg(null);
    const res = await fetch(`/api/admin/audits/${id}/rerun`, { method: 'POST' }).catch(() => null);
    if (!res?.ok) {
      setMsg({ ok: false, text: await errorText(res, 'Relance impossible. Réessayez.') });
      return;
    }
    setMsg({ ok: true, text: 'Audit relancé.' });
    void refresh();
  };

  const name = audit.businessName ?? audit.contactName ?? 'Sans nom';
  const costs = audit.costs;

  return (
    <>
      <AdminBar />
      <main className="adm-main">
        <a className="adm-link adm-back" href="/admin">
          Tous les audits
        </a>

        <section className="adm-summary">
          <div className="adm-summary__id">
            <AdminLogo name={name} url={audit.logoUrl} />
            <div>
              <h1 className="adm-title">{name}</h1>
              <p className="adm-mono">{[audit.domain, audit.professionLabel, audit.city].filter(Boolean).join(' · ') || '—'}</p>
            </div>
            <StatusChip status={audit.status} />
          </div>
          <div className="adm-summary__act">
            <CopyLink token={audit.token} />
            {audit.token ? (
              <a className="adm-btn" href={`/c/${encodeURIComponent(audit.token)}`} target="_blank" rel="noopener noreferrer">
                Ouvrir
              </a>
            ) : null}
            <TwoStep label="Relancer l’audit" confirm="Confirmer la relance" onConfirm={rerun} disabled={isRunning(audit.status) || audit.status === 'needs_domain'} />
          </div>
        </section>

        {audit.error ? <p className="adm-alert">{audit.error}</p> : null}
        {audit.status === 'needs_domain' ? (
          <p className="adm-alert">
            Domaine manquant. <a href="/admin">Renseignez-le depuis la liste</a> pour lancer cet audit.
          </p>
        ) : null}
        {msg ? <p className={msg.ok ? 'adm-note adm-note--ok' : 'adm-note adm-note--ko'} role="status">{msg.text}</p> : null}

        <dl className="adm-facts">
          <div>
            <dt>Contact</dt>
            <dd>{audit.contactName ?? '—'}</dd>
          </div>
          <div>
            <dt>E-mail</dt>
            <dd className="adm-mono">{audit.contactEmail ?? '—'}</dd>
          </div>
          <div>
            <dt>Rendez-vous</dt>
            <dd className="adm-mono">{dateTime(audit.meetingAt)}</dd>
          </div>
          <div>
            <dt>Créé le</dt>
            <dd className="adm-mono">{dateTime(audit.createdAt)}</dd>
          </div>
          <div>
            <dt>Crédits kie</dt>
            <dd className="adm-mono">{costs.kieCredits ?? '—'}</dd>
          </div>
          <div>
            <dt>Générations</dt>
            <dd className="adm-mono">{costs.generations ?? '—'}</dd>
          </div>
          <div>
            <dt>LLM</dt>
            <dd className="adm-mono">{costs.llmUsd != null ? `${costs.llmUsd.toFixed(2)} $` : '—'}</dd>
          </div>
          <div>
            <dt>Apify</dt>
            <dd className="adm-mono">{costs.apifyUsd != null ? `${costs.apifyUsd.toFixed(2)} $` : '—'}</dd>
          </div>
        </dl>

        <section className="adm-section">
          <div className="adm-section__head">
            <h2 className="adm-h">Créatives</h2>
            <p className={`adm-count${visible === MAX_VISIBLE ? '' : ' adm-count--warn'}`}>
              {visible} visible{visible > 1 ? 's' : ''} sur {audit.creatives.length} · objectif {MAX_VISIBLE}
            </p>
          </div>
          {audit.creatives.length === 0 ? <p className="adm-empty">Aucune créative pour l’instant.</p> : null}
          <ul className="adm-creas">
            {audit.creatives.map((c) => (
              <li key={c.id} className={`adm-crea${c.locked ? ' is-locked' : ''}`}>
                <div className="adm-crea__img" style={{ ['--r' as string]: RATIO[c.format] ?? 0.8 } as CSSProperties}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  {c.imageUrl ? <img src={c.imageUrl} alt={c.headline ?? c.concept} loading="lazy" /> : null}
                  {regen[c.id] ? <span className="adm-crea__busy">Régénération</span> : null}
                </div>
                <div className="adm-crea__meta">
                  <p className="adm-crea__tag">
                    <span>
                      {String(c.index).padStart(2, '0')} · {c.format}
                    </span>
                    <span className={c.locked ? 'tag-lock' : 'tag-open'}>{c.status && c.status !== 'ready' ? c.status : c.locked ? 'Floutée' : 'Visible'}</span>
                  </p>
                  <h3>{c.concept}</h3>
                  {c.angle ? <p className="adm-crea__angle">{c.angle}</p> : null}
                  {c.headline ? <p className="adm-crea__head">{c.headline}</p> : null}
                  {c.primaryText ? <p>{c.primaryText}</p> : null}
                  {c.bullets.length ? (
                    <ul>
                      {c.bullets.map((b) => (
                        <li key={b}>{b}</li>
                      ))}
                    </ul>
                  ) : null}
                  {c.cta ? <p className="adm-crea__cta">{c.cta}</p> : null}
                  <div className="adm-crea__act">
                    <button type="button" className="adm-btn" disabled={busyId === c.id} onClick={() => void toggle(c)}>
                      {c.locked ? 'Rendre visible' : 'Verrouiller'}
                    </button>
                    <TwoStep label="Régénérer" confirm="Confirmer" disabled={Boolean(regen[c.id])} onConfirm={() => void regenerate(c)} />
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="adm-section">
          <div className="adm-section__head">
            <h2 className="adm-h">Journal des étapes</h2>
          </div>
          {audit.steps.length === 0 ? <p className="adm-empty">Pas encore d’étape enregistrée.</p> : null}
          <ol className="adm-log">
            {audit.steps.map((s) => (
              <li key={`${s.name}-${s.at ?? ''}`}>
                <span className="adm-mono">{dateTime(s.at)}</span>
                <span className="adm-log__label">{s.label}</span>
                <span className="adm-mono adm-log__status">{STEP_STATUS[s.status] ?? s.status}</span>
                <span className="adm-log__detail">{s.detail ?? ''}</span>
              </li>
            ))}
          </ol>
        </section>
      </main>
    </>
  );
}
