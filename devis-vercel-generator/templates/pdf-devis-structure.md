# Structure du bloc PDF caché

Le `<div id="pdf-devis">` est **dans la page HTML** mais rendu hors-écran (`position: absolute; left: -10000px`). Il est invisible à l'œil mais lisible par `html2pdf.js` qui le sérialise en PDF A4 au clic sur "Télécharger PDF".

Raison d'être : produire un **vrai document devis** (1-2 pages A4) sans les sections marketing (hero, stats, calculateur ROI, CTA final), juste les sections **légalement/commercialement nécessaires**.

---

## Layout complet

```
┌─────────────────────────────────────────────────────────┐
│ [Logo the platform]         DEVIS N° LF-20260421-002     │
│                            Émis le 21/04/2026            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 1. Les parties                                           │
│ ┌─────────────────┐  ┌─────────────────┐                │
│ │ Émetteur        │  │ Destinataire    │                │
│ │ [Your Company LLC]  │  │ [Client Name]│                │
│ │ the operator  │  │ Fermetures …    │                │
│ │ …              │  │ …               │                │
│ └─────────────────┘  └─────────────────┘                │
│                                                          │
│ 2. Détail du devis                                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Prestation        │ Description      │ Montant      │ │
│ ├───────────────────┼──────────────────┼──────────────┤ │
│ │ Équipe dédiée     │ …                │ Inclus       │ │
│ │ Setup & Stratégie │ …                │ Inclus       │ │
│ │ Créatives (10+2)  │ …                │ Inclus       │ │
│ │ Meta Ads (1 mois) │ …                │ Inclus       │ │
│ │ Pré-qualif        │ …                │ Inclus       │ │
│ │ Prise de RDV      │ …                │ Inclus       │ │
│ │ Call hebdo        │ …                │ Inclus       │ │
│ │ Call bilan        │ …                │ Inclus       │ │
│ │ Plateforme & CRM  │ …                │ Inclus       │ │  ← NOUVELLE LIGNE
│ │ Formation setting │ …                │ Inclus       │ │  ← NOUVELLE LIGNE
│ ├───────────────────┴──────────────────┴──────────────┤ │
│ │ TOTAL TTC                                  790 €    │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ 3. Conditions générales                                  │
│ 1. Offre test d'un mois, sans engagement…                │
│ 2. Budget Meta non inclus…                               │
│ … (8 items)                                              │
│                                                          │
├─────────────────────────────────────────────────────────┤
│ Paiement sécurisé via Stripe : https://buy.stripe…       │
│ Devis valable 7 jours jusqu'au 28/04/2026 —              │
│ the platform · Leads qualifiés en automatique.            │
└─────────────────────────────────────────────────────────┘
```

---

## CSS — résumé

- Taille : `width: 800px` (= ~A4 210mm à 96 DPI avec marges de 10mm)
- Background : `#FFFDF5` (crème — jamais blanc pur)
- Font : Inter Tight body, Space Grotesk titres
- Borders : 2px noir (plus fin que la page web pour ne pas manger l'espace d'une A4)
- Pas d'ombres portées (inutiles en PDF)
- Pas de hover effects
- Une couleur seulement pour l'accent : bleu `#3B82F6`
- Ligne TOTAL en bleu plein + prix en jaune

---

## Tokens injectés

Les mêmes que la page web (voir `placeholders-map.md`), notamment :

- `{{DEVIS_REF}}` × 3 (header PDF + émetteur + footer)
- `{{DATE_FR}}` × 3
- `{{DEADLINE_FR}}` × 2 (conditions + footer)
- `{{CLIENT_FULL_NAME}}`, `{{CLIENT_COMPANY}}`, `{{CLIENT_ROLE}}`, `{{CLIENT_ADDRESS_LINE}}`, `{{CLIENT_POSTAL_CODE}}`, `{{CLIENT_CITY}}`, `{{CLIENT_PHONE}}`, `{{CLIENT_EMAIL}}`
- `{{LF_FEE}}` × 2 (table total + conditions)
- `{{STRIPE_LINK}}` × 2 (vrai lien cliquable dans le PDF, critique)
- `{{SETUP_DESCRIPTION}}`, `{{CREATIVES_ANGLE_CONTEXT}}`, `{{GEO_RADIUS_KM}}`, `{{CLIENT_CITY}}`, `{{PREQUAL_FILTERS_SHORT}}`
- `{{MEETING_WORD_PLURAL_CAPS}}`, `{{MEETING_WORD_PLURAL}}`

---

## Configuration html2pdf.js

```js
const opt = {
  margin: [10, 10, 10, 10],            // mm
  filename: 'Devis-{ClientName}-{YYYYMMDD}.pdf',
  image: { type: 'jpeg', quality: 0.98 },
  html2canvas: { scale: 2, useCORS: true, backgroundColor: '#FFFDF5' },
  jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
  pagebreak: { mode: ['css', 'legacy'] }
};
html2pdf().set(opt).from(document.getElementById('pdf-devis')).save();
```

Le nom de fichier `{ClientName}` = slug kebab-case de `meta.company_legal_name` sans caractères spéciaux (ex : `Fermetures-Acme`).

---

## Ce qui n'est PAS dans le PDF

- Pas de hero / H1 / badge
- Pas de section cards "Ce que vous obtenez" (marketing)
- Pas de section "Chiffres the platform" (marketing)
- Pas de calculateur ROI
- Pas de bloc "Marché vs notre offre"
- Pas de timeline 4 étapes
- Pas de CTA final

→ Le PDF est un document **strictement commercial/légal** : identité parties + détail des prestations + conditions + moyens de paiement.
→ La landing page HTML = marketing + vente.
→ Les 2 supports sont complémentaires, pas redondants.

---

## Quality check visuel (preview)

Pour tester le PDF en dev, ajouter temporairement :

```css
#pdf-devis { left: 0 !important; position: relative !important; border: 2px dashed red; }
```

puis cliquer "Télécharger PDF". Le visuel doit être :
- 1 page si les 10 lignes + conditions tiennent serré
- 2 pages si besoin (page 1 = parties + table, page 2 = conditions + footer)
- Jamais de coupure au milieu d'une ligne de table (CSS `page-break-inside: avoid` hérité)
