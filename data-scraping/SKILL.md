---
name: data-scraping
description: >
  Build autonomous B2B data-sourcing engines that scrape, qualify, dedupe and export prospect
  bases from public/legal data — the platform way. Broad data-scraping skill whose flagship
  method is the FREE FRENCH STACK: source companies from open-data SIRENE
  (recherche-entreprises.api.gouv.fr, no key, no cost), score them against an ICP, dedupe by SIREN,
  export multi-sheet CSV/XLSX, then enrich (director name + email) cheapest-first. Use whenever the
  user wants to "scraper des leads", "sourcer des prospects", "build a deal-sourcer / lead list",
  "trouver des entreprises par secteur/NAF/département", "enrichir des emails", "construire une base
  adressable", "scraper des dirigeants", "find companies to contact", or any prospect-database build.
  Deploy parallel sub-agents to build the modules and to validate the output against ground truth.
---

# Data Scraping Engine

How to build a **prospect-sourcing engine** the platform way: real, legal, free data first;
deterministic code for the scraping loop; sub-agents for building & validation; cheapest-first
enrichment last. Scope is broad (any B2B data scraping) — but the **default method** below is the
one to reach for unless the data lives elsewhere.

---

## Core principles (non-negotiable)

1. **Real data or nothing.** Never let an LLM *invent* company rows (SIREN, directors, ages). For a
   GDPR-sensitive subject that is worse than useless. If there is no real source, say so and stop.
2. **Free & legal first.** Exhaust public open-data (SIRENE/INSEE, INPI, BODACC, legal notices)
   before spending a cent. French public registries are gold and free.
3. **The scraping LOOP is deterministic code, not LLM agents.** 50 LLM agents all calling the same
   HTTP endpoint is waste and non-reproducible. The engine is `fetch` + scoring + dedup in TS/Python.
   "50 sub-agents" = 50 **lots** (sector × department) the code iterates — not 50 model calls.
4. **Sub-agents do JUDGEMENT, not loops.** Deploy parallel agents to (a) build the modules against a
   shared type contract, (b) fix scoring heuristics after seeing real data, (c) **validate output
   against ground truth** (official registries). That is where their unique value is.
5. **Pilot before scale.** Run ONE lot, *look at the actual rows*, fix the heuristics, validate a
   sample externally, THEN scale. Every scoring bug below was caught this way, not by typecheck.
6. **Source ≠ outreach.** This skill SOURCES and QUALIFIES only. No message is ever sent. Outreach is
   a separate phase (app / outbound skills).

---

## MÉTHODE Nº1 — Sourcing (free French stack) — step by step

This is the procedure proven on the deal-sourcer-PE build (1757 qualified prospects, 0 cost,
8/8 validated against the Ordre des Vétérinaires). Reuse it verbatim, swap the ICP.

