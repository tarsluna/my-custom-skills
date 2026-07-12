# Framework 05 — Bibliothèque de FORMATS / CONCEPTS natifs (réutilisable, client-agnostic)

> Pourquoi ce framework : le framework `01-art-direction-system` couvre les **styles de design** (éditorial, dataviz, typo…) — mais sur Meta 2026, ce sont souvent les **formats natifs / scroll-stopping** (UGC, screenshots, advertorial, pattern-interrupt) qui surperforment le « beau branding ». Une erreur fréquente = livrer 20 créatives qui se ressemblent toutes. Ce framework fournit une **banque de ~14 concepts radicalement différents**, chacun avec un prompt-template paramétrable, pour **varier les formats** d'un pack et d'un client à l'autre.

**Comment l'utiliser :** dans la variation matrix (`frameworks/03`), piochez 8-12 concepts DISTINCTS ci-dessous (pas 12 variations du même). Remplacez les placeholders. Le **branding est volontairement léger** sur les formats natifs (logo discret ou absent) — c'est ce qui les rend crédibles. Génération recommandée : **GPT Image 2** (`gpt_image_2`, quality `high`, 2k) — excellent rendu de texte + UI + screenshots. Ratios CLI autorisés : `1:1, 4:3, 3:4, 16:9, 9:16, 3:2, 2:3` (⚠️ **pas de 4:5** en CLI → utiliser `3:4` pour le feed).

