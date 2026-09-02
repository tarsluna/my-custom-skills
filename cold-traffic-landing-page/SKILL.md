---
name: cold-traffic-landing-page
description: Generate a high-converting, branded, responsive landing page for a client, optimized for COLD Meta/TikTok/YouTube traffic. Inputs = client website URL + onboarding form (agency questionnaire) + 3 deepsearch reports + (optional) VSL strategy. Output = a production-ready static landing page (HTML/CSS/JS or Next.js), brand-faithful, mobile-first, optimized for opt-in / lead capture / call booking. Use when the user asks to "génère une landing page", "fais une LP pour {client}", "landing page trafic froid", "page d'opt-in {client}", "build a cold-traffic landing page", "LP pour ma campagne Meta", "page de capture {client}". Trigger phrases: "landing page {client}", "LP {client}", "page froid {client}", "build LP", "génère la LP".
---

# Cold Traffic Landing Page Builder

End-to-end skill that ingests a client's full context (website + onboarding questionnaire + deep-search reports + optional VSL strategy) and produces a **production-ready, branded, responsive, conversion-optimized landing page** designed for **cold paid traffic** (Meta/TikTok/YouTube). The page is built statically (HTML/CSS/JS by default, Next.js only if explicitly requested), deployed to Vercel, and optimized for **a single primary action** (opt-in form, call booking, or VSL view).

This skill is the **stage 4** of pipeline:

```
[Stage 1] deep-search          → 3 research reports
[Stage 2] vsl-copywriter       → VSL script + strategy
[Stage 3] meta-ads-copywriter  → Meta ad pack
[Stage 4] cold-traffic-landing-page → Landing page (THIS SKILL)
```

The landing page must be **congruent** with the Meta ads driving traffic to it (same promise, same mechanism, same CTA), and (if a VSL exists) must serve as the host page for the VSL.

---

## 🎯 When to use this skill

Trigger when the user asks any of:
- "Génère/fais une landing page pour {client}"
- "LP {client}", "Page froid {client}", "Page d'opt-in {client}"
- "Build a cold-traffic landing page", "Build LP"
- "Page de capture / page de candidature {client}"
- "Refais la LP de {client}"

DO NOT trigger when the user asks for:
- A long sales letter with no traffic context → use `static-vercel-landing-page` (the generic one)
- A VSL script → use `vsl-copywriter`
- Meta ad copies → use `meta-ads-copywriter`
- A full app or dashboard → use `frontend-design` or `fullstack-developer`

---

## 📦 Inputs (read EVERYTHING before writing a single line)

### Required
1. **Client website URL** — fetch with `WebFetch` to extract:
   - Brand colors (CSS, screenshots, hero), logo, typography, tone of voice
   - Existing offer language (so we can sharpen, not contradict)
   - Existing CTA targets (Calendly, Tally, custom form)
2. **Onboarding form** (agency questionnaire `responses`) — usually in:
   - `projects/{client-slug}/00-brief.md` or
   - the original JSON/text the user paste
   - Extract: offer, prix, ICP, douleurs, bénéfices, CTA, preuves, branding (h_logo, h_visuels, h_preuves), e_url, e_post_clic_phrase1/2
3. **3 deepsearch reports** at:
   ```
   projects/{client-slug}/research/
   ├── 01-market-awareness.md
   ├── 02-competitors.md
   └── 03-psychographic.md
   ```
   Extract: awareness level, sophistication level, top 10 verbatim pains, top 5 dreams, hooks gagnants, gaps concurrentiels, big idea recommandée.

### Optional but strongly preferred
4. **VSL strategy & script** at `projects/{client-slug}/vsl/` — to inherit big idea, named mechanism, and offer stack.
5. **Meta Ads pack** at `projects/{client-slug}/meta-ads/` — to ensure ad → LP congruence (same hook, same promise, same CTA).
6. **Brand assets** : logo URLs (h_logo Figma), visuals (h_visuels), proof folder (h_preuves Drive).

### If anything is missing
Use `AskUserQuestion` to collect ONLY the strict minimum:
- URL site web
- Slug client
- Objectif primaire (opt-in form / RDV calendly / VSL view)
- URL du formulaire de RDV / Tally / Calendly
- (si pas de research) ICP en 1 phrase + offre + prix

NEVER invent proof, testimonials, numbers, or client names. If missing, flag explicitly.

---

## 🔄 Pipeline (7 phases)

