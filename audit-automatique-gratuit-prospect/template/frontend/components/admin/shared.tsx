'use client';

import { useState } from 'react';
import type { AdminStatus } from '@/lib/types';
import { initials } from '@/lib/format';
import { safeImg } from '@/lib/safe';

export const STATUS_LABEL: Record<AdminStatus, string> = {
  queued: 'En file',
  analyzing: 'Analyse du site',
  ads: 'Concurrents',
  creatives: 'Créatives',
  ready: 'Prêt',
  failed: 'Erreur',
  needs_domain: 'Domaine manquant',
};

export const isRunning = (s: AdminStatus) => s === 'queued' || s === 'analyzing' || s === 'ads' || s === 'creatives';

export function StatusChip({ status }: { status: AdminStatus }) {
  return (
    <span className={`chip chip--${status}${isRunning(status) ? ' chip--live' : ''}`}>
      <i aria-hidden="true" />
      {STATUS_LABEL[status]}
    </span>
  );
}

export function AdminLogo({ name, url }: { name: string; url: string | null }) {
  const src = safeImg(url);
  return (
    <span className="adm-logo">
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt="" loading="lazy" />
      ) : (
        <span>{initials(name)}</span>
      )}
    </span>
  );
}

export function CopyLink({ token, className }: { token: string | null; className?: string }) {
  const [state, setState] = useState<'idle' | 'ok' | 'ko'>('idle');
  const copy = async () => {
    if (!token) return;
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/c/${token}`);
      setState('ok');
    } catch {
      setState('ko');
    }
    window.setTimeout(() => setState('idle'), 1800);
  };
  return (
    <button type="button" className={className ?? 'adm-btn'} onClick={copy} disabled={!token}>
      {state === 'ok' ? 'Copié' : state === 'ko' ? 'Échec de la copie' : 'Copier le lien'}
    </button>
  );
}

export function AdminBar({ children }: { children?: React.ReactNode }) {
  const logout = async () => {
    await fetch('/api/admin/logout', { method: 'POST' }).catch(() => null);
    window.location.href = '/admin/login';
  };
  return (
    <header className="adm-bar">
      <a href="/admin" className="adm-bar__home" aria-label="Retour à la liste des audits">
        <span>Audits</span>
      </a>
      <div className="adm-bar__right">
        {children}
        <button type="button" className="adm-link" onClick={logout}>
          Déconnexion
        </button>
      </div>
    </header>
  );
}
