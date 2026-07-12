s---
name: vsl-copywriter
description: Generate world-class Video Sales Letter (VSL) scripts for your clients by consuming the 3 deep-search reports (market awareness, competitors, psychographic) and applying elite copywriting frameworks (Schwartz, the platform, Imperium Acquisition, RMBC). Use when the user asks to "write a VSL", "écrire une VSL", "script VSL", "VSL copywriter", "build VSL script for {client}", "fais le script VSL", "génère la VSL". Trigger phrases: "VSL pour {client}", "écris la VSL", "script de vente vidéo", "the platform VSL", "VSL copywriter {client}".
---

# VSL Copywriter (Elite Script Generator)

End-to-end skill that transforms the 3 DeepSearch reports produced by `deep-search` into a complete, high-converting VSL script + strategy doc for a client. Combines the best of Eugene Schwartz, the platform, Imperium Acquisition, RMBC Method, and B2B Meta Ads playbooks.

## 🎚️ Modes (à choisir avant génération)

Demander à l'utilisateur (ou détecter via le brief) quel mode utiliser :

### Mode A — `coach-dtc` (par défaut)
Coach / consultant / DTC / info-produit. Ton storytelling personnel, "tu", durée 8–12 min, structure 16 blocs (voir plus bas). Émotionnel, identité, transformation.

### Mode B — `b2b-specialist`
SaaS / conseil / services B2B. Ton **pro, consultatif, sobre, anti-hype**, "vous", durée **3–5 min**, structure 8 blocs courte (Hook → Problème → Agitation → Solution → Bénéfices → Preuves → Offre/Urgence soft → CTA). Preuves > promesses. Vocabulaire métier clair, aucune hyperbole.

