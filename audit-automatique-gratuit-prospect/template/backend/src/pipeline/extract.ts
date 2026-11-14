import type { Llm } from '../lib/llm.js';
import { collapse, normalizeForMatch, publicSafe, UNTRUSTED_RULE, untrusted } from '../lib/text.js';
import { geocodeCity } from '../lib/geo.js';
import type { CrawledPage } from './crawl.js';
import { niche } from '../niche.js';

export type Profession = string;

export type SiteAnalysis = {
  businessName: string;
  profession: Profession;
  professionLabel: string;
  city: string | null;
  department: string | null;
  region: string | null;
  geo: { lat: number; lon: number } | null;
  specialties: string[];
  projectTypes: string[];
  tone: string;
  summary: string;
  leader: { name: string; role: string | null } | null;
  facts: string[];
};

type RawAnalysis = {
  businessName?: string;
  profession?: string;
  professionLabel?: string;
  city?: string | null;
  department?: string | null;
  region?: string | null;
  specialties?: string[];
  projectTypes?: string[];
  tone?: string;
  summary?: string;
  leader?: { name?: string; role?: string | null } | null;
  facts?: Array<{ fact?: string; evidence?: string }>;
};

function system(): string {
  const n = niche();
  const b = n.business;
  const keys = n.sector.professions.map((p) => `"${p.key}"`).join(' | ');
  const rules = n.sector.professions.map((p) => `- "${p.key}" : ${p.label}. Indices attendus sur le site : ${p.evidence}.`).join('\n');
  return `Tu analyses le site web d'${b.un} (${n.sector.description}) pour préparer un audit.
${UNTRUSTED_RULE}

Réponds en JSON, uniquement avec ces clés :
{
  "businessName": "nom commercial exact, tel que publié sur le site",
  "profession": ${keys},
  "professionLabel": "métier réel en toutes lettres, en français, au singulier",
  "city": "ville principale telle que publiée, sinon null",
  "department": "département s'il est publié, sinon null",
  "region": "région si elle est publiée, sinon null",
  "specialties": ["spécialités réelles, 6 au maximum"],
  "projectTypes": ["types de ${n.sector.portfolioWord} proposées, 6 au maximum"],
  "tone": "le ton du site en une courte phrase",
  "summary": "deux phrases factuelles à partir du site",
  "leader": {"name":"nom de la personne dirigeante si publié","role":"son titre tel que publié"} ou null,
  "facts": [{"fact":"fait vrai et précis","evidence":"citation exacte, mot pour mot, copiée du site"}]
}

Métiers possibles :
${rules}

Règles de vérité : n'invente rien. Aucun chiffre, aucune date, aucune récompense, aucun projet, aucun témoignage qui ne figure pas mot pour mot sur le site. Chaque fait porte sa citation exacte. Sans information, renvoie null ou une liste vide.`;
}

function corpusOf(pages: CrawledPage[]): string {
  return pages.map((p) => `${p.title} ${p.description} ${p.headings.join(' ')} ${p.text}`).join(' ');
}

function pagesForPrompt(pages: CrawledPage[]): string {
  return pages
    .map((p) => `# PAGE ${p.url}\nTitre : ${p.title}\nDescription : ${p.description}\nTitres : ${p.headings.slice(0, 20).join(' | ')}\nTexte : ${p.text.slice(0, 6000)}`)
    .join('\n\n')
    .slice(0, 50_000);
}

const evidenceOf = (p: { evidence: string }, corpus: string) => new RegExp(p.evidence, 'i').test(corpus);

/** Garde déterministe : un métier n'est retenu que si le site en porte réellement la trace. */
export function reconcileProfession(llmValue: string | undefined, corpus: string): Profession {
  const { professions, defaultProfession } = niche().sector;
  const chosen = professions.find((p) => p.key === llmValue);
  if (chosen && evidenceOf(chosen, corpus)) return chosen.key;
  return (professions.find((p) => evidenceOf(p, corpus)) ?? professions.find((p) => p.key === defaultProfession) ?? professions[0]).key;
}

