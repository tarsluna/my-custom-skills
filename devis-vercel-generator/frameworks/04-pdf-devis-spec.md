# Framework 04 — Spec du PDF devis (html2pdf.js)

Le bouton "Télécharger PDF" produit un **vrai document PDF A4**, pas un `window.print()` du navigateur. C'est une exigence non-négociable (feedback utilisateur : `window.print()` imprime toute la page marketing, pas acceptable).

Implémentation : `html2pdf.js` (CDN) + un `<div id="pdf-devis">` caché dans la page HTML qui contient **uniquement** le devis formaté pour A4.

---

## Librairie & CDN

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
```

Inclusion dans le `<head>` du template. Pas de import ESM, pas de bundler — injection directe pour simplicité de deploy Vercel.

Alternative considérée (rejetée) : `jsPDF` + `autotable`. Raison du rejet : moins de contrôle sur le layout visuel (il faut tout coder cellule par cellule), et pas de fidélité HTML → PDF native.

---

## Configuration html2pdf.js

⚠️ **Bug historique (2026-04-30) — PDF blanc** : si `#pdf-devis` est caché via `position: absolute; left: -10000px;` ou `display: none;` ou `visibility: hidden;`, html2canvas ne le rasterise pas correctement et produit un PDF vide.

**Pattern obligatoire pour cacher l'élément** : `position: fixed; top: 0; left: 0; opacity: 0; pointer-events: none; z-index: -1;` — l'élément reste dans le render tree, mais invisible pour l'utilisateur. Puis on remet `opacity: 1` **uniquement dans le clone html2canvas** via la callback `onclone` (le clone vit dans une iframe isolée, donc rien ne flashe à l'écran).

