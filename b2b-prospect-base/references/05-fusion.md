# Fusion, MX et suppression

```bash
python3 -I scripts/merge.py --project DOSSIER
```

Produit `livrable/base_prospects.csv` (en lecture pour le seul propriétaire) et `livrable/stats.md`.

## Dédoublonnage

Sur l'email en minuscules. On garde la ligne la plus complète, on remplit ses champs vides avec les autres lignes du même email, on cumule les `source_url` (séparées par ` | `, `nb_sources` en compte le nombre) et on garde la date de collecte **la plus ancienne**, celle qui fait courir le délai d'information.

## Motifs de rejet

| Motif | Cas |
| --- | --- |
| `mail_absent`, `format_invalide` | Pas d'adresse ou adresse mal formée |
| `parasite:*` | Fichier (`x@2x.png`), exemple, no-reply, webmaster, DPO, RGPD, adresse technique |
| `sans_preuve_d_origine` | Pas de `source_url` en http(s) |
| `liste_opposition` | Présent dans `suppression.csv` |
| `boite_perso_exclue` | Boîte personnelle, en mode `exclude` |
| `organisme_public` | Domaine couvert par `merge.public_mail_regex` |
| `portable_dans_le_mail` | Numéro de portable dans l'adresse |
| `domaine_sans_mx`, `mx_indetermine` | Le MX ne répond pas. Un MX indéterminé n'est pas mis en cache et se relance |
| `jugement_hors_cible` | Verdict LLM au-dessus du seuil |

## La liste de suppression

`suppression.csv`, à la racine du projet : une adresse par ligne (colonne `email` ou première colonne), ou `@domaine.fr` pour tout un domaine. Elle est appliquée à chaque fusion. Alimentez-la avec les oppositions et désinscriptions reçues, et relancez la fusion avant chaque envoi.

## Les boîtes personnelles

Une adresse gmail ou orange affichée par une entreprise est classée `domaine_perso`. Par défaut elle est **exclue**. Avec `merge.personal_mailboxes` à `flag`, elle reste dans le fichier pour arbitrage, avec le drapeau `boite_perso`, et ne passe jamais en `pret_campagne=oui`.

## Complétion du prénom

Si une ligne n'a pas de prénom, la fusion le cherche dans le registre par SIREN, sinon par le domaine du site s'il désigne une seule entreprise. Elle écarte ce prénom si le nom publié ou la boîte nominative désignent quelqu'un d'autre que le dirigeant.

`prenom_source` indique `publie` ou `dirigeant_registre`. Un prénom déduit reste une déduction : relisez ces lignes avant de personnaliser.

## Colonnes de sortie

Le schéma commun, plus :

| Colonne | Sens |
| --- | --- |
| `prenom_source` | `publie`, `dirigeant_registre` ou vide |
| `nb_sources` | Nombre d'URL distinctes où l'adresse a été vue |
| `a_arbitrer` | `boite_perso`, `qc_absent`, `qc_insuffisant`, `qc_trop_de_mauvaises`, ou un drapeau de `merge.arbitrate` |
| `jugement_metier` | Verdict du LLM, s'il a tourné |
| `pret_campagne` | `oui` seulement avec prénom, email, entreprise et rien à arbitrer |

## Drapeaux à arbitrer

`merge.arbitrate` pose un drapeau sur les lignes dont toutes les preuves viennent d'une source donnée :

```json
"arbitrate": [{"flag": "liste_a_verifier", "url_contains": "opendata.example"}]
```

Ces lignes restent dans le fichier, marquées, et ne sont pas prêtes tant que vous n'avez pas tranché.

## stats.md

Totaux, lignes à arbitrer, rejets par motif et alertes : domaines qui concentrent beaucoup d'adresses (signe d'un annuaire), prénoms écartés, MX indéterminés, date limite d'information. Lisez les alertes avant d'annoncer un chiffre : le total brut n'est jamais le nombre de contacts utilisables.
