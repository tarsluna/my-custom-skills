#!/usr/bin/env node
/**
 * generate.mjs
 *
 * Reads a brief-output.json produced by sales-call-analyzer and
 * the template.html from this skill, performs mustache-style replacement,
 * and writes index.html + vercel.json into
 * projects/{client_slug}/07-devis-page/.
 *
 * Usage:
 *   node scripts/generate.mjs <path/to/brief-output.json> <output-dir>
 *
 * Example:
 *   node scripts/generate.mjs \
 *     ~/skills/projects/acme/00-sales-brief/brief-output.json \
 *     ~/skills/projects/acme/07-devis-page
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const SKILL_ROOT = resolve(__dirname, '..');

// ---------- CLI ----------
const [, , briefPathArg, outDirArg] = process.argv;
if (!briefPathArg || !outDirArg) {
  console.error('Usage: node scripts/generate.mjs <brief.json> <output-dir>');
  process.exit(1);
}
const briefPath = resolve(briefPathArg);
const outDir = resolve(outDirArg);

if (!existsSync(briefPath)) {
  console.error(`[!] Brief not found: ${briefPath}`);
  process.exit(1);
}

// ---------- Load brief ----------
let brief;
try {
  brief = JSON.parse(readFileSync(briefPath, 'utf8'));
} catch (e) {
  console.error(`[!] Invalid JSON in brief: ${e.message}`);
  process.exit(1);
}

// ---------- Required fields check ----------
const REQUIRED = [
  ['meta.prospect_full_name', brief?.meta?.prospect_full_name],
  ['meta.company_legal_name', brief?.meta?.company_legal_name],
  ['contact.email', brief?.contact?.email],
  ['contact.city', brief?.contact?.city],
  ['pricing.stripe_link', brief?.pricing?.stripe_link],
  ['dream_state.headline_hook', brief?.dream_state?.headline_hook],
  ['objections.headline_subtitle_bullets', brief?.objections?.headline_subtitle_bullets],
];
const missing = REQUIRED.filter(([, v]) => !v || (Array.isArray(v) && v.length < 3));
if (missing.length) {
  console.error('[!] Brief incomplet. Champs manquants :');
  for (const [k] of missing) console.error(`   - ${k}`);
  console.error('\nRelance `sales-call-analyzer` pour combler les trous.');
  process.exit(1);
}

// ---------- Load template ----------
const templatePath = join(SKILL_ROOT, 'templates', 'template.html');
if (!existsSync(templatePath)) {
  console.error(`[!] Template not found: ${templatePath}`);
  process.exit(1);
}
let html = readFileSync(templatePath, 'utf8');

// ---------- Helpers ----------
const pad = (n, w = 2) => String(n).padStart(w, '0');
const today = new Date();
const YYYY = today.getFullYear();
const MM = pad(today.getMonth() + 1);
const DD = pad(today.getDate());
const YYYYMMDD = `${YYYY}${MM}${DD}`;
const DATE_FR = `${DD}/${MM}/${YYYY}`;

const toDeadlineFr = (isoOrFallback) => {
  if (isoOrFallback) {
    const d = new Date(isoOrFallback);
    if (!isNaN(d.getTime())) {
      return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
    }
  }
  // default: today + 7 days
  const fallback = new Date(today.getTime() + 7 * 86400000);
  return `${pad(fallback.getDate())}/${pad(fallback.getMonth() + 1)}/${fallback.getFullYear()}`;
};

const slugifyName = (s) =>
  s
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-|-$/g, '');

const capitalize = (s) => (s && s.length ? s[0].toUpperCase() + s.slice(1) : s);

const pluralize = (word) => {
  // French pluralization — naive
  if (!word) return word;
  const last = word.slice(-1).toLowerCase();
  if (word.endsWith('s') || word.endsWith('x') || word.endsWith('z')) return word;
  if (word.endsWith('al') && !['bal', 'carnaval', 'festival'].includes(word)) return word.slice(0, -2) + 'aux';
  return word + 's';
};

// short form = first word, lowercased
const firstWord = (s) => (s ? s.split(/\s+/)[0] : s);

// ---------- Derive tokens ----------
const m = brief.meta || {};
const c = brief.contact || {};
const b = brief.business || {};
const p = brief.pricing || {};
const roi = brief.roi_calc_defaults || {};
const vocab = m.industry_vocab || {};

const companyName = m.company_legal_name;
const clientNameSlug = slugifyName(companyName);

// Devis ref: use brief value or auto-generate
let devisRef = m.devis_ref;
if (!devisRef) {
  // figure out seq from existing 07-devis-page folders — best effort; fallback 001
  let seq = '001';
  try {
    const parent = resolve(outDir, '..', '..');
    // Look for sibling client folders with 07-devis-page + LF-YYYYMMDD-*
    // Keep it simple: always 001 unless user pre-sets meta.devis_ref
  } catch (_) {
    seq = '001';
  }
  devisRef = `LF-${YYYYMMDD}-${seq}`;
}

const deadlineFr = toDeadlineFr(m.decision_deadline_iso);

// Industry vocab
const dealWord = vocab.deal_word || 'client';
const customerWord = vocab.customer_word || 'client';
const meetingWord = vocab.meeting_word || 'RDV téléphonique';
const meetingWordShort = firstWord(meetingWord) === 'RDV' ? 'RDV' : firstWord(meetingWord);
const meetingWordPluralShort = meetingWordShort === 'RDV' ? 'RDV' : pluralize(meetingWordShort);
const meetingWordPlural = firstWord(meetingWord) === 'RDV' ? `RDV ${pluralize(meetingWord.split(/\s+/).slice(1).join(' '))}`.trim() || 'RDV' : `${pluralize(firstWord(meetingWord))} ${meetingWord.split(/\s+/).slice(1).join(' ')}`.trim();
const meetingWordPluralCaps = capitalize(meetingWordPluralShort);
const dealWordPlural = pluralize(dealWord);
const dealWordPluralCaps = capitalize(dealWordPlural);
const customerWordPlural = pluralize(customerWord);

// Hero copy
const heroH1 = brief.dream_state.headline_hook; // already HTML with <em>…</em> per framework 03
const [fini1, fini2, fini3] = brief.objections.headline_subtitle_bullets;

// Geo/city
const clientCity = c.city || '';
const geoRadiusKm = b.geo_radius_km || 50;
const geoZone = b.geo_zone_label || 'votre région';

// Context strings (industry-aware with safe defaults)
const industryLabel = m.industry_label || m.industry_primary || 'de votre secteur';
const foundedAge = b.founded_year ? `${new Date().getFullYear() - b.founded_year} ans d'ancienneté` : 'votre positionnement';

const setupDescription =
  m.setup_description ||
  `Audit secteur ${industryLabel.replace(/^de\s+/i, '')}, stratégie d'angles premium, création compte Meta, paramétrage pixel`;

const creativesAngleContext = m.creatives_angle_context || (b.founded_year ? `votre image ${foundedAge}` : 'votre expertise et votre positionnement');

const servicesIntro =
  m.services_intro ||
  `Tout le nécessaire pour générer des leads qualifiés sur votre offre — et protéger le temps de votre commercial.`;

const prequalFilters = m.prequal_filters || 'Filtre budget, type de projet, urgence, zone';
const prequalFiltersShort = m.prequal_filters_short || 'budget, projet, urgence, zone';

const panierHint = m.panier_hint || `Montant moyen d'un ${dealWord} facturé`;

// Pricing
const lfFee = p.lf_fee_eur || 790;
const stripeLink = p.stripe_link;

// ---------- Build replacements map ----------
const tokens = {
  DEVIS_REF: devisRef,
  DATE_FR,
  YYYYMMDD,
  DEADLINE_FR: deadlineFr,

  CLIENT_FULL_NAME: m.prospect_full_name,
  CLIENT_COMPANY: companyName,
  CLIENT_ROLE: m.role_title || 'Décideur',
  CLIENT_NAME_SLUG: clientNameSlug,
  CLIENT_ADDRESS_LINE: c.address_line || '—',
  CLIENT_POSTAL_CODE: c.postal_code || '',
  CLIENT_CITY: clientCity,
  CLIENT_PHONE: c.phone || '—',
  CLIENT_EMAIL: c.email,

  HERO_H1_HTML: heroH1,
  FINI_LES_1: fini1,
  FINI_LES_2: fini2,
  FINI_LES_3: fini3,
  SERVICES_INTRO: servicesIntro,

  LF_FEE: String(lfFee),
  STRIPE_LINK: stripeLink,

  DEAL_WORD: dealWord,
  DEAL_WORD_PLURAL: dealWordPlural,
  DEAL_WORD_PLURAL_CAPS: dealWordPluralCaps,
  CUSTOMER_WORD: customerWord,
  CUSTOMER_WORD_PLURAL: customerWordPlural,
  MEETING_WORD: meetingWord,
  MEETING_WORD_SHORT: meetingWordShort,
  MEETING_WORD_PLURAL: meetingWordPlural,
  MEETING_WORD_PLURAL_SHORT: meetingWordPluralShort,
  MEETING_WORD_PLURAL_CAPS: meetingWordPluralCaps,

  GEO_RADIUS_KM: String(geoRadiusKm),
  GEO_ZONE: geoZone,

  PREQUAL_FILTERS: prequalFilters,
  PREQUAL_FILTERS_SHORT: prequalFiltersShort,
  SETUP_DESCRIPTION: setupDescription,
  CREATIVES_ANGLE_CONTEXT: creativesAngleContext,
  PANIER_HINT: panierHint,

  AVG_BASKET_EUR: String(roi.avg_basket_eur || 2000),
};

// ---------- Do the replacement ----------
for (const [key, val] of Object.entries(tokens)) {
  const pattern = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
  html = html.replace(pattern, val == null ? '' : String(val));
}

// ---------- Sanity check: no remaining {{TOKEN}} ----------
const leftover = html.match(/\{\{[A-Z_]+\}\}/g);
if (leftover && leftover.length) {
  console.warn('[!] Tokens non-remplacés détectés :', [...new Set(leftover)]);
  console.warn('    -> corriger template.html OU enrichir generate.mjs');
}

// ---------- Sanity check: PDF download not regressed (incident PDF blanc 2026-04-30) ----------
// A blank PDF download breaks the entire deliverable. Hard-fail if the template
// loses any of the elements that make the download actually work end-to-end.
const pdfRegressions = [];
if (!/document\.fonts\s*&&\s*document\.fonts\.ready/.test(html) && !/document\.fonts\.ready/.test(html)) {
  pdfRegressions.push('await document.fonts.ready missing — PDF fonts may render as fallback');
}
if (!/pdf-render-overlay/.test(html)) {
  pdfRegressions.push('full-screen #pdf-render-overlay missing — user would see the raw devis flash on screen during capture');
}
if (!/el\.style\.display\s*=\s*['"]block['"]/.test(html)) {
  pdfRegressions.push('downloadPDF must set #pdf-devis to display:block before capture (in-flow layout) — otherwise html2pdf measures 0 height and PDF is blank');
}
if (!/el\.style\.position\s*=\s*['"]static['"]/.test(html)) {
  pdfRegressions.push('downloadPDF must set #pdf-devis to position:static before capture (so html2pdf wrapper has measurable height)');
}
if (!/html2pdf\(\)\.set\(opt\)\.from\(el\)\.save\(\)/.test(html)) {
  pdfRegressions.push('html2pdf().set(opt).from(el).save() call signature missing or modified');
}
const pdfBlock = (html.match(/#pdf-devis\s*\{[^}]*\}/) || [''])[0];
if (!/display\s*:\s*none/.test(pdfBlock)) {
  pdfRegressions.push('#pdf-devis CSS must be display:none by default (JS toggles it on during capture)');
}
if (/left\s*:\s*-?\d{4,}px/.test(pdfBlock)) {
  pdfRegressions.push('#pdf-devis hidden via left:-XXXXpx — html2canvas will render blank. Keep display:none default + JS toggle.');
}
if (pdfRegressions.length) {
  console.error('[!] PDF download will be broken — refusing to write output:');
  for (const reason of pdfRegressions) console.error(`   - ${reason}`);
  console.error('\nVoir frameworks/04-pdf-devis-spec.md (incident PDF blanc 2026-04-30).');
  process.exit(2);
}

// ---------- Ensure outDir exists ----------
if (!existsSync(outDir)) mkdirSync(outDir, { recursive: true });

// ---------- Write index.html ----------
const indexPath = join(outDir, 'index.html');
writeFileSync(indexPath, html, 'utf8');
console.log(`[ok] index.html  -> ${indexPath}`);

// ---------- Write vercel.json ----------
const vercelJson = {
  $schema: 'https://openapi.vercel.sh/vercel.json',
  cleanUrls: true,
  trailingSlash: false,
};
const vercelPath = join(outDir, 'vercel.json');
writeFileSync(vercelPath, JSON.stringify(vercelJson, null, 2) + '\n', 'utf8');
console.log(`[ok] vercel.json -> ${vercelPath}`);

// ---------- Summary ----------
console.log('\n=== Devis généré ===');
console.log(`Client       : ${m.prospect_full_name} (${companyName})`);
console.log(`Ref          : ${devisRef}`);
console.log(`Date / Deadl : ${DATE_FR} -> ${deadlineFr}`);
console.log(`Deal word    : ${dealWord} / ${dealWordPlural}`);
console.log(`Meeting word : ${meetingWord}`);
console.log(`Panier ROI   : ${tokens.AVG_BASKET_EUR} €`);
console.log(`LF fee       : ${lfFee} €`);
console.log(`Stripe link  : ${stripeLink}`);
console.log(`\nOutput dir   : ${outDir}`);
console.log(`Next step    : scripts/deploy.sh ${outDir} ${clientNameSlug.toLowerCase()}`);
