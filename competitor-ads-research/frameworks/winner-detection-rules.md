# Règles de détection des "ads winners" — the platform

Une ad gagnante (winner) est une ad qu'un concurrent laisse tourner longtemps. Sur Meta, **personne ne brûle son budget sur des ads qui ne convertissent pas**. Donc la durée d'activité est notre proxy #1 pour la performance.

## Règle principale : durée d'activité

| Durée d'activité | Statut | Interprétation |
|---|---|---|
| < 7 jours | Test | Trop tôt pour conclure |
| 7-21 jours | Validation | En cours d'optimisation |
| **> 21 jours** | **Winner ✓** | Performe assez pour justifier le budget |
| **> 60 jours** | **Hero ✓✓** | Top performer du concurrent |
| > 180 jours | Evergreen ✓✓✓ | Pilier du compte, à étudier en priorité |

**Règle d'or** : **on annote `winner = true` dès 21 jours**. C'est le seuil the platform.

## Critères secondaires (renforcement)

Une ad est doublement intéressante si elle cumule :
- ✓ Active > 21 jours
- ✓ Plusieurs versions (variantes A/B du même angle) — signal de scaling
- ✓ Diffusion multi-pays (le concurrent étend la portée)
- ✓ Multiple plateformes (FB + IG + Audience Network) — confiance dans l'ad
- ✓ Ad récente (< 180 jours) → pas de biais survivor évergreen

## Signaux faibles à noter

- **Ad relancée plusieurs fois** : si la même créative apparaît avec plusieurs IDs sur 6 mois → winner historique
- **Ad copiée chez plusieurs concurrents** : pattern qui marche dans tout le marché
- **Ad avec landing page custom dédiée** : signal d'investissement, donc d'intérêt

## Anti-signaux (ne PAS considérer comme winner)

- Ad de notoriété pure (campagne brand awareness) — long ≠ performance leads
- Ad qui n'a pas de CTA clair
- Ad en boucle avec un budget < 5€/jour (visible au reach très faible si dispo)
- Ad qui tourne uniquement le weekend ou en off-peak

## Comment exploiter les winners dans le brief

Dans le `data.csv` : colonne `winner = true` pour les ads > 21j.

Dans `analysis.md` :
- Section "Top Winners" liste les 10 meilleures par durée d'activité
- Pour chaque winner : verbatim du hook + angle + format + jours d'activité

Dans le `.docx` final :
- Les "Top hooks détectés" et "Top CTAs" sont **uniquement extraits des winners**, jamais des ads de < 21j
- Les recommandations s'appuient en priorité sur les patterns des winners
