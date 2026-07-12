# Prompt Template — Invoquer `sales-call-analyzer`

Copie-colle l'un des prompts ci-dessous dans Claude Code pour lancer le skill sur une nouvelle transcription.

---

## 🧪 Prompt minimal (transcription sur disque)

```
Analyse l'appel de vente {client} en lisant la transcription située à {chemin_absolu_transcription}. Produis brief-output.json + brief-output.md dans projects/{client_slug}/00-sales-brief/.
```

**Exemple Acme** :
```
Analyse l'appel de vente Prénom Acme en lisant la transcription située à ~/Desktop/appel-acme-2026-04-21.txt. Produis brief-output.json + brief-output.md dans projects/acme/00-sales-brief/.
```

---

## 🧪 Prompt avec transcription collée directement

```
Analyse l'appel de vente {client}. Voici la transcription brute :

---
{coller la transcription ici}
---

Produis brief-output.json + brief-output.md dans projects/{client_slug}/00-sales-brief/.
```

---

## 🧪 Prompt avec enrichissement site explicite

```
Analyse l'appel de vente {client}. Transcription : {chemin}. Site web du prospect : {url_site}. 
Enrichis les champs manquants (email, raison sociale complète, avis Google) depuis le site.
Produis brief-output.json + brief-output.md dans projects/{client_slug}/00-sales-brief/.
```

**Exemple Acme enrichi** :
```
Analyse l'appel de vente Prénom Acme. Transcription : ~/Desktop/appel-acme.txt. Site : https://example-client.com. Enrichis email + mentions légales. Produis brief-output.json + brief-output.md dans projects/acme/00-sales-brief/.
```

---

## 🧪 Prompt pour chaînage vers le skill devis

```
Analyse l'appel de vente {client} (transcription : {chemin}). Après avoir produit le brief JSON + MD, chaîne immédiatement avec devis-vercel-generator pour générer la landing page de devis personnalisée.
```

---

## 🔧 Variables à remplacer

| Variable | Signification | Exemple |
|---|---|---|
| `{client}` | Nom usuel du prospect | `Prénom Acme` |
| `{client_slug}` | Slug kebab-case pour le path | `acme` |
| `{chemin_absolu_transcription}` | Path absolu du .txt / .vtt / .md | `~/Desktop/appel.txt` |
| `{url_site}` | URL racine du site prospect | `https://example-client.com` |

---

## 📌 Ce que le skill va faire

1. Lire la transcription (ou la prendre collée).
2. Appliquer les 4 frameworks :
   - `01-dream-vs-objection-framework.md` → extraire headline hook + 3 bullets "Fini les"
   - `02-voice-of-customer-extraction.md` → vocabulaire industrie + ICP + pricing
   - `03-dossier-facts-checklist.md` → tous les faits société
   - `04-enrichment-from-website.md` → WebFetch si champs critiques manquent
3. Remplir `templates/brief-output.json` avec toutes les extractions.
4. Générer une version markdown human-readable.
5. Valider les 7 quality gates avant livraison.
6. Sauvegarder dans `projects/{client_slug}/00-sales-brief/`.
7. Retourner un résumé au user (extractions clés + statut gates).
