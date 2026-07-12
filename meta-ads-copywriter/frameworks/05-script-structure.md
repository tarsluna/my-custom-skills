# Framework 05 — Script Structure & Copy Format

> Source : `creative_narrative_studio_v1` + `MetaAds_Copywriting_Rules` + `structure_copy.json` + Lya playbook.
> Used in **Phase 4** of the skill.

> **Format obligatoire** : copy uniquement (pas de VO/Onscreen split, pas de timestamps en colonnes). Indications scéniques en italique uniquement si critiques pour le sens.

---

## A. Architecture Hook → Body → CTA

C'est la structure universelle, à appliquer à TOUTES les durées.

```
HOOK (0–3s)            ─── 1–2 phrases courtes, accroche immédiate
   ↓
BODY (selon durée)     ─── reformulation pain + preuve/mécanisme + bénéfice
   ↓
CTA                    ─── 1 action + 1 bénéfice + 1 raison maintenant
```

---

## B. Architecture par durée

> **⚠️ RÈGLE DURÉE MINIMUM** : aucune variante en dessous de **30 secondes**. Pas de format 15s livré, même en retargeting. Le 30s est le plancher pour ton offre — il faut le temps de poser un pain + un mécanisme + une preuve. Le 15s est un format historique non utilisé sur ce skill.

### Format 30 secondes (~70–90 mots) — PLANCHER MINIMUM

Structure : **Hook + Pain + Mécanisme + Preuve + CTA**.

```
Hook (3s, 1 phrase)
Pain reformulé (5s, 1–2 phrases) — verbatim de l'avatar idéalement
Mécanisme nommé (10s, 2 phrases) — nom propre + ce qu'il fait de différent
Preuve courte (8s, 1 phrase) — chiffre + nom client si possible
CTA (4s, 1 phrase) — action + raison
```

**Quand utiliser** : format polyvalent, le plus testé en cold acquisition.

---

### Format 60 secondes (~150–180 mots)

Structure : **Hook + Pain + Common Enemy + Mécanisme + Preuve + Bénéfice + Objection + CTA**.

```
Hook (3s)
Pain (8s) — verbatim ou pain-stat
Common enemy / real problem (8s) — reframer pourquoi les solutions courantes échouent
Mécanisme nommé (12s) — nom + 2 raisons pourquoi ça marche
Preuve (10s) — 1–2 résultats chiffrés avec nom
Bénéfice émotionnel (10s) — what's in it for them, ressenti
Objection levée + safety net (5s) — garantie nommée
CTA (4s)
```

**Quand utiliser** : prospects froids, marché sophistiqué, offre haut de gamme. Le format qui convertit le mieux pour ton offre.

---

## C. Copywriting rules (apply to every variant)

### Mobile-first oral
- Phrases courtes (≤15 mots idéalement, ≤20 max)
- 1 idée par phrase
- Vocabulaire parlé (pas de tournures littéraires)
- Pas de subordonnées en cascade
- Lis à voix haute en 1 souffle, sinon coupe

### Voix
- **"Tu"** par défaut (proximité, coaching, agencies, B2C)
- **"Vous"** si B2B premium, consulting, SaaS enterprise (cf. `structure_copy.json`)
- Cohérent dans toute la variante (jamais de switch tu→vous)

### Rythme oral (Sugarman's slippery slide)
- Chaque phrase doit donner envie d'entendre la suivante
- Pas de paragraphe > 3 phrases
- Alterner phrases courtes et très courtes
- Cliffhangers tolérés mais pas systématiques

### Specificity
- Chiffres précis > arrondis ("3 247€" > "environ 3000€")
- Noms réels (avec accord du client) > "un de nos clients"
- Délais précis ("en 17 jours") > vagues ("rapidement")
- Lieux précis pour le local

### No-go words (red flags)
- ❌ "Incroyable", "révolutionnaire", "unique au monde" — sauf si proof immédiat
- ❌ "Probablement", "peut-être", "dans certains cas"
- ❌ "Beaucoup de gens", "la plupart des gens"
- ❌ "Cliquez ici", "n'hésitez pas"
- ❌ Jargon métier non expliqué dans les 5 premières secondes

