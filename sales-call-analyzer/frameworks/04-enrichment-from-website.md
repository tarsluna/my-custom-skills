# Framework 04 — Enrichment from Website

**Objectif** : compléter les champs critiques du brief qui n'étaient pas dans la transcription, en fetchant le site web du prospect via `WebFetch`.

**Règle** : **jamais inventer**. Si l'info n'est ni dans le call ni sur le site → marquer `needs_human_review: true` sur le champ et demander au user.

---

## 🎯 Quand déclencher l'enrichissement

Après avoir extrait tout ce qui est extractible de la transcription, si **un de ces champs critiques est vide** → enrichir via WebFetch :

**Critique (bloquant)** :
- `contact.email`
- `meta.company_legal_name` (raison sociale complète)
- `contact.address_line`, `contact.postal_code`, `contact.city`

**Important (fortement recommandé)** :
- `business.founded_year`
- `business.social_proof` (avis Google / Trustpilot)
- `business.geo_cities_covered`

**Nice-to-have** :
- SIRET (si visible en mentions légales)
- Nom complet du gérant (si différent de l'interlocuteur du call)

---

## 🔎 Déduction de l'URL du site

Si l'URL n'est pas fournie par le user, la déduire depuis la transcription :

1. Le prospect dit explicitement "mon site c'est X.com" → utiliser.
2. Nom société dominant → essayer dans l'ordre :
   - `https://{company-kebab}.com`
   - `https://{company-kebab}.fr`
   - `https://{company-kebab}-{city}.com`
   - `https://{company-kebab}{departement-number}.com` (ex : `example-client.com`)
3. Si rien ne marche, utiliser `WebSearch` avec `"{nom société} {ville} site officiel"`.

### Exemple Acme

Nom société : "Fermetures Acme", ville : Villexemple (00).

URLs tentées dans l'ordre :
1. `https://fermetures-acme.com` → test
2. `https://acme-fermetures.fr` → test
3. `https://example-client.com` → ✅ trouvé (c'est le bon)

---

## 📄 Pages à fetcher (dans cet ordre)

### 1. Page d'accueil `/`
Objectifs :
- Vérifier le nom société (titre de page, balise `<title>`)
- Choper les avis Google si widget présent
- Identifier le positionnement / année de création (souvent en hero ou about)

### 2. Page `/contact` ou `/nous-contacter`
Objectifs :
- Email de contact
- Téléphone
- Adresse complète
- Horaires (bonus)

### 3. Page `/mentions-legales` ou `/legal` ou `/cgv`
Objectifs :
- Raison sociale complète (ex : "ACME FERMETURES SARL")
- SIRET
- Capital social
- Nom du gérant / représentant légal (si différent)
- Adresse du siège social

### 4. Page `/a-propos` / `/about` / `/qui-sommes-nous`
Objectifs :
- Année de création (si pas en home)
- Histoire / ancienneté
- Taille équipe
- Géographie d'intervention

### 5. Page `/avis` ou widget Google embed
Objectifs :
- Note Google exacte (ex : 4.9/5)
- Nombre d'avis (ex : 120)

---

## 🛠️ Procédure WebFetch

Exemple pour Acme :

```
WebFetch(url="https://example-client.com/", prompt="Extract: company legal name, year founded, director name, email, phone, full address with postal code and city, Google reviews count and rating, geographic service area in km, list of services offered")
```

Répéter sur `/mentions-legales` et `/contact` si la home ne suffit pas.

**Timeout** : chaque fetch ~10-20s. Budget total pour enrichissement : max 4 fetches.

---

## 🧪 Matching des infos fetchées

Après fetch, mapper vers le schéma JSON :

| Info site | Champ JSON |
|---|---|
| Nom légal en mentions légales | `meta.company_legal_name` |
| Adresse siège | `contact.address_line` + `contact.postal_code` + `contact.city` |
| Email contact | `contact.email` |
| Téléphone fixe en header/footer | `contact.phone` (si absent du call) |
| "Depuis 1986" ou "40 ans d'expérience" | `business.founded_year`, `business.years_in_business` |
| Widget Google avis | `business.social_proof` |
| "Nous intervenons dans le département..." | `business.geo_cities_covered` |
| SIRET | `meta.siret` (ajout optionnel si présent) |

---

## 🚧 Cas particuliers

### Site inaccessible / 404
→ Fallback WebSearch : `"{company} {ville} mentions légales"` pour trouver via Pappers / Societe.com / Infogreffe.

### Site en construction ou one-pager minimaliste
→ Chercher la fiche Google Business Profile : `WebSearch("{company} {ville} google maps")`.

### Pas d'email public, uniquement formulaire de contact
→ Laisser `contact.email: null` avec `needs_human_review: true`. Ne pas inventer.

### Prospect indépendant sans site
→ Scanner LinkedIn public : `WebSearch("{prénom} {nom} linkedin {ville}")`. Ne jamais scraper — juste utiliser les infos publiques accessibles.

---

## ✅ Check-list post-enrichissement

- [ ] Tous les champs critiques remplis OU marqués `needs_human_review`
- [ ] `contact.email` renseigné (via call ou site)
- [ ] `meta.company_legal_name` complet (incluant forme juridique si trouvée : SARL, SAS, EURL…)
- [ ] `contact.address_line` + postal + ville cohérents avec ce que disait le prospect
- [ ] `business.founded_year` extrait (sinon calculé depuis `years_in_business`)
- [ ] `business.social_proof` rempli avec au moins 1 source

---

## 📌 Exemple complet Acme (enrichissement)

**Avant enrichissement** (champs manquants après Phase 2) :
- `contact.email` → manquant
- `meta.company_legal_name` → "Fermetures Acme" (peut-être incomplet)
- `business.social_proof` → "120 avis Google 4.9/5" (mentionné dans le call → OK)

**Fetch** :
```
WebFetch("https://example-client.com/", ...)
WebFetch("https://example-client.com/contact", ...)
WebFetch("https://example-client.com/mentions-legales", ...)
```

**Après enrichissement** :
- `contact.email` → récupéré sur /contact
- `meta.company_legal_name` → "Fermetures Acme SARL" (depuis mentions légales)
- Tous les autres champs confirmés ou complétés

Brief prêt pour génération.
