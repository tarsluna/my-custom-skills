'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { AdminAuditRow, AdminStats, AdminStatus } from '@/lib/types';
import { meetingShort } from '@/lib/format';
import { normalizeDomain } from '@/lib/domain';
import { AdminBar, AdminLogo, CopyLink, isRunning, StatusChip } from './shared';

const FILTERS: Array<{ key: string; label: string; match: (s: AdminStatus) => boolean }> = [
  { key: 'all', label: 'Tous', match: () => true },
  { key: 'running', label: 'En cours', match: isRunning },
  { key: 'ready', label: 'Prêts', match: (s) => s === 'ready' },
  { key: 'needs_domain', label: 'Domaine manquant', match: (s) => s === 'needs_domain' },
  { key: 'failed', label: 'Erreurs', match: (s) => s === 'failed' },
];

type Prefill = { rowId: string; name: string | null; email: string | null } | null;

export function AdminHome({
  initialAudits,
  initialStats,
  backendDown,
}: {
  initialAudits: AdminAuditRow[];
  initialStats: AdminStats | null;
  backendDown: boolean;
}) {
  const [audits, setAudits] = useState(initialAudits);
  const [stats, setStats] = useState(initialStats);
  const [down, setDown] = useState(backendDown);
  const [filter, setFilter] = useState('all');
  const [q, setQ] = useState('');
  const [domain, setDomain] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [prefill, setPrefill] = useState<Prefill>(null);
  const [formMsg, setFormMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [sending, setSending] = useState(false);
  const domainInput = useRef<HTMLInputElement>(null);
  const qRef = useRef(q);
  qRef.current = q;

  const refresh = useCallback(async () => {
    const params = new URLSearchParams();
    if (qRef.current.trim()) params.set('q', qRef.current.trim());
    const res = await fetch(`/api/admin/audits?${params}`, { cache: 'no-store' }).catch(() => null);
    if (res?.status === 401) {
      window.location.href = '/admin/login';
      return;
    }
    if (!res?.ok) {
      setDown(true);
      return;
    }
    const data = (await res.json()) as { audits: AdminAuditRow[]; stats: AdminStats | null };
    setDown(false);
    setAudits(data.audits);
    if (data.stats) setStats(data.stats);
  }, []);

  useEffect(() => {
    const tick = () => {
      if (document.visibilityState === 'visible') void refresh();
    };
    const t = window.setInterval(tick, 4000);
    return () => window.clearInterval(t);
  }, [refresh]);

  useEffect(() => {
    const t = window.setTimeout(() => void refresh(), 250);
    return () => window.clearTimeout(t);
  }, [q, refresh]);

  const launch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (sending) return;
    const clean = normalizeDomain(domain);
    if (!clean) {
      setFormMsg({ ok: false, text: 'Ce domaine n’est pas valide. Exemple : exemple.fr' });
      return;
    }
    setSending(true);
    setFormMsg(null);
    /* Un audit sans domaine garde son rendez-vous : on le complète au lieu d'en créer un autre. */
    const res = await fetch(prefill ? `/api/admin/audits/${encodeURIComponent(prefill.rowId)}/rerun` : '/api/admin/audits', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(prefill ? { domain: clean } : { domain: clean, contact: { name, email } }),
    }).catch(() => null);
    setSending(false);
    if (!res?.ok) {
      const err = (await res?.json().catch(() => null)) as { error?: string } | null;
      setFormMsg({ ok: false, text: err?.error && err.error !== 'upstream' && err.error !== 'invalid_domain' ? err.error : 'Lancement impossible. Réessayez.' });
      return;
    }
    setFormMsg({ ok: true, text: `Audit lancé pour ${clean}.` });
    setDomain('');
    setName('');
    setEmail('');
    setPrefill(null);
    void refresh();
  };

  const fillFrom = (row: AdminAuditRow) => {
    setPrefill({ rowId: row.id, name: row.contactName, email: row.contactEmail });
    setName(row.contactName ?? '');
    setEmail(row.contactEmail ?? '');
    setDomain('');
    setFormMsg(null);
    domainInput.current?.focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const active = FILTERS.find((f) => f.key === filter) ?? FILTERS[0];
  const rows = audits.filter((a) => active.match(a.status));
  const count = (f: (typeof FILTERS)[number]) => audits.filter((a) => f.match(a.status)).length;

  return (
    <>
      <AdminBar>
        <dl className="adm-stats">
          <div>
            <dt>Crédits kie</dt>
            <dd>{stats?.kieCredits != null ? stats.kieCredits.toLocaleString('fr-FR') : '—'}</dd>
          </div>
          <div>
            <dt>Audits du jour</dt>
            <dd>
              {stats?.auditsToday ?? '—'}
              {stats?.maxAuditsPerDay ? <small> / {stats.maxAuditsPerDay}</small> : null}
            </dd>
          </div>
        </dl>
      </AdminBar>

      <main className="adm-main">
        {down ? <p className="adm-alert">Le backend ne répond pas. Les données affichées peuvent être anciennes.</p> : null}

        <form className="adm-launch" onSubmit={launch}>
          <div className="adm-launch__head">
            <h1 className="adm-h">Lancer un audit</h1>
            {prefill ? (
              <p className="adm-launch__for">
                Domaine à renseigner pour {prefill.name ?? prefill.email ?? 'ce contact'}
                <button
                  type="button"
                  className="adm-link"
                  onClick={() => {
                    setPrefill(null);
                    setName('');
                    setEmail('');
                  }}
                >
                  Annuler
                </button>
              </p>
            ) : null}
          </div>
          <div className="adm-launch__row">
            <label className="adm-f adm-f--grow">
              <span>Domaine</span>
              <input ref={domainInput} value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="exemple.fr" inputMode="url" autoCapitalize="off" spellCheck={false} required />
            </label>
            <label className="adm-f">
              <span>Contact (facultatif)</span>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Prénom Nom" disabled={Boolean(prefill)} />
            </label>
            <label className="adm-f">
              <span>E-mail (facultatif)</span>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="contact@exemple.fr" disabled={Boolean(prefill)} />
            </label>
            <button type="submit" className="btn btn--sm adm-launch__go" disabled={sending}>
              {sending ? 'Lancement' : 'Lancer l’audit'}
            </button>
          </div>
          {formMsg ? <p className={formMsg.ok ? 'adm-note adm-note--ok' : 'adm-note adm-note--ko'} role="status">{formMsg.text}</p> : null}
        </form>

        <div className="adm-tools">
          <div className="adm-filters" role="tablist" aria-label="Filtrer par statut">
            {FILTERS.map((f) => (
              <button key={f.key} type="button" role="tab" aria-selected={f.key === filter} className={f.key === filter ? 'is-on' : ''} onClick={() => setFilter(f.key)}>
                {f.label}
                <small>{count(f)}</small>
              </button>
            ))}
          </div>
          <input className="adm-search" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Entreprise, domaine, contact" aria-label="Rechercher" />
        </div>

        <div className="adm-table" role="table">
          <div className="adm-tr adm-tr--head" role="row">
            <span role="columnheader">Entreprise</span>
            <span role="columnheader">Domaine</span>
            <span role="columnheader">Statut</span>
            <span role="columnheader">Rendez-vous</span>
            <span role="columnheader">Actions</span>
          </div>
          {rows.length === 0 ? <p className="adm-empty">Aucun audit ici.</p> : null}
          {rows.map((a) => {
            const label = a.businessName ?? a.contactName ?? a.contactEmail ?? 'Sans nom';
            const sub = [a.professionLabel, a.city].filter(Boolean).join(' · ');
            return (
              <div className="adm-tr" role="row" key={a.id}>
                <span className="adm-td adm-biz" role="cell">
                  <AdminLogo name={label} url={a.logoUrl} />
                  <span className="adm-cab__t">
                    <a href={`/admin/audits/${encodeURIComponent(a.id)}`}>{label}</a>
                    {sub ? <small>{sub}</small> : null}
                  </span>
                </span>
                <span className="adm-td adm-mono" role="cell" data-l="Domaine">
                  {a.domain ?? '—'}
                </span>
                <span className="adm-td" role="cell" data-l="Statut">
                  <StatusChip status={a.status} />
                </span>
                <span className="adm-td adm-mono" role="cell" data-l="Rendez-vous">
                  {meetingShort(a.meetingAt)}
                </span>
                <span className="adm-td adm-actions" role="cell">
                  {a.status === 'needs_domain' ? (
                    <button type="button" className="adm-btn adm-btn--main" onClick={() => fillFrom(a)}>
                      Renseigner le domaine
                    </button>
                  ) : (
                    <>
                      <CopyLink token={a.token} />
                      {a.token ? (
                        <a className="adm-btn" href={`/c/${encodeURIComponent(a.token)}`} target="_blank" rel="noopener noreferrer">
                          Ouvrir
                        </a>
                      ) : (
                        <span className="adm-btn is-off">Ouvrir</span>
                      )}
                    </>
                  )}
                </span>
              </div>
            );
          })}
        </div>
      </main>
    </>
  );
}
