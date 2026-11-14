# Les fichiers

## Le dossier de projet

```text
<projet>/
├── project.json, style.json, BRIEF.md
├── rushes/             Prises, sauf si project.json pointe ailleurs
├── sounds/             Tes effets sonores
├── fonts/              Police de style.json
├── audio/Txx.wav       Audio 16 kHz de chaque prise
├── transcripts/Txx.json        Mot à mot (champ words)
├── transcripts/text/Txx.json   Texte fidèle (champ transcription)
├── work/               takes.json, faces.json, casting.md, plan-bak/
├── ads/<ID>/           edit.json, captions.json, plan.json, build/, hf-v/, hf-h/, qa/
└── out/                Les vidéos finies
```

## project.json

| Clé | Rôle |
| --- | --- |
| `name` | Préfixe des fichiers livrés |
| `language` | Langue forcée dans toutes les transcriptions, code ISO |
| `rushes` | Dossier des prises, relatif au projet ou absolu |
| `mirror` | `true` si la caméra enregistre l'image retournée. Regarde un texte à l'écran pour trancher |
| `takes.include`, `takes.exclude` | Motifs de fichiers, sans casse. `exclude` s'applique au chemin complet dans `rushes` |
| `framing.vcrop` | Part de la hauteur gardée en vertical. `1.0` sur une source 1080p pour perdre moins de définition |
| `framing.h_width` | Part de la largeur gardée en horizontal |
| `framing.v_face_y`, `h_face_y` | Hauteur des yeux dans le cadre, en fraction |
| `transcription.words` | Modèle faster-whisper pour le mot à mot et le texte de secours |
| `transcription.captions` | Modèle pour `caps.py` et `seams.py` |
| `audio.voice_lufs` | Niveau de la voix avant montage, −17 par défaut. Avec cette valeur, le film rendu a mesuré −14,1 LUFS |
| `audio.seam_max_db` | Seuil de `seams.py` au raccord, −35 par défaut |
| `render.hyperframes` | Version épinglée de HyperFrames |
| `render.quality`, `workers` | Options du rendu |
| `tools.*` | Chemins de whisper.cpp et de DPDFNet, facultatifs |

## style.json

Un fichier partiel suffit, le reste prend les valeurs par défaut.

| Bloc | Clés |
| --- | --- |
| `font` | `family`, `file` (relatif au projet), `weight`, `weight_range` (la plage déclarée en CSS, à mettre égale à `weight` pour une police statique), `tracking_em` |
| `colors` | `caption`, `keyword`, `hook`, `background`, `keyword_dim` (voile sous le mot-clé), `scrim` (voile sur le fond flou) |
| `captions` | `size`, `line_height`, `max_words`, `max_chars`, `top_vertical`, `top_horizontal` (position du cadre de 140 px, le texte est centré dedans) |
| `keywords` | `min_size`, `max_size`, `char_width_em` (largeur moyenne d'un caractère de ta police en capitales) |
| `hook` | `on_vertical`, `bottom_vertical`, `bottom_horizontal`, `char_width_em`, tailles `target_*`, `goal_*`, `alone_*` |
| `zoom` | `levels_vertical`, `levels_horizontal`, `min_shot`, `max_shot`, `drift_per_s`, `drift_max` |
| `sfx` | Voir [03-sons.md](03-sons.md) |

Si tu changes de police, règle `char_width_em` puis regarde les planches : les mots-clés sont dimensionnés avec cette valeur.

## edit.json

```json
{"id":"A02","vcrop":0.9,"segments":[
  {"take":"T03","s":0.95,"e":12.4},
  {"take":"T04","s":1.2,"e":30.2,"nosnap":true}]}
```

`s` et `e` en secondes dans la prise. `nosnap` désactive le recalage. `vcrop` remplace `framing.vcrop` pour cette pub. `vx` est écrit par `track.py`, n'y touche pas.

## captions.json

`[{"t0":0.64,"t1":1.0,"text":"essayez pendant"}]`. Temps sur la timeline montée. C'est le fichier que le sous-agent corrige à la main.

## plan.json

| Clé | Rôle |
| --- | --- |
| `h_target` | La cible, en gros au-dessus de la vidéo horizontale. Vide : l'offre seule |
| `h_goal` | L'offre |
| `hook` | Texte de repli si `h_goal` est absent |
| `hook_d` | Temps réservé au début sans mot-clé. Durée du hook si `hook.on_vertical` est activé |
| `keywords` | `[{"t":8.2,"d":1.5,"text":"14 JOURS"}]`. `\n` force un saut de ligne |

## ajouts.json (topup.py)

`{"A01": [[12.4, "essai gratuit", "ESSAI GRATUIT"]]}` : temps approximatif, extrait d'un sous-titre, mot-clé. Le mot-clé se cale au début du sous-titre qui contient l'extrait. Il est refusé si l'extrait est introuvable, à plus d'une seconde du temps donné, pendant `hook_d`, ou à moins de 1,6 s d'un autre.
