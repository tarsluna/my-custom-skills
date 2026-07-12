---
name: meta-ads-copywriter
description: Generate elite Meta Ads (Facebook/Instagram) for your clients — face-camera video scripts (30s minimum, default 30s/60s/90s) + ad copies (primary text / headline / description). Always offer-first (audit + reconstruct if weak), then multi-variant output (3+ angles). Combines the platform, Imperium Acquisition (Pillars/Pools/Action Threshold), the platform, Meta Ads playbooks (Callout/Value/CTA, What-Who-When, Hooks library). Use when the user asks to "écris des pubs Meta", "scripts pubs Facebook", "Meta Ads pour {client}", "génère des pubs vidéo face caméra", "ad copy", "publicités Meta", "pubs Instagram", "Lya pubs", "scripts UGC face cam". Trigger phrases: "pubs Meta {client}", "scripts pub face caméra", "Meta Ads {client}", "fais-moi des pubs", "génère 3 variantes pub Meta".
---

# Meta Ads Copywriter (Elite Multi-Variant Generator)

End-to-end skill that produces **face-camera video scripts (30s minimum — default 30s/60s/90s, never below 30s)** AND **Meta ad copies (primary text / headline / description)** for any client. Always starts by auditing the offer (the platform Value Equation + Imperium Pillars). If the offer is weak, the skill reconstructs it before writing a single ad. Output is always **multi-variant** (minimum 3 angles), always in **French**, always **markdown**.

This skill is the spiritual successor of "Lya" (the Custom GPT previously used for the same job) and encodes 5 reference documents into a repeatable pipeline.

---

## 🎯 When to use this skill

Trigger when the user asks any of:
- "Écris-moi des pubs Meta pour {client}"
- "Fais des scripts de pubs vidéo face caméra"
- "Génère 3 variantes de pubs Facebook/Instagram"
- "Meta Ads {client}", "pubs UGC", "scripts pub courte"
- "J'ai besoin de copies pour ma campagne Meta"
- Any explicit reference to "Lya" or "meta-ads-copywriter"

DO NOT trigger when the user asks for:
- A long VSL (3–12 min) → use `vsl-copywriter` instead
- Deep customer research → use `deep-search` first
- Landing page copy → out of scope (mention LP brief in `frameworks/05-landing-congruence.md` for alignment only)

---

## 📦 Skill structure

This skill is split into modular reference files. The main agent reads `SKILL.md` (this file) for the orchestration, then loads the specific framework files **on demand** as it progresses through the pipeline.

```
meta-ads-copywriter/
├── SKILL.md                          ← you are here (orchestration + pipeline)
├── frameworks/
│   ├── 01-offer-audit.md             ← the platform Value Equation + Imperium 6 Pillars + 10-step offer creation
│   ├── 02-hooks-library.md           ← Banque de hooks (verbal + visuel) + first-3s checklist
│   ├── 03-value-angles.md            ← What-Who-When + 8 leviers + 5 Pools of Pain + 3 Pools of Confidence
│   ├── 04-cta-library.md             ← CTAs simples / urgency / scarcity / because
│   └── 05-script-structure.md        ← Architecture des scripts 30s / 60s / 90s (minimum 30s — jamais en dessous) + structure copy texte Meta
├── templates/
│   ├── brief-input.md                ← Inputs à collecter (ICP, offre, preuves, contraintes)
│   ├── output-ad-pack.md             ← Template du livrable final (multi-variantes)
│   └── output-offer-rebuild.md       ← Template si l'offre doit être reconstruite
├── checklists/
│   ├── pre-flight.md                 ← Avant de générer (offre OK, ICP clair, preuves dispo)
│   └── quality-gate.md               ← Avant de livrer (Meta policy, congruence, multi-variantes, etc.)
└── examples/
    └── (à remplir au fil des clients — Top Closer = premier cas)
```

---

## 🔄 Pipeline (6 phases)

### Phase 1 — Load context & Inputs

**1.1** Identify the client slug (e.g., `TopCo`, `maje-conseil`).

**1.2** Check if a brief already exists at:
```
projects/clients/{client-slug}/00-brief.md
```

**1.3** If a brief exists → read it. If not → load `templates/brief-input.md` and ask the user to fill the **minimum required fields** (don't ask for everything at once, ask only what's strictly needed):