### Step 0 — Probe the source BEFORE designing anything
Curl the API by hand first. The shape of the data decides the whole architecture.
```bash
curl -s "https://recherche-entreprises.api.gouv.fr/search?activite_principale=75.00Z&departement=13&per_page=1" | python3 -m json.tool
```
Check: does it expose what the ICP needs (NAF, dirigeants, année_naissance, effectif, nb_établissements,
catégorie) ? what is `per_page` max (it's **25** — above returns an error with no `results`) ? rate-limit ?
total_results / total_pages ? See `references/sirene-api.md` for the full field map and gotchas.

### Step 1 — Lay the shared type contract YOURSELF
Write `types.ts` (the `Company`, `Lot`, `Source`, `ScoreResult`, output-row types) by hand before
delegating. Sub-agents build *against* it so their modules compose without conflict. Put the NAF
table, effectif-code map and enums here as the single source of truth.

### Step 2 — Deploy parallel sub-agents to build the modules
Independent files, one shared dependency (`types.ts`) → 100% parallelisable. Use a **Workflow** with
`parallel(...)`. Give every agent the same SHARED_CONTEXT (source URL + gotchas + TS/ESM constraints
+ "read BRIEF.md and types.ts in full; create ONLY your file; never edit the shared contract").
Typical split: `sources/sirene.ts`, `sources/<paid>.ts` (dormant), `scoring.ts`, `consolidateurs.ts`
(or ICP table), `csv.ts`. Keep the integration pieces (`orchestrator.ts`, `export-xlsx.ts`,
`funnel-*.ts`, `lots.ts`) for yourself — that's where cross-module coherence matters most.
See `templates/` for ready-to-adapt versions.

### Step 3 — Orchestrator: lots, dedup, parallel pool, atomic CSV
Lots = **sector × department** (priority depts: IDF, PACA, AURA, métropoles). A shared `Set` dedupes
by SIREN across lots. A small concurrency pool (≈4) runs lots politely. Append CSV atomically. Two
buckets: `_CEDANTS.csv` (score ≥ threshold) and `_CEDANTS_froid.csv` (below).

### Step 4 — PILOT (mandatory gate)
Run one lot. **Open the CSV and read the rows.** Then interrogate the cold bucket — that's where real
prospects hide behind weak heuristics. The two real bugs found this way:
- **Director with `qualite: null` ignored** → for 1-establishment SMEs the sole physical director IS
  the owner; fall back to first physical person when `nombre_etablissements <= 2`.
- **No `année_naissance`** (≈60% of FR rows) → no age points. Add a **proxy** from `date_creation`
  (company ≥30 y → +20, 20-29 y → +10) as a fallback *only* when real age is null (never double-count).
Both are heuristic gaps you only see on real data. Re-run, confirm cold→hot recovery, confirm no
regression on rows that already had a real birth year.

### Step 5 — Validate against ground truth (sub-agent + Playwright)
Spin a Playwright sub-agent to check a sample against an OFFICIAL registry (Tableau de l'Ordre des
Vétérinaires, mon-enfant.fr, INPI…). Target ≥5 confirmations. This is the GDPR safety net: it proves
the rows are real, in-business entities, not artefacts. On the reference build: 8/8 confirmed, 0 false
positive. If the registry is captcha-walled, fall back to a light WebSearch existence check — and SAY so.

### Step 6 — Buyer funnel (if double-funnel)
Same SIRENE data, opposite filter. The boundary (used identically in `scoring.ts` AND the buyer
finder): a company is a **consolidator/group** (→ buyer funnel, excluded from sellers) iff
`known-name OR catégorie ∈ {ETI,GE} OR nombre_établissements ≥ 8`. Else (1-7 sites, PME) → seller.
Tune the `≥8` threshold by *looking at the data* — `≥3` is too low (catches multi-site indie SMEs).

### Step 7 — Export & QA at scale
Merge to a multi-sheet `.xlsx` (ExcelJS): hot / cold / buyers / synthèse, frozen header + autofilter,
defensive dedup on `siren`. Then run a QA pass on the FULL base: score distribution, **field
completeness** (be honest — SIRENE gives email 0%, birth-year ~39%), integrity (0 dup, 0 missing
siren, 0 buyer leaked into sellers), geo spread. Write a `QA-RAPPORT.md` next to the data.

### Step 8 — Enrich (cheapest-first) — see `references/email-enrichment-fr.md`
No FR public source gives the email directly. Pipeline: **find domain → generate patterns
(`prenom.nom@domaine`) → verify (MX/SMTP)**. Cleanest free route = scrape the **mentions légales**
(legally-mandated public contact email on every FR pro site). Paid fallback: smallest FR actor
(Societeinfo / Icypeas / Pappers), pay-as-you-go. Be cash about success rates — FR email enrichment
is never 100%.

---

## MÉTHODE Nº2 — Enrichissement email (name→domain→email, OSS gratuit)

> Pour transformer une base de raisons sociales (issue de la Méthode nº1) en base d'emails adressables.
> **Issue d'un banc d'essai réel de 10 outils de scraping** sur 12 cliniques véto FR (11 sous-agents,
> chiffres mesurés, non théoriques). Le pipeline name→domain est porté en local dans le deal-sourcer
> (`src/sources/domain-finder.ts` + `email-finder.ts` + `enrich.ts`, commande `npm run enrich`).
> Détail complet des scores : `references/scraping-tools-benchmark.md`.

### Le combo gagnant (mesuré)
| Étape | Outil gagnant | Pourquoi (chiffres du banc) | Coût |
|---|---|---|---|
| A. Désambiguïsation | API `recherche-entreprises.api.gouv.fr` | ville/CP/dirigeant exacts → **tue les homonymes** (sinon on sort une clinique de Montréal/Toulouse au lieu de l'IDF). Licence Etalab, commercial OK | Gratuit |
| B. Résolution domaine | **SearXNG self-host** (prioritaire) → **ddgs** (fallback gratuit) → Serper (payant) | SearXNG = **0 rate-limit**, 83s/12 ; ddgs gratuit sans clé. 7/12 domaines (plafond réel ~58% car ~40% des PME FR n'ont pas de site) | ~Gratuit (1 VPS) |
| C. Scoring domaine | code maison (`scoreDomainCandidate`) | **NE JAMAIS prendre la 1ère URL** : blacklist annuaires + vérif ville/nom dans le titre. C'est la leçon nº1 — sans ça, 33% de faux positifs (annuaires) | Gratuit |
| D. Extraction email | **Scrapy** (BSD-3) ou fetch+regex maison | 34s/12 (le plus rapide+scalable), AUTOTHROTTLE. Crawl home + /contact + /mentions-legales | Gratuit |
| E. Nettoyage | blacklist maison | rejeter placeholders (`utilisateur@domaine.com`), emails d'éditeurs de template, emails WAF | Gratuit |
| F. Fallback WAF | curl `-k` puis Playwright (dernier recours) | ~15-20% des sites (Imperva, TLS FR cassé). **Le rendu JS n'apporte RIEN sinon** (emails en HTML statique même sur Wix) | Marginal |

### Verdict du banc — à retenir
- **Gagnant résolution domaine : API gouv + SearXNG/ddgs** (8/10). La désambiguïsation SIRENE est l'arme secrète.
- **Gagnant extraction email : Scrapy** (scalable) / email-scraper (meilleur score brut 6/12).
- **À BANNIR** : `googlesearch-python` (1/10, Google a tué le HTML scrapable, échec silencieux), slug+DNS pur (2/10, faux positifs dangereux), `theHarvester` (2/10, OSINT pentest, ne mappe pas société→domaine, modules payants, GPL contaminant), Playwright/crawl4ai en moteur principal (rendu JS inutile ici, 10x plus lent — fallback only).
- **Taux réaliste bout-en-bout** pour 1757 PME : ~1000 domaines, ~700-750 emails. Plafonné par la réalité (~40% sans site), pas par l'outil. Tout chiffre supérieur = faux positifs.
- **Seul point payant éventuel** : proxies résidentiels FR (~30-80€) UNIQUEMENT si forçage WAF à l'échelle. Avec SearXNG self-host, quasi inutiles. Aucune clé API payante requise.

### Lancer la Méthode nº2
```bash
# backend gratuit recommandé : SearXNG (docker run -d -p 8888:8080 searxng/searxng ; activer format JSON)
#   puis SEARXNG_URL=http://localhost:8888 dans .env
# OU plus simple : pip install --break-system-packages ddgs  (fallback gratuit auto-détecté)
npm run enrich -- --limit 50      # test sur 50
npm run enrich                    # toute la base de cédants chauds
# → ajoute colonnes domain / email / source / confidence au CSV
```

---

## When to use
- "scraper / sourcer des leads, prospects, entreprises, dirigeants" (FR especially)
- "build a deal-sourcer, lead list, base adressable, prospect database"
- "trouver des boîtes par secteur / NAF / département / effectif"
- "enrichir des emails", "trouver les dirigeants de ces boîtes"

## When NOT to use
- The user wants to *send* the outreach → `outbound/*`, `app`
- The data is NOT company-registry-shaped (e.g. scraping ad creatives) → `competitor-ads-research`
- A bespoke single-site scrape with no qualification step → just write the scraper inline

## Output contract
A `data/` folder (git-ignored — prospect data is GDPR-sensitive): `*_CEDANTS.csv` (hot, score ≥ seuil),
`*_CEDANTS_froid.csv`, `*_ACHETEURS.csv`, `*.xlsx` (multi-sheet, deduped), `QA-RAPPORT.md`.
Deliver to the user as `.xlsx` on the Desktop (drag into Drive → auto-converts to multi-tab Sheet) —
this avoids any OAuth/token friction. Never print tokens/secrets in chat.

## GDPR guardrails
Public/legal registry data only. No personal-email scraping. **No contact sent.** Sensitive subject
(a director's professional life) → respectful tone reserved for phase 2, human R1 non-negotiable.
The most defensible email source is the publicly-displayed legal-notice address.

## Reference build
A local TS engine (`deal-sourcer`) built with this method produced 1757 qualified FR SME sellers
+ 97 consolidators, 100% free SIRENE, validated.