export function professionLabelFor(profession: Profession): string {
  const { professions } = niche().sector;
  return professions.find((p) => p.key === profession)?.label ?? professions[0].label;
}

const digitsIn = (text: string) => text.match(/\d[\d\s.,]*\d|\d/g) ?? [];

/** Retire d'un texte généré les phrases dont un nombre n'apparaît nulle part sur le site. */
export function dropUnverifiedNumbers(text: string, corpus: string): string {
  const normalizedCorpus = corpus.replace(/\s+/g, '');
  return text
    .split(/(?<=[.!?])\s+/)
    .filter((sentence) => digitsIn(sentence).every((d) => normalizedCorpus.includes(d.replace(/\s+/g, ''))))
    .join(' ')
    .trim();
}

/** Ne garde que les faits dont la citation se retrouve dans le contenu du site. */
export function verifiedFacts(facts: RawAnalysis['facts'], corpus: string): string[] {
  const normalized = normalizeForMatch(corpus);
  const out: string[] = [];
  for (const entry of facts ?? []) {
    const fact = collapse(entry?.fact);
    const evidence = normalizeForMatch(entry?.evidence ?? '');
    if (!fact || evidence.length < 8 || !normalized.includes(evidence)) continue;
    const safe = publicSafe(dropUnverifiedNumbers(fact, corpus));
    if (safe) out.push(safe);
  }
  return out.slice(0, 12);
}

function strings(list: unknown, max: number): string[] {
  if (!Array.isArray(list)) return [];
  return [...new Set(list.filter((v) => typeof v === 'string').map((v) => collapse(v)).filter((v) => v && v.length <= 120))].slice(0, max);
}

function nameFromDomain(domain: string): string {
  return domain.split('.')[0].split('-').map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w)).join(' ');
}

export async function analyzeSite(pages: CrawledPage[], domain: string, llm: Llm): Promise<SiteAnalysis> {
  const user = `Domaine : ${domain}\n\nContenu du site :\n${untrusted(domain, pagesForPrompt(pages))}\n\nProduis le JSON demandé.`;
  const raw = await llm.json<RawAnalysis>({ system: system(), user });
  const corpus = corpusOf(pages);
  const normalized = normalizeForMatch(corpus);

  const inCorpus = (value: string | null | undefined): boolean => {
    const needle = normalizeForMatch(value ?? '');
    return needle.length > 1 && normalized.includes(needle);
  };

  const profession = reconcileProfession(raw.profession, corpus);
  const professionLabel = professionLabelFor(profession);

  const llmName = collapse(raw.businessName);
  const businessName = llmName && inCorpus(llmName) ? llmName : nameFromDomain(domain);

  const declaredCity = collapse(raw.city) || null;
  const city = inCorpus(declaredCity) ? declaredCity : null;
  const point = city ? await geocodeCity(city) : null;

  const leaderName = collapse(raw.leader?.name) || null;
  const leader = leaderName && inCorpus(leaderName) ? { name: leaderName, role: collapse(raw.leader?.role) || null } : null;

  const summaryText = publicSafe(dropUnverifiedNumbers(collapse(raw.summary), corpus)) ?? '';
  const summary = summaryText || `${businessName}, ${professionLabel}${city ? ` à ${city}` : ''}.`;

  return {
    businessName,
    profession,
    professionLabel,
    city: point?.city ?? city,
    department: (inCorpus(raw.department ?? null) ? collapse(raw.department) : null) || point?.department || null,
    region: (inCorpus(raw.region ?? null) ? collapse(raw.region) : null) || point?.region || null,
    geo: point ? { lat: point.lat, lon: point.lon } : null,
    specialties: strings(raw.specialties, 6),
    projectTypes: strings(raw.projectTypes, 6),
    tone: collapse(raw.tone).slice(0, 200) || 'sobre et précis',
    summary,
    leader,
    facts: verifiedFacts(raw.facts, corpus),
  };
}
