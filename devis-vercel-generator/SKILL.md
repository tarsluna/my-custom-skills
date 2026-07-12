---
name: devis-vercel-generator
description: Génère la page devis personnalisée (HTML + vraie génération PDF via html2pdf.js) à partir du brief produit par `sales-call-analyzer` et la déploie sur Vercel sous le pattern `devis-{client-slug}.vercel.app`. Le template (néo-brutal crème + bleu + ombres dures, Space Grotesk + Inter Tight) est une copie de `projects/devis-template/index.html` — 12 sections figées (NAV, HERO, PARTIES, CE QUE VOUS OBTENEZ, PREUVE, SIMULATEUR ROI, DÉTAIL DU DEVIS, MARCHÉ, 4 ÉTAPES, CONDITIONS, CTA FINAL, FOOTER). Les chiffres sont FIXES ([X] RDV / [X]€ CA / [X] clients / [X]/5 Google — remplace par tes vrais chiffres). Le vocabulaire industrie (chantier / patient / deal / client) est adapté via `industry_vocab.deal_word` du brief. La section DÉTAIL ajoute deux nouvelles lignes obligatoires : "Plateforme & CRM" et "Formation setting & closing". Le bouton "Télécharger PDF" produit un VRAI PDF via html2pdf.js (pas `window.print()`). Use when the user asks "génère le devis", "crée la page devis Vercel", "deploy devis {client}", "a client proposal page", "page de proposition commerciale {client}". Trigger phrases: "génère le devis", "devis Vercel", "deploy devis", "a client proposal page", "page de proposition commerciale", "devis-{slug}-lf".
---

# Devis Vercel Generator

Skill qui transforme un brief commercial (`brief-output.json` produit par `sales-call-analyzer`) en **page devis Vercel déployée**, fidèle au template `projects/devis-template/index.html`, avec génération d'un **vrai PDF** téléchargeable (pas `window.print()`).

Sortie finale : une URL publique `https://devis-{client-slug}.vercel.app` que the operator envoie au prospect.

---

## Quand utiliser ce skill

Trigger sur :
- "Génère le devis pour {client}"
- "Crée la page devis Vercel {client}"
- "Deploy devis {client}"
- "a client proposal page {client}"
- "Page de proposition commerciale {client}"

Ne pas trigger pour :
- Analyser une transcription d'appel → `sales-call-analyzer`
- Créer la proposition de campagne Meta (post-onboarding) → un document de proposition de campagne
- Écrire les ads → `meta-ads-copywriter`

---

## Inputs requis

Un seul fichier : `projects/{client_slug}/00-sales-brief/brief-output.json` (schéma défini par le skill `sales-call-analyzer`).

Champs critiques consommés :

