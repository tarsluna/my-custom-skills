# Audience targeting — comment construire les 2 ad sets

## Ad set 1 — Audience par intérêts

Objectif : valider les signaux d'intérêt explicites du marché.

### Critères à définir
- **Géographie** : pays / région / ville (si local, rayon de 25-50 km)
- **Âge** : tranche resserrée selon ICP (ex : 25-45 pour un produit pro)
- **Sexe** : H / F / Tous (selon ICP)
- **Langue** : Français (par défaut sauf marché international)
- **Intérêts** : 3 à 8 intérêts pertinents
  - Mélanger intérêts directs (concurrents, formations) et adjacents (outils, médias)
  - Éviter les intérêts ultra-larges qui ressemblent à du broad
- **Exclusions** : exclure les acheteurs existants (custom audience CRM si dispo)

### Taille d'audience cible
- Idéal : 500K à 5M
- < 200K : trop niche, l'algo manque de leads pour optimiser
- > 10M : trop large, autant passer en broad

## Ad set 2 — Audience Broad

Objectif : laisser Meta optimiser librement sans contraintes.

### Critères à définir
- **Géographie** : identique à l'ad set 1
- **Âge** : peut être un peu plus large (ex : 25-55)
- **Sexe** : Tous (sauf si produit clairement genré)
- **Langue** : Français
- **Intérêts** : AUCUN
- **Exclusions** : uniquement les exclusions business critiques (acheteurs existants)

### Pourquoi le broad gagne (post-Andromeda)
- L'algo Andromeda de Meta exploite les signaux comportementaux du pixel et du formulaire
- Il trouve mieux les acheteurs que les intérêts déclarés
- Sur ~80% des comptes PME observés, le broad bat l'audience par intérêts au bout de 7-14 jours

## Tableau type pour le doc client

| Ad set | Audience | Taille | Optimisation |
|---|---|---|---|
| Intérêts | [Liste 3-8 intérêts], [Géo], [Âge], [Sexe] | ~X M | Lead / Conversion |
| Broad | [Géo], [Âge], [Sexe], aucun intérêt | ~X M | Lead / Conversion |
