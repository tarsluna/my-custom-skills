# 05 — Format Specs : Specifications Techniques par Placement Meta

Reference des specifications techniques officielles Meta pour chaque placement publicitaire. A utiliser pour configurer les frames Figma et les exports.

---

## Specs par placement

### Images statiques

| Placement | Dimensions (px) | Ratio | Max file size | Format fichier | Notes |
|-----------|-----------------|-------|---------------|----------------|-------|
| Feed image | 1080 x 1080 | 1:1 | 30 MB | JPG, PNG | Format le plus polyvalent |
| Feed image (paysage) | 1200 x 628 | 1.91:1 | 30 MB | JPG, PNG | Moins d'engagement que 1:1 |
| Feed image (portrait) | 1080 x 1350 | 4:5 | 30 MB | JPG, PNG | Prend plus de place dans le feed |
| Story / Reel image | 1080 x 1920 | 9:16 | 30 MB | JPG, PNG | Full screen vertical |
| Carousel slide | 1080 x 1080 | 1:1 | 30 MB / slide | JPG, PNG | 2 a 10 slides |
| Right column (desktop) | 1200 x 1200 | 1:1 | 30 MB | JPG, PNG | Petit format, texte gros |

### Videos

| Placement | Dimensions (px) | Ratio | Max file size | Duree | Codec | Notes |
|-----------|-----------------|-------|---------------|-------|-------|-------|
| Feed video | 1080 x 1080 | 1:1 | 4 GB | 1s - 241 min | H.264, MP4 | 15-60s recommande |
| Feed video (portrait) | 1080 x 1350 | 4:5 | 4 GB | 1s - 241 min | H.264, MP4 | Plus immersif |
| Story / Reel video | 1080 x 1920 | 9:16 | 4 GB | 1s - 120s | H.264, MP4 | 15-30s optimal |
| In-stream video | 1280 x 720 | 16:9 | 4 GB | 5s - 600s | H.264, MP4 | Pre-roll / mid-roll |
| Carousel video slide | 1080 x 1080 | 1:1 | 4 GB / slide | 1s - 240s | H.264, MP4 | Mix image + video possible |

### Specs video detaillees

| Parametre | Valeur recommandee |
|-----------|--------------------|
| Codec video | H.264 |
| Codec audio | AAC, 128kbps+ |
| Framerate | 30fps (stable, pas de VFR) |
| Bitrate video | 8-12 Mbps pour 1080p |
| Bitrate audio | 128-256 kbps |
| Conteneur | MP4 |
| Vignette (thumbnail) | Extraite automatiquement ou uploadee manuellement (1080x1080 ou 1080x1920) |

---

## Zones safe par placement

### Feed (1080 x 1080)

```
┌─────────────────────────────────┐
│  ↕ 120px margin top              │
│  ↔ 120px margin left/right       │
│                                 │
│     ┌─────────────────────┐     │
│     │                     │     │
│     │    SAFE TEXT ZONE   │     │
│     │    840 x 840px      │     │
│     │                     │     │
│     └─────────────────────┘     │
│                                 │
│  ↕ 120px margin bottom           │
└─────────────────────────────────┘
```

### Story / Reel (1080 x 1920)

```
┌─────────────────────────────────┐
│                                 │
│  ⚠ TOP SAFE ZONE: 250px         │  <- UI: nom du compte, icones
│  ⚠ Do not put critical content  │
│                                 │
├─────────────────────────────────┤
│  ↔ 80px margins left/right       │
│                                 │
│     ┌─────────────────────┐     │
│     │                     │     │
│     │   CONTENT ZONE      │     │
│     │   920 x 1320px      │     │
│     │                     │     │
│     └─────────────────────┘     │
│                                 │
├─────────────────────────────────┤
│                                 │
│  ⚠ BOTTOM SAFE ZONE: 350px      │  <- UI: CTA natif, swipe, texte
│  ⚠ Do not put critical content  │
│                                 │
└─────────────────────────────────┘
```

