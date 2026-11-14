const TZ = 'Europe/Paris';

function parse(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** « jeudi 13 novembre à 14 h 30 » */
export function meetingLong(iso: string | null | undefined): string | null {
  const d = parse(iso);
  if (!d) return null;
  const day = new Intl.DateTimeFormat('fr-FR', { timeZone: TZ, weekday: 'long', day: 'numeric', month: 'long' }).format(d);
  return `${day} à ${clock(d)}`;
}

/** « 13 nov. 14:30 » : colonne dense de l'admin. */
export function meetingShort(iso: string | null | undefined): string {
  const d = parse(iso);
  if (!d) return '—';
  const day = new Intl.DateTimeFormat('fr-FR', { timeZone: TZ, day: '2-digit', month: 'short' }).format(d);
  const time = new Intl.DateTimeFormat('fr-FR', { timeZone: TZ, hour: '2-digit', minute: '2-digit' }).format(d);
  return `${day} ${time}`;
}

function clock(d: Date): string {
  const parts = new Intl.DateTimeFormat('fr-FR', { timeZone: TZ, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(d);
  const h = String(Number(parts.find((p) => p.type === 'hour')?.value ?? '0'));
  const m = parts.find((p) => p.type === 'minute')?.value ?? '00';
  return m === '00' ? `${h}\u00A0h` : `${h}\u00A0h\u00A0${m}`;
}

export function sheetDate(iso?: string | null): string {
  const d = parse(iso) ?? new Date();
  return new Intl.DateTimeFormat('fr-FR', { timeZone: TZ, day: '2-digit', month: '2-digit', year: 'numeric' }).format(d);
}

export function dayCount(n: number | null | undefined): string | null {
  if (n == null || !Number.isFinite(n)) return null;
  return n <= 1 ? '1\u00A0jour' : `${Math.round(n)}\u00A0jours`;
}

export function km(n: number | null | undefined): string | null {
  if (n == null || !Number.isFinite(n)) return null;
  return `${Math.round(n)}\u00A0km`;
}

/** « de Maison X », « d’Exemple X » : les noms d’entreprise arrivent tels quels. */
export function deName(name: string): string {
  return /^[aeiouyàâäéèêëîïôöùûü]/i.test(name) ? `d’${name}` : `de ${name}`;
}

/** Initiales pour un monogramme lorsque le site n'a pas de logo exploitable. */
export function initials(name: string): string {
  const words = name
    .replace(/https?:\/\//, '')
    .split(/[\s.\-_'’]+/)
    .filter((w) => w.length > 2 || /^[A-Z]/.test(w));
  const letters = words.slice(0, 2).map((w) => w[0]?.toUpperCase() ?? '');
  return letters.join('') || name.slice(0, 1).toUpperCase() || 'L';
}