**Minimum required fields:**
- **ICP** : 1 sentence (industry + role + geo)
- **Offer** : product/service + price + delivery
- **Dream outcome** : what the client gets (1 sentence, measurable if possible)
- **Top 3 pains** : in customer's own words if possible
- **Proof** : 1+ result (numbers, names, screenshots, testimonial)
- **CTA target** : booked call / free audit / lead magnet / direct purchase
- **Format target** : durations wanted (**minimum 30s — jamais en dessous**. Default: 30s + 60s + 90s) and number of variants per duration (default: 3)

**1.4** Optional fields (ask only if relevant):
- LTV / ACV (for budgeting/scaling notes)
- Existing winning hooks from past campaigns
- Brand voice constraints (tu/vous, premium/casual)
- Compliance constraints (regulated industry)

**1.5** If deep-search reports exist for this client at `projects/clients/{client-slug}/research/`, **read them** to enrich the avatar (verbatim pains, competitor angles, awareness level). This is optional but strongly preferred.

---

### Phase 2 — Offer audit (mandatory but conditional)

**This phase is non-negotiable. No ads are written until the offer passes the audit.**

**2.1** Load `frameworks/01-offer-audit.md`.

**2.2** Run the **Value Equation diagnostic** on the client's current offer:
```
Value = (Dream Outcome × Perceived Likelihood) / (Time Delay × Effort & Sacrifice)
```

For each of the 4 components, score 1–5 and write a 1-line justification:
- **Dream Outcome** : is it specific, measurable, time-bound, emotionally compelling?
- **Perceived Likelihood** : are there proofs / guarantees / track record?
- **Time Delay** : how fast does the customer get the result? Is it tangible quickly?
- **Effort & Sacrifice** : how much friction / work / risk for the customer?

**2.3** Run the **Imperium 6-Pillars check** : Drive / Goal / Problem / Pain / Action / Confidence. Note any pillar that is weak or missing.

**2.4** Decide:

| Total Value Equation score | Verdict | Action |
|----------------------------|---------|--------|
| 16–20 | **Solid** | Skip rebuild, proceed to Phase 3 directly |
| 11–15 | **Mediocre** | Propose 2–3 surgical improvements, ask user to validate, then proceed |
| ≤10 | **Weak** | STOP. Load `templates/output-offer-rebuild.md` and propose a full reconstruction. Do NOT write ads on a weak offer. |