| Champ brief.json | Usage dans le devis |
|---|---|
| `meta.prospect_full_name` | Destinataire bloc + filename PDF |
| `meta.company_legal_name` | Destinataire bloc |
| `meta.role_title` | Destinataire bloc |
| `meta.devis_ref` (sinon auto `LF-{YYYYMMDD}-{seq}`) | NAV + footer + PDF header |
| `meta.decision_deadline_iso` | Validité hero + conditions + footer |
| `meta.industry_vocab.deal_word` | ROI calc + conditions + CTA ("chantier" / "client" / "patient" / "deal") |
| `meta.industry_vocab.customer_word` | ROI calc ("propriétaire" / "contact" / "patient") |
| `meta.industry_vocab.meeting_word` | Cards + timeline ("RDV téléphonique" / "démo call" / "consultation") |
| `contact.email` / `contact.phone` | Destinataire bloc |
| `contact.address_line` / `postal_code` / `city` | Destinataire bloc |
| `business.founded_year` | Hero H1 reference (X ans d'image premium) |
| `business.geo_radius_km` | Ciblage Meta card + table + timeline |
| `business.city` | Ciblage Meta card + table + timeline |
| `dream_state.headline_hook` | HERO H1 (rythme X. Y. Sans Z.) |
| `objections.headline_subtitle_bullets` | HERO subtitle (3 x "Fini les") |
| `roi_calc_defaults.avg_basket_eur` | Input panier par défaut ROI |
| `pricing.lf_fee_eur` (défaut 790) | Total devis + CTA + Stripe label |
| `pricing.stripe_link` | CTA hero + CTA finale + footer PDF |

Si le brief est incomplet, tu t'arrêtes et tu demandes à l'utilisateur de relancer `sales-call-analyzer`.

---

## Pipeline (5 phases)

### Phase 1 — Lecture du brief
- Charger `brief-output.json` depuis `projects/{client_slug}/00-sales-brief/`.
- Vérifier la présence des champs critiques (liste ci-dessus).
- Si un champ manque → stop + message à l'utilisateur.

### Phase 2 — Remplissage du template
- Charger `templates/template.html`.
- Faire le remplacement mustache `{{token}}` selon `templates/placeholders-map.md`.
- Calculer la ref devis `LF-{YYYYMMDD}-{seq}` si absente du brief (seq = nombre de sous-dossiers `07-devis-page` existants + 1, fallback `001`).
- Adapter le vocabulaire industrie partout où le mot "chantier"/"client"/"RDV" apparaît dans les zones variables (ROI calc hints, conditions, CTA final, card 3 bullets). Voir `frameworks/02-industry-vocab-mapping.md`.
- Vérifier que les valeurs verrouillées ([X] / [X]€ / [X] / [X]/5) n'ont pas bougé. Voir `frameworks/01-immutable-vs-variable.md`.

### Phase 3 — Injection du bloc PDF caché
- Le template contient déjà un `<div id="pdf-devis">` caché (structure détaillée dans `templates/pdf-devis-structure.md`).
- Remplir ce bloc avec les mêmes variables que la page + le lien Stripe en clair pour qu'il soit cliquable depuis le PDF.
- Le script du bouton "Télécharger PDF" appelle `html2pdf.js` sur ce `<div>`, filename `Devis-{ClientName}-{YYYYMMDD}.pdf`.
- Aucun `window.print()` dans la page finale.

### Phase 4 — Preview local
- Écrire `index.html` + `vercel.json` dans `projects/{client_slug}/07-devis-page/`.
- Démarrer `python3 -m http.server 8791` dans ce dossier (en background) pour QA visuelle.
- QA checklist (voir Quality Gates ci-dessous).

### Phase 5 — Déploiement Vercel
- `cd projects/{client_slug}/07-devis-page/`
- `vercel --prod --yes --name devis-{client-slug}` (via `scripts/deploy.sh`).
- Extraire l'URL alias finale et la retourner à l'utilisateur.

---

## Design rules (non-négociables)

### Les 12 sections — ordre figé

1. **NAV** — ton logo (cercle bleu + éclair SVG inliné) + référence devis `LF-YYYYMMDD-seq`.
2. **HERO** — badge pink "Offre test 1er mois — Sans engagement", H1 dream-vs-objection (italique bleu sur le mot clé), subtitle avec 3 bullets "Fini les…", price tag `{{lf_fee}}` €, CTA Stripe, bouton Télécharger PDF, note de validité.
3. **LES PARTIES** — 2 meta blocks :
   - Émetteur : **[Your Company LLC], [Your Name], CEO, you@example.com** — VALEURS FIXES, ne jamais remplacer.
   - Destinataire : champs prospect depuis `brief.json`.
4. **CE QUE VOUS OBTENEZ** — 6 cartes (ORDRE FIXE) :
   1. Campagnes Meta Ads (adapter géo et ICP bullet 2 : radius_km + city + customer_word).
   2. Pré-qualification des leads (garder les 4 bullets, adapter "budget/type de projet" si secteur non-BTP).
   3. RDV bookés automatiquement (adapter vocab : `meeting_word` = "RDV téléphonique" / "démo call" / "consultation").
   4. Équipe humaine dédiée (toujours : Account Manager + Media Buyer senior + Designer + Copywriter + Call hebdo).
   5. **Plateforme & CRM inclus** — LOCKED. 4 bullets fixes : accès plateforme de gestion & tracking / CRM dédié pour les prospects / analyse campagnes et suivi conversions / historique complet `{{DEAL_WORD_PLURAL}}` → signatures.
   6. **Formation sales offerte** — LOCKED. 4 bullets fixes : 4h modules vidéo spécifiques / Setting (leads → RDV) / Closing (signer `{{DEAL_WORD_PLURAL}}` au prix premium) / Valeur 990 € offert avec l'offre test.
5. **PREUVE / CHIFFRES CLÉS** — 4 stat cards avec ces **chiffres verrouillés** :
   - [X] RDV qualifiés générés
   - [X]€ CA ajouté à vos clients
   - [X] Clients accompagnés
   - [X]/5 Note Google (JAMAIS afficher de nombre d'avis — jamais le mot "avis")
6. **SIMULATEUR ROI** — calculateur interactif :
   - Panier moyen : défaut `roi_calc_defaults.avg_basket_eur` du brief (5000 € BTP, 300 € coaching, etc.)
   - Budget Meta : défaut 500 €
   - CPL : défaut **toujours 20 €**, éditable
   - Slider conv lead→RDV : défaut **toujours 50 %**, range 10-100 step 5
   - Slider conv RDV→{deal_word} : défaut **toujours 20 %**, range 5-80 step 5
   - Ordre d'affichage : Investissement total → Retour sur investissement → **CA estimé généré** (pill jaune, font 2.8rem — c'est la ligne hero du résultat)
   - Constante `LF_FEE = {{lf_fee}}` (790 par défaut)
7. **DÉTAIL DU DEVIS** — table avec 10 lignes (les 8 originales + les 2 nouvelles) :
   1. Équipe dédiée (humaine)
   2. Setup & Stratégie
   3. Créatives (10 statiques + 1-2 vidéos IA)
   4. Meta Ads (1 mois)
   5. Formulaire de pré-qualification
   6. Prise de RDV automatisée
   7. Call hebdomadaire (humain)
   8. Call bilan & décision
   9. **Plateforme & CRM** — *Plateforme et CRM de gestion des prospects et d'analyse des campagnes inclus, avec suivi des conversions* (AJOUT obligatoire)
   10. **Formation setting & closing** — *Formation offerte setting & closing : 4h de modules vidéo spécifiques* (AJOUT obligatoire)
   - Row TOTAL : `{{lf_fee}} €` TTC (= 790 par défaut, ne bouge que si `pricing.lf_fee_eur` diffère).
8. **MARCHÉ VS NOTRE OFFRE** — bloc pill jaune verbatim : concurrents 1 690 €/mois + 3 mois d'engagement vs vous 790 € sans engagement → Économie 1er mois −900 €. **Ne pas personnaliser.**
9. **4 ÉTAPES** — timeline (adapter géo en étape 1 + `deal_word` en étape 4).
10. **CONDITIONS** — 7-8 items en checklist. Adapter la ligne géo + `meeting_word` sur le bullet objectif.
11. **CTA FINAL** — "Prêt à recevoir vos premiers {meeting_word_plural} qualifiés en 10 jours ?". H2 italique jaune sur les mots clés.
12. **FOOTER** — ton logo + tagline "Leads qualifiés en automatique." + ref devis. **JAMAIS "[Your Company]" dans le footer** (seulement dans Émetteur pour la mention légale).

### Palette + typos

- Fond : `#FFFDF5` crème (jamais `#FFFFFF`).
- Primaire : `#3B82F6` bleu.
- Bordures : 3px noir, ombres dures `6-8px 6-8px 0 #000`.
- Radius : pill 9999px (boutons/badges), 16px (cards), 0 (sections).
- Titres : Space Grotesk 700, `letter-spacing: -0.02em`.
- Body : Inter Tight 400-500.
- Accents pop : pink `#FFC4EB`, jaune `#FDE047`, vert `#58BC82`.
- Emojis autorisés : badges, card icons, CTAs. **Jamais dans les headlines H1/H2.**

---

## Vraie génération PDF (NOUVEAU — html2pdf.js)

Le bouton "Télécharger PDF" **ne doit pas** appeler `window.print()`. Il doit produire un vrai document PDF téléchargeable.

### Implémentation

Dans `<head>` :
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
```

Un `<div id="pdf-devis">` qui contient le devis formaté pour A4. Spec complète dans `frameworks/04-pdf-devis-spec.md`.

⚠️ **NE JAMAIS** cacher `#pdf-devis` via `display:none`, `visibility:hidden` ou `position:absolute; left:-10000px;` → bug PDF blanc reproductible (incident PDF blanc 2026-04-30). html2canvas ne capture pas les éléments hors viewport ou non rendus.

**Pattern correct** : laisser l'élément dans le render tree mais invisible utilisateur via `opacity:0 + z-index:-1 + pointer-events:none`, puis remettre `opacity:1` **uniquement dans le clone html2canvas** via la callback `onclone` (le clone vit dans une iframe — rien ne flashe à l'écran).

