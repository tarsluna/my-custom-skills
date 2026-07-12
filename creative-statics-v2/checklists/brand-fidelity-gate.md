# Checklist — Brand Fidelity Gate (V2)

À passer sur chaque créative AVANT curation finale. La force de la V2 = des visuels
qui ressemblent vraiment au client. Si une créative échoue → FIX-BRANDLOCK ou REGEN.

## Palette
- [ ] Le fond utilise un hex du `client-brand-profile.json` (pas une couleur inventée par l'IA) ?
- [ ] L'accent n'apparaît QUE sur le CTA (1 seul point focal) ?
- [ ] Pas de 4e/5e couleur parasite introduite par l'IA ?

## Logo & identité
- [ ] Le logo est présent, lisible, NON halluciné (pas un faux logo inventé) ?
- [ ] Si brand asset produit fourni → le produit affiché correspond (pas un produit différent) ?
- [ ] Si spokesperson récurrent → même visage d'une créative à l'autre (sinon → Soul ID) ?

## Ton & voix
- [ ] L'univers visuel respecte l'`accent_archetype` (Confiance/Urgence/Énergie/Authority/Luxe) ?
- [ ] Aucun élément ∈ `dont` du profil (emoji, style off-brand, etc.) ?
- [ ] Le registre visuel est cohérent sur tout le pack (pas 30 marques différentes) ?

## Texte incrusté
- [ ] Le hook rendu est exactement celui de la matrice (orthographe OK) ?
- [ ] Le CTA est exactement celui prévu ?
- [ ] Aucun texte parasite / gibberish ajouté par l'IA ?

## Verdict
- [ ] **SHIP** : tout coché → curation.
- [ ] **FIX-BRANDLOCK** : visuel OK mais texte/logo flou → `brand_lock_pass.py`.
- [ ] **REGEN** : palette/produit/identité ratés → corriger le prompt, re-générer.
- [ ] **KILL** : hors-marque irrécupérable.
