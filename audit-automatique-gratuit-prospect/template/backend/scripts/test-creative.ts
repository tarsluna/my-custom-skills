/**
 * Test réel du moteur créatif : une seule image, environ 10 crédits. À lancer avant le premier audit complet.
 *   node --env-file=.env --import tsx scripts/test-creative.ts scripts/brand.example.json ba_vertical
 * Sortie dans ./out. Regardez l'image : logo net, texte exact, rendu réaliste.
 */
import { promises as fs } from 'node:fs';
import path from 'node:path';
import { CONCEPTS } from '../src/creative/concepts.js';
import { planCreatives, renderCreative } from '../src/creative/index.js';
import type { BrandProfile, CompetitorInsights } from '../src/creative/types.js';
import { createLlm } from '../src/lib/llm.js';

const [brandFile, conceptKey = 'ba_vertical'] = process.argv.slice(2);
if (!brandFile) {
  console.error('Usage : scripts/test-creative.ts <brand.json> [clé de concept]');
  console.error(`Concepts : ${CONCEPTS.map((c) => c.key).join(', ')}`);
  process.exit(1);
}

const concept = CONCEPTS.find((c) => c.key === conceptKey);
if (!concept) {
  console.error(`Concept inconnu : ${conceptKey}`);
  process.exit(1);
}

const brand = JSON.parse(await fs.readFile(brandFile, 'utf8')) as BrandProfile;
const insights: CompetitorInsights = { hooks: [], angles: [], styleNotes: [], saturated: [] };
const out = path.resolve('out');
await fs.mkdir(out, { recursive: true });

const llm = createLlm();
const specs = await planCreatives(brand, insights, llm);
const spec = specs.find((s) => s.concept === concept.label);
if (!spec) throw new Error('Concept absent du plan.');

console.log(`Accroche : ${spec.headline}`);
console.log(`Puces : ${spec.bullets.join(' | ')}`);
const result = await renderCreative(spec, brand, out, llm, { maxGenerations: 2 });
console.log(`Image : ${result.imagePath}`);
console.log(`Générations : ${result.attempts}`);
console.log(`Défauts relevés : ${result.issues.join(' ; ') || 'aucun'}`);
