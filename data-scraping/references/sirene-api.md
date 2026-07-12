# Référence — API Recherche Entreprises (open-data SIRENE/INSEE)

**Base** : `https://recherche-entreprises.api.gouv.fr/search`
**Coût** : gratuit · **Clé** : aucune · **Légalité** : open-data registre INSEE (donnée pro publique)

C'est la source #1 de la méthode. Elle expose, par entreprise FR : SIREN, raison sociale, NAF,
dirigeants (avec année de naissance quand connue), effectif, nombre d'établissements, catégorie
(PME/ETI/GE), nature juridique, date de création, commune. **Pas de CA** (limite assumée — Pappers le débloque).

## Paramètres utiles
| Param | Exemple | Note |
|---|---|---|
| `activite_principale` | `75.00Z` | NAF format **"NN.NNX" avec un point** (pas `7500Z`) |
| `departement` | `13` | filtre géo principal |
| `tranche_effectif_salarie` | `02,03,11,12` | codes INSEE séparés par virgule (voir mapping) |
| `categorie_entreprise` | `PME` | PME/ETI/GE |
| `page` | `1` | pagination 1..~1000 |
| `per_page` | `25` | **MAX 25.** Au-delà → réponse SANS champ `results` (= erreur silencieuse) |
| `q` | `THIERRY ROY` | recherche texte (utile pour matcher un nom précis) |

## ⚠️ Gotchas découverts (coûteux à re-découvrir)
1. **`per_page > 25` casse tout** : pas d'erreur HTTP propre, juste pas de `results`. Plafonner à 25.
2. **NE PAS utiliser `minimal=true`** : renvoie `siege: null` → on perd ville/CP/dept/tranche, qui sont
   dans `siege`. Et l'API refuse `include=...` *sans* `minimal` (HTTP 400). → Requêter SANS ces deux
   params : la réponse par défaut contient déjà `siege` ET `dirigeants`.
3. **Le tri par défaut sort les gros groupes en tête** (nombre d'établissements décroissant). Cadeau :
   les premières pages = consolidateurs/acheteurs ; les pages profondes = indépendants/cédants.
4. **`année_de_naissance` souvent null** (~60% des lignes). Beaucoup de vrais dirigeants n'ont pas de
   date. → proxy via `date_creation`. Ne JAMAIS rejeter une boîte juste parce que l'âge manque.
5. **`qualite` souvent null** pour les EI / petites structures. Le dirigeant existe quand même
   (`type_dirigeant: "personne physique"`). Ne pas le filtrer sur la présence d'une qualité.
6. **Entreprise individuelle** : la raison sociale EST le nom de la personne ("THIERRY ROY"), un seul
   dirigeant PP, souvent sans année ni qualité. Profil cédant solo prioritaire — bien le capter.

## Mapping `tranche_effectif_salarie` (code INSEE → borne basse salariés)
`00`=0 · `01`=1 · `02`=3 · `03`=6 · `11`=10 · `12`=20 · `21`=50 · `22`=100 · `31`=200 · `32`=250 ·
`41`=500 · `42`=1000 · `51`=2000 · `52`=5000 · `53`=10000
→ pour cibler les PME 3-49 salariés : `tranche_effectif_salarie=02,03,11,12`.

## NAF utiles (secteurs en consolidation)
- Vétérinaire : `75.00Z`
- Crèche / accueil jeunes enfants : `88.91A`
- EHPAD : `87.10A`, `87.30A`

## Forme de la réponse
```jsonc
{
  "results": [{
    "siren": "...", "nom_complet": "...", "nombre_etablissements": 1,
    "categorie_entreprise": "PME", "nature_juridique": "5710", "date_creation": "1988-02-15",
    "dirigeants": [{ "nom": "ROY", "prenoms": "THIERRY", "annee_de_naissance": null,
                     "qualite": null, "type_dirigeant": "personne physique" }],
    "siege": { "activite_principale": "75.00Z", "libelle_commune": "...", "code_postal": "...",
               "departement": "13", "tranche_effectif_salarie": "03" }
  }],
  "total_results": 781, "total_pages": 32
}
```

## Backoff
Backoff exponentiel sur `429` et `5xx` (base ~800ms, ×2, max ~5 essais). Délai poli ~250ms entre pages.
User-Agent explicite. L'API est robuste (~1.1s/req observé, pas de rate-limit agressif) mais reste poli.

## Sources FR complémentaires (gratuites) — pour aller plus loin
- **INPI RNE** (Registre National des Entreprises) : API gratuite, dirigeants complets + actes.
- **BODACC** (data.gouv) : annonces légales, **mutations/cessions** = signal de cession direct.
- **SIRENE dump complet** (INSEE) : téléchargement gratuit de toute la base (gros volume).
- **Pappers** (payant) : débloque CA réel + actionnariat fin + dates de naissance manquantes.
