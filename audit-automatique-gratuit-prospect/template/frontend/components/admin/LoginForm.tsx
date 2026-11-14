'use client';

import { useState } from 'react';

export function LoginForm() {
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setMsg(null);
    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      if (res.ok) {
        window.location.href = '/admin';
        return;
      }
      if (res.status === 429) setMsg('Trop d’essais. Réessayez dans quinze minutes.');
      else if (res.status === 500) setMsg('Accès non configuré sur le serveur.');
      else setMsg('Mot de passe incorrect.');
    } catch {
      setMsg('Le serveur ne répond pas.');
    }
    setBusy(false);
  };

  return (
    <form className="adm-login__form" onSubmit={submit}>
      <label className="adm-f">
        <span>Mot de passe</span>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" autoFocus required />
      </label>
      <button type="submit" className="btn" disabled={busy || !password}>
        {busy ? 'Vérification' : 'Entrer'}
      </button>
      {msg ? (
        <p className="adm-login__msg" role="alert">
          {msg}
        </p>
      ) : null}
    </form>
  );
}
