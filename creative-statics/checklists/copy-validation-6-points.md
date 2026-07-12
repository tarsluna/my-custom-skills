# Checklist Copy Validation — 6 points obligatoires

À appliquer sur **chaque bloc** (hook / sub / body / CTA) avant qu'il parte en production.

---

## ☐ 1. AGENCY — qui fait l'action ?

Pour chaque verbe-promesse, identifier le sujet :
- Si c'est **le fournisseur / la marque** → OK
- Si c'est **le prospect** ET qu'il n'a pas encore levé la main → ❌ **reformuler**

### Exemples

| ❌ | ✅ | Pourquoi |
|---|---|---|
| « Devis fixe **signé** en 48 h » | « Devis fixe **envoyé** en 48 h » | 'signé' implique que le prospect signe = pression |
| « Remplis le formulaire **maintenant** » | « Remplis le formulaire. Tu as ton devis sous 48 h. » | injonction temporelle artificielle |
| « **Tu as raté** le coche » | « Voilà ce qu'on te propose maintenant » | conditionnel reproche |
| « **Candidate** pour un créneau » (sans proof sociale massive) | « Voir s'il reste un créneau ce trimestre » | inversion pouvoir non crédible |

---

## ☐ 2. AWARENESS STAGE (Schwartz 1-5)

Identifier à quel stade parle le hook :

| Stade | Nom | Hook doit |
|---|---|---|
| 1 | Unaware | nommer un malaise flou |
| 2 | Problem Aware | **nommer le problème** en vocabulaire prospect |
| 3 | Solution Aware | **comparer** à une catégorie connue |
| 4 | Product Aware | **citer la preuve unique** |
| 5 | Most Aware | **demander la commande** |

### Règle
- 1 hook = 1 stade. Mélange 3 stades = 0 conversion.
- Cible Acme principale : stade 2 → 3.

---

## ☐ 3. PAIN vs DESIRE POOL

- **Hook** doit puiser dans le **pain pool** (peur, échaudage, perte) pour cibles échaudées
- **Body + CTA** doivent ouvrir sur le **desire pool** (lever, scaler, déléguer)
- Inversé (hook=désir, body=douleur) = weak

---

## ☐ 4. SPECIFICITY — chaque claim a-t-il une ancre concrète ?

| ❌ Flou | ✅ Ancré |
|---|---|
| « Vite » | « en 5 mois » |
| « Beaucoup » | « 1,2 M€ » |
| « On livre » | « Alex livre » |
| « Large portfolio » | « 40 dossiers repris en 3 ans » |
| « Nos experts » | « Alex + 2 seniors Paris » |

---

## ☐ 5. SOURCE — chaque chiffre est-il sourçable ?

Pour chaque chiffre cité :
- [ ] Source publique identifiée (article, presse, site tiers) ?
- [ ] OU confirmé par devis client existant (signature fondateur) ?

Si ni l'un ni l'autre → reformuler en « on », en catégorie, ou retirer.

**Chiffres ronds suspects** : 70 %, 80 %, 100 %, « jamais en 3 ans », « toujours », « 9 sur 10 ». Presque systématiquement non-sourcables. À challenger.

---

## ☐ 6. VOIX — test de la cantine

Ton fondateur (ex : Alex) peut-il **dire cette phrase à voix haute en face d'un prospect** sans que ça sonne « plaquette » ?

Si **non** → réécrire à voix haute.

### Mots qui déclenchent le test

- « transforme ton business » → plaquette
- « passionnés par l'excellence » → plaquette
- « accompagnement sur mesure » → plaquette
- « notre équipe d'experts » → plaquette
- « expérience unique » → plaquette

---

## ☐ 7. TRAÇABILITÉ (bonus — règle de la maison)

Pour chaque phrase du hook + sub + body + CTA, annoter la source :
- `[V]` verbatim psychographic direct
- `[W]` white space concurrentiel (0 concurrent ne le joue)
- `[P]` preuve chiffrée sourçable
- `[C]` core belief / peur cachée du target

Si **aucune annotation** → la phrase est décorative → réécrire ou supprimer.

---

## ☐ 8. BANLIST — jargon et angles saturés

### Jargon à traduire

| Banni | Traduction Acme |
|---|---|
| Stack / scalable / scaling | « techno qu'un autre dev comprend » |
| MVP | « première version livrée » (sauf cible stade 4) |
| Sprint | « 2 semaines de dev » |
| Due diligence | « quand le VC regarde ton code » |
| Agile | à virer |
| API | « tes outils se parlent » |
| Refactor | « recoder proprement » |

### Angles bannis (saturés dans le marché)

- « Agence 360° / sur mesure / clés en main »
- « Expert / n°1 / leader »
- « On conçoit des produits digitaux »
- « Transformons ensemble »
- Liste stack tech en hook

---

## Format de sortie attendu

Après passage de la checklist sur un bloc, annoter :

```
Hook : "BookNow a levé 1,2 M€ avec le MVP qu'on a codé."
  ✓ AGENCY — sujets explicites (BookNow / on)
  ✓ STAGE — 3 Solution Aware
  ✓ PAIN/DESIRE — hook desire OK si cible stade 4
  ✓ SPECIFICITY — 1,2 M€ (chiffre), MVP (objet nommé)
  ✓ SOURCE — article de presse public
  ✓ VOIX — Alex peut le dire
  [V] "avec le MVP qu'on a codé" proche du verbatim interne Acme
  [P] 1,2 M€ sourçable
  VERDICT : ✅ validé pour production
```

---

*Framework issu de l'audit copywriter Council Acme (avril 2026). Voir `frameworks/03-copywriting-framework.md` pour le raisonnement complet.*
