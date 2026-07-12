# Framework 01 — Immuable vs Variable

Tout ce qui se trouve dans `templates/template.html` tombe dans une des 2 catégories. **La règle** : n'adapter que les zones marquées VARIABLE. Ne jamais toucher une zone IMMUABLE même si le prospect est dans un secteur inhabituel.

---

## IMMUABLE — jamais toucher

### Identité émetteur (mention légale)

**Bloc Émetteur** (section PARTIES) :
```
[Your Company LLC]
the operator, CEO
you@example.com
```

Ces 3 lignes sont **verrouillées**. [Your Company LLC] est la raison sociale de votre agence. L'email contact est `you@example.com`. Jamais remplacer par "the platform" ou "the platform.my" ou une autre adresse.

### Chiffres de preuve the platform (section PREUVE)

Les 4 stat cards contiennent **ces valeurs exactes** :

| Valeur | Libellé | ❌ À ne jamais modifier |
|---|---|---|
| `[X]` | RDV qualifiés générés | Jamais 5400, jamais 6000 |
| `5 M€` | CA ajouté à nos clients | Jamais 4,5M€ ni 6M€ |
| `130` | Clients accompagnés | Jamais 120, jamais 150 |
| `[X]/5` | Note Google | **Jamais afficher un nombre d'avis** (pas de "[X]/5 sur 87 avis" — juste "[X]/5 Note Google") |

Le sous-titre de la section (verbatim) :
> [X] clients accompagnés. [X] rendez-vous qualifiés générés. [X]€ ajoutés aux chiffres d'affaires de vos clients. Notés [X]/5 sur Google.

### Bloc "Marché vs notre offre"

Bloc pill jaune sous la table devis, **verbatim** :
- "Nos concurrents facturent en moyenne **1 690 €/mois avec 3 mois d'engagement** pour la même prestation Meta Ads."
- "Vous, vous testez 1 mois à **790 €**, sans engagement."
- "Économie 1er mois : **−900 €**"

Ne **jamais** personnaliser ces chiffres, même si la vraie économie calculée est différente. C'est un argument de vente figé, pas un calcul sur-mesure.

### Prix test the platform

- Prix test 1er mois = **790 €** par défaut
- Surcharger **uniquement** si `pricing.lf_fee_eur` dans le brief est différent de 790 (rare — négociations exceptionnelles).
- Le prix affiché dans le hero price-tag, dans la table TOTAL, dans le hero CTA, dans le CTA final, dans les conditions générales, et dans le PDF → **tous doivent être cohérents**. Le script `generate.mjs` utilise le même `{{LF_FEE}}` partout.

### Chiffres ROI "défaut"

Le calculateur ROI affiche trois "défauts" qui ne sont **jamais** pilotés par le brief :
- CPL = **20 €**
- Conv lead → RDV = **50 %**
- Conv RDV → {deal} = **20 %**

Seul le **panier moyen** et le **budget Meta** peuvent partir d'un défaut issu du brief (via `roi_calc_defaults.avg_basket_eur`). Les 3 autres sont des moyennes agence, volontairement constantes.

### Structure & ordre des 12 sections

L'ordre est **figé** : NAV → HERO → PARTIES → CE QUE VOUS OBTENEZ → PREUVE → SIMULATEUR ROI → DÉTAIL DU DEVIS → MARCHÉ VS OFFRE → 4 ÉTAPES → CONDITIONS → CTA FINAL → FOOTER.

Ne pas réorganiser, ne pas supprimer une section (même si le brief ne contient pas toutes les infos — utiliser les fallbacks).

### Les 2 nouvelles lignes de la table devis (AJOUT OBLIGATOIRE)

Toujours présentes, toujours ces libellés exacts, toujours "Inclus" :

1. **Plateforme & CRM** — *Plateforme et CRM de gestion des prospects et d'analyse des campagnes inclus, avec suivi des conversions*
2. **Formation setting & closing** — *Formation offerte setting & closing : 4h de modules vidéo spécifiques*

### Footer

```
the platform  ·  Leads qualifiés en automatique.  ·  Devis {{DEVIS_REF}}
```

**Jamais** "[Your Company]" dans le footer. [Your Company] apparaît uniquement dans le bloc Émetteur (obligation légale).

### Design system (couleurs / bordures / typos)

Tout ce qui est détaillé dans `brand-identity.md` est IMMUABLE :
- Background `#FFFDF5`, jamais blanc pur
- Bordures noires 3px, ombres dures
- Space Grotesk (titres) + Inter Tight (body)
- Radius pill 9999px / cards 16px / sections 0

---

## VARIABLE — à personnaliser depuis `brief.json`

### Tout ce qui est prospect-spécifique

- Nom, société, rôle, adresse, téléphone, email du destinataire
- Date d'émission + date de validité (J+7)
- Référence devis `LF-YYYYMMDD-seq`
- Le slug dans l'URL Vercel : `devis-{client-slug}.vercel.app`

### Copie hero

- H1 (`headline_hook` du brief) — rythme "X. Y. Sans Z." obligatoire, voir framework 03
- Les 3 "Fini les…" (verbatim des objections du call)
- Subtitle wrapper autour des 3 bullets (défaut : `Fini les X. Fini les Y. Fini les Z. the platform filtre 5 à 10 fois vos leads Meta avant qu'ils n'atteignent l'agenda de votre commercial.`)

### Vocabulaire industrie (`meta.industry_vocab`)

- `deal_word` : chantier / client / patient / deal / commande / mandat — voir framework 02
- `customer_word` : propriétaire / client / coaché / patient / vendeur
- `meeting_word` : RDV téléphonique / démo call / consultation / call découverte

Injecté partout où la page web parle de "RDV", "clients signés", "chantier" etc.

### Géographie

- `{{CLIENT_CITY}}` : ville du prospect (apparaît dans les cards, table, timeline)
- `{{GEO_RADIUS_KM}}` : rayon de ciblage Meta (55-80 km selon le brief)
- `{{GEO_ZONE}}` : label de la région (Île-de-France, PACA, Grand Est…) — fallback "votre région"

### Lien de paiement Stripe

`pricing.stripe_link` — critique : doit être présent dans la page ET dans le PDF (pour que le client puisse cliquer depuis le PDF téléchargé).

### Contexte secteur dans les cards & table

- Description Setup ("Audit secteur BTP" vs "Audit secteur coaching" vs "Audit secteur dentaire…")
- Contexte créatives (age de l'entreprise, positionnement premium/accessible…)
- Filtres pré-qualification (budget + projet + urgence + zone pour BTP ; budget + niveau + timeline + objectif pour coaching…)

### Panier moyen ROI

Le `input[value]` du champ `roi-panier` est initialisé depuis `roi_calc_defaults.avg_basket_eur`. L'utilisateur peut ensuite l'éditer dans la calculette. Voir framework 02 pour les plages typiques par industrie.

---

## Règle d'arbitrage

Si tu hésites entre "immuable" et "variable" pour un détail non listé ici → **défaut = immuable**. Ne pas inventer de variations, garder la page cohérente avec la version de référence `devis-{client-slug}.vercel.app`.

Les seuls éléments qui bougent sans ambiguïté entre deux clients sont ceux listés en **VARIABLE** ci-dessus.
