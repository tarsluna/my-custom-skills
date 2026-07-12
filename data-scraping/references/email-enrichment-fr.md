# Référence — Enrichissement email pour PME françaises (open-source / low-cost)

> Recherche vérifiée (juin 2026, repos GitHub confirmés en direct). Cas de référence : enrichir
> 1757 PME FR avec dirigeant + email, en évitant les gros SaaS (Dropcontact/Hunter/Apollo).

## La vérité à dire au client d'emblée
**Aucune source publique FR ne contient l'email d'un dirigeant.** Ni l'API Recherche Entreprises,
ni SIRENE, ni BODACC, ni Infogreffe, ni le RNE/INPI. Le RNE donne nom + date de naissance du
dirigeant, jamais l'email. **L'email ne se trouve pas, il se RECONSTRUIT** : trouver le domaine →
extraire l'email public OU générer des patterns → vérifier. Un enrichissement FR à 100% n'existe pas
(réaliste : ~85-92% en hybride gratuit + low-cost).

Patterns FR dominants : `prenom.nom@` (~40%), `p.nom@` (~25%), `prenom@` (TPE/PME). 30-40% des
domaines sont en catch-all → fiabilité d'un email *deviné* dégradée.

## Le pipeline (4 étapes)

### Étape 0 — Nom du dirigeant (gratuit, déjà dans la méthode)
API Recherche Entreprises (`recherche-entreprises.api.gouv.fr`, ~7 req/s, sans clé) → SIREN, ville,
statut actif, **nom + prénom dirigeant**. C'est la source du nom.

### Étape 1 — Trouver le domaine (LE goulot d'étranglement)
Aucune base ne lie raison sociale → domaine. Options :
- **`ddgs`** (deedy5, ex-`duckduckgo_search`, MIT) — metasearch. Requête `"<raison sociale>" <ville>`,
  prendre 1er résultat non-annuaire (blacklist societe.com, pappers, pagesjaunes, linkedin…).
  ⚠️ throttle ~20-30 req/min/IP → étaler + délais aléatoires + proxies pour 1757.
- **SearXNG self-hosted** (Docker, "SerpAPI gratuit") = plus robuste.
- **Brave Search API** — 2000 req/mois gratuites (clé), suffit pour 1757 sur un mois.
- Taux de résolution réaliste : **~70-85%**.

### Étape 2 — Extraire l'email PUBLIC du site (la voie n°1, propre & gratuite)
Tout site pro FR DOIT afficher des mentions légales avec un contact (LCEN art. 6) → email rendu
public par l'entreprise elle-même. Une fois le domaine connu, le scraping vise des serveurs tous
différents → **risque de blocage quasi nul**, faisable en quelques heures (asyncio/Scrapy).
- **`email-scraper`** (kichik, PyPI) — gère mailto, base64/`atob()`, entités HTML. Le plus adapté.
- **`mhashirhassan22/Bulk-Email-Scraper`** — entrée = CSV de domaines, visite home+contact/about (= notre cas).
- **+10 lignes pour décoder Cloudflare email protection** (`data-cfemail`, simple XOR) — très répandu en FR.
- Respect `robots.txt` (stdlib `urllib.robotparser`). Priorité : mentions-légales > contact > home.
- Taux sur domaine résolu : **~80-90%**. Limite : emails souvent **génériques** (`contact@`, `info@`) —
  parfait pour cold B2B et le plus défendable RGPD, mais pas l'email perso du dirigeant.

### Étape 3 — Générer les patterns (si pas d'email public trouvé)
- **`batuhanaky/mailscout`** (MIT, ~82★) — génère ET vérifie SMTP, **détection catch-all native** (rare).
- Snippet **`Satys/python-email-permutator`** (pas de licence claire → recopier comme snippet, pas dépendance).

### Étape 4 — Vérifier
- **`JoshData/python-email-validator`** (Unlicense, ~1,4k★, très actif) — syntaxe + **MX**. Fiable
  partout, **sans port 25**. Le socle obligatoire.
- **`disposable-email-domains`** (CC0) + mailchecker — filtre jetables, 100% offline.
- SMTP réel (RCPT TO) : **`reacherhq/check-if-email-exists`** (Rust, le + sérieux, catch-all + greylisting
  retry — ⚠️ **AGPL**, piège si SaaS fermé) ou **`AfterShip/email-verifier`** (Go, MIT, plus simple).

