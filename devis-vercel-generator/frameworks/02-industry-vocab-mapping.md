# Framework 02 — Industry vocab mapping

Règle d'or : le prospect ne doit **jamais** lire le mot "deal" ni "RDV" s'il ne parle pas comme ça dans son métier. Un menuisier parle de "chantier", un dentiste de "patient", un consultant B2B de "contact" ou "prospect".

Le brief JSON contient `meta.industry_vocab` avec 3 champs (`deal_word`, `customer_word`, `meeting_word`). Le skill les injecte partout où le template utilise les tokens `{{DEAL_WORD}}`, `{{CUSTOMER_WORD}}`, `{{MEETING_WORD}}` et leurs variantes (plural / caps / short).

---

## Table d'adaptation par industrie

| Industrie | `deal_word` | `customer_word` | `meeting_word` | Panier moyen défaut |
|---|---|---|---|---|
| **BTP / menuiserie / rénovation** | chantier | propriétaire | RDV téléphonique | 5 000 € |
| **Coaching / formation indépendants** | client | coaché | call découverte | 300-2 000 € (1 500 médian) |
| **B2B SaaS** | deal | contact | démo call | 50 000 € |
| **Healthcare / médical privé** | patient | patient | consultation | 150-500 € |
| **E-commerce / D2C** | commande | client | appel conseil | 80-400 € (150 médian) |
| **Immobilier** | mandat | vendeur | RDV agence | 12 000 € |
| **Services locaux (plombier, paysagiste, serrurier…)** | intervention | propriétaire | RDV technique | 800-3 000 € |
| **Agence / freelance premium** | mission | client | call découverte | 8 000 € |
| **Assurance / mutuelle** | contrat | assuré | RDV conseiller | 600 € |
| **Automobile (concession, tuning…)** | véhicule | client | essai | 15 000 € |

**Défaut fallback si le brief ne précise rien** : `client / client / RDV téléphonique` + panier 2 000 €.

---

## Où chaque token apparaît dans le template

### `{{DEAL_WORD}}` et variantes

- Calculateur ROI : label slider conv2 → "Taux conversion RDV → **chantier**"
- Calculateur ROI : hint slider conv2 → "% des RDV qui aboutissent à un **chantier** signé"
- Calculateur ROI : stat card droite → "**Chantiers** signés" (`{{DEAL_WORD_PLURAL_CAPS}}`)
- Timeline étape 4 → "**chantiers** signés"

### `{{CUSTOMER_WORD}}` et variantes

- Card 1 bullet 1 → "Publicités Facebook & Instagram ciblées **propriétaires**" (`{{CUSTOMER_WORD_PLURAL}}`)
- Calculateur ROI : label panier → "Panier moyen **propriétaire** (€)" (ou `client` si BTP garde "client" comme vocab plus naturel — à décider case par case)
- Timeline étape 1 → "avatar **propriétaire** qualifié"

### `{{MEETING_WORD}}` et variantes

- Card 3 titre → "**RDV** bookés automatiquement" (`{{MEETING_WORD_PLURAL_CAPS}}`)
- Card 3 bullet 2 → "**RDV téléphonique** 15 min pour valider le projet" (`{{MEETING_WORD}}`)
- Calculateur ROI : slider conv1 → "Taux conversion lead → **RDV**"
- Calculateur ROI : stat card milieu → "**RDV** bookés"
- Table devis : ligne 6 → "Prise de **RDV** automatisée" (`{{MEETING_WORD_PLURAL_CAPS}}`)
- Timeline étape 3 → "qualité des **RDV** bookés"
- Timeline étape 4 → "volume de **RDV** qualifiés générés"
- Conditions : dernier bullet → "**RDV téléphoniques** pré-qualifiés" (`{{MEETING_WORD_PLURAL}}`)
- CTA final H2 → "Prêt à recevoir vos premiers **RDV qualifiés**" (`{{MEETING_WORD_PLURAL_SHORT}}`)
- Section title "4 étapes" → "jusqu'aux premiers **RDV**" (`{{MEETING_WORD_PLURAL_SHORT}}`)

---

## Variantes dérivées (plural / caps / short)

Le script `generate.mjs` calcule les variantes automatiquement à partir de `meeting_word` :

| Input brief | `{{MEETING_WORD}}` | `{{MEETING_WORD_SHORT}}` | `{{MEETING_WORD_PLURAL}}` | `{{MEETING_WORD_PLURAL_SHORT}}` | `{{MEETING_WORD_PLURAL_CAPS}}` |
|---|---|---|---|---|---|
| "RDV téléphonique" | RDV téléphonique | RDV | RDV téléphoniques | RDV | RDV |
| "démo call" | démo call | démo | démos call | démos | Démos |
| "consultation" | consultation | consult. | consultations | consults | Consultations |
| "call découverte" | call découverte | call | calls découverte | calls | Calls |

Règle :
- `_SHORT` = premier mot si compose, sinon premier mot tronqué
- `_PLURAL` = ajouter "s" au premier mot (ou règles spéciales si irrégulier)
- `_CAPS` = première lettre en majuscule de la forme courte plurielle

Idem pour `{{DEAL_WORD_PLURAL}}` et `{{DEAL_WORD_PLURAL_CAPS}}` :
- chantier → chantiers → Chantiers
- client → clients → Clients
- patient → patients → Patients
- deal → deals → Deals
- mandat → mandats → Mandats

---

## Panier moyen ROI — plage de cohérence

Si `roi_calc_defaults.avg_basket_eur` du brief est **hors plage** pour l'industrie annoncée → flag et re-vérifier avant de générer :

| Industrie | Plage sensée | Flag si hors plage |
|---|---|---|
| BTP / menuiserie | 2 000 – 30 000 € | < 2 000 ou > 30 000 |
| Coaching | 200 – 5 000 € | < 200 ou > 5 000 |
| B2B SaaS | 5 000 – 200 000 € | < 5 000 ou > 200 000 |
| Santé | 50 – 3 000 € | > 3 000 |
| E-commerce | 30 – 1 000 € | > 1 000 |
| Immobilier | 5 000 – 50 000 € | hors de cette plage |

Si flag : demander confirmation à l'utilisateur avant génération. Sinon : injecter tel quel.

---

## Cas spécial : industries hybrides

Si le brief indique deux industries possibles (ex : un coach qui fait aussi du conseil B2B) → utiliser l'industrie **principale** indiquée dans `meta.industry_primary` (s'il existe), sinon celle dont parle le plus le prospect dans la transcription. En cas de doute, défaut = `client / client / RDV téléphonique`.

---

## Règle : ne pas mélanger les vocabulaires

Une fois `deal_word` choisi, utiliser **seul** ce mot dans tout le devis. Ne pas écrire "chantiers ou clients" — choisir un seul. Cohérence avant tout.

Exception : le bloc des **chiffres** (section PREUVE) garde le vocabulaire agence (`RDV qualifiés` + `clients accompagnés`) car c'est une stat de ton offre, pas du prospect. Immuable.
