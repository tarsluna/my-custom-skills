---
name: deep-search
description: Run the 3 DeepSearch studies (Market Awareness, Competitor Research, Psychographic Research) automatically for a client and produce 3 finished markdown reports. Use when the user asks for "deep search", "market research", "étude de marché", "recherche concurrentielle", "psychographic research", "agency research", or wants research documents for a client. Trigger phrases: "deep search pour {client}", "market research {client}", "étude de marché client", "lance le deep search", "deep search agence".
---

# Deep Search (Automated Pipeline)

End-to-end pipeline that takes a client brief and produces **3 finished DeepSearch reports** automatically. The user only provides the client. The skill handles prompt generation, execution (deep web research), and document output.

## Pipeline (3 steps)

### Step 1 — Generate the 3 prompts (internal)
Build the 3 prompts using the EXACT templates below, replacing variables with the client's info:
- `YOUR NICHE` → client's market/niche
- `PRODUCT` → client's specific product or service
- `GEOGRAPHY` → geographical market (default: France)
- `DETAILS` → additional market context (optional)
- `[TYPE OF COMPETITOR PRODUCT, BASED ON THE INDUSTRY]` → competitor product type
- `DEMO/Market Information` → target demographic / ICP

ALWAYS append at the end of EACH prompt:
➡️ **I would like to get the output of this in French and focusing my research on the French market.**

These prompts are NOT shown to the user. They are internal instructions guiding the research.

### Step 2 — Execute the 3 DeepSearches
For EACH of the 3 prompts, run a real deep web research pass using available tools. Use the `Agent` tool with `subagent_type: "general-purpose"` (one agent per study, in **parallel**, single message with 3 tool calls) so each study runs independently and uses `WebSearch` + `WebFetch` aggressively.

Each agent receives:
- The full prompt text (in English, with the French output instruction at the end)
- Instructions to use WebSearch/WebFetch extensively (minimum 10-15 queries per study)
- Instructions to focus on the French market
- Instructions to return a complete, well-structured markdown report in **French**, with:
  - Executive summary
  - All sections requested in the prompt
  - Sourced quotes (URL + date)
  - Data tables when relevant
  - Final synthesis/recommendation

### Step 3 — Save the 3 reports
Write the 3 returned reports as markdown files in:
```
projects/clients/{client-slug}/research/
├── 01-market-awareness.md
├── 02-competitors.md
└── 03-psychographic.md
```

Create the directory if it doesn't exist. The `{client-slug}` is the client name lowercased and kebab-cased (e.g., "TopCo" → "topco").

### Step 4 — Générer les 3 PDFs brandés à l'agence

Après avoir sauvegardé les 3 fichiers .md, générer **en parallèle** les 3 PDFs brandés à l'agence correspondants. Utiliser le script `build_deep_search_pdf.py` situé dans `skills/deep-search/assets/`.

Exécuter les 3 commandes en parallèle (3 appels Bash simultanés) :

```bash
python3 ~/skills/deep-search/assets/build_deep_search_pdf.py \
    "projects/clients/{client-slug}/research/01-market-awareness.md" \
    "projects/clients/{client-slug}/research/DeepSearch-Conscience-Marche-{Client}.pdf" \
    --client "{Client Name}" \
    --report-type "market-awareness"
```

```bash
python3 ~/skills/deep-search/assets/build_deep_search_pdf.py \
    "projects/clients/{client-slug}/research/02-competitors.md" \
    "projects/clients/{client-slug}/research/DeepSearch-Concurrents-{Client}.pdf" \
    --client "{Client Name}" \
    --report-type "competitors"
```

```bash
python3 ~/skills/deep-search/assets/build_deep_search_pdf.py \
    "projects/clients/{client-slug}/research/03-psychographic.md" \
    "projects/clients/{client-slug}/research/DeepSearch-Psychographique-{Client}.pdf" \
    --client "{Client Name}" \
    --report-type "psychographic"
```

