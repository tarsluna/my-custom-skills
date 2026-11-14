import type { Llm } from '../lib/llm.js';
import { cleanPublicLine, collapse, hasBannedTerm, hasForbiddenAngle, UNTRUSTED_RULE, untrusted } from '../lib/text.js';
import type { SiteAnalysis } from './extract.js';
import { niche } from '../niche.js';

export type SetterContent = { assistantName: string; firstProspectMessage: string; suggestedReplies: string[] };

function system(): string {
  const n = niche();
  const b = n.business;
  return `Tu prépares une démonstration : un assistant de premier contact répond aux personnes qui écrivent à ${b.un} pour leur ${n.sector.projectWord}.
${UNTRUSTED_RULE}

À partir des informations fournies, écris :
- "firstProspectMessage" : le premier message réaliste d'une personne qui écrit ${b.au}, à la première personne, en deux ou trois phrases, décrivant un ${n.sector.projectWord} typique, dans sa zone. Rien de plus.
- "suggestedReplies" : 4 réponses courtes (moins de 60 caractères) que cette personne pourrait donner ensuite aux questions de l'assistant, sur : ${n.assistant.topics.slice(2).join(', ')}. Une par sujet, chiffres plausibles.

Respecte le métier exact. Pas de ${n.assistant.priceLabel}. Pas de point d'exclamation, pas d'emoji. Français courant, avec tous les accents.
Réponds en JSON : {"firstProspectMessage":"…","suggestedReplies":["…","…","…","…"]}`;
}

export function fallbackSetter(analysis: Pick<SiteAnalysis, 'businessName' | 'city' | 'projectTypes' | 'professionLabel'>): SetterContent {
  const n = niche();
  const project = analysis.projectTypes[0]?.toLowerCase() ?? n.assistant.fallbackProject;
  const zone = analysis.city ? ` à ${analysis.city}` : '';
  return {
    assistantName: `Assistant de ${analysis.businessName}`,
    firstProspectMessage: `Bonjour, nous avons ${/^un |^une /.test(project) ? project : `un projet : ${project}`}${zone} et nous aimerions en parler avec vous.`,
    suggestedReplies: n.assistant.fallbackReplies,
  };
}

export async function generateSetterContent(analysis: SiteAnalysis, llm: Llm): Promise<SetterContent> {
  const context = `Nom : ${analysis.businessName} (${analysis.professionLabel})
Zone : ${analysis.city ?? 'non précisée'}${analysis.region ? `, ${analysis.region}` : ''}
Spécialités : ${analysis.specialties.join(', ') || 'non précisées'}
Types de projets : ${analysis.projectTypes.join(', ') || 'non précisés'}
Présentation : ${analysis.summary}`;
  const fallback = fallbackSetter(analysis);
  const priceRe = new RegExp(niche().assistant.pricePattern, 'i');
  try {
    const out = await llm.json<{ firstProspectMessage?: string; suggestedReplies?: string[] }>({ system: system(), user: untrusted('fiche business', context) });
    const message = cleanPublicLine(collapse(out.firstProspectMessage));
    const replies = (Array.isArray(out.suggestedReplies) ? out.suggestedReplies : [])
      .filter((r): r is string => typeof r === 'string')
      .map((r) => cleanPublicLine(r))
      .filter((r) => r && r.length <= 80 && !hasForbiddenAngle(r) && !hasBannedTerm(r) && !priceRe.test(r))
      .slice(0, 4);
    const usable = message.length >= 30 && !hasForbiddenAngle(message) && !hasBannedTerm(message) && !priceRe.test(message);
    return {
      assistantName: fallback.assistantName,
      firstProspectMessage: usable ? message : fallback.firstProspectMessage,
      suggestedReplies: replies.length >= 2 ? replies : fallback.suggestedReplies,
    };
  } catch {
    return fallback;
  }
}
