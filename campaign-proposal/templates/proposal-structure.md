# Template structure du document de proposition

Structure markdown source que `build_proposal.py` consomme pour générer le PDF final (`{{AGENCY_NAME}}` y est remplacé par le nom de ton agence).

---

## Section 1 — Brief stratégique & objectif de test

[Paragraphe court 4-7 phrases. Contexte, offre, funnel choisi, objectif de la phase de test, ce qu'on cherche à valider. Style direct, zéro jargon IA.]

Exemple :
> L'objectif de cette première phase est de valider l'appétence du marché francophone pour la Méthode 5JC (offre fictive d'exemple) sur un budget de test de 50€/jour. On lance une campagne Meta Lead Form ciblant les closers en activité bloqués entre 1 et 5K€/mois. On cherche à atteindre un CPL inférieur à 8€ et à générer 30 leads qualifiés sur les 14 premiers jours. Si ces seuils sont validés, on passe en phase de scaling immédiatement.

---

## Section 2 — Formulaire de qualification (SI Instant Form)

### Question 1 — [Énoncé]
**Type** : Choix unique
**Options** :
- Option A
- Option B
- Option C
- Option D

### Question 2 — [Énoncé]
[...]

### Règle de qualification
**Lead qualifié si** :
- Q1 = [...]
- ET Q2 = [...]
- ET Q3 = [...]

**Lead disqualifié si** :
- Q1 = [...]
- OU Q2 = [...]

---

## Section 2 — Script VSL (SI funnel VSL)

### Bloc 1 — [Titre] (00:00–00:15)
[Texte voice over]

### Bloc 2 — [Titre] (00:15–00:45)
[Texte voice over]

[etc.]

---

## Section 3 — Structure des campagnes Meta

### Campagne 1 — [Nom de campagne]

**Objectif Meta** : [Leads / Conversions / Sales]
**Budget quotidien** : [X €/jour]
**Durée test** : [14 jours / 21 jours / etc.]

#### Ad set 1 — Audience par intérêts
- Géo : [...]
- Âge : [...]
- Sexe : [...]
- Intérêts : [liste]
- Taille : ~[X M]

#### Ad set 2 — Audience Broad
- Géo : [...]
- Âge : [...]
- Sexe : [...]
- Intérêts : aucun
- Taille : ~[X M]

#### Créatives ([N] créatives — images statiques par défaut)

##### Créative 1 — [Nom] (Angle : [Douleur/Désir/Preuve/ContreIntuitif/Urgence])

**Format** : Image statique 1080x1080
**Headline image** : [phrase courte qui arrête le scroll]
**Primary text** : [texte d'accompagnement — angle + bénéfice + CTA]

##### Créative 2 — [Nom] (Angle)
[...]

[Répéter pour chaque créative jusqu'à 5-10]

> **Note** : si l'utilisateur demande explicitement des scripts vidéo (face cam, UGC), remplacer le format ci-dessus par : Hook (0-3s) / Body (3-25s) / CTA (25-30s).
