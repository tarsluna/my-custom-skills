# Framework 02 — Hooks Library

> Source : `meta_hook_library_v1` + `MetaAds_Callout_Framework` + Lya playbook.
> Used in **Phase 4** of the skill.

> **Règle d'or de Ogilvy** : le hook = 80% de l'impact d'une pub.
> **Règle Meta** : la première seconde vend la suivante. 80% de l'efficacité se joue dans les 5 premières secondes (idéalement les 3 premières).

---

## A. Verbal hook patterns (8 archetypes)

Chaque hook doit s'adresser à une douleur, un goal ou une croyance spécifique de l'avatar.

### 1. Label local / niche
> "Hey {Ville} !" / "Parents de {Quartier}…" / "Dirigeants BTP : ..." / "Coachs à Lyon, ..."

**Quand utiliser** : marché local, ciblage géo. Filtre l'audience en 1 seconde.

### 2. Yes-Question
> "Vous vous réveillez la nuit pour {symptôme} ?" / "Vous avez du mal à remplir votre agenda ?"

**Quand utiliser** : douleur quotidienne reconnue par l'ICP. Crée immédiatement l'identification.

### 3. If-Then
> "Si vous {condition}, alors {bénéfice}…" / "Si vos pubs Meta brûlent du cash sans résultats, regardez ça."

**Quand utiliser** : pour qualifier le viewer ET promettre une solution en un seul souffle.

### 4. Résultat atypique / Bold claim
> "{Problème} réglé en {délai}, voici comment." / "Cette PME a doublé son CA en 90 jours sans augmenter son budget pub."

**Quand utiliser** : quand on a un proof-point chiffré. Curiosité + crédibilité.

### 5. Pain-stat
> "75% des PME perdent de l'argent à cause d'un processus obsolète de prospection."

**Quand utiliser** : marché B2B, consulting, où l'autorité chiffrée fait poids.

### 6. Contrarian
> "Tout ce qu'on t'a appris sur la prospection LinkedIn est faux."

**Quand utiliser** : marché saturé (sophistication ≥4) où il faut casser les conventions.

### 7. Story opener
> "Il y a 18 mois, j'étais à 3000€ de CA. Aujourd'hui, j'en signe 80k. Voilà comment."

**Quand utiliser** : coaching, transformation personnelle, identité.

### 8. Common enemy
> "Si tu en as marre des agences qui promettent monts et merveilles et livrent rien…"

**Quand utiliser** : quand l'avatar a déjà un ennemi clair (concurrents, croyances, statu quo).

---

## B. Visual / sonore hook patterns (pour scripts vidéo)

Note : on **ne livre pas** de storyboard. Mais une indication scénique courte est autorisée si elle change le sens du hook.

- **Contraste visuel** : couleur, vêtement, environnement très contrasté
- **Mouvement immédiat** : pas de plan fixe les 2 premières secondes
- **Likeness** : porte-parole qui ressemble à l'audience cible
- **Scène-problème** : agenda vide, ordi qui plante, écran de stats catastrophiques
- **Geste inattendu** : casser quelque chose, jeter, déchirer (si pertinent et non gratuit)
- **Signal sonore** : ding, claquement, snap fingers — synchronisé avec un sous-titre géant

---

## C. The first-3s checklist

Chaque hook doit cocher **au moins 3** des 5 cases suivantes :

- [ ] **Contraste** visuel ou sonore évident
- [ ] **Label** explicite qui filtre l'ICP ("Coachs", "Agences SaaS", "Dirigeants…")
- [ ] **Mouvement** dès 0–1s (le visage parle, les mains bougent, plan changeant)
- [ ] **Sous-titres** natifs présents (la vidéo doit fonctionner sans son)
- [ ] **Promesse ou tension** posée dans la première phrase

---

## D. DO / DON'T

### DO
- Contraste couleur / vêtement
- Mouvement immédiat
- Sous-titres natifs (90% des utilisateurs Meta scrollent en muet)
- UGC brut > vidéo trop léchée en prospection cold
- Hook spécifique > hook générique
- Filtrer l'ICP dès la 1ère seconde

### DON'T
- ❌ Intro avec logo > 2 secondes
- ❌ Jargon avant que le bénéfice soit énoncé
- ❌ Hook qui pourrait s'adresser à n'importe qui (= s'adresse à personne)
- ❌ Démarrer par "Bonjour, je m'appelle…"
- ❌ Démarrer par une question rhétorique molle ("Vous en avez marre de… ?")
- ❌ Hook qui spoile la solution (garde la curiosité ouverte)

---

## E. Hook templates by market awareness level (Schwartz)

| Niveau | État du marché | Hook recommandé |
|---|---|---|
| 1. Unaware | Ne sait pas qu'il a un problème | **Story opener** ou **Pain-stat** ("75% des X font cette erreur sans le savoir") |
| 2. Problem Aware | Connaît le problème, pas la solution | **Yes-Question** ou **Common enemy** |
| 3. Solution Aware | Connaît les solutions, hésite entre elles | **Contrarian** ou **Mécanisme nommé** ("Notre Méthode X fait l'inverse de ce qu'on t'a appris") |
| 4. Product Aware | Connaît ton produit, pas convaincu | **Résultat atypique** chiffré + nom client |
| 5. Most Aware | Connaît tout, attend une raison d'agir | **Offre directe** ("3 places ouvertes ce mois, voici comment réserver") |

---

## F. Hook templates by sector (from `structure_copy.json`)

### SaaS B2B
> "Boostez votre taux de conversion de 2x sans coder."
> "Lancez votre feature en moins de 10 minutes."
> "Tout ce que vous voulez sans tout ce que vous détestez."

### Marketing Agency
> "Votre budget pub s'envole sans résultats ?"
> "Comment {Client} a doublé ses ventes sans augmenter son budget pub."
> "E-commerçants : votre CAC explose ce trimestre ?"

### Coaching Business
> "Débordé et proche du burn-out chaque dimanche soir ?"
> "Et si vous doubliez votre revenu en travaillant moins ?"
> "Il y a 1 an, je faisais faillite. Aujourd'hui je génère 20k€/mois."

### Consulting
> "75% des PME perdent de l'argent à cause de [process obsolète]."
> "Combien vous coûte chaque jour l'inefficacité de [tel process] ?"
> "Votre concurrent améliore sa marge de 5% chaque année. Et vous ?"

---

## G. Testing rule

> **Toujours tester d'abord le hook, jamais la créa entière.**
> Le hook = 80% de l'efficacité. Changer le hook peut multiplier le CTR par 2–5x.
> Règle Lya : 1 test/plateforme/semaine, attaquer le hook en priorité.

Quand tu génères les variantes pour le client, **assure-toi que les hooks sont vraiment distincts** (pas 3 variantes du même hook avec des mots différents). Chaque variante = un angle différent → un hook différent.