### Phase 1 — Context loading

**1.1** Identify client slug.
**1.2** `WebFetch` the client website (homepage + 1-2 deep pages if linked) to extract brand DNA: colors (note hex if visible), typography family, hero imagery style, tone (tu/vous, premium/casual), existing CTA wording.
**1.3** Read in parallel:
   - `projects/{slug}/00-brief.md` (or onboarding JSON)
   - `projects/{slug}/research/01-market-awareness.md`
   - `projects/{slug}/research/02-competitors.md`
   - `projects/{slug}/research/03-psychographic.md`
   - (if exists) `projects/{slug}/vsl/strategy.md` and `script-v1.md`
   - (if exists) `projects/{slug}/meta-ads/v1.md`
**1.4** Build internal scratchpad:
   - Avatar (1 sentence) + Awareness level + Sophistication level
   - Top 3 verbatim pains
   - Top 3 desired outcomes
   - Big idea + Named mechanism (inherited from VSL if exists)
   - Offer composition + price + risk reversal
   - Proof inventory (numbers, names, screenshots, testimonials)
   - Brand: 2 hex colors + 1 accent + font family + tone + logo path
   - Primary CTA goal & destination URL

---

### Phase 2 — Strategy decision (page archetype)

Choose ONE archetype based on awareness/sophistication and CTA goal:

| Awareness | CTA goal | Archetype | Length |
|-----------|----------|-----------|--------|
| Solution/Product Aware | Book a call | **Application page** | Short, qualification-heavy |
| Solution/Product Aware | View VSL → book call | **VSL host page** | Ultra-short, 1 video + 1 CTA below |
| Problem Aware | Free lead magnet / opt-in | **Opt-in squeeze** | Hero + 3 bullets + form |
| Most Aware | Direct purchase | **Sales page** | Long-form, full stack |
| Cold + low awareness | Book a call | **Advertorial → call** | Medium, story-led |

**Default for cold Meta traffic on a high-ticket coaching/service offer = "Application page"** with optional VSL block above the fold if a VSL exists.

Document the archetype choice in 1 line.

---

### Phase 3 — Copy blueprint