Le bouton :
```html
<button class="btn btn-secondary" id="btn-download-pdf">⬇ Télécharger PDF</button>
```

Script (version complète et obligatoire — le quality gate `pdf_uses_onclone_pattern` vérifie sa présence) :
```js
async function downloadPDF(button) {
  const el = document.getElementById('pdf-devis');
  if (!el) return;

  const restoreLabel = button ? button.textContent : null;
  if (button) {
    button.disabled = true;
    button.textContent = 'Génération du PDF…';
  }

  try {
    if (document.fonts && document.fonts.ready) {
      await document.fonts.ready;            // garantit Space Grotesk chargée
    }
    const opt = {
      margin: [10, 10, 10, 10],
      filename: 'Devis-{{ClientName}}-{{YYYYMMDD}}.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: {
        scale: 2,
        useCORS: true,
        backgroundColor: '#FFFDF5',
        windowWidth: 900,
        scrollX: 0,
        scrollY: 0,
        onclone: (clonedDoc) => {            // FIX bug PDF blanc — obligatoire
          const clone = clonedDoc.getElementById('pdf-devis');
          if (clone) {
            clone.style.position = 'static';
            clone.style.opacity = '1';
            clone.style.zIndex = 'auto';
            clone.style.pointerEvents = 'auto';
            clone.style.left = 'auto';
            clone.style.top = 'auto';
          }
        },
      },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
      pagebreak: { mode: ['css', 'legacy'] },
    };
    await html2pdf().set(opt).from(el).save();
  } catch (err) {
    console.error('[devis] PDF generation failed:', err);
    alert("Le téléchargement du PDF a échoué. Réessayez ou contactez you@example.com.");
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = restoreLabel || '⬇ Télécharger PDF';
    }
  }
}
document.getElementById('btn-download-pdf')
  .addEventListener('click', (e) => downloadPDF(e.currentTarget));
```