**Règles spécifiques mode B2B (verrouillées) :**
- Output = **uniquement le script final** (voix off + texte à l'écran). Aucun JSON, aucune section meta, aucun "context profile".
- **Indications de réalisation en _italique_**, texte de voix off et onscreen en texte brut.
- Chaque section nommée en _italique_ (ex. _Hook_, _Problème_, _Solution_).
- Sous chaque section, deux lignes : `VO : ...` et `Onscreen : "..."`.
- Slides de **5–12 secondes** chacune.
- Angle dominant à choisir : **pain-stat / mechanism / case-result / ROI / compliance**.
- Urgence soft uniquement (créneau limité, audit offert, bonus). Jamais de FOMO agressif.
- Si données manquent → hypothèses réalistes _en italique_. Jamais de chiffres inventés sans préciser "estimation".
- Ne JAMAIS livrer hooks_bank, CTAs alternatifs, objections_matrix, storyboard, plan de test ou tout élément hors script.
- Ne pas numéroter ni baliser JSON.

**Exemple de rendu mode B2B :**
```
_Hook_
VO : Vous cherchez à accélérer vos ventes B2B, mais vos campagnes peinent à générer des rendez-vous qualifiés…
Onscreen : "Accélérez votre prospection B2B — sans perdre de temps"

_Problème_
VO : ...
Onscreen : "..."
```

Pour le mode A (coach-dtc), suivre intégralement le pipeline 7 étapes ci-dessous. Pour le mode B (b2b-specialist), suivre les étapes 1–3 (recherche + avatar + stratégie internes, **non affichées**) puis générer directement le script court selon les règles verrouillées ci-dessus.

## Pipeline (7 steps)

### Step 1 — Load context (research input)
Read the 3 deep-search reports for the client:
```
projects/clients/{client-slug}/research/01-market-awareness.md
projects/clients/{client-slug}/research/02-competitors.md
projects/clients/{client-slug}/research/03-psychographic.md
```

If any are missing → tell the user to run `deep-search` first for this client, and stop.

Also read (if exists) `projects/clients/{client-slug}/00-brief.md` for offer/pricing/CTA details.

### Step 2 — Avatar & Market synthesis
From the 3 reports, extract and write down (internal scratchpad before generating):
- **ICP (Ideal Customer Profile)**: demographic + psychographic in 3 lines
- **Awareness level** (Schwartz, 1–5): Unaware / Problem Aware / Solution Aware / Product Aware / Most Aware → from `01-market-awareness.md`
- **Sophistication level** (1–5): First to market / Naissante / Avertie / Saturée / Hyper-sophistiquée → infer from `02-competitors.md`
- **Top 5 Pains** (verbatim quotes from `03-psychographic.md`)
- **Top 3 Beliefs / Objections** (verbatim quotes)
- **Dream Outcome** (1 sentence, in customer's own words)
- **Existing solutions tried + why they failed** (from `03-psychographic.md`)
- **Common Enemy** (outside force the avatar blames)
- **Top 3 competitors hooks/angles** (from `02-competitors.md`)

This becomes the foundation. Every sentence in the VSL must trace back to one of these.

### Step 3 — Strategy (Big Idea + Mechanism + Offer)
Build the strategic spine:

**Big Idea** (1 sentence): a contrarian, intriguing claim that reframes the problem.

**Unique Mechanism** (named): give it a memorable proper noun (e.g., "Méthode LEAN", "Système TopCo", "Protocole 3C"). Required for sophistication level ≥3.

**Promise** (1 sentence, structured):
> [Dream Outcome] in [Timeframe] without [Primary Pain] — even if [Common Objection].

**Offer composition** (Imperium Acquisition framework):
- **Outcome**: what they will achieve
- **Timeframe**: how fast
- **Method**: the named mechanism
- **Secrets**: 3–5 unique insights they'll learn
- **Safety net**: guarantee / risk reversal
- **Polarising element**: who it's NOT for
- **Pricing**: anchor + actual price + payment terms

**Angle selection by sophistication level** (apply this rule):
| Level | Strategy |
|-------|----------|
| 1 | Direct: state what it is + benefit |
| 2 | Amplify: bigger/faster/better than competitors |
| 3 | Mechanism: introduce named method explaining HOW |
| 4 | Niche or attack: hyper-specialise or compare directly |
| 5 | Identity/story: sell lifestyle, values, tribe — not features |

Coaches/consultants and marketing agencies are **almost always level 4–5** in France today → default to identity + named mechanism + radical specificity.

### Step 4 — Script structure (16 blocks + timestamps)
Write the script in the following structure (adapted from coach VSL framework + French structure_vsl + the platform What-Who-When). Target length: **8–12 minutes** (1200–1800 words).

Format every block as:
```
[MM:SS] [VISUAL CUE]
Voice-over text in French, written for the ear (short sentences, oral rhythm, 2nd person "tu/vous").
```

**Blocks (mandatory order):**

1. **[0:00–0:15] HOOK** — Pattern interrupt + Promise. Use one of: shock stat, contrarian claim, "If you're [X] watching this, in the next [Y] minutes you'll discover…" Hook MUST land in first 5 seconds.
2. **[0:15–0:45] WHO THIS IS FOR / NOT FOR** — Polarising filter. "C'est pour toi si… ce n'est PAS pour toi si…"
3. **[0:45–1:30] WHO I AM + AUTHORITY** — Name, title, 3 credibility proofs (numbers, names, results). No fluff.
4. **[1:30–2:30] STARTING POINT (life before)** — Frustrating context the avatar identifies with. Use a verbatim pain quote from research.
5. **[2:30–3:15] WAKE-UP CALL** — The exact moment everything had to change. Emotional peak.
6. **[3:15–4:15] LOGICAL ATTEMPTS (and why they failed)** — Lists the existing solutions the market tried (from `03-psychographic.md`) and explains why they all fail. This is where you neutralise competitors.
7. **[4:15–5:00] THE REAL PROBLEM** — Reframe: the issue isn't what they thought it was. Introduce the **Common Enemy** (outside force).
8. **[5:00–5:45] HITTING THE WALL** — Maximum pain. Apply the 4 indirect amplification angles: cost of inaction, comparison with peers who made it, future regret, identity erosion.
9. **[5:45–6:30] BIG REALISATION** — The insight that changes everything. Sets up the mechanism.
10. **[6:30–7:30] SOLUTION EMERGES + NAMING THE METHOD** — Reveal the **Unique Mechanism** by name. Explain in 3 simple steps WHY it works (not how — keep some mystery).
11. **[7:30–8:30] NEW LIFE / TRANSFORMATION** — Dream Outcome made tangible. Sensory details. Time/financial/identity freedom.
12. **[8:30–9:15] PROOF STACK** — 3+ concrete proofs: client results, screenshots described, named names, before/after numbers. Sourced from `02-competitors.md` benchmarks + brief.
13. **[9:15–10:00] BENEFITS OF THE METHOD** — 4 bullet-style benefits of the mechanism (read aloud as a list, slow rhythm).
14. **[10:00–10:45] OFFER REVEAL** — Apply the platform **What-Who-When + 8 value elements**: Dream Outcome ↑, Likelihood ↑, Time Delay ↓, Effort ↓. Stack everything included. Anchor price.
15. **[10:45–11:30] OBJECTION HANDLING + SAFETY NET** — Address top 3 objections from `03-psychographic.md` head-on. Add guarantee / risk reversal.
16. **[11:30–12:00] CTA (single, clear, urgent)** — One action only: "Clique sur le bouton, réserve ton call." Repeat the dream outcome + scarcity element. NO secondary CTA, NO "or you can also…".

### Step 5 — Copywriting rules (apply throughout)

**Slippery slide** (Sugarman): every sentence must make the viewer want to read/hear the next one. No paragraph longer than 3 sentences.

**Action Threshold equation** (Imperium Acquisition):
> Action = (Pain% + Confidence%) / 2

→ Increase **Pain** with the 5 Pools (Problem, Unmet needs, How would it work, What would it hurt, Consequences).
→ Increase **Confidence** with the 3 Pools (Confidence in the Offer, in You, in the Clients).

**the platform 8 Value Elements** (apply at offer reveal):
- ↑ Dream Outcome
- ↑ Perceived Likelihood of Achievement
- ↓ Time Delay
- ↓ Effort & Sacrifice

**Voice & tone**:
- 2nd person ("tu" by default, "vous" if B2B premium)
- Oral French, short sentences, no jargon
- 1 idea per sentence, 1 emotion per block
- Use verbatim quotes from `03-psychographic.md` whenever possible (italicised in script)
- French market only, French references, French names

**Mechanism rule**: name your method ONCE clearly, then repeat the name 4–6 times throughout the script to anchor it.

### Step 6 — Quality checklist (self-audit before saving)
The script MUST pass ALL of these:

**Must-haves:**
- [ ] Hook lands in the first 5 seconds
- [ ] ICP filter (who for / who not for) present
- [ ] Authority block with ≥3 concrete proofs
- [ ] Named Unique Mechanism (if sophistication ≥3)
- [ ] At least 2 verbatim customer quotes from research
- [ ] Common Enemy clearly named
- [ ] Offer reveal with 8 value elements
- [ ] Top 3 objections handled
- [ ] ONE single CTA repeated 2x at the end
- [ ] Length 1200–1800 words (8–12 min spoken)
- [ ] Every claim sourced (proof, screenshot description, name)

**Must-avoid (errors from playbook):**
- [ ] NOT too long (>15 min kills retention)
- [ ] NOT too salesy (no "amazing offer act now" vibes)
- [ ] NO missing CTA
- [ ] NO distracting jokes/effects in the script directions
- [ ] NO generic claims without proof
- [ ] NO multiple CTAs

If any check fails → fix before saving.

### Step 7 — Save outputs
Create the directory if needed and save 2 files:

```
projects/clients/{client-slug}/vsl/
├── strategy.md      # Avatar + Big Idea + Mechanism + Offer (from steps 2–3)
└── script-v1.md     # Full timestamped script (from step 4)
```

**`strategy.md` template:**
```markdown
# Stratégie VSL — {CLIENT}

## Avatar
- ICP : ...
- Niveau de conscience (Schwartz) : ...
- Niveau de sophistication marché : ...
- Top 5 douleurs : ...
- Top 3 croyances/objections : ...
- Dream Outcome : ...
- Solutions déjà essayées + pourquoi ça a échoué : ...
- Ennemi commun : ...

## Big Idea
> ...

## Mécanisme unique
**Nom** : ...
**Pourquoi ça marche (3 raisons)** : ...

## Promesse
> [Outcome] en [Timeframe] sans [Pain] — même si [Objection].

## Offre (Imperium Acquisition)
- Outcome : ...
- Timeframe : ...
- Méthode : ...
- Secrets (3–5) : ...
- Safety net : ...
- Polarising : ...
- Pricing : ...

## Angle stratégique (basé sur sophistication niveau X)
...
```

**`script-v1.md` template:**
```markdown
# Script VSL v1 — {CLIENT}
**Durée cible** : ~10 min | **Mots** : ~1500 | **Mécanisme** : {NOM}

---

[0:00–0:15] [VISUAL: ...]
...

[0:15–0:45] [VISUAL: ...]
...

[etc. — 16 blocks]

---

## Notes de production
- Ton : ...
- Rythme : ...
- B-roll suggéré : ...
- Musique : ...
```

### Final user message (in French)
After saving:

> ✅ Script VSL généré pour **{CLIENT}**.
> - `projects/clients/{slug}/vsl/strategy.md` — stratégie complète (avatar, big idea, mécanisme "{NOM}", offre)
> - `projects/clients/{slug}/vsl/script-v1.md` — script timestampé ~{X} mots / ~{Y} min
>
> **Mécanisme unique** : {NOM}
> **Big Idea** : {phrase}
> **Promesse** : {phrase}
>
> Prochaine étape suggérée : review du script à voix haute, puis production vidéo.

---

## REFERENCE — Frameworks library

### A. Eugene Schwartz — Awareness levels
1. **Unaware** → Lead with problem identification, story
2. **Problem Aware** → Agitate problem, hint at solution category
3. **Solution Aware** → Compare solutions, position yours as best
4. **Product Aware** → Differentiate your specific product, proof
5. **Most Aware** → Direct offer, urgency, price

### B. Market Sophistication levels (5)
1. First to market → simple direct claim
2. Naissante → bigger/better promise
3. Avertie → introduce mechanism
4. Saturée → niche or attack
5. Hyper → identity, story, tribe (most coaches/agencies are HERE in FR market)

### C. Imperium Acquisition — 6 Pillars of an Offer
1. **Drive** — internal motivation
2. **Goal** — measurable outcome
3. **Problem** — what blocks them
4. **Pain** — emotional cost
5. **Action** — what they must do
6. **Confidence** — why it will work

**3 Pools of Confidence**: Offer / You / Clients
**5 Pools of Pain**: Problem / Unmet needs / How Would It Work / What Would It Hurt / Consequences
**Action Threshold**: (Pain% + Confidence%) / 2

### D. the platform — Value Equation (What-Who-When)
**Value = (Dream Outcome × Likelihood) / (Time Delay × Effort)**
Maximize numerator, minimize denominator at the offer reveal.

### E. the platform — More-Better-New (Rule of 100)
Daily output: 100 outreach OR 100 minutes of content OR $100 of ads.

### F. RMBC Method — Research questions (use to extract from `03-psychographic.md`)
- Who is the customer?
- Attitudes (religious/political/social/economic)?
- Hopes, dreams, victories, failures?
- Outside forces blocking them?
- Prejudices?
- Core beliefs about life/love/family in 1–3 sentences?
- Existing solutions + experience with them?
- Conspiracies/older attempts/forgotten methods?

### G. 10 Meta Ads frameworks (for the promo ads driving traffic to the VSL)
1. **FOMO** — scarcity + missed opportunity
2. **PAS** — Problem / Agitation / Solution
3. **AIDA** — Attention / Interest / Desire / Action
4. **Objection-Réassurance** — name objection upfront, dismantle it
5. **Liste** — "5 raisons pour lesquelles…"
6. **Storytelling héros** — personal transformation narrative
7. **Ennemi commun** — outside force the audience already hates
8. **Avant/Après** — visual transformation
9. **Guide/Éducative** — give value first, sell second
10. **Démonstration technique** — show the mechanism in action

### H. 8 Psychological triggers
Curiosity • FOMO • Gain • Identification • Social proof / Authority • Reciprocity • Exclusivity • Fear / Safety

### I. Best practices (must-do)
- Short duration (8–12 min ideal)
- Hook in first 30 seconds (best: first 5)
- Client-first language (you/tu, not we/I)
- Authentic tone (no salesy)
- Stories > features
- Sourced proofs
- High-quality audio + video

### J. Common errors (must-avoid)
- Video too long
- Too salesy / aggressive
- Missing or unclear CTA
- Distracting jokes/effects/off-topic
- Poor production quality

---

## Notes
- TOUJOURS lire les 3 rapports deep-search AVANT de générer.
- TOUJOURS nommer le mécanisme unique (sauf niveau 1–2).
- TOUJOURS écrire en français oral, 2e personne.
- TOUJOURS sourcer les preuves et citer des verbatim.
- JAMAIS plus d'un CTA.
- JAMAIS de promesse sans preuve.
- Si les rapports deep-search manquent → demander de lancer `deep-search` d'abord.