### Carousel (1080 x 1080 par slide)

Memes zones safe que le Feed (120px margins), avec en plus :
- **Edge left (40px)** : zone ou la slide precedente est encore visible
- **Edge right (40px)** : zone ou la slide suivante est deja visible
- Eviter le texte critique dans les 40px lateraux

---

## Export Settings Figma

### Pour images statiques

| Setting | Valeur | Raison |
|---------|--------|--------|
| Format | PNG | Qualite maximum, pas de compression lossy |
| Scale | 2x (export a 2160px pour 1080px frame) | Super-resolution, Meta down-scale automatiquement |
| Color profile | sRGB | Standard web, Meta ne supporte pas P3 |
| Transparence | Desactivee | Meta n'accepte pas les PNG avec alpha |

**Alternative compression** : JPG a 95% de qualite si le fichier PNG depasse 10 MB. La difference visuelle est negligeable a 95%.

### Pour video frames (export vers montage)

| Setting | Valeur | Raison |
|---------|--------|--------|
| Format | PNG | Pas de compression inter-frames |
| Scale | 1x (1080px natif) | Le montage video ne beneficie pas du 2x |
| Color profile | sRGB | Coherence avec le montage |
| Sequence | Frame-by-frame si animation | Nomage: frame-001.png, frame-002.png... |

**Assembly video** : les frames exportees depuis Figma sont assemblees dans CapCut, Premiere Pro, After Effects, ou DaVinci Resolve. Figma ne produit pas de video nativement.

### Pour composants Figma (partage equipe)

| Setting | Valeur |
|---------|--------|
| Format | Figma natif (.fig) |
| Publish | Publier comme composant dans la Team Library |
| Naming | `[Client] / Meta Ads / [Format] / [Variant]` |
| Description | Inclure l'archetype couleur et les fonts utilisees |

---

## Tableau recapitulatif rapide

A copier-coller dans le brief pour rappel :

```
FEED IMAGE     : 1080x1080  | 1:1   | JPG/PNG | 30MB max
FEED VIDEO     : 1080x1080  | 1:1   | MP4     | 4GB max  | 15-60s
STORY/REEL IMG : 1080x1920  | 9:16  | JPG/PNG | 30MB max
STORY/REEL VID : 1080x1920  | 9:16  | MP4     | 4GB max  | 15-30s
CAROUSEL       : 1080x1080  | 1:1   | JPG/PNG | 30MB/slide | 2-10 slides
IN-STREAM      : 1280x720   | 16:9  | MP4     | 4GB max  | 5-600s
```

---

## Notes sur la compression Meta

Meta recompresse systematiquement les images et videos uploadees. Pour minimiser la degradation :

1. **Uploader en PNG 2x** (2160px) : Meta downscale proprement, le resultat est meilleur qu'un upload a 1080px
2. **Ne pas pre-compresser** : un JPG 70% uploade sur Meta sera recompresse une seconde fois, resultat floute
3. **Eviter le texte fin** (< 18px rendu final) : la compression Meta degrade le texte fin en premier
4. **Les gradients subtils** peuvent montrer du banding apres compression : utiliser du grain/noise overlay (2-3%) pour masquer
5. **Les flat colors** (aplats) resistent mieux a la compression que les gradients ou les photos tres detaillees

---

## Checklist format avant export

- [ ] Frame au bon ratio (verifier 1:1 ou 9:16 exactement)
- [ ] Dimensions en px (pas en points, pas en rem)
- [ ] Export en sRGB (pas P3, pas Adobe RGB)
- [ ] PNG @2x pour images statiques
- [ ] PNG @1x pour frames video
- [ ] JPG 95% si PNG > 10 MB
- [ ] Pas de transparence/alpha sur l'export final
- [ ] Fichier < 30 MB (images) ou < 4 GB (video)
- [ ] Vignette video preparee si applicable