---

## D. Format de sortie pour le copywriting (LIVRABLE)

C'est le **format obligatoire** des variantes dans le fichier final. Rappel : **pas de VO/Onscreen, pas de tableaux de timestamps, pas de storyboards**.

```markdown
### Variante {N} — {Angle name} ({durée})

**Hook**
{Texte exact prononcé. 1 ou 2 phrases courtes.}

**Body**
{Texte exact prononcé. Plusieurs phrases courtes, séparées par des sauts de ligne pour le rythme oral si nécessaire. 1 idée par phrase.}

**CTA**
{Texte exact. 1 action + 1 raison maintenant.}

*Indication scénique (optionnel) : {uniquement si critique pour le sens — ex: "regard caméra direct sur le mot 'maintenant'", "montrer screenshot du résultat ici"}*

---

**Copies Meta associées**
- **Primary text — court (≤125c)** : {hook + bénéfice + CTA}
- **Primary text — moyen (125–200c)** : {callout + preuve + CTA}
- **Primary text — long (200–280c)** : {angle complet + CTA + raison}
- **Headline (≤40c)** : {résultat en délai sans sacrifice}
- **Description (≤30c)** : {urgence ou rareté}
```

**Règles de format** :
- **Pas plus de 3 indications scéniques** sur l'ensemble du pack (on est en mode copy, pas storyboard)
- **Italique** pour les indications scéniques uniquement
- **Gras** pour les labels (Hook, Body, CTA, Primary text…)
- **Sauts de ligne** dans le Body pour respecter le rythme oral

---

## E. Sector-specific tone (rappel `structure_copy.json`)

### SaaS B2B
- Ton **pragmatique, ROI-driven, crédible**
- Hook chiffré orienté gain de temps ou revenus
- Body : pas de jargon technique, axé bénéfice métier
- CTA : essai gratuit, démo, pas d'engagement long

### Marketing Agency
- Ton **professionnel + empathique**
- Hook qui pointe la frustration du dirigeant (budget pub qui brûle, leads en chute…)
- Body : avant/après client + ce qui rend votre méthode différente
- CTA : audit gratuit, consultation stratégique offerte

### Coaching Business
- Ton **émotionnel + identification personnelle**
- Hook qui reflète une douleur intime (burn-out, doute, stagnation…)
- Body : transformation, story, before-after-bridge
- CTA : masterclass offerte, session découverte, appel diagnostic

### Consulting
- Ton **autoritaire + factuel**
- Hook chiffré ou data-driven
- Body : expertise visible, méthode propriétaire, cas client B2B notable
- CTA : entretien exploratoire, livre blanc, diagnostic sur mesure

---

## F. Congruence rule (ad ⇄ LP)

La pub n'est qu'une moitié du système. La landing page doit reprendre **exactement** :
- Le **même hook** (verbatim si possible)
- Le **même visuel** dominant
- La **même promesse** (mots identiques)
- Le **même CTA**
- Le **même mécanisme nommé**

> Le viewer doit avoir l'impression que la LP est **la suite directe** de la pub. PS sur la LP : "Puisque tu viens de cliquer sur [hook spécifique], voici la prochaine étape : …"

Si le client n'a pas encore de LP congruente → le mentionner en note finale comme priorité numéro 1.

---

## G. Output of this phase

À la fin de la Phase 4, le skill doit avoir produit :

- ✅ 3+ variantes par durée demandée
- ✅ Chaque variante au format markdown copy-only (pas VO/Onscreen)
- ✅ Chaque variante avec son pack copies texte (3 primary text + headline + description)
- ✅ Chaque variante respecte la structure Hook + Body + CTA
- ✅ Tone aligné avec le secteur du client
- ✅ Mécanisme nommé répété 1× (30s) / 2–3× (60s+)
- ✅ Indications scéniques minimales (≤3 pour tout le pack)
