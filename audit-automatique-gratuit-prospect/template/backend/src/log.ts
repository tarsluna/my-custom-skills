const SECRET_ENV = ['OPENROUTER_API_KEY', 'APIFY_TOKEN', 'KIE_API_KEY', 'ICLOSED_API_KEY', 'ICLOSED_WEBHOOK_SECRET', 'ADMIN_API_KEY', 'DATABASE_URL'];

function scrub(text: string): string {
  let out = text;
  for (const name of SECRET_ENV) {
    const value = process.env[name];
    if (value && value.length >= 6) out = out.split(value).join(`<${name}>`);
  }
  return out.replace(/(authorization|bearer|x-admin-key|secret=)[^\s,&"']*/gi, '$1<masqué>');
}

function emit(level: 'info' | 'warn' | 'error', msg: string, meta?: Record<string, unknown>) {
  const line = JSON.stringify({ t: new Date().toISOString(), level, msg, ...meta });
  (level === 'error' ? console.error : console.log)(scrub(line));
}

export const log = {
  info: (msg: string, meta?: Record<string, unknown>) => emit('info', msg, meta),
  warn: (msg: string, meta?: Record<string, unknown>) => emit('warn', msg, meta),
  error: (msg: string, meta?: Record<string, unknown>) => emit('error', msg, meta),
};

export function errMsg(e: unknown): string {
  if (!(e instanceof Error)) return String(e);
  const cause = (e as Error & { cause?: { code?: string; message?: string } }).cause;
  return cause ? `${e.message} (${cause.code ?? cause.message ?? 'cause inconnue'})` : e.message;
}
