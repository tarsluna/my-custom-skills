export type Format = '4:5' | '9:16' | '1:1';
export type Palette = { primary: string; secondary: string; accent: string; background: string; text: string };

export type CompetitorItem = {
  pageName: string; city: string | null; distanceKm: number | null; logoUrl: string | null; activeDays: number | null;
  adLibraryUrl: string; imageUrl: string | null; body: string; title: string | null; why: string;
};
export type CreativeItem = {
  id: string; index: number; concept: string; format: Format; locked: boolean; imageUrl: string;
  headline: string | null; primaryText: string | null; bullets: string[] | null;
  /** Null tant que l'opérateur n'a pas fourni de fourchette réelle. */
  estimatedCostEur: number | null;
};
export type ProjectItem = { title: string; location: string | null; imageUrl: string; sourceUrl: string };

export type Operator = { name: string; logoUrl: string | null; websiteUrl: string; motto: string | null };
export type Theme = { background: string; backgroundAlt: string; backgroundLight: string; foreground: string; foregroundSoft: string; muted: string; accent: string };
export type PageCopy = {
  title: string; lockedSentence: string; conceptNote: string; indexCta: string;
  sections: { business: string; competitors: string; creatives: string; projects: string; assistant: string; next: string };
  businessTitle: string; creativesTitle: string; creativesLead: string; projectsTitle: string; projectsLead: string;
  assistantTitle: string; assistantLead: string; assistantNotes: { tag: string; text: string }[];
  nextTitle: string; closing: string; teaser: { title: string; sub: string }[];
  costLabel: string; costLabelShort: string; costAverageLabel: string; footerLegal: string;
};

export type PublicAudit = {
  operator: Operator; theme: Theme; copy: PageCopy;
  token: string; status: 'processing' | 'ready' | 'failed';
  contact: { firstName: string | null }; meetingAt: string | null; bookingUrl: string;
  business: {
    name: string; profession: string; professionLabel: string; city: string | null; region: string | null;
    domain: string; websiteUrl: string; logoUrl: string | null; logoIsFallback: boolean; palette: Palette;
    specialties: string[]; projectTypes: string[]; summary: string;
  };
  competitors: { radiusKm: number | null; widened: boolean; insights: string[]; items: CompetitorItem[] };
  creatives: CreativeItem[];
  projects: ProjectItem[];
  setter: { assistantName: string; firstProspectMessage: string; suggestedReplies: string[] };
};

export type ChatTurn = { role: 'user' | 'assistant'; content: string };
export type ChatResponse = { replies: string[]; done: boolean };

export type AuditLookup =
  | { kind: 'ok'; audit: PublicAudit }
  | { kind: 'not_found' }
  | { kind: 'unavailable' };

/* Admin : formes normalisées, le backend est adapté à la frontière (lib/admin.ts). */
export type AdminStatus = 'queued' | 'analyzing' | 'ads' | 'creatives' | 'ready' | 'failed' | 'needs_domain';
export type AdminStats = { kieCredits: number | null; auditsToday: number | null; maxAuditsPerDay: number | null };
export type AdminAuditRow = {
  id: string; token: string | null; status: AdminStatus; domain: string | null; businessName: string | null;
  professionLabel: string | null; city: string | null; logoUrl: string | null; contactName: string | null;
  contactEmail: string | null; meetingAt: string | null; createdAt: string | null; error: string | null;
};
export type AdminCreative = {
  id: string; index: number; concept: string; format: Format; locked: boolean; imageUrl: string;
  headline: string | null; primaryText: string | null; bullets: string[]; cta: string | null; angle: string | null; status: string | null;
};
export type AdminStep = { name: string; label: string; status: string; at: string | null; detail: string | null };
export type AdminCosts = { kieCredits: number | null; generations: number | null; llmUsd: number | null; apifyUsd: number | null };
export type AdminAuditDetail = AdminAuditRow & { creatives: AdminCreative[]; steps: AdminStep[]; costs: AdminCosts };
