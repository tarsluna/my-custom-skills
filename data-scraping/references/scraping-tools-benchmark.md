# Banc d'essai outils de scraping — résultats mesurés (référence Méthode nº2)

> 10 outils testés en parallèle par 11 sous-agents (worktrees isolés) sur le MÊME échantillon réel :
> 12 cliniques vétérinaires FR (raison sociale + ville). Chiffres MESURÉS sur des runs réels, pas théoriques.
> ~18 min, 543k tokens. Vérité terrain solide : les emails trouvés ont été confirmés par 4-6 outils indépendants.

## Classement (trié par perf réelle)

| # | Outil | Domaines /12 | Emails /12 | Vitesse (12) | Bloqué ? | Licence | Note |
|---|-------|--------------|------------|--------------|----------|---------|------|
| 1 | **API gouv + ddgs** | 7 (+1) | 4 | ~265 s | mineur (WAF, sleeps ddgs) | Etalab 2.0 + MIT | **8/10** |
| 1 | **SearXNG self-host** | 7 (9 large) | 5 | **83 s** | léger (config JSON) | AGPL-3.0 | **8/10** |
| 3 | **Scrapy** | 9* | 5 | **34 s** | oui (403 WAF ~15-20%) | BSD-3 | 7/10 |
| 4 | Crawlee-python | 7* | 4 | ~29 s crawl | oui (TLS FR) | Apache-2.0 | 7/10 |
| 5 | crawl4ai + Playwright | 8* (1 faux+ CA) | 5 | ~250 s | oui (Imperva) | Apache-2.0 | 6/10 |
| 6 | email-scraper + cfemail | — (n'en fait pas) | **6** | ~115 s | oui (Imperva) | MIT | 5/10 |
| 7 | ddgs (brave seul) | 4 | 5 | ~188 s | **sévère** (brave KO après 2 req) | MIT | 4/10 |
| 8 | slug + DNS heuristique | 1 | 0 | ~96 s | faux positifs massifs | maison | 2/10 |
| 9 | theHarvester | — (n'en fait pas) | 1 | ~244 s | sources free stériles, modules payants | GPL-2.0 | 2/10 |
| 10 | googlesearch-python | **0** | 0 | (cassé) | **Google a tué le HTML no-JS** | MIT | 1/10 |

\* Les "9/12", "8/12" de Scrapy/Crawlee/crawl4ai = domaines obtenus via WebSearch (outil agent) EN AMONT,
pas par l'outil lui-même. Ces outils sont des EXTRACTEURS, ils ne résolvent pas le domaine. WebSearch
n'est pas une brique de prod scriptable → en prod, la résolution vient de SearXNG/ddgs/API gouv.

## Gagnants par étape
- **Résolution domaine (name→domain)** : **API gouv (SIRENE) + SearXNG/ddgs**. La désambiguïsation SIRENE
  injecte ville/CP/adresse exacts → élimine les homonymes géographiques (crawl4ai a sorti une clinique de
  **Montréal** ; d'autres une de **Toulouse** au lieu de l'IDF). SearXNG = 0 rate-limit, pas de proxies.
- **Extraction email (domaine connu)** : **Scrapy** (scalable, 34s, BSD-3) ; email-scraper a le meilleur
  score brut (6/12, 86% sur domaines joignables) mais ne fait que l'extraction.

## Enseignements transversaux (à ne pas réapprendre)
1. **Le rendu JS n'apporte RIEN.** 4-5 des emails FR sont déjà dans le HTML statique, même sur Wix.
   Playwright/crawl4ai (250s, 260Mo Chromium) n'a débloqué aucun email qu'un `httpx+regex` ne prenait. → fallback only.
2. **Ne jamais prendre la 1ère URL.** ddgs/SearXNG remontent massivement des annuaires (pagesjaunes, infobel,
   veterinaires.org, monrendezvousveto, lefigaro, lagazettefrance…). Il FAUT scorer : blacklist + vérif ville/nom dans le titre.
3. **Cloudflare cfemail = inutile sur PME véto FR** (0/12 derrière Cloudflare ; elles sont sur OVH/Wanadoo/Wix).
   Le décodeur reste dans le code (gratuit, sert sur d'autres secteurs) mais n'attends rien dessus en véto.
4. **Plafond réel ~40% des PME n'ont PAS de site** (juste annuaires/SIREN). Domaine ~7-9/12 max, email ~5-6/12.
   Tout outil annonçant 12/12 ment. Pour 1757 : viser ~1000 domaines, ~700-750 emails.
5. **Filtrer les faux emails** : placeholders (`utilisateur@domaine.com`, `vous@exemple.com`), emails d'éditeurs
   de templates annuaires (`*@editeur-annuaire.fr`), emails de WAF (`*+waf@*`). Sans ça on livre du déchet.
6. **Blocages réels rencontrés** : WAF Imperva/Incapsula (403 sur certains sites — non contournable sans
   navigateur réel/proxy), certificats TLS FR cassés (curl `-k` passe, fetch refuse), sites parking/morts.

## Pièges d'install (machine de l'auteur)
- **2 interpréteurs Python** : forcer `/opt/homebrew/bin/python3.14` (sinon ModuleNotFoundError sur ddgs).
- PEP 668 : `pip install --break-system-packages <pkg>`.
- Ne pas exécuter depuis `/tmp` (un `inspect.py` parasite y shadow la stdlib).
- `pip install theHarvester` = STUB vide de 97Ko → cloner le repo Git à la place.
- `pip install googlesearch-python` → endpoint Google mort, échec SILENCIEUX (retourne [] sans erreur). À bannir.
- Scrapy 2.16 : utiliser `async def start(self)` (pas `start_requests`) sinon 0 requête.
- SearXNG : `format=json` désactivé par défaut (403) → l'activer dans settings.yml et remonter le conteneur.
- ⚠️ Installer ddgs bumpe `httpx` à 0.28.1 globalement → conflit annoncé avec supabase/gotrue/postgrest Python (sans rapport avec ce projet Node, mais à surveiller).

## Pipeline final recommandé (concret)
```
1. SIRENE   → recherche-entreprises.api.gouv.fr (HTTP, sans clé) : CP+commune+adresse+dirigeant exacts
2. SEARCH   → SearXNG self-host (docker, format=json) ; fallback ddgs (pip) ; fallback Serper (clé)
3. SCORE    → scoreDomainCandidate : rejet annuaires + vérif <title>/domaine contient commune OU nom
4. EMAIL    → Scrapy (async def start, AUTOTHROTTLE, conc 4-8) : home + /contact + /mentions-legales
5. CLEAN    → drop placeholders/éditeurs/WAF ; fallback www./http ; décodeur cfemail XOR (rare)
6. FALLBACK → curl -k puis Playwright headless en TOUT DERNIER recours (~15-20% des sites)
```
Implémenté dans le deal-sourcer : `src/sources/domain-finder.ts` (étapes 2-3), `src/sources/email-finder.ts`
(étapes 4-5), `src/enrich.ts` (orchestration), `npm run enrich`. Backends auto-sélectionnés via env
(`SEARXNG_URL` > ddgs > `SERPER_API_KEY`). Testé réel : une raison sociale + ville → le bon domaine officiel (annuaire #1 écarté par le scoring).