Contenu du PDF (ordre) :
1. Header : ton logo (inline SVG) + "DEVIS N° LF-{YYYYMMDD}-{seq}" + date d'émission.
2. Les parties (Émetteur + Destinataire côte à côte).
3. Détail du devis (table complète 10 lignes + TOTAL).
4. Conditions générales (liste numérotée 8 items).
5. Footer : `Paiement sécurisé via Stripe : {{stripe_link}}` (vrai lien cliquable) + "Devis valable 7 jours".

Spec complète : `frameworks/04-pdf-devis-spec.md`.

---

## Industry-vocab adaptation — règles rapides

Tous ces mots sont pilotés par `meta.industry_vocab` du brief (défaut entre parenthèses si absent) :

| `deal_word` | `customer_word` | `meeting_word` | Panier typique |
|---|---|---|---|
| chantier (BTP) | propriétaire | RDV téléphonique | 5 000 € |
| client (coaching) | coaché | call découverte | 300-2000 € |
| deal (B2B SaaS) | contact | démo call | 50 000 € |
| patient (santé) | patient | consultation | 150-500 € |
| commande (e-com) | client | appel conseil | 80-400 € |
| mandat (immo) | vendeur | RDV agence | 12 000 € |

Défaut si brief vide : `client` / `client` / `RDV téléphonique` / 2000 €.

Détail complet + endroits exacts dans le template : `frameworks/02-industry-vocab-mapping.md`.

---

## Quality Gates (bloquants avant deploy)

