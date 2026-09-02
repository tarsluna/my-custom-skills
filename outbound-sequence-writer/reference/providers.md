# Providers outbound — syntaxe des merge tags

Référence complète des 8 providers (syntaxe officielle de chaque outil, vérifiée dans leur doc). Utilise **exactement** la syntaxe du provider choisi.

## Table des 8 providers

### 1. Emelia

- **Casse :** camelCase
- **Wrap :** `{{ ... }}` (double brace)
- **Spintax :** ✓ — `{Hello|Hi|Hey}`
- **Fallback :** ✓ — `{{firstName | "there"}}`

Variables clés :
- `{{firstName}}` — first name
- `{{lastName}}` — last name
- `{{companyName}}` — company
- `{{jobTitle}}` — job title
- `{{email}}` — email
- `{{linkedinUrl}}` — LinkedIn URL
- `{{city}}` — city

### 2. Lemlist

- **Casse :** camelCase
- **Wrap :** `{{ ... }}`
- **Spintax :** ✓
- **Fallback :** ✓
- **Spécial :** `{{icebreaker}}` — généré par Lemlist AI pour la première ligne

Variables :
- `{{firstName}}`, `{{lastName}}`, `{{companyName}}`, `{{jobTitle}}`
- `{{icebreaker}}` — opener AI personnalisé Lemlist
- `{{linkedinUrl}}`, `{{city}}`

### 3. Smartlead

- **Casse :** snake_case
- **Wrap :** `{{ ... }}`
- **Spintax :** ✓
- **Fallback :** ✗

Variables :
- `{{first_name}}`, `{{last_name}}`, `{{company_name}}`, `{{job_title}}`
- `{{email}}`, `{{linkedin_url}}`, `{{city}}`, `{{website}}`

### 4. Instantly

- **Casse :** camelCase
- **Wrap :** `{{ ... }}`
- **Spintax :** ✓
- **Fallback :** ✓
- **Spécial :** `{{personalization}}` — variable libre custom (ligne perso)

Variables :
- `{{firstName}}`, `{{lastName}}`, `{{companyName}}`, `{{jobTitle}}`
- `{{personalization}}` — champ libre pré-rempli (icebreaker, observation, etc.)
- `{{email}}`, `{{linkedinUrl}}`

### 5. La Growth Machine (LGM)

- **Casse :** TitleCase
- **Wrap :** `% ... %` (percent-wrapped, **pas** des braces)
- **Spintax :** ✗
- **Fallback :** ✗

Variables :
- `%FirstName%`, `%LastName%`, `%CompanyName%`, `%JobTitle%`
- `%Email%`, `%LinkedinUrl%`, `%City%`

### 6. HeyReach

- **Casse :** camelCase
- **Wrap :** `{ ... }` — **SINGLE brace** (attention, piège)
- **Spintax :** ✗
- **Fallback :** ✗

Variables :
- `{firstName}`, `{lastName}`, `{companyName}`, `{jobTitle}`
- `{linkedinUrl}`, `{industry}`

### 7. Apollo.io

- **Casse :** snake_case
- **Wrap :** `{{ ... }}`
- **Spintax :** ✗
- **Fallback :** ✗

Variables :
- `{{first_name}}`, `{{last_name}}`, `{{organization_name}}`, `{{title}}`
- `{{email}}`, `{{linkedin_url}}`

### 8. Woodpecker

- **Casse :** UPPERCASE_SNAKE
- **Wrap :** `{{ ... }}`
- **Spintax :** ✓
- **Fallback :** ✓ — `{{FIRST_NAME|there}}`

Variables :
- `{{FIRST_NAME}}`, `{{LAST_NAME}}`, `{{COMPANY}}`, `{{TITLE}}`
- `{{EMAIL}}`, `{{LINKEDIN_URL}}`, `{{INDUSTRY}}`

---

## Règle pour le LLM

> Tu DOIS utiliser les merge tags ci-dessus EXACTEMENT tels qu'écrits.
> Pas de variation de casse, de séparateur, ou de braces.
> Si l'utilisateur n'a pas précisé le provider, demande-lui avant de générer.

---

## Cheatsheet spintax (Emelia / Lemlist / Smartlead / Instantly / Woodpecker)

Permet de générer N variantes d'une même phrase pour échapper aux filtres spam.

```
{Hello|Hi|Hey} {{firstName}}, {quick thought|short question|noticed something}…
```

À utiliser dans :
- Le **subject** (1-2 variantes max, pour pas casser la lisibilité)
- La **première phrase du body** (la plus répétée d'un envoi à l'autre)
- La **signature** ("Cheers" / "Best" / "Talk soon")

Ne pas mettre de spintax dans :
- Les chiffres / faits / preuves
- Le CTA
- Les merge tags eux-mêmes

---

## Cheatsheet fallback (Emelia / Lemlist / Instantly / Woodpecker)

Si la variable est vide, affiche un fallback :

```
{{firstName | "there"}}
{{companyName | "your team"}}
{{FIRST_NAME|there}}      ← Woodpecker, pas d'espace autour du |
```

À utiliser **systématiquement** sur `firstName` et `companyName` (les deux plus enrichis et donc les plus à risque d'être vides).