## Placeholders
- `{BRAND}` — nom de marque (ou **vide** pour les formats natifs où l'on ne veut pas brander).
- `{OFFER}` — l'offre / le lead magnet (ex. « diagnostic gratuit », « audit », « rapport »).
- `{ICP}` — la cible (ex. « entrepreneurs en ligne », « e-commerçants », « coachs »).
- `{HOOK_FR}` — l'accroche en français (1re ligne, choc/curiosité).
- `{LINE_FR}` — une ligne de soutien.
- `{CTA_FR}` — le call-to-action en MAJUSCULES (ex. « FAIRE LE DIAGNOSTIC »).
- `{PRIMARY_HEX}` / `{ACCENT_HEX}` — couleurs de marque (pour les rares éléments brandés : logo, CTA chip).
- `{LANG}` — langue (défaut français, accents parfaits).

> **Garde-fou texte IA** : toujours finir le prompt par `ALL embedded text in FLAWLESS {LANG}, correct accents, perfectly legible, no spelling mistakes, no gibberish.` Auditer chaque sortie (lettres parasites, accents).
> **Compliance finance/santé/$$** : pour les niches sensibles, bannir gains garantis, avant/après chiffrés, « 0 % / tu paies trop » (personal-attributes Meta). Cadrer en éducation / outil / témoignage d'expérience.

---

## 1. NOTE iOS (Notes app) — *organique, low-fi, confession*
**Quand :** confession/leçon personnelle, « ce que j'aurais aimé savoir », listes d'erreurs. **Pourquoi :** ressemble à un screenshot perso partagé, zéro feel pub → thumb-stop + confiance.
**Prompt :** `A realistic iOS NOTES APP screenshot, authentic and low-fi, white note background with the iOS Notes top bar and toolbar icons. A typed {LANG} personal note titled «{HOOK_FR}» followed by a short bullet list: «– {LINE_FR}», «– {LINE_FR}», «– {LINE_FR}». Looks like a personal screenshot shared organically — NOT an ad. Fills the full frame, no border. ALL text in FLAWLESS {LANG}…`
**Ratio :** 3:4 / 9:16. **Branding :** aucun (ou nom cité en passant dans le texte).

## 2. ARTICLE / ADVERTORIAL — *éditorial, réchauffe le cold, safe compliance*
**Quand :** sujet à éduquer, high-ticket cold. **Pourquoi :** crédibilité presse, angle éducatif (le plus conforme), convertit le froid.
**Prompt :** `A realistic screenshot of an online news/magazine ARTICLE page in {LANG} — clean white background, real editorial layout: serif headline, byline 'Par la rédaction · {RUBRIQUE}', a small article hero photo, two short body paragraphs, and a highlighted call-out box. Headline: «{HOOK_FR}». Sub: «{LINE_FR}». Looks like a NATIVE article, not an ad. Optional small '{BRAND}' mention in the box. Fills frame…`
**Ratio :** 3:4 / 9:16. **Branding :** discret.

## 3. iMESSAGE / CONVERSATION — *preuve sociale conversationnelle*
**Quand :** recommandation entre pairs, objection→réponse. **Pourquoi :** ultra-natif, on lit une « vraie » conversation, recommandation implicite.
**Prompt :** `A realistic iMessage conversation screenshot on a smartphone, authentic native look, white background, grey + blue bubbles, iOS status bar. Two {ICP} texting in {LANG}: grey «{HOOK_FR}», blue «{LINE_FR} 👌», grey «Tu me passes le lien ?». Casual, real, scroll-stopping. Fills frame…`
**Ratio :** 3:4 / 9:16. **Branding :** aucun (nom cité dans une bulle max).

## 4. TWEET / X SCREENSHOT — *pattern-interrupt, punchline*
**Quand :** opinion clivante/contre-intuitive, statement choc. **Pourquoi :** format social reconnu, lecture instantanée, peu coûteux à décliner en volume.
**Prompt :** `A realistic tweet / X post screenshot card on a clean light background. A {LANG} tweet from a credible {ICP} account: round avatar, display name, @handle. Tweet text: «{HOOK_FR}». Small reply / repost / like counts. Native social, pattern-interrupt…`
**Ratio :** 1:1 / 3:4. **Branding :** aucun.

## 5. UGC SELFIE / TALKING-HEAD (statique) — *authenticité créateur*
**Quand :** témoignage, « j'ai testé », autorité accessible. **Pourquoi :** format le plus « survivant » 2026 ; visage humain = confiance, désamorce la peur sur sujets sensibles.
**Prompt :** `An authentic UGC-style SELFIE photo (slightly imperfect phone-camera look, NOT polished studio): a credible {ICP}, natural setting (home desk / café), natural window light. A bold caption bar overlay near the top (white text on a semi-transparent black strip): «{HOOK_FR}». A burned-in subtitle bar near the bottom: «{LINE_FR}». Looks like a real creator ad. FLAWLESS {LANG}…`
**Ratio :** 3:4 (feed) + 9:16 (Reels). **Branding :** aucun.

## 6. PORTRAIT AUTORITÉ + lower-third — *expert / founder*
**Quand :** crédibilité, offre conseil/expertise, sujet anxiogène. **Pourquoi :** autorité rassurante, « une vraie personne sérieuse derrière l'offre ».
**Prompt :** `A premium yet authentic PORTRAIT of a credible {EXPERT_ROLE} (sober attire, trustworthy, slight warm smile) in a refined office, looking at camera, natural light, shallow depth of field, realistic photography (not over-retouched). A clean lower-third caption: «{HOOK_FR}». A small {ACCENT_HEX} logo + name chip «{BRAND} · {TAGLINE}». Reassuring authority…`
**Ratio :** 3:4 / 1:1. **Branding :** léger (chip lower-third).

## 7. POV (Reels/Story vertical) — *immersion 2e personne*
**Quand :** prise de conscience, « POV : tu réalises que… ». **Pourquoi :** la 2e personne projette le viewer dans la scène ; natif Reels.
**Prompt :** `A vertical 9:16 UGC STORY/Reels still, authentic phone-camera look: a {ICP} POV in a real setting, natural light, candid. Top caption (white on subtle dark strip): «POV : {HOOK_FR}». A burned-in subtitle lower third, and an {ACCENT_HEX} CTA pill at the bottom: «{CTA_FR}». Native Reels feel. FLAWLESS {LANG}…`
**Ratio :** 9:16. **Branding :** CTA pill seulement.

## 8. LISTICLE — *curiosité spécifique, CTR élevé*
**Quand :** « 3 erreurs / 3 leviers / 5 raisons ». **Pourquoi :** curiosité quantifiée, scannable, porte d'entrée vers l'advertorial.
**Prompt :** `A native-looking LISTICLE ad on a soft off-white background. Bold {LANG} headline: «{HOOK_FR}» (e.g. «3 {THINGS} que {ICP} ignorent»). Three numbered rows (1,2,3), each a short line with a small {ACCENT_HEX} check icon: «1. {LINE_FR}», «2. {LINE_FR}», «3. {LINE_FR}». Optional small {BRAND} logo bottom. Editorial, curiosity-driven, very readable…`
**Ratio :** 3:4 / 9:16. **Branding :** discret.

## 9. MOCKUP PRODUIT / LEAD-MAGNET sur téléphone — *matérialise l'outil*
**Quand :** quiz, rapport, app, audit. **Pourquoi :** rend l'offre tangible, promet un OUTIL (pas un gain) → très conforme.
**Prompt :** `A realistic 3D smartphone mockup held in a hand, centered, soft neutral studio background with a subtle {ACCENT_HEX} gradient. The phone screen shows {PRODUCT_UI} (e.g. a quiz / report app screen with {BRAND} branding). Bold {LANG} caption above the phone: «{HOOK_FR}». An {ACCENT_HEX} CTA chip below: «{CTA_FR}». Clean app/product ad…`
**Ratio :** 3:4 / 1:1. **Branding :** présent (c'est le produit).

## 10. TÉMOIGNAGE CARD — *preuve sociale (sur l'expérience)*
**Quand :** rassurer, lever l'objection confiance. **Pourquoi :** levier n°1 du high-ticket. ⚠️ témoignage sur **l'expérience/clarté**, jamais sur un montant gagné.
**Prompt :** `A clean premium TESTIMONIAL card on an off-white background with subtle {PRIMARY_HEX} / {ACCENT_HEX} accents. A {LANG} client quote in elegant serif: «{HOOK_FR}». Below: a small round avatar, «{NAME} · {ICP}», and five {ACCENT_HEX} stars. Small {BRAND} logo corner. Trust-focused, NO money figures…`
**Ratio :** 3:4 / 1:1. **Branding :** léger.

## 11. INFOGRAPHIE ÉDUCATIVE « 1 frame » — *autorité pédagogique*
**Quand :** expliquer un mécanisme. **Pourquoi :** installe l'expertise, format gagnant en finance/B2B, zéro promesse.
**Prompt :** `A clean minimal EDUCATIONAL infographic on a light background, premium and simple. {LANG} title: «{HOOK_FR}». A simple 3-step horizontal diagram with thin {ACCENT_HEX} connectors and small line icons, each box a short label: «{LINE_FR}» → «{LINE_FR}» → «{LINE_FR}». Subtle {PRIMARY_HEX}/{ACCENT_HEX}, small {BRAND} logo. Authority/education, no promise…`
**Ratio :** 3:4 / 1:1. **Branding :** léger.

## 12. BOLD STAT / DATA-VIZ — *hook chiffré (contexte)*
**Quand :** 1er frame puissant. **Pourquoi :** un gros chiffre stoppe le scroll. ⚠️ **stat de contexte/marché**, jamais un gain perso garanti.
**Prompt :** `A clean bold DATA-VIZ ad on a light background. A large {ACCENT_HEX} CONTEXT statistic: «{HOOK_FR}» (a market/category stat, not a personal-gain claim). A simple elegant donut or bar chart beside it. {LANG} subhead: «{LINE_FR}». Small {BRAND} logo, {ACCENT_HEX} CTA chip «{CTA_FR}»…`
**Ratio :** 3:4 / 1:1. **Branding :** léger.

## 13. POST ORGANIQUE NATIF (Facebook/IG feed) — *faux post boosté*
**Quand :** cold, créateur réel. **Pourquoi :** native feel + crédibilité créateur ; on dirait un post recommandé, pas une pub.
**Prompt :** `A realistic FACEBOOK feed POST screenshot (native, not a polished ad): a round profile photo + name «{AUTHOR}» + a small 'Suggéré'/'Sponsorisé' tag, a {LANG} text post: «{HOOK_FR} {LINE_FR} 👇», then a link-preview card titled «{OFFER} — {BRAND}» with a small thumbnail. Looks organic. FLAWLESS {LANG}…`
**Ratio :** 3:4 / 1:1. **Branding :** dans le link preview.

## 14. PATTERN-INTERRUPT TEXTE CHOC (« visual statement ») — *typo plein cadre*
**Quand :** déclaration brutale/contre-intuitive. **Pourquoi :** lecture < 1 s, thumb-stop max, décline en volume à bas coût.
**Prompt :** `A bold full-bleed TYPOGRAPHIC statement on a solid {PRIMARY_HEX} background. Huge {LANG} sentence in a strong font: «{HOOK_FR}», with one key phrase highlighted in {ACCENT_HEX}. Minimal, high-contrast, lots of negative space. Optional tiny {BRAND} logo corner…`
**Ratio :** 1:1 / 3:4. **Branding :** minuscule ou absent.

---

## Règle d'or de DIVERSITÉ (à appliquer à chaque pack)
Un pack performant **mélange** : 2-3 natifs (notes/iMessage/tweet/post), 2-3 UGC/portrait, 1-2 advertorial/listicle, 1 mockup produit, 1 témoignage, 1-2 éducatif/dataviz, 1 pattern-interrupt. **Jamais 12 variations du même style.** Décliner les gagnants en 4-6 variantes (hook/visuel) APRÈS le 1er test, pas avant.

## Bonnes pratiques de format technique (rappel)
- **2 crops minimum** : `3:4` (feed) + `9:16` (Reels/Story).
- **Hook dans le 1er frame / la 1re ligne** (avant « voir plus »), idée unique par créa.
- **Texte burn-in** (85 % regardent sans son), gros et lisible thumbnail.
- **Cible hook rate 25-30 %** ; itérer sur les survivants.
- **GPT Image 2** = défaut (texte/UI/screenshots). Auditer chaque PNG (texte IA, accents, mains, logo halluciné).