**2.5** When proposing a rebuild, use the **10 the platform steps** (see `frameworks/01-offer-audit.md`) :
1. Niche & 11 psychographic questions
2. Define the final outcome (big promise + measurable)
3. Define duration (realistic + how to shorten)
4. Define methodology (steps simplified to 6–9 words each)
5. Create value elements (problems → tangible solutions)
6. Risk reversal (named guarantee)
7. Exclusion (who it's NOT for — strengthens perceived value)
8. Ultimatum (best vs worst scenario)
9. Packaging (positioning)
10. Pricing (high price = high value, justify 2x/5x/10x)

**2.6** Output (only if rebuild needed) : a clean offer doc saved to `projects/clients/{client-slug}/offer/v1.md`. Then loop back to Phase 3 with the new offer.

---

### Phase 3 — Avatar synthesis & Angle strategy

**3.1** Write down (internal scratchpad, not shown to user):
- **Avatar** : ICP + top 3 pains (verbatim if possible) + dream outcome + common enemy
- **Awareness level** (Schwartz 1–5) : Unaware / Problem Aware / Solution Aware / Product Aware / Most Aware
- **Sophistication level** (1–5) : First / Naissante / Avertie / Saturée / Hyper

**Default for FR coaches/consultants/agencies = level 4–5** → use named mechanism + radical specificity.

**3.2** Load `frameworks/03-value-angles.md` and generate the **angle palette** using **What-Who-When** :

**What (8 leviers, paired)** :
- Dream Outcome ↔ Nightmare
- Perceived Likelihood ↔ Risk
- Speed ↔ Time Delay
- Ease ↔ Effort & Sacrifice

**Who (perspectives)** :
- The prospect themselves
- Their spouse / family
- Their colleagues / team
- Their rivals / competitors

**When (timelines)** :
- Past (regret / missed)
- Present (current pain / urgency)
- Future (vision / consequence)

**3.3** From this palette, **select 3+ distinct angles** to test. Examples of angle archetypes :
- **Pain-stat** : start with a brutal statistic about the pain
- **Mechanism** : reveal the named method as the differentiator
- **Case-result** : start with a specific client win (numbers + name)
- **Common enemy** : attack an outside force the avatar already hates
- **Identity** : "this is for [type of person] who refuse to [accept X]"
- **Contrarian** : reframe the conventional wisdom
- **Demonstration** : show the mechanism in action
- **Before/After** : visual transformation

Each chosen angle must trace back to **at least one verbatim pain or proof** from the brief/research.

**3.4** Document the angle choices briefly (1 line per angle, max 3 lines total) in the output — the user wants to see **why** each variant exists.

---

### Phase 4 — Generate variants

**4.1** Load `frameworks/02-hooks-library.md`, `frameworks/04-cta-library.md`, and `frameworks/05-script-structure.md`.

**4.2** For each duration requested (**minimum 30s — jamais en dessous**. Default: 30s + 60s + 90s), generate **3 variants**, each with a **distinct angle** from Phase 3. **Aucune variante <30s ne doit être livrée**, même en retargeting.

**4.3** Each variant follows this exact structure (markdown, no JSON, no tables of timestamps, no VO/Onscreen columns) :

```markdown
### Variante {N} — {Angle name}

**Hook (0–3s)**
{Texte exact prononcé face caméra. 1–2 phrases courtes maximum. Doit accrocher en moins de 3 secondes.}

**Body**
{Texte exact prononcé. Phrases courtes (≤15 mots), rythme oral, 1 idée par phrase. Inclure : reformulation du pain, preuve/mécanisme, bénéfice clé.}

**CTA**
{Une seule action, claire, avec raison d'agir maintenant.}

*Indication scénique (optionnel) : {uniquement si critique pour le sens — ex: "montrer screenshot ici", "regard caméra direct"}*

---

**Copies Meta associées**
- **Primary text** (≤125c) : {hook direct + bénéfice + CTA}
- **Headline** (≤40c) : {résultat + délai sans sacrifice}
- **Description** (≤30c) : {urgence ou rareté}
```

**4.4** Rules for the script text itself (must apply to every variant) :
- **Hook < 3 seconds** : the first sentence must stop the scroll
- **No jargon** before the first benefit is stated
- **Mobile-first oral French** : phrases courtes, rythme parlé, "tu" par défaut, "vous" si B2B premium
- **One idea per sentence**, one emotion per block
- **Verbatim pain quote** if available from research/brief — italicised
- **Named mechanism** if sophistication ≥3 — repeat the name 2–3 times in the 60s+ versions, 1× in 30s. **Durée minimum absolue : 30s. Jamais de format <30s livré.**
- **One single CTA** — never two, never "ou alors tu peux aussi…"
- **No salesy hyperbole** ("incroyable", "révolutionnaire", "unique au monde") unless backed by a proof
- **Meta policy compliance** : no medical claims, no financial guarantees, no before/after weight loss, no discriminatory targeting language

**4.5** Rules for the copies texte (Meta ad copy) :
- **3 variants of primary text** (one per length tier per the playbook):
  - Tier 1 : ≤125c — hook direct + bénéfice + CTA
  - Tier 2 : 125–200c — callout local + preuve + CTA
  - Tier 3 : 200–280c — angle What-Who-When + CTA + raison maintenant
- **Headline** : "{Résultat} en {délai} sans {sacrifice}" or "Étude de cas : {chiffre} en {ville}"
- **Description** : "Places limitées {semaine}" / "Offre valable jusqu'à {date}" / similar urgency
- All copies must be **congruent** with the script (same promise, same CTA, same mechanism name)

---

### Phase 5 — Quality gate (self-audit before saving)

**5.1** Load `checklists/quality-gate.md` and verify EVERY item :

**Must-haves :**
- [ ] Offer passed the audit (or was rebuilt and validated)
- [ ] Minimum 3 variants per duration
- [ ] Each variant has a distinct angle (no two variants on the same angle)
- [ ] Each variant has Hook + Body + CTA (text only, no VO/Onscreen split)
- [ ] Each variant has an associated copy pack (primary text 3 tiers + headline + description)
- [ ] Hook lands in <3 seconds
- [ ] One single CTA per variant
- [ ] At least one verbatim pain or proof per variant (sourced from brief/research)
- [ ] Named mechanism present (if sophistication ≥3)
- [ ] French oral, mobile-first, "tu/vous" consistent
- [ ] Congruence between video script and copies texte (same promise/mechanism/CTA)

**Must-avoid :**
- [ ] No JSON, no tables of timestamps, no VO/Onscreen columns
- [ ] No medical / financial guarantee claims
- [ ] No multiple CTAs
- [ ] No generic claims without proof
- [ ] No copy-paste between variants (each must feel distinct)
- [ ] No more than 3 indications scéniques across the whole pack (we want copy, not storyboards)

If any check fails → fix before saving. If a fix is impossible (e.g., no proof available), flag it explicitly to the user instead of inventing.

---

### Phase 6 — Save outputs

**6.1** Save the final pack to :
```
projects/clients/{client-slug}/meta-ads/v1.md
```

Use the structure from `templates/output-ad-pack.md` (header with avatar/angles summary, then variants grouped by duration).

**6.2** If the offer was rebuilt, also save :
```
projects/clients/{client-slug}/offer/v1.md
```

**6.3** Final user message (in French) :

> ✅ Pack pubs Meta généré pour **{CLIENT}**.
> - `projects/clients/{slug}/meta-ads/v1.md` — {N} variantes × {durées} = {total} scripts + copies
> - {si rebuild} `projects/clients/{slug}/offer/v1.md` — offre reconstruite
>
> **Angles testés** :
> 1. {Angle 1} — {1 ligne pourquoi}
> 2. {Angle 2} — {1 ligne pourquoi}
> 3. {Angle 3} — {1 ligne pourquoi}
>
> **Mécanisme** : {nom si applicable}
>
> Prochaine étape suggérée : tournage face caméra des 3 variantes 60s en priorité, lancement Meta avec budget test, puis itération sur le hook gagnant (cf. règle "tester d'abord le hook" — `frameworks/02-hooks-library.md`).

---

## 🔗 Integration with ecosystem

This skill is **stage 3** of client production pipeline :

```
[Stage 1] deep-search   →  3 research reports (market, competitors, psychographic)
[Stage 2] vsl-copywriter →  Long VSL script (8–12 min) + strategy doc
[Stage 3] meta-ads-copywriter → Meta ad pack (this skill) — drives traffic to the VSL
```

**Strong recommendation** : if `deep-search` has been run for the client, **read its 3 reports** during Phase 1 to enrich the avatar — verbatim pains, competitor angles, and awareness level make the ads much sharper. The skill works without them, but worse.

If `vsl-copywriter` has been run, **read `strategy.md`** to inherit the named mechanism, big idea, and offer composition. The Meta ads must be **congruent** with the VSL they drive traffic to (same promise, same mechanism name, same CTA target).

---

## 🚦 Hard rules (never break)

1. **Offer-First is non-negotiable.** No ads on a weak offer. Period.
2. **Multi-variant always.** Minimum 3 variants per duration, each with a distinct angle.
3. **Copy is the deliverable, not storyboards.** No VO/Onscreen split. No timestamp tables. Indications scéniques only when critical (max 3 per pack).
4. **Markdown only.** No JSON in the output, ever.
5. **French oral, mobile-first.** Phrases courtes, ton adapté à l'ICP.
6. **One single CTA per variant.** Never two.
7. **Sourced proofs only.** Never invent numbers, names, or testimonials. If missing, flag it.
8. **Meta policy compliance.** No medical, financial guarantee, or discriminatory claims.
9. **Congruence with VSL & LP.** If a VSL exists, the ads must match its mechanism/promise/CTA.
10. **Save to the canonical path** : `projects/clients/{client-slug}/meta-ads/v1.md`.

---

## 📚 Notes

- This skill is the FR-market successor of "Lya" (ChatGPT Custom GPT). Methodology preserved, format simplified per user preference (no VO/Onscreen, copy-only, markdown).
- Source documents (canonical reference) :
  - `leadgen_adscopy.json` (13 modules : copy structure, hooks, value angles, CTA, storyboard, targeting, lead magnet, LP, testing, budgeting, CFA, lead handling, rule of 100)
  - `MetaAds_Strategy_Fundamentals.json` (6 expert profiles : strategy, callout, value, CTA, copywriting rules, scaling)
  - `structure_copy.json` (sector-specific Hook/Body/CTA guidelines : SaaS B2B / Marketing Agency / Coaching / Consulting)
  - `Fiche de Création d'Offre.pdf` (10-step the platform-style FR offer creation)
  - `Acquisition Catalysts Offer Creation.pdf` (Imperium Acquisition : 6 Pillars, Pools of Pain/Confidence, Action Threshold, Offer Composition, Pricing Philosophy, Latent Conditions)
- The detailed frameworks live in `frameworks/`. Load them on demand — don't dump them into the agent context preemptively.