Le bouton doit également afficher un état "Génération du PDF…" et disabled pendant la capture, et `await document.fonts.ready` avant de lancer `html2pdf()` pour garantir que Space Grotesk est chargée (sinon le PDF tombe sur la fallback sans-serif).

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
      await document.fonts.ready;
    }

    const opt = {
      margin: [10, 10, 10, 10],                       // mm — marges égales
      filename: 'Devis-{ClientNameSlug}-{YYYYMMDD}.pdf',
      image: { type: 'jpeg', quality: 0.98 },         // haute qualité
      html2canvas: {
        scale: 2,                                     // double DPI pour netteté
        useCORS: true,
        backgroundColor: '#FFFDF5',                   // cream — jamais blanc pur
        windowWidth: 900,
        scrollX: 0,
        scrollY: 0,
        // FIX bug PDF blanc : on rend visible le clone html2canvas (iframe interne).
        // Le DOM live reste invisible utilisateur grâce à opacity:0 + z-index:-1.
        onclone: (clonedDoc) => {
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
      pagebreak: { mode: ['css', 'legacy'] },         // respect css page-break-*
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

### CSS associé du `#pdf-devis`

```css
/* HIDDEN PDF DIV — rendu live mais invisible utilisateur. Ne JAMAIS utiliser
   display:none, visibility:hidden ni left:-10000px : html2canvas ne capture pas. */
#pdf-devis {
  position: fixed;
  top: 0;
  left: 0;
  width: 800px;
  background: #FFFDF5;
  color: #000;
  font-family: 'Inter Tight', system-ui, sans-serif;
  padding: 32px;
  opacity: 0;          /* invisible utilisateur */
  pointer-events: none;/* non cliquable */
  z-index: -1;         /* derrière le contenu */
}
```

### Filename pattern

`Devis-{ClientNameSlug}-{YYYYMMDD}.pdf`

- `ClientNameSlug` = `meta.company_legal_name` en kebab-case, caractères spéciaux retirés, espaces → tirets. Exemple : `Fermetures Acme` → `Fermetures-Acme`.
- `YYYYMMDD` = date de génération au format ISO sans tiret. Exemple : `20260421`.

Exemple final : `Devis-Fermetures-Acme-20260421.pdf`.

Le script `generate.mjs` remplace `{{CLIENT_NAME_SLUG}}` et `{{YYYYMMDD}}` dans le template HTML avant deploy, pour que le filename soit pré-rempli côté client (le JS lit des constantes déjà substituées au build).

---

## Contenu obligatoire du PDF (sections + ordre)

### 1. Header

- **Logo the platform** (SVG inline — le même que la nav) à gauche
- **DEVIS N° LF-YYYYMMDD-seq** + **Émis le DD/MM/YYYY** à droite
- Séparateur : bordure noire 3px en bas du header

### 2. Section 1 — Les parties

Deux blocs côte à côte (flex: 1 chacun, gap 16px) :

**Émetteur** (fond crème, label pill bleu)
```
[Your Company LLC]
the operator, CEO
you@example.com

Réf : LF-YYYYMMDD-seq
Date : DD/MM/YYYY
Validité : 7 jours
```

**Destinataire** (fond crème, label pill jaune)
```
{CLIENT_FULL_NAME}
{CLIENT_COMPANY} — {CLIENT_ROLE}
{CLIENT_ADDRESS_LINE}
{CLIENT_POSTAL_CODE} {CLIENT_CITY}
{CLIENT_PHONE}
{CLIENT_EMAIL}
```

Les champs vides (téléphone, adresse…) sont remplacés par `—` ou simplement omis (voir `placeholders-map.md`).

### 3. Section 2 — Détail du devis

Table complète **10 lignes** (toutes les prestations, ordre du template) + **1 ligne TOTAL** :

| # | Prestation | Description |
|---|---|---|
| 1 | Équipe dédiée (humaine) | Account Manager, Media Buyer senior, Designer, Copywriter, Monteur vidéo |
| 2 | Setup & Stratégie | `{{SETUP_DESCRIPTION}}` contextualisée industrie |
| 3 | Créatives (10 + 2) | 10 visuels statiques + 1 à 2 vidéos IA, angles adaptés à `{{CREATIVES_ANGLE_CONTEXT}}` |
| 4 | Meta Ads (1 mois) | Gestion complète Facebook & Instagram, ciblage `{{GEO_RADIUS_KM}}` km autour de `{{CLIENT_CITY}}` |
| 5 | Formulaire de pré-qualification | Instant Form Meta avec 5 à 10 filtres (`{{PREQUAL_FILTERS_SHORT}}`) |
| 6 | Prise de `{{MEETING_WORD_PLURAL_CAPS}}` automatisée | Redirection agenda + notifications au commercial en temps réel |
| 7 | Call hebdomadaire (humain) | 1 call/sem avec votre Account Manager + dashboard + rapport chaque lundi |
| 8 | Call bilan & décision | Call de fin de mois : résultats, ROI, leads, recommandations |
| 9 | **Plateforme & CRM** *(nouveau)* | Plateforme et CRM de gestion des prospects et d'analyse des campagnes inclus, avec suivi des conversions |
| 10 | **Formation setting & closing** *(nouveau)* | Formation offerte setting & closing : 4h de modules vidéo spécifiques |
| TOTAL | TOTAL TTC — Mois test (sans engagement) | `{{LF_FEE}} €` (790 par défaut) |

La colonne "Montant" affiche "Inclus" pour les 10 lignes et le total `790 €` en bleu + jaune sur la ligne TOTAL.

### 4. Section 3 — Conditions générales

Liste ordonnée de **8 items** (ol, pas ul — pour numérotation légale) :

1. Offre test d'un mois, sans engagement de renouvellement.
2. Budget publicitaire Meta à la charge du client (non inclus). Recommandation : 500 € minimum/mois.
3. Paiement à la commande via le lien Stripe fourni (sécurisé et immédiat).
4. Devis valable 7 jours à compter du `{{DATE_FR}}` (expire le `{{DEADLINE_FR}}`).
5. Démarrage des campagnes sous 48–72h après règlement et accès aux comptes publicitaires.
6. Reporting hebdomadaire envoyé chaque lundi par email.
7. Objectif : `{{MEETING_WORD_PLURAL}}` pré-qualifiés dans l'agenda du commercial, zéro déplacement inutile.
8. En cas de renouvellement, les tarifs sont redéfinis selon les résultats obtenus.

### 5. Footer PDF

Bordure noire 2px séparation + texte centré :

```
Paiement sécurisé via Stripe : {{STRIPE_LINK}}   ← lien cliquable (<a href>)
Devis valable 7 jours jusqu'au {{DEADLINE_FR}} — the platform · Leads qualifiés en automatique.
```

**Le lien Stripe doit être un vrai `<a href="{{STRIPE_LINK}}">{{STRIPE_LINK}}</a>`** — html2pdf.js préserve les liens cliquables dans le PDF final. Ne pas le transformer en texte inerte.

---

## Page break rules

Le PDF doit tenir en 1-2 pages A4. Règles CSS :

- `#pdf-devis { width: 800px; }` → ~21 cm à 96 DPI, match A4
- `table { page-break-inside: auto; }` — par défaut
- Chaque `<tr>` : `page-break-inside: avoid;` hérité (CSS standard table)
- `.pdf-total-row { page-break-before: avoid; }` — le total ne se détache pas de la dernière ligne
- `.pdf-page-break { page-break-before: always; }` — classe utilitaire utilisable si besoin de forcer une coupe

Avec 10 lignes + en-tête de table + parties + conditions, on est souvent sur 2 pages. C'est acceptable. Pas chercher à compresser en 1 page au détriment de la lisibilité.

---

## Ce qui est EXPLICITEMENT ABSENT du PDF

Le PDF **ne contient pas** :
- Le hero (H1 + badge + subtitle)
- Les 4 cards "Ce que vous obtenez" (marketing)
- La section "Chiffres the platform" (preuve sociale)
- Le calculateur ROI interactif
- Le bloc "Marché vs notre offre" (argument commercial)
- La timeline "4 étapes" (process)
- Le CTA final

Raison : le PDF est un document **légal et commercial** sobre. Le client le stocke dans ses archives, l'envoie à son comptable, l'imprime éventuellement. La page web = marketing + vente. Les 2 artefacts sont complémentaires, pas redondants.

---

## Quality gates PDF

Avant de livrer une URL :

- [ ] Le PDF se télécharge au clic sur le bouton (pas `window.print()`)
- [ ] Nom du fichier : `Devis-{ClientName}-{YYYYMMDD}.pdf`
- [ ] Le PDF contient les 5 sections dans l'ordre : header / parties / table / conditions / footer
- [ ] Le lien Stripe est cliquable dans le PDF (pas juste visible)
- [ ] Les 10 lignes de la table sont toutes présentes + la ligne TOTAL
- [ ] Les 2 nouvelles lignes (Plateforme & CRM + Formation setting & closing) sont présentes
- [ ] Les valeurs numériques (LF_FEE, dates) sont cohérentes avec la page web
- [ ] Background `#FFFDF5` (cream — pas blanc pur)
- [ ] Le PDF fait 1 ou 2 pages max (pas 4)
- [ ] Pas de coupure au milieu d'une ligne de la table
- [ ] Le ton logo est lisible en haut
- [ ] [Your Company] apparaît dans Émetteur, **jamais** dans le footer du PDF