### ⚠️ La limite du port 25 (à connaître absolument)
La vérif SMTP "vraie" ne marche que depuis une IP avec **port 25 sortant ouvert + reverse DNS propre +
bonne réputation**. Donc **jamais depuis un Mac, jamais depuis AWS/GCP/Azure** (port 25 bloqué en dur).
Seulement dégradé depuis un VPS OVH/Hetzner (port 25 ouvrable sur demande). Gmail/Yahoo + MX FR
(OVH/Gandi/Orange/Free) renvoient souvent `unknown`, et le catch-all (~30-40%) crée des faux positifs
structurels. → **En pratique : MX-only fiable partout (python-email-validator). Le SMTP full n'est
exploitable qu'avec un VPS dédié, et reste aveugle sur catch-all/Gmail.**

## Si un peu de budget — top 3 FR low-cost (pour ~2000 emails)
1. **Icypeas 🇫🇷** — ~19-39$ (~0,01-0,02$/email), facture uniquement le validé. Le moins cher au crédit. API partout.
2. **Enrow 🇫🇷** — ~24$/mois (24k crédits/an), API 50 req/s. Excellent rapport Q/P.
3. **Societeinfo 🇫🇷** — plus cher (~0,25→0,05€/crédit dégressif) mais **meilleure data légale FR**
   (licencié INPI/INSEE, 11M fiches SIRENE, 1 crédit = 1 contact). Pour SIREN+dirigeant+email générique fiable.

⚠️ Piège : Snov.io / FindThatLead = crédit pas cher mais **match FR faible** → coût réel/lead bien supérieur.
Pour 1757 PME tout-en-API : **plancher ~17-35$**. Le coût n'est pas l'enjeu — c'est devine-nominatif (Icypeas/Enrow)
vs légal-générique-fiable (Societeinfo).

## Recommandation finale (hybride, du gratuit au payant minimal)
- **Phase 1 (gratuit)** : API Recherche Entreprises (dirigeant) → `ddgs`/SearXNG (domaine) →
  `email-scraper`+Cloudflare decode (email public) → `python-email-validator` MX-only +
  `disposable-email-domains`. → **~970-1230 emails (55-70%), propres et légaux.**
- **Phase 2 (~10-20$)** : le reliquat (~530-790 PME) en API FR low-cost (Icypeas/Enrow). → couverture **~85-92%**.
- **Phase 3 (optionnel)** : Societeinfo pour l'email dirigeant fiable sur le sous-ensemble prioritaire.
- Laisser les 8-15% restants en "non trouvé" (sites sans email, emails en image, PME sans site).

## RGPD
Email pro nominatif = donnée personnelle même publique. Prospection B2B licite SI : collecte loyale
(mentions légales publiques = source la + défendable), objet = activité pro du destinataire, expéditeur
identifié, **opt-out dans chaque email**, conservation ≤3 ans après dernier contact, droit d'opposition.
Emails **génériques** (`contact@`/`info@`) = personne morale, hors donnée perso → cible la + sûre.
Tenir un registre de traitement. **Toujours privilégier générique > nominatif.**

## Repos GitHub (vérifiés, juin 2026)
| Repo | Rôle | Licence | État |
|---|---|---|---|
| `deedy5/duckduckgo_search` (`ddgs`) | résolution domaine (metasearch) | MIT | actif |
| `kichik` → PyPI `email-scraper` | extraction email d'une page | — | utilisable |
| `mhashirhassan22/Bulk-Email-Scraper` | batch CSV domaines → emails | — | utilisable |
| `JoshData/python-email-validator` | syntaxe + MX (socle) | Unlicense | très actif |
| `disposable-email-domains` | filtre jetables | CC0 | actif |
| `batuhanaky/mailscout` | génération + vérif SMTP + catch-all | MIT | petit/ok |
| `Satys/python-email-permutator` | patterns (snippet) | ⚠️ aucune | abandonné |
| `reacherhq/check-if-email-exists` | SMTP full (catch-all) | ⚠️ AGPL | sérieux |
| `AfterShip/email-verifier` | SMTP (Go) | MIT | actif |
| `laramies/theHarvester` | OSINT recon emails | — | très actif |