Build the copy block-by-block BEFORE touching code. Use this canonical structure (skip blocks that don't fit the archetype):

```
1. Hero
   - Eyebrow (category cue, 3-6 words)
   - Headline (≤12 words, dream outcome + timeframe + without sacrifice)
   - Subheadline (≤25 words, who it's for + named mechanism)
   - Primary CTA button (action verb + outcome)
   - Trust strip (3-5 logos OR "+X clients" OR Trustpilot/note)
   - Hero visual: video VSL embed | client photo | mockup | abstract

2. Pain agitation (1 block)
   - "Si tu te reconnais dans ces situations…" + 4-5 verbatim bullets

3. Vision / Dream outcome
   - "Imagine si…" + 3 bullets future-state

4. Mechanism / How it works
   - Named mechanism (3-4 word brand)
   - 3-4 step cards (Step 1 / 2 / 3 / 4)

5. Proof (NEVER skip if proof exists)
   - 2-3 testimonials (verbatim, photo, name, result)
   - Logos / numbers strip
   - 1 case study card with before/after numbers

6. Offer / What you get
   - Bullet list of deliverables
   - Bonus stack (if applicable)
   - Risk reversal / guarantee

7. Who it's for / NOT for (polarization)
   - 2 columns: ✅ Pour toi si | ❌ Pas pour toi si

8. About (founder credibility, 1 paragraph + photo)

9. FAQ (5-7 questions, real objections from research)

10. Final CTA section
    - Repeat headline
    - Primary CTA button
    - Last micro-proof line

11. Footer
    - Mentions légales, contact, copyright
```

For each block, write the **final copy in French oral** (or `vous` for B2B premium). Use verbatim pains from research. Repeat the named mechanism 3-5x across the page. NEVER more than ONE primary CTA action across the whole page (it can appear 3-4 times but always the same destination).

---

### Phase 4 — Design system

**4.1 Brand mapping** — extract from website analysis:
   - Primary color (hex)
   - Secondary / accent color (hex)
   - Background (light/dark/neutral)
   - Font family (Google Fonts equivalent if proprietary)
   - Border radius (sharp / rounded / pill)
   - Vibe (premium minimal / playful bold / luxury / brutalist / corporate)

**4.2 Design defaults if brand is weak/absent:**
   - Background: `#0A0A0A` (dark) or `#FAFAF7` (warm light)
   - Primary: client's strongest brand color OR `#0EA5E9` (sky-500)
   - Accent: complementary
   - Font: `Inter` is BANNED. Use instead: `Geist`, `Satoshi`, `General Sans`, `Manrope`, `Sora`, `Space Grotesk`, `Instrument Serif` (display) or `Fraunces` (display) — pair sans + serif when premium.
   - Buttons: large (`py-4 px-8`), high contrast, subtle shadow, rounded-lg (not pill unless playful)
   - Spacing: generous (`py-24 md:py-32` between sections)
   - Mobile-first: every block must look perfect at 375px

**4.3 Anti-AI-slop rules** (HARD)
   - ❌ NO Inter / Roboto / Open Sans
   - ❌ NO purple gradients
   - ❌ NO 3 SaaS feature cards in a row with generic icons
   - ❌ NO "✨ AI-Powered" / generic emoji stuffing
   - ❌ NO low-contrast gray-on-gray text
   - ❌ NO glassmorphism unless it fits the brand
   - ❌ NO stacked giant headlines back-to-back
   - ✅ DO use asymmetry, negative space, one bold accent, distinctive type
   - ✅ DO use real photos / real logos / real numbers when available
   - ✅ DO use one signature visual element (badge, marquee, cursor-follow, sticky CTA)

---

### Phase 5 — Build

**5.1 Tech default: static HTML/CSS/JS** with Tailwind CDN (fastest path, no build).
Folder structure:
```
projects/{slug}/landing-page/
├── index.html
├── styles.css         (custom overrides)
├── script.js          (sticky CTA, FAQ accordion, smooth scroll, simple form post)
├── assets/
│   ├── logo.svg
│   ├── og-image.jpg
│   └── favicon.ico
└── vercel.json
```

**5.2 If user asks for Next.js / shadcn / React** → scaffold a minimal Next.js 14 app with Tailwind v4 + shadcn/ui blocks. Same structure under `landing-page/`.

**5.3 HTML head essentials** (always include):
- `<meta name="viewport" content="width=device-width, initial-scale=1">`
- Open Graph tags (title, description, og:image)
- Favicon
- Tailwind CDN OR compiled CSS
- Google Fonts link (only the chosen family)
- Meta Pixel snippet placeholder `<!-- META PIXEL: paste pixel_id from brief -->`
- (if applicable) GA4 placeholder

**5.4 Sections**: write each block from Phase 3 as a `<section>` with id, semantic HTML (`<h1>`, `<h2>`, `<button>`, `<form>`), aria labels, and Tailwind utility classes. Mobile-first: design at 375px first, then desktop.

**5.5 Form** (if archetype = opt-in or application):
   - HTML form posting to `e_url` from brief OR a Tally/Typeform embed OR a Calendly inline embed
   - Required fields: prénom, email, téléphone (+ 1-2 qualifying questions if "application")
   - Honeypot anti-spam field
   - Success state: thank-you message OR redirect URL
   - On submit: fire Meta Pixel `Lead` event

**5.6 Sticky mobile CTA bar** (almost always for cold traffic): bottom-fixed bar with primary button, visible after scrolling 30% of page.

**5.7 `vercel.json`**:
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "cleanUrls": true,
  "trailingSlash": false
}
```

---

### Phase 6 — QA & polish (mandatory before delivery)

Run this checklist and fix every failure:

**Content**
- [ ] Hero headline ≤12 words, makes a claim, includes timeframe or specificity
- [ ] One single primary CTA destination across the whole page
- [ ] Named mechanism appears 3-5 times
- [ ] At least 3 verbatim pains from research used as bullets
- [ ] At least 1 sourced proof (number, name, screenshot, or testimonial — NEVER invented)
- [ ] FAQ contains 5-7 real objections from research
- [ ] Footer has mentions légales placeholder + contact email

**Design**
- [ ] Looks great at 375px (iPhone SE), 768px (tablet), 1280px (desktop), 1920px
- [ ] Banned fonts not used (no Inter / Roboto / Open Sans)
- [ ] Contrast passes WCAG AA on all text
- [ ] Hero loads instantly (no 5MB image)
- [ ] One signature design element (not generic SaaS template)
- [ ] All CTAs have hover + active states

**Tech**
- [ ] All anchors resolve, no broken `<a href="#">`
- [ ] Form action set to real URL (or flagged placeholder)
- [ ] Meta Pixel placeholder present
- [ ] OG tags + favicon
- [ ] No console errors
- [ ] Lighthouse mobile score target: Performance ≥85, Accessibility ≥95, Best Practices ≥95, SEO ≥90

**Congruence with Meta Ads (if exists)**
- [ ] Hero headline echoes the winning ad hook
- [ ] Same named mechanism
- [ ] Same primary CTA destination
- [ ] Same offer language

If a check fails and cannot be fixed (e.g., no real proof exists) → flag explicitly to the user, never invent.

---

### Phase 7 — Deploy & deliver

**7.1** Local preview:
```bash
cd projects/{slug}/landing-page && python3 -m http.server 8791
```
Open in browser, screenshot mobile + desktop, do a vision pass.

**7.2** Deploy (only if user has Vercel CLI authenticated):
```bash
vercel whoami  # check auth
vercel --prod --yes  # deploy
```
Capture the production URL.

**7.3** Save artifacts:
```
projects/{slug}/landing-page/
├── index.html
├── styles.css
├── script.js
├── assets/
├── vercel.json
└── README.md  ← contains: deploy URL, what's missing, next steps
```

**7.4** Final user message (in French):
> ✅ Landing page **{CLIENT}** générée et déployée.
> - **URL preview** : `{vercel-url}` (ou local)
> - **Archetype** : {archetype} — optimisée pour {CTA goal}
> - **Mécanisme repris** : {nom}
> - **Brand** : {color1}/{color2}, font {family}
> - **À remplacer avant lancement** :
>   - [ ] Logo réel : {h_logo}
>   - [ ] Pixel Meta ID
>   - [ ] URL du formulaire de RDV ({e_url})
>   - [ ] Visuels client / témoignages photo
> - **Prochaine étape** : revue visuelle, swap des placeholders, test sur mobile réel, lancement Meta avec un budget test sur 1 ad set.

---

## 🚦 Hard rules (never break)

1. **Read everything before writing a single line.** Website + brief + 3 research reports + VSL/ads if exists.
2. **One primary CTA only.** Repeated 3-4× across the page, same destination.
3. **Cold traffic = mobile-first.** Design at 375px first, always.
4. **No invented proof.** Numbers, names, testimonials, logos must be real or flagged.
5. **Brand congruence.** Page must look like the client's brand, not a generic template.
6. **Ad → LP congruence.** Same hook, same mechanism, same CTA as the Meta ads.
7. **Anti-AI-slop.** No Inter, no purple gradients, no generic 3-card SaaS layout.
8. **Performance.** Lighthouse mobile ≥85, hero loads <1.5s on 4G.
9. **One signature visual element.** Marquee, sticky badge, asymmetric layout, distinctive type pairing — pick one and own it.
10. **Save under canonical path** : `projects/{slug}/landing-page/`.

---

## 🎨 Reference design inspirations (anti-template)

When in doubt about aesthetic direction, lean toward these references (do not copy, adapt to the brand):

- **Premium minimal coaching** : Linear-style dark + serif display + one vivid accent (Stripe, Vercel, Linear, Amie)
- **High-ticket consulting** : Cream background + serif display (Fraunces) + black accent (Patrick Campbell, ProfitWell, CXL)
- **Bold founder-led** : Big punchy sans (Sora, Geist) + photo of founder + 1 wild accent
- **Editorial advertorial** : Newspaper-style serif body + small caps + thin rules (long-form sales pages)

---

## 🔗 Companion skills

- `deep-search` — must run BEFORE this skill if no research exists
- `vsl-copywriter` — its `strategy.md` provides big idea + mechanism inherited here
- `meta-ads-copywriter` — produces the ads that drive traffic to this LP (must be congruent)
- `frontend-design` — load it for design philosophy if a deeper aesthetic exploration is needed
- `static-vercel-landing-page` — the generic version of this skill (use it only when no client context exists)

---

## 📚 Notes

- Default tech = static HTML/CSS/JS + Tailwind CDN. Switch to Next.js/shadcn ONLY if explicitly asked.
- This skill encodes lessons from: `static-vercel-landing-page` (workflow), `frontend-design` (anti-AI-slop), Hormozi (offer stack), Schwartz (awareness levels), Sugarman (slippery slide), Brunson (squeeze pages), shadcn/ui blocks (component composition).
- Always sanity-check the LP against the winning Meta ad hook BEFORE deploying — if they don't match, you'll burn ad spend.
