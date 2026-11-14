/** « https://www.exemple.fr/contact » devient « exemple.fr ». Renvoie null si ce n'est pas un domaine. */
export function normalizeDomain(input: string): string | null {
  let v = input.trim().toLowerCase();
  if (!v || v.length > 300) return null;
  v = v.replace(/^[a-z]+:\/\//, '').split(/[/?#]/)[0].replace(/^www\./, '').replace(/:\d+$/, '');
  if (v.length > 253) return null;
  return /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/.test(v) ? v : null;
}