- [ ] Les 12 sections sont présentes dans l'ordre exact défini ci-dessus.
- [ ] Chiffres verrouillés [X] / 5 M€ / 130 / 4,8 **inchangés**.
- [ ] `[Your Company]` n'apparaît **que** dans le bloc Émetteur. Nulle part ailleurs.
- [ ] Le footer dit `the platform`, pas `[Your Company]`.
- [ ] La table devis contient **les 2 nouvelles lignes** : Plateforme & CRM + Formation setting & closing (10 lignes total + TOTAL).
- [ ] Le lien Stripe est inclus dans le BODY du PDF (pas seulement dans la page web).
- [ ] Le calculateur ROI utilise le `deal_word` industrie partout (ex : "chantiers signés" pour Acme, pas "clients").
- [ ] La date de validité dans hero + conditions + footer = `brief.meta.decision_deadline_iso`.
- [ ] **Aucun `window.print()`** dans le HTML final. PDF = vrai document via html2pdf.js.
- [ ] **PDF non blanc** — le HTML doit contenir simultanément `onclone:` dans la config html2canvas, `document.fonts.ready` dans le `downloadPDF`, et `#pdf-devis` doit être caché via `opacity: 0` (jamais via `display:none`, `visibility:hidden` ni `left:-10000px`). Tester réellement le download dans un navigateur avant de livrer l'URL — un PDF blanc = livrable cassé. Voir incident PDF blanc 2026-04-30 dans `frameworks/04-pdf-devis-spec.md`.
- [ ] URL déployée matche exactement `devis-{client-slug}.vercel.app`.
- [ ] Preview local (`python3 -m http.server 8791`) passe la QA visuelle.

Si un gate ne passe pas : corriger avant déploiement. Ne jamais livrer une URL partielle à l'utilisateur.

---

## Exemple de référence : Acme / Fermetures Acme

Le brief d'exemple `brief-output-example-filipe.json` (produit par `sales-call-analyzer`) → génère une page `devis-{client-slug}.vercel.app`.

Caractéristiques injectées :
- H1 : *Moins de RDV. Mieux qualifiés. Sans diluer vos 40 ans d'image premium.*
- 3 Fini les : prospects qui "comparent 3 devis" / RDV à 55 km qui n'ont pas le budget / promos low-cost qui salissent la marque.
- `deal_word` = chantier (pas "client").
- Panier ROI = 5000 €.
- Géo = 60 km autour de la ville du client.
- Stripe link = `https://buy.stripe.com/<your-payment-link>` (from `pricing.stripe_link`).

La page générée doit être pixel-identique à la page de référence `devis-{client-slug}.vercel.app`, plus les 2 nouvelles lignes de table et le nouveau PDF.

---

## Structure du skill

```
devis-vercel-generator/
├── SKILL.md                              ← ce fichier
├── templates/
│   ├── template.html                     ← template HTML source (avec {{tokens}} + bloc PDF caché)
│   ├── placeholders-map.md               ← chaque {{token}} → champ brief.json
│   └── pdf-devis-structure.md            ← structure du <div id="pdf-devis"> caché
├── scripts/
│   ├── generate.mjs                      ← Node ESM : brief.json + template → index.html + vercel.json
│   └── deploy.sh                         ← vercel --prod --yes → URL alias
└── frameworks/
    ├── 01-immutable-vs-variable.md       ← sections/strings figés vs variables
    ├── 02-industry-vocab-mapping.md      ← table industrie → deal_word / panier
    ├── 03-dream-vs-objection-hero.md     ← règles du H1 (12 mots, rythme, <em> bleu)
    └── 04-pdf-devis-spec.md              ← spec complète du PDF html2pdf.js
```

---

## Style éditorial du skill (voix the platform)

**À faire** : phrases courtes, tutoiement-vouvoiement business ("On vous génère"), promesses chiffrées, affirmations sans hedge, zéro jargon IA.

**À ne pas faire** : "Dans cette proposition…", "Il est important de noter que…", "Nous allons explorer…", émojis dans les H1/H2, blanc pur `#FFFFFF`, ombres soft floues, gradients multi-stops.
