# Visual Quality Gate — Checklist pré-export

À appliquer sur **chaque créative** avant export final ou upload Meta Ads Manager.

---

## ☐ 1. Dimensions Meta exactes

- [ ] Feed 1:1 = **1080 × 1080**
- [ ] Feed 4:5 = **1080 × 1350**
- [ ] Story/Reel 9:16 = **1080 × 1920**

Largeur = 1080 px toujours. Si hors spec → FAIL, ne pas uploader.

---

## ☐ 2. Safe zones Meta respectées

- [ ] CTA pill entièrement dans les **14% bottom** laissés libres
- [ ] Pour Story/Reel : safe zone top **220 px** (UI Instagram) et bottom **220 px**
- [ ] Pour Carousel : idem Feed + swipe indicator visible

---

## ☐ 3. Grille verticale locked (W = 1080)

- [ ] Logo à y = 0.055 × H
- [ ] Chip eyebrow à y = 0.145 × H
- [ ] Hero à y = 0.20 × H
- [ ] CTA pill à y = H − 0.075 × H − pill_height
- [ ] Marges L/R = 70 px (W × 0.065)

---

## ☐ 4. Typography

- [ ] **2 fonts maximum** : Instrument Serif + Space Grotesk
- [ ] Hero en Italic si hook, Regular si chiffre — **jamais les deux dans la même créative**
- [ ] Hook max **3 lignes** (auto-shrink si dépassement)
- [ ] Wrap à W × 0.87 = 940 px
- [ ] Accent bar orange 6-8 px × 150 px sous le hero

---

## ☐ 5. Contraste

| Zone | Minimum | Combo à utiliser |
|---|---|---|
| Hero | **AAA ≥ 7:1** | OFFWHITE/NAVY ou NAVY/OFFWHITE |
| Body | AA ≥ 4.5:1 | GREY/NAVY ou GREY_DARK/OFFWHITE |
| CTA pill | AA large ≥ 3:1 | OFFWHITE sur ACCENT (text ≥ 37px bold) |
| Chip | AA large ≥ 3:1 | OFFWHITE sur ACCENT ou NAVY |

**Combos à bannir** :
- ❌ ORANGE sur OFFWHITE/CREAM pour texte-clé (3.1:1)
- ❌ NAVY sur NAVY pour logo
- ❌ 3 accents concurrents

---

## ☐ 6. Règle d'or — UN seul accent

- [ ] **Un seul** point focal en couleur accent (ACCENT / ORANGE)
- [ ] CTA pill obtient l'accent **par défaut**
- [ ] Si chip catégorie en ACCENT → hero doit rester navy/offwhite
- [ ] Max 1 underline orange (logo) + 1 accent bar (sous hero) + 1 CTA = OK

Plus de 3 zones ACCENT = **FAIL** (Council score < 8).

---

## ☐ 7. Audit heuristique automatisé

Lancer `scripts/audit_heuristic.py --latest` qui vérifie :
- [ ] Dimensions exactes
- [ ] Poids fichier entre 80 KB et 8 MB
- [ ] Variance pixel ∈ [20, 85] (contraste global)
- [ ] Luminance raisonnable

Récap dans `audit.md` avec verdict par créative (OK / WARN / FAIL).

---

## ☐ 8. Council LLM (obligatoire après v1)

Avant de produire v{N+1}, lancer le Council 4 seats (`templates/council-brief-template.md`) :
- [ ] Brand Guardian rendu
- [ ] UX Researcher rendu
- [ ] UI Designer rendu
- [ ] Copywriter rendu

Lire les 4 verdicts avant toute décision stratégique v_next.

---

## ☐ 9. Voix cohérente

- [ ] Fondateur cité explicitement (ex : « Alex »)
- [ ] Preuves chiffrées en bloc (5 mois / 1,2 M€ / 500+) dans au moins 1 créa du pack
- [ ] Zero émoji
- [ ] Verbes d'action concrets uniquement (coder, livrer, envoyer)

---

## ☐ 10. Format de livraison

- [ ] PNG optimisé (pas JPG)
- [ ] Nommage : `{client-slug}_{angle-id}_{format}.png` (ex : `acme_angle-1-booknow_feed-4x5.png`)
- [ ] Organisé en dossier versionné `creatives/v{N}/` ou `iterations/iter-{N}-{timestamp}/`
- [ ] README.md à jour

---

## Verdict final

```
☐ Gate passé — prêt pour upload Meta
☐ Gate partiel — corrections mineures possibles avant upload
☐ Gate failed — repasser en build v_next
```

---

*Inspiré des audits Council v2 Acme (avril 2026). Voir `frameworks/02-design-system.md` pour le raisonnement complet derrière chaque règle.*
