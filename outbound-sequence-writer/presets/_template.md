# Preset <NOM DE LA BOÎTE>

> Copier ce fichier vers `presets/<slug>.md` (slug kebab-case) puis remplir tous les champs.
> Date de création : <YYYY-MM-DD>
> Sources : <URL landing, repo, docs internes, conversation avec founder…>

---

## Identification

```yaml
entreprise: "<Nom de la boîte qui ENVOIE les emails>"
resumeOffre: "<Quoi vous vendez, en 1 phrase>"
typeOffre: "<SaaS / Service / Hybride / Agence / Conseil>"
prix: "<Ex: 'à partir de 49€/mois', '690€ one-shot', 'sur devis'>"
```

## Promesse & différenciation

```yaml
promesse: "<La promesse principale — le résultat tangible>"
benefice1: "<Bénéfice 1>"
benefice2: "<Bénéfice 2>"
benefice3: "<Bénéfice 3>"
differenciants: |
  - <Pourquoi vous vs alternative A>
  - <Pourquoi vous vs alternative B>
preuves: |
  - <Logo client / cas / chiffre vérifiable 1>
  - <Logo client / cas / chiffre vérifiable 2>
  - <Testimonial 1 phrase>
```

## ICP(s)

> Un preset peut contenir plusieurs ICPs. Dans ce cas, le skill demandera lequel cibler avant d'écrire.

### ICP 1 — <Label court>

```yaml
cibleDescription: "<Persona en 1 phrase>"
cibleSecteur: "<Secteur ou verticale>"
cibleFonctions: "<Founder / CEO / CMO / Head of Growth / Directeur commercial…>"
cibleProblemes: |
  - <Douleur concrète 1>
  - <Douleur concrète 2>
  - <Douleur concrète 3>
cibleValeur: "<Ce qui les motive>"
cibleFreins: |
  - <Objection probable 1>
  - <Objection probable 2>
cibleMotivations: |
  - Rationnels : <…>
  - Émotionnels : <…>
```

### ICP 2 — <Label court> (optionnel, dupliquer si plusieurs)

(idem)

---

## CTA + parcours

```yaml
ctaType: "<reply / book / watch / register / download / audit>"
ctaExact: "<Phrase exacte du CTA>"
conversion: "<Métrique cible (taux de réponse, taux d'audit, taux de call)>"
destination: "<URL ou ressource>"
```

## Méta

```yaml
langue: "fr"     # ou "en"
objectif: "<génération de leads / réactivation / upsell / lancement>"
```

---

## Angles pré-définis

> 3 angles par défaut à proposer quand l'utilisateur demande une séquence sans préciser l'angle. Adapter selon ICP si plusieurs.

### Angle 1 — <Titre>

<1 phrase de positionnement. Framework recommandé. Cible parfaite.>

### Angle 2 — <Titre>

<idem>

### Angle 3 — <Titre>

<idem>

---

## Anti-patterns spécifiques

> Ce que la séquence ne doit JAMAIS dire / faire pour cette boîte (au-delà des anti-patterns universels du SKILL.md §8).

- ❌ <Claim à ne jamais faire>
- ❌ <Positionnement à éviter>
- ✅ <Préférence : "préférer X > Y">

---

## Subjects testés / à tester

> Liste de subjects qui marchent bien (à reprendre) et de subjects à itérer.

À reprendre :
- "<Subject 1>"
- "<Subject 2>"

À tester :
- "<Subject expérimental 1>"

---

## Provider par défaut

```yaml
provider_default: "<emelia / lemlist / smartlead / instantly / lgm / heyreach / apollo / woodpecker>"
provider_rationale: "<Pourquoi ce provider pour ce sender>"
```
