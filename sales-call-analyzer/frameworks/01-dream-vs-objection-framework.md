# Framework 01 — Dream vs Objection Extraction

**Objectif** : extraire les 2 blocs verbatim qui nourrissent le hero de la landing page de devis :
- Le **dream state** (ce que le prospect veut vraiment) → alimente le headline hero (`Moins de RDV. Mieux qualifiés. Sans diluer vos 40 ans d'image premium.`).
- Les **objections / douleurs** (ce qu'il fuit) → alimentent les 3 bullets "Fini les X" sous le headline.

**Règle absolue** : **verbatim > paraphrase**. Si le prospect a dit "ça bloquait souvent au niveau du prix", on garde ces mots exacts. On ne reformule pas.

---

## 🎯 1. Trouver le dream state verbatim

Scanner la transcription pour 4 types de signaux.

### 1.1 Les phrases "il vaut mieux" / "je préfère" / "l'idéal ce serait"

Ces marqueurs introduisent presque toujours le dream state explicite.

**Exemple Acme** :
> « Il vaut mieux en avoir moins, qu'on a payé un peu plus cher, mais qui correspondent vraiment à l'image. »

→ Capturer la phrase complète. Mettre dans `dream_state.verbatim_wins[]`.

### 1.2 Les phrases sur "le bon client" / "le bon prospect"

Le prospect décrit son ICP idéal. À capter mot pour mot.

**Exemple Acme** :
> « Des gens qui ont le budget. »

→ Capturer. Mettre dans `dream_state.verbatim_wins[]` ET exploiter pour `icp.budget_range_label`.

### 1.3 Les phrases sur l'image / la marque / le positionnement

Très fréquent chez les entreprises à forte ancienneté ou positionnement premium.

**Exemple Acme** :
> « Image haut de gamme préservée. »

→ Capturer. Exploiter pour le "Sans Z." du headline hero.

### 1.4 Les phrases "moi, mon objectif c'est..."

Quand le prospect dit explicitement ce qu'il veut atteindre.

---

## ⚡ 2. Construire le `headline_hook`

Le `headline_hook` est le titre H1 du hero de la landing page.

**Formule obligatoire** :
```
{Gain 1}. {Gain 2}. Sans {dilution / douleur}.
```

3 segments, max 12 mots total, ponctuation forte (points entre segments).

**Exemple Acme** : *"Moins de RDV. Mieux qualifiés. Sans diluer vos 40 ans d'image premium."*

### Règles de construction

- **Segment 1 & 2** : tirés du dream verbatim (le prospect veut quoi ? formulation positive, chiffrée si possible).
- **Segment 3 "Sans X"** : ce que le prospect refuse absolument de sacrifier (image, marge, temps du commercial, qualité). Tiré des objections verbatim.
- Max 12 mots total. Si tu arrives à 14, coupe.
- Pas de "vous" au début (on commence par le bénéfice, pas par le pronom).
- Pas d'adjectifs vides ("incroyable", "exceptionnel", "premium" OK s'il vient du vocabulaire du prospect).

### Anti-exemples (ce qu'il ne faut PAS faire)

- ❌ *"Générez plus de leads qualifiés pour votre entreprise de menuiserie."* → trop long, pas de "Sans X", pas de spécifique.
- ❌ *"Des leads premium pour votre marque."* → flou, pas de verbatim.
- ❌ *"Arrêtez les mauvais prospects dès aujourd'hui !"* → impératif + ton IA + rien de spécifique.

---

## 🚫 3. Trouver les objections / douleurs verbatim

Scanner la transcription pour 5 types de signaux.

### 3.1 Les phrases "ça bloque" / "le problème c'est" / "ce qui me gonfle"

Introduisent presque toujours une douleur exprimée.

**Exemple Acme** :
> « Ça bloquait souvent au niveau du prix. »
> « Pas vraiment les gens qualifiés. »

### 3.2 Les phrases sur les coûts cachés

Déplacements, temps, carburant, véhicules, absences.

**Exemple Acme** :
> « Mon commercial a été absent de l'entreprise, beaucoup de frais de véhicules de carburant. »
> « Les coûts en plus de carburant ont encore augmenté. »

### 3.3 Les phrases sur l'image / la réputation abîmée

Très fort chez les entreprises établies.

**Exemple Acme** :
> « À un moment donné, je vais mettre de la confusion dans l'esprit… créer aussi une distorsion de l'image de l'entreprise sur le long terme. »

### 3.4 Les phrases "ça ne m'intéresse pas" / "je veux plus" / "je refuse"

Refus explicites.

**Exemple Acme** :
> « Ça ne m'intéresse pas d'aller perdre du temps. »

### 3.5 Les phrases sur l'agence précédente / outil précédent

Quasi toujours une mine d'or d'objections verbatim.

**Exemple Acme** :
> « 15 000 sur 4 mois… 3 clients… CA équivalent au montant investi… zéro marge. »

---

## 🧱 4. Construire les 3 bullets `"Fini les X"`

Le sous-titre hero affiche **exactement 3 bullets**, chacun commence par **"Fini les"** et cite une douleur verbatim mappée sur la solution the platform.

**Formule** :
```
Fini les {douleur verbatim courte} {détail contextuel optionnel}
```

### Exemple Acme (gold standard)

Douleurs verbatim extraites :
- "ça bloquait souvent au niveau du prix" + "pas vraiment les gens qualifiés"
- "commercial absent, frais véhicules/carburant" + déplacements à 60km
- "promotions low-cost" → image diluée

→ 3 bullets produits :
1. `Fini les prospects qui "comparent 3 devis"`
2. `Fini les RDV à 55 km qui n'ont pas le budget`
3. `Fini les promos low-cost qui salissent votre marque`

### Règles

- **Exactement 3 bullets**, pas 2, pas 4.
- Chaque bullet doit être **traçable** à un verbatim de la transcription (sinon pas de preuve de personnalisation).
- Max 10 mots par bullet.
- Si un verbatim fait plus de 10 mots, en citer le fragment essentiel entre guillemets.
- Mélanger : (1) douleur commerciale chiffrée, (2) douleur opérationnelle, (3) douleur image/positionnement. Les 3 bullets doivent couvrir 3 angles différents.
- Toujours finir par une promesse subliminale : la phrase finale du subtitle (après les 3 bullets) explique ce que ton offre fait pour remplacer ces douleurs.

### Phrase finale subtitle (après les 3 bullets)

Exemple Acme : *"the platform filtre 5 à 10 fois vos leads Meta avant qu'ils n'atteignent l'agenda de votre commercial."*

Formule : `the platform {mécanisme spécifique} avant {étape où la douleur se manifesterait}.`

---

## ✅ Check-list avant de remplir le JSON

- [ ] Au moins **2 verbatim** dans `dream_state.verbatim_wins` (citations entre guillemets, mot pour mot)
- [ ] Au moins **3 verbatim** dans `objections.verbatim_pains` (citations entre guillemets)
- [ ] `dream_state.headline_hook` = 3 segments "X. Y. Sans Z.", max 12 mots
- [ ] `objections.headline_subtitle_bullets` = exactement 3 bullets, chacun commence par "Fini les"
- [ ] Chaque bullet est traçable à un verbatim
- [ ] Le dernier élément du subtitle hero (hors des 3 bullets) est une promesse mécanisme the platform
