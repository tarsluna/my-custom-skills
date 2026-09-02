# Extraction des patterns récurrents

Une fois toutes les ads classifiées en angles + flaggées winner/non-winner, on extrait les **patterns** qui reviennent à travers le set concurrentiel. C'est ce qui rend le brief actionnable.

## Pattern 1 — Hook structures

Identifier les formules de hooks qui reviennent (≥3 occurrences à travers les concurrents).

Exemples de structures :
- `Si tu [persona] et que tu [galère], ...` (Pain Hook classique)
- `Voilà comment [résultat chiffré] en [délai]` (Outcome Hook)
- `Tout le monde te dit [croyance]. C'est faux.` (Pattern Interrupt)
- `[Prénom] a fait [résultat] en [délai]` (Social Proof)

Pour chaque structure : noter combien de concurrents l'utilisent et avec quelles variations.

## Pattern 2 — Frameworks de copy (corps de l'ad)

Détecter les structures récurrentes du corps des ads :
- **PAS** (Problem-Agitate-Solution)
- **AIDA** (Attention-Interest-Desire-Action)
- **Hook-Story-Offer**
- **Before/After/Bridge**
- **Listicle** ("3 erreurs que..", "5 raisons pour...")

Pour chaque framework : combien d'ads winners l'utilisent.

## Pattern 3 — Formats dominants par angle

Croiser angle × format :

| Angle | Format dominant chez les winners |
|---|---|
| Douleur | FaceCam ? UGC ? Static ? |
| Désir | Vidéo lifestyle ? Carrousel résultats ? |
| Preuve | UGC client ? Capture screenshot ? |
| Contre-intuitif | FaceCam dirigeant ? |
| Urgence | Static avec deadline ? Story countdown ? |

C'est ce qui guide les recommandations : si tous les winners "Douleur" sont en FaceCam, on copie ce format pour le client.

## Pattern 4 — CTAs récurrents

Lister tous les CTAs des winners et compter les occurrences. Top 5 = CTAs à tester.

Catégories à isoler :
- **Direct** : "Réserve ton appel", "Démarre maintenant"
- **Soft** : "Découvre la méthode", "Voir la vidéo"
- **Conditional** : "Si t'es éligible, candidate"
- **Scarcity** : "Plus que X places", "Avant vendredi"

## Pattern 5 — Pain points partagés (saturation)

Lister les douleurs verbalisées dans les ads. Si la même douleur revient chez ≥4 concurrents → **angle saturé**, à éviter ou à twister.

Exemples de saturation typiques :
- "Closing francophone saturé" (chez 6 concurrents → saturé)
- "Plafond 3-5K€/mois" (chez 5 concurrents → saturé)

## Pattern 6 — White spaces (opportunités)

À l'inverse, lister les douleurs / angles qu'AUCUN concurrent n'exploite alors qu'ils sont pertinents pour le marché. C'est là que ton offre positionne son client.

Méthode :
1. Lister les 10 douleurs majeures du marché (depuis le brief client ou la deep search)
2. Cocher celles qui apparaissent chez les concurrents
3. Les non-cochées = white spaces

## Pattern 7 — Évolution temporelle (si profondeur ≥ 90 jours)

Si on a 90 jours de data :
- Quels angles ont émergé récemment ?
- Quels angles sont en déclin (ads tuées, plus relancées) ?
- Y a-t-il une saisonnalité ?

## Output dans `analysis.md`

Le fichier `analysis.md` doit avoir une section **"Patterns détectés"** structurée :

```markdown
## Patterns détectés

### Hooks (structures récurrentes)
1. "Si t'es [persona] et que tu [galère]" — 8 occurrences, 4 concurrents
2. "Voilà comment [résultat] en [délai]" — 6 occurrences, 3 concurrents
[...]

### Frameworks de copy
- PAS : 12 ads (43%)
- Hook-Story-Offer : 7 ads (25%)
- Listicle : 4 ads (14%)
[...]

### Angles saturés
- Douleur "plafond 3-5K€" : 5 concurrents
- Douleur "saturation marché" : 6 concurrents

### White spaces (à exploiter)
- Aucun concurrent ne joue l'angle "garantie placement 14 jours"
- Aucun concurrent ne joue l'angle "spécialisation Challenges 5 jours"
```