Les PDFs générés reprennent l'identité visuelle de l'agence (logo en filigrane via `--logo` ou env `AGENCY_LOGO`, couleurs #4A7FD4 / #1E2A4A, footer "{Agence} — Confidentiel" via `--brand` ou env `AGENCY_NAME` — défaut neutre "Confidentiel", page de couverture brandée).

Si `reportlab` n'est pas installé, l'installer avec : `pip3 install reportlab --break-system-packages`

After saving, report to the user (in French):
- The 3 .md file paths created
- The 3 .pdf file paths created
- A 2-3 line summary of each report's key finding
- Suggest next steps (review, validate, feed into VSL skill)

## Discovery (if information is missing)
If the user provides only a client name without context, use `AskUserQuestion` to gather the minimum required:
- **Niche / industry**
- **Specific product or service**
- **Target demographic / ICP**
- **Type of competitor products to analyze**
- **Geography** (default France — only ask if doubt)
- **Additional market details** (optional, can skip)

Do NOT proceed to Step 2 without at least: niche, product, demo, competitor type.

If the client already has a file in `projects/clients/{client}/` or is mentioned in your agency's client notes, READ it first to auto-fill the variables before asking the user.

---

## TEMPLATE — Prompt 1 — Market Awareness DeepSearch

```
I want your help evaluating the level of Market Awareness for a product in the **YOUR NICHE** space. The specific product is **PRODUCT**.

I would like for you to dive deep to help me understand the current level of market awareness for this product in **GEOGRAPHY**.

**Optional:** Here are more details about the market: **DETAILS**

To do this, we can look at the classic levels of Product and Market awareness that is often attributed to Eugene Schwarz, which can be categorized as follows:

1. Unaware: Prospects are not even aware of a problem or need that your product or service can solve.
2. Problem Aware: Prospects recognize they have a problem or need but are unaware of potential solutions.
3. Solution Aware: Prospects know that solutions exist for their problem, but they are not yet aware of your specific solution.
4. Product Aware: Prospects know about your solution, your product or service, and are evaluating its features and benefits.
5. Most Aware: Prospects are highly aware of your solution, its benefits, and are likely to make a purchase decision soon.

For the intents of this exercise, let's not consider Product Aware or Most Aware to be for our specific product and brand. Instead let's consider it to be an awareness about similar/nearly identical products and brands that offer those products.

In order to make this assessment please utilize a variety of signals including social media chatter, articles and blog posts, influencer content, search trends, any available sales data on the product category (and its growth), and so on.

Additionally:

1. Please provide an overview of the estimated TAM (total addressable market) for this product.
2. Please provide a rough estimate of what percentage of the TAM falls into each category of product/market awareness.
3. At the end of your review, please give me a FINAL selection for which stage of Product/Market Awareness the majority of individuals within the market fall.

Thanks!

➡️ **I would like to get the output of this in French and focusing my research on the French market.**
```

---

## TEMPLATE — Prompt 2 — Competitor DeepSearch

```
I want your help doing competitor research for a product in the **YOUR NICHE** space. The specific product is **PRODUCT** and we are focused on competitors in **GEOGRAPHY**.

Specifically, we're looking for [TYPE OF COMPETITOR PRODUCT, BASED ON THE INDUSTRY]

For each competitor you find, I want to understand:

* Who is the target demo they speak to?
* What are their main new customer acquisition funnels?
* What is their core messaging in their ads, advertorials, and other advertising assets?
* What are examples of their advertisements or landing page assets if available?
* Are there any recurring or repetitive hooks/angles/big ideas you see consistently appearing in their advertising assets?
* What is their pricing structure?
* What do customers love and what do customers dislike about them (use reviews, social signals, social media platforms, etc to answer this)?
* If available, what is their estimated overall business revenue and revenue for their hero product(s) that are most similar to the one I've mentioned?

**Optional:** Here are more details about the market: **DETAILS**

Please go ahead and get started now, and thank you!

➡️ **I would like to get the output of this in French and focusing my research on the French market.**
```

---

## TEMPLATE — Prompt 3 — Psychographic Research

```
I am writing some sales copy targeted towards **DEMO/Market Information**.

I'd like your help doing psychographic research. What are their struggles and pain points? What are their beliefs?

Below is a series of questions I used in the past, as part of my RMBC Method for copywriting, where the R stands for research. This should be a good framework to use while doing research on the demo. I'd love it if you can even provide 'quotes' from folks in this demo by looking at comments on social media, or in forums, etc. Basically we want to hear what they're saying and what they believe. We want to hear answers in their own words!

Here's the list of questions:

**Insights Into Demographic:**

* Who Is Your Customer?
* What Attitudes Do They Have? (Religious, Political, Social, Economic)?
* What Are Their Hopes and Dreams?
* What Are Their Victories and Failures?
* What Outside Forces Do THEY Believe Have Prevented Their Best Life?
* What Are Their Prejudices?
* Sum Up Their Core Beliefs About Life, Love, and Family In 1-3 Sentences.

**Other Existing Solutions:**

* What is the Market Already Using? (List Out)
* What Has Their Experience Been Like?
* What Does the Market Like About Existing Solutions?
* What Does the Market Dislike About Existing Solutions?
* Are Their Horror Stories About Existing Solutions?
* Does the Market Believe Existing Solution Works?
* If Not, Why?

**Curiosity:**

* Has Someone Tried to Solve the Market's Pain Points Before In A Very Unique Way?
* What Was The Result?
* Is There A Conspiratorial Story Behind Why Old Solutions Didn't Work?
* Are There Any Older Attempts to Solve the Problem (Pre-1960) That Are Unique?
* What Happened? Were they successful but forgotten? Or were they a failure? Why?

**Corruption:**

* Is There A Belief That the Market's Pain Point Used To Not Exist, Or Used To Not Be So Bad?
* Is There A Belief That It's Been Recently Exacerbated By Outside Forces?
* If So, What Are Those Forces And What's The Reason Behind Their Presence?

Thanks!

➡️ **I would like to get the output of this in French and focusing my research on the French market.**
```

---

## Sub-agent execution instructions

When delegating each prompt to a `general-purpose` sub-agent, frame the task like this:

> You are running a deep market research study for the agency. Below is the full research prompt. You MUST:
> 1. Use WebSearch and WebFetch extensively (minimum 10-15 queries) to gather real, sourced data about the **French market**.
> 2. Cite every claim with a URL and a date when possible.
> 3. Include quotes from real prospects/customers (forums, Reddit FR, Trustpilot, Avis Vérifiés, LinkedIn comments, Twitter/X, YouTube comments).
> 4. Structure the final answer as a complete French markdown report covering ALL sections of the prompt — no skipping.
> 5. End with an executive synthesis and a clear recommendation.
> 6. Return ONLY the markdown report (no preamble, no meta-commentary) so it can be saved directly to a file.
>
> Here is the research prompt to execute:
>
> [INSERT FULL PROMPT TEXT HERE]

Run the 3 sub-agents **in parallel** (single message, 3 Agent tool calls) for speed.

## Output structure
```
projects/clients/{client-slug}/
└── research/
    ├── 01-market-awareness.md                          # rapport markdown
    ├── 02-competitors.md                                # rapport markdown
    ├── 03-psychographic.md                              # rapport markdown
    ├── DeepSearch-Conscience-Marche-{Client}.pdf        # PDF brandé à l'agence
    ├── DeepSearch-Concurrents-{Client}.pdf              # PDF brandé à l'agence
    └── DeepSearch-Psychographique-{Client}.pdf          # PDF brandé à l'agence
```

## Final user message (in French)
After saving, send something like:

> ✅ Deep Search terminé pour **{CLIENT}**. 6 livrables sauvegardés (3 .md + 3 .pdf) :
>
> **Rapports Markdown :**
> - `01-market-awareness.md` — niveau de conscience marché : {niveau}
> - `02-competitors.md` — {N} concurrents analysés
> - `03-psychographic.md` — {N} insights psychographiques + quotes
>
> **Documents PDF brandés à l'agence :**
> - `DeepSearch-Conscience-Marche-{Client}.pdf`
> - `DeepSearch-Concurrents-{Client}.pdf`
> - `DeepSearch-Psychographique-{Client}.pdf`
>
> Prochaine étape suggérée : feeder ces rapports dans le skill `vsl-end-to-end-builder` pour construire la stratégie et le script.

## Notes
- NE JAMAIS modifier le contenu des templates de prompts (sauf les variables).
- TOUJOURS exécuter les 3 sub-agents en parallèle.
- TOUJOURS sauvegarder en markdown français.
- TOUJOURS inclure les sources (URLs + dates) dans les rapports.
- TOUJOURS générer les 3 PDFs brandés à l'agence après les .md (Step 4).
- Si une étude échoue ou retourne un contenu trop léger, relancer le sub-agent concerné avec une instruction plus stricte sur le volume de recherche.
- Si la génération PDF échoue (reportlab manquant), installer avec `pip3 install reportlab --break-system-packages` puis relancer.

## Structure du skill
```
deep-search/
├── SKILL.md                          ← ce fichier
└── assets/
    └── build_deep_search_pdf.py      ← générateur PDF brandé à l'agence
```
