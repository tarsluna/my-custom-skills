---
name: cold-call-expert
description: Génère des scripts de cold call B2B world-class pour vendre du high-ticket service (3-15k€) à des fondateurs d'agences, consultants, cabinets de conseil. Calibré sur Cold Calling Sucks (Farrokh/Cegelski 2024), Josh Braun, 30MPC, Voss, Sandler, SPIN, Sales Odyssey FR, Modjo, Enzo Colucci, Gong Labs 90 380 cold calls. Use when the user asks to "write a cold call script", "écrire un script de cold call", "script de prospection téléphonique", "cold call pour {offre}", "génère un script d'appel à froid". La feature SaaS live est exposée dans your-app.example.com → /client/sales/cold-call-script.
---

# Cold Call Script Expert

Skill méta qui consolide la recherche marché complète sur le cold call B2B
services et l'expose en :

1. **Corpus baked** → `output/cold-call-expertise.md` (synthèse en 14 sections)
2. **System prompt** intégré dans la feature SaaS the platform
   (`app/apps/web/src/lib/cold-call-script-writer/script-prompt.ts`)
3. **UI live** dans l'espace client : `/client/sales/cold-call-script`
   (à côté de la carte Sales Call Analyzer)

## Status

**✅ v1.0 — 2026-05-23 — En production**
- [x] Recherche corpus (5 sous-agents parallèles) → `research/01..05.md`
- [x] Synthèse → `output/cold-call-expertise.md`
- [x] System prompt expert → encodé dans le SaaS (`script-prompt.ts`)
- [x] API + UI Next.js shippées sur main + Vercel
- [x] Migration Supabase 033 — **à appliquer manuellement** (cf. `APPLY.md` du repo)

## Architecture

```
SKILL.md                                     ← ce fichier
├── research/
│   ├── 01-youtube-channels.md              ← 15 chaînes FR + EN
│   ├── 02-books-and-courses.md             ← 15 livres + formations
│   ├── 03-top-practitioners.md             ← 14 practitioners + 10 podcasts
│   ├── 04-frameworks-b2b-services.md       ← 15 frameworks documentés
│   └── 05-objections-gatekeeper-voicemail.md ← 22 objections + gatekeepers + VM
└── output/
    └── cold-call-expertise.md              ← corpus consolidé (source de vérité)
```

## Doctrine clé (extrait — voir corpus pour version complète)

1. Context-first > Permission générique
2. Problème > Pitch (Gong : +3x conversion avec problem language)
3. Mr. Miyagi sur les objections (30MPC)
4. Single CTA = book discovery 30-45 min
5. 15 secondes pour gagner le droit de continuer
6. Tonalité = 70% du résultat (Voss)
7. 1 résultat max, daté et nommé
8. Esquiver le prix en cold call
9. Anti-patterns interdits ("Comment allez-vous ?", "Est-ce un bon moment ?")
10. Peer-context > generic personalization

## Combos par tone (utilisés par CCSW)

- **direct_sec** → PVC + Pattern Interrupt + Close direct
- **consultatif_pro** → Problem-Centric + SPIN + Close consultatif
- **curiosite_doux** → Permission-Based Braun + Curiosity gap + Mr. Miyagi
- **referral_chaleureux** → Heard the name (Farrokh) + Social proof + Close chaleureux

## Re-bake périodique

Si nouvelles sources majeures sortent (ex: nouveau livre Cegelski, gros pivot
Josh Braun) → rerunner le pipeline :

1. Mettre à jour les prompts des 5 sous-agents
2. Relancer en parallèle via Agent tool
3. Régénérer `output/cold-call-expertise.md`
4. Updater le `SYSTEM_PROMPT` dans `script-prompt.ts`
5. Bumper la version SKILL (v1.1, v1.2…)

## Tags
#leadgen #cold-call #outbound #sales #b2b-services #live
