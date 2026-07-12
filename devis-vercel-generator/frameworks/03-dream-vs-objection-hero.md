# Framework 03 — Dream-vs-Objection hero

Le H1 du hero est **le seul moment** où le devis parle à l'ego du prospect : il doit faire lever les yeux, donner envie de scroller, et éteindre les objections des 30 secondes suivantes. Si le H1 rate, tout rate.

Source : `brief.json` → `dream_state.headline_hook` (injecté dans `{{HERO_H1_HTML}}`).

---

## Règle de rythme : X. Y. Sans Z.

3 segments, séparés par des points. **Max 12 mots au total**.

- **X.** = l'anti-pain (ce que le prospect n'aura plus)
- **Y.** = la vraie promesse, le dream (accent `<em>` bleu italique)
- **Sans Z.** = la peur qu'on désamorce d'entrée (l'objection frontale dans la tête du prospect)

### Exemples conformes

| Exemple (Acme menuiserie) | Segments |
|---|---|
| Moins de RDV. *Mieux qualifiés.* Sans diluer vos 40 ans d'image premium. | X = Moins de RDV / Y = Mieux qualifiés / Z = diluer vos 40 ans d'image premium |
| Moins de patients. *Plus sélectionnés.* Sans perdre vos consultations rentables. | santé privée |
| Moins de leads. *Mieux qualifiés.* Sans brader votre expertise. | coaching premium |
| Moins de démos. *Plus d'achats.* Sans dégrader votre ARR cible. | B2B SaaS |
| Moins de mandats. *Plus rentables.* Sans sacrifier votre pipeline. | immobilier |

### Exemples non-conformes (ne pas produire)

- *"Obtenez plus de leads qualifiés grâce à notre méthode éprouvée en marketing digital."* — 13 mots, ton IA, pas de rythme, pas d'objection désamorcée.
- *"Boostez votre chiffre d'affaires avec the platform !"* — pub generic, pas de dream verbatim.
- *"On va vous trouver plein de clients."* — pas d'accent sur un dream, pas de Sans Z.

---

## Règle typographique : italique bleu sur le "dream"

Le **2e segment** (le Y, le dream) est entouré de `<em>…</em>` dans le HTML. Le CSS rend automatiquement :
- `color: var(--blue)` (`#3B82F6`)
- `font-style: italic`
- `font-weight: 700`

Le 1er et 3e segment restent en noir `#000` droit, weight 700.

### Exemple de HTML produit

```html
<h1>Moins de RDV. <em>Mieux qualifiés.</em><br>Sans diluer vos 40 ans d'image premium.</h1>
```

- `<br>` entre le 2e et le 3e segment **seulement** si la ligne 3 est longue (+7 mots).
- Sinon, tout sur une seule ligne fluide.

---

## Source du dream : verbatim du call

Le brief `sales-call-analyzer` extrait le dream state via `frameworks/01-dream-vs-objection-framework.md`. Le `headline_hook` du brief est déjà formaté selon la règle X. Y. Sans Z. — le skill devis ne fait que l'injecter tel quel.

Si le brief ne contient pas de `headline_hook` ou s'il est > 12 mots → **stop**, demander à l'utilisateur de régénérer le brief.

**Ne jamais** ré-écrire le `headline_hook` dans ce skill. Le seul rôle du skill devis est l'injection + la vérification du rythme.

---

## Subtitle — règle des 3 "Fini les"

Juste sous le H1, le subtitle contient **exactement 3 bullets** commençant par "Fini les" et enchaînant un verbatim d'objection du prospect :

```
Fini les prospects qui "comparent 3 devis".
Fini les RDV à 55 km qui n'ont pas le budget.
Fini les promos low-cost qui salissent votre marque.
```

Chaque bullet = `brief.json / objections.headline_subtitle_bullets[0..2]` → injecté dans `{{FINI_LES_1}}`, `{{FINI_LES_2}}`, `{{FINI_LES_3}}`.

### Règles de forme

- **Toujours 3** (pas 2, pas 4).
- **"Fini les"** au début de chaque — jamais "Fini le" ni "Adieu les" ni "Plus de…".
- **Verbatim du call** : si le prospect a dit "ça bloquait souvent au niveau du prix" → écrire `prospects qui "comparent 3 devis"` (le sous-texte). Si possible, conserver des guillemets autour d'une phrase exacte du prospect pour authenticité.
- Une **douleur concrète**, pas abstraite : "RDV à 55 km sans budget" ✅ vs "prospects peu qualifiés" ❌.
- Pas de majuscule sur le 1er mot après "Fini les" (sauf nom propre).

### Wrapper fixe

Le template utilise ce wrapper exact :
> Fini les `{{FINI_LES_1}}`. Fini les `{{FINI_LES_2}}`. Fini les `{{FINI_LES_3}}`. the platform filtre 5 à 10 fois vos leads Meta avant qu'ils n'atteignent l'agenda de votre commercial.

La dernière phrase ("the platform filtre…") est **immuable** — elle résume la ta promesse et clôt le hero en redirigeant sur l'agence.

---

## Quality check pour le H1 (avant deploy)

- [ ] ≤ 12 mots au total
- [ ] 3 segments séparés par des points
- [ ] Le 2e segment est enveloppé dans `<em>…</em>`
- [ ] Le 3e segment commence par "Sans"
- [ ] Le mot clé du 2e segment reprend un terme du verbatim du call (pas un mot inventé)
- [ ] Pas d'adjectif générique ("innovant", "performant", "automatisé", "efficace") — interdit dans un dream hero
- [ ] Pas d'émoji dans le H1

Si un critère n'est pas coché → régénérer le brief avec le sibling skill avant de relancer le skill devis.
