# Preset Acme SEO (exemple fictif)

> Sender : Acme SEO (SaaS SEO en pilote automatique pour SaaS B2B). **Sender fictif** : sert de modèle de preset complet ; remplacer par ta propre boîte.
> Date de mise à jour : <YYYY-MM-DD>
> Sources : landing du produit + composants de la landing (hero, features, mode autopilote) + notes produit

---

## Identification

```yaml
entreprise: "Acme SEO"
resumeOffre: "Agent SEO autonome qui recherche les mots-clés, écrit les articles, les optimise et les publie automatiquement sur ton CMS."
typeOffre: "SaaS B2B"
prix: "à partir de 49€/mois (audit gratuit à l'entrée du funnel sur audit.acme-seo.example)"
```

## Promesse & différenciation

```yaml
promesse: "Votre contenu SEO, en pilote automatique. 6-12 articles SEO/mois publiés sans recruter, sans agence, sans micro-management."
benefice1: "Plus besoin d'agence à 3-5k€/mois ni de rédacteurs freelance"
benefice2: "6-12 articles publiés par mois (vs 1-2 typiquement via agence)"
benefice3: "Tracking GEO inclus — vous voyez si ChatGPT, Perplexity et Claude citent votre marque"
differenciants: |
  - Agent autonome end-to-end (recherche → draft → publication CMS) vs outils qui font 1 étape
  - GEO tracking natif (LLM citations) — quasi-personne ne le fait en SaaS SEO en 2026
  - YOLO Mode : tout est piloté pour vous, validation 10 min/semaine max
  - Mode dérivé en fallback : tu vois quand même tes métriques estimées si tu n'as pas câblé OpenRouter
preuves: |
  - Audit gratuit sur audit.acme-seo.example (point d'entrée principal)
  - Funnel tracké de bout en bout (pixel Meta + CAPI) — chiffres d'audit → signup disponibles
  - Cas client : "3-5x le trafic organique en 6 mois" (à valider/sourcer avant claim)
```

---

## ICP(s)

### ICP 1 — Founder / Head of Growth SaaS B2B

```yaml
cibleDescription: "Founder ou Head of Growth dans un SaaS B2B early-stage à scale-up, qui sait que le SEO est important mais qui n'a ni le temps ni l'envie de gérer une agence ou une équipe content."
cibleSecteur: "SaaS B2B, agences digitales, e-commerce ambitieux"
cibleFonctions: "Founder / CEO / Head of Growth / Head of Marketing / CMO"
cibleProblemes: |
  - "Mon SEO stagne mais je n'ai pas le temps de m'en occuper"
  - "Mon agence me coûte 3-5k€/mois et sort 2 articles/mois — pas rentable"
  - "Je perds 6-8h/semaine à briefer/relire des drafts"
  - "Je ne sais pas si ChatGPT et Perplexity citent ma marque (GEO blindspot)"
cibleValeur: "Du temps récupéré, du trafic organique scalable, une vraie visibilité dans les LLM (qui deviennent le nouveau Google)"
cibleFreins: |
  - "L'IA va écrire du mauvais contenu"
  - "Google va déclasser le contenu IA"
  - "J'ai déjà une agence, c'est trop chiant à remplacer"
  - "Je n'ai pas le budget"
cibleMotivations: |
  - Rationnels : ROI clair (vs agence), gain de temps mesurable, GEO competitive moat
  - Émotionnels : se libérer du content ops, retrouver de la latitude stratégique
```

---

## CTA + parcours

```yaml
ctaType: "audit"
ctaExact: "Vous voulez un audit SEO gratuit de votre site (5 min) ?"
conversion: "Taux de réponse cible 5-10% (cold B2B SaaS), taux de complétion audit cible 30%+"
destination: "https://audit.acme-seo.example"
```

## Méta

```yaml
langue: "fr"
objectif: "génération de leads SaaS B2B vers l'audit gratuit, qui alimente le funnel de l'app"
```

---

## Angles pré-définis

### Angle 1 — "L'agence SEO est obsolète"

Comparer frontalement le coût agence (3-5k€/mois pour 2 articles) vs Acme SEO (49€/mois pour 6-12 articles). Framework **PAS** ou **SLAP**. Cible : founders qui ont déjà une agence et la trouvent décevante.

### Angle 2 — "GEO blindspot"

Tu ne sais pas si ChatGPT/Perplexity/Claude citent ta marque — et c'est en train de devenir aussi important que Google. Framework **AIDA** ou **4U**. Cible : Head of Growth curieux et early-adopter, founders ambitieux.

### Angle 3 — "Pilote automatique"

Avant : 8h/semaine à manager le content. Après : 10 min de validation. Framework **BAB**. Cible : founders sur-bookés qui veulent juste que le SEO tourne sans eux.

---

## Anti-patterns spécifiques

- ❌ Ne **jamais** promettre des positions Google précises ("rank #1 en 3 mois")
- ❌ Ne **jamais** dénigrer la qualité éditoriale agence ("agences écrivent mal") — angle perdant
- ❌ Ne **jamais** vendre "le SEO mort, vive le GEO" — c'est un AND, pas un OR
- ❌ Pas de claim sans source : si on cite un cas client, le sourcer
- ✅ Préférer l'angle **temps récupéré** > l'angle **trafic** (le trafic est trop "promesse SEO classique")

---

## Subjects testés / à tester

À reprendre / itérer :

- "Votre SEO en pilote automatique ?"
- "{{firstName}}, 6 articles SEO/mois sans agence"
- "Audit SEO gratuit pour {{companyName}} (5 min)"
- "ChatGPT cite-t-il {{companyName}} ?"
- "8h/semaine récupérées sur le SEO"
- "Le SEO en 10 min/semaine"

À tester :
- "On a remplacé l'agence SEO de [client] par un agent" (valider le claim avant)
- "Combien d'articles SEO sortez-vous par mois ?"

---

## Provider par défaut

```yaml
provider_default: "lemlist"
provider_rationale: "Icebreaker AI utile pour personnaliser la première ligne par lead. Déjà dans la stack outbound du sender."
```
