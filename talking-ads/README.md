<div align="center">

<img src="https://img.shields.io/badge/VID%C3%89O-TALKING_ADS-B8893B?style=flat-square&labelColor=B8893B&color=14120E" alt="VIDÉO · TALKING ADS">

# Autonomous Talking Ads

### D'un dossier de prises face caméra à une série de pubs montées.

Chaque prise devient une pub, en vertical et en horizontal.<br>
Sous-titres, mots-clés, zooms, effets sonores.<br>
Un sous-agent par pub, un seul brief pour toute la série.

**[Installer le skill](#installation)** · **[Lire le playbook](SKILL.md)** · **[Les pièges rencontrés](references/04-pieges.md)**

<sub>Claude Code + Codex · 1080×1920, deux formats · texte seul · local, aucune clé d'API · police et couleurs dans un fichier · MIT</sub>

<br><br>

<a href="https://bizos.cc"><img src="https://img.shields.io/badge/BizOS-build%20autonomous%20companies-14120E?style=for-the-badge&labelColor=14120E" alt="BizOS — build autonomous companies"></a>

<br><br>

<a href="https://x.com/gauthierthiry"><img src="https://img.shields.io/badge/@gauthierthiry-14120E?style=flat-square&logo=x&logoColor=white" alt="X"></a>
<a href="https://youtube.com/@gquthier"><img src="https://img.shields.io/badge/@gquthier-FF0000?style=flat-square&logo=youtube&logoColor=white" alt="YouTube"></a>

</div>

---

## Ce que ça fait

Tu tournes vingt prises face caméra dans l'après-midi. Il faut enlever les faux départs, couper les blancs, recadrer, sous-titrer, décliner chaque pub en deux formats. À la main, ça prend des jours. Ce skill confie chaque pub à un sous-agent et garde la série cohérente avec un brief unique.

Le montage est volontairement simple, parce que c'est ce qui a tenu face aux retours d'un vrai tournage : **le visage, du texte, des effets sonores, et rien d'autre.**

```text
   VERTICAL                     HORIZONTAL
 ┌───────────┐                ┌───────────┐
 │           │                │  CIBLE    │  hook, toute la durée
 │   visage  │                │  offre    │
 │  plein    │                ├───────────┤
 │  cadre    │                │ vidéo 16:9│  fond : la même vidéo, floutée
 │           │                ├───────────┤
 │ sous-titre│                │ sous-titre│
 └───────────┘                └───────────┘
     1080×1920                    1080×1920
```

- **Vidéo complète de A à Z.** Du premier au dernier mot. Seuls les faux départs, reprises et apartés partent.
- **Raccords vérifiés.** Chaque coupe se cale au creux d'énergie, puis est réécoutée par Whisper et mesurée en décibels.
- **Sous-titres relus.** Quatre mots et 22 caractères au plus par groupe, corrigés à la main sur le texte fidèle.
- **Mots-clés en gros au centre.** La promesse ou le chiffre fort, au moment exact où c'est dit, avec un effet sonore.
- **Zooms réguliers.** Une coupe de zoom à chaque raccord et toutes les 3 à 4 secondes, plus une légère poussée.
- **Ton style dans un fichier.** Police, couleurs, tailles, zooms et sons dans `style.json`.
- **Voix nettoyée.** Débruitage, compression, niveau réglé, contrôle de la loudness à la sortie.

Pour un montage plus chargé, à partir d'une seule prise, avec du motion design : **[autonomous-shortform-facecam-editing](https://github.com/gquthier/autonomous-shortform-facecam-editing)**. Les deux dépôts sont complémentaires, celui-ci sert à produire une série sobre.

## Installation

**Claude Code** :

```bash
git clone https://github.com/gquthier/autonomous-talking-ads.git \
  ~/.claude/skills/talking-ads
```

**Codex** :

```bash
git clone https://github.com/gquthier/autonomous-talking-ads.git \
  ~/.codex/skills/talking-ads
```

Puis les dépendances Python, de préférence dans un environnement dédié :

```bash
python3 -m venv ~/.venvs/talking-ads
source ~/.venvs/talking-ads/bin/activate
pip install -r ~/.claude/skills/talking-ads/requirements.txt
```

## Prérequis et clés

**Aucune clé d'API.** Tout tourne sur ta machine. [`.env.example`](.env.example) ne liste que des chemins facultatifs.

| Outil | Rôle | Obligatoire |
| --- | --- | --- |
| Python 3.9+ | Les outils | Oui |
| ffmpeg et ffprobe | Coupes, audio, planches | Oui |
| Node.js 22+ | Lance [HyperFrames](https://hyperframes.heygen.com) via `npx`, version épinglée | Oui |
| faster-whisper | Temps mot à mot et sous-titres | Oui, modèles téléchargés au premier lancement |
| opencv | Position du visage | Oui |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Texte le plus fidèle | Non : faster-whisper prend le relais |
| [Modèle DPDFNet](https://github.com/k2-fsa/sherpa-onnx/releases/tag/speech-enhancement-models) (`dpdfnet2_48khz_hr.onnx`) et sherpa-onnx | Débruitage de la voix | Non : `ffmpeg afftdn`, plus faible |
| Tes effets sonores | Whoosh, impact, clic | Non : voir ci-dessous |

Le chemin de whisper.cpp et de DPDFNet se donne dans la section `tools` de `project.json`.

**Aucun son n'est fourni.** Pose les tiens dans `<projet>/sounds/`, avec une licence qui autorise la publicité : [references/03-sons.md](references/03-sons.md). Bricolage Grotesque est incluse sous licence SIL OFL.

Filme en 4K si tu peux : le vertical recadre fortement.

## Utilisation

Dans une nouvelle session, demande :

> Utilise le skill talking-ads pour monter les prises de ce dossier en série de pubs, en vertical et en horizontal. Commence par une pilote.

L'agent suit huit étapes, détaillées dans [SKILL.md](SKILL.md) :

1. Crée le projet et lit le dossier de prises.
2. Transcrit chaque prise et mesure le visage.
3. Fait le casting : quelle prise devient quelle pub.
4. Fige le brief unique et le style.
5. Monte une pilote, attend ta validation.
6. Lance un sous-agent par pub.
7. Contrôle les planches et corrige.
8. Livre, en listant ce qui reste douteux.

À la main, sur une pub :

```bash
S=~/.claude/skills/talking-ads/scripts
python3 $S/init_project.py ./mes-pubs --rushes ~/Videos/tournage --name MaMarque
python3 $S/extract_audio.py ./mes-pubs
python3 $S/transcribe.py ./mes-pubs
python3 $S/text_pass.py ./mes-pubs
python3 $S/faces.py ./mes-pubs
# écris ads/A01/edit.json (voir references/02-fichiers.md)
python3 $S/cut.py ./mes-pubs A01
python3 $S/seams.py ./mes-pubs A01
python3 $S/caps.py ./mes-pubs A01
# relis captions.json, écris plan.json
python3 $S/gen.py ./mes-pubs A01
python3 $S/finish.py ./mes-pubs A01 mon-slug
```

Change le style dans `style.json`, puis `python3 $S/rerender.py ./mes-pubs` refait toute la série sans refaire les coupes.

## Dans le dépôt

```text
SKILL.md                      Le playbook, de A à Z
references/01-sous-agents.md  Casting, mission type, lancement, retours
references/02-fichiers.md     Tous les fichiers de configuration et de montage
references/03-sons.md         Fournir ses effets sonores
references/04-pieges.md       Ce qui a cassé en production
template/BRIEF.md             Le brief unique des sous-agents
template/project.json         Technique : langue, cadrage, modèles
template/style.json           Police, couleurs, tailles, zooms, sons
scripts/                      Un outil par étape, avec --dry-run
tests/                        Tests hors ligne, sans modèle ni vidéo
```

## Limites honnêtes

**Ce qui a été vérifié.** Ces outils viennent d'une vraie série tournée et montée en une journée. Sa marque, ses textes et ses chiffres ne sont pas dans ce dépôt. Cette version publique a tourné de bout en bout sur un extrait réel de 13 secondes : inventaire, transcription, visage, coupe, réécoute des raccords, sous-titres, composition, `hyperframes check`, rendu des deux formats, 8,80 s et −14,1 LUFS en sortie. Sont aussi testés le repli sans DPDFNet ni whisper.cpp, une source portrait en mono à 25 i/s et le suivi de tête. Les tests hors ligne couvrent les recadrages, les sous-titres, le style, les ajouts de mots-clés et le `--dry-run`.

**Ce qui ne l'a pas été.** Le déroulé complet à plusieurs sous-agents n'a tourné que sur la version d'origine, pas sur celle-ci. Ni rotation de téléphone, ni source HDR, ni Linux ou Windows pour le rendu. Les sons fournis par défaut n'existent pas : les volumes de `style.json` sont à régler à l'oreille.

**Personne n'écoute à ta place.** Les contrôles lisent des transcriptions, des niveaux et des planches d'images. Une voix qui remonte à la jointure entre deux prises ou un mot mal articulé leur échappent. Écoute avant de diffuser.

**Les textes te regardent.** Un mot-clé ou une offre engage ta marque. Ce dépôt ne juge pas si une promesse est tenable, légale ou conforme aux règles des plateformes publicitaires. Les garanties et les professions réglementées demandent une relecture par quelqu'un de qualifié.

**Le montage n'est pas réglable à l'infini.** Si tu veux des animations ou du b-roll, prends l'autre dépôt cité plus haut.

**La charge.** Les sous-agents font du décodage 4K et de la transcription en parallèle. Sur une machine modeste, baisse la taille des vagues.

**Le casting se relit.** Ce sont des transcriptions qui décident quelle prise est bonne. Une prise bien dite peut être mal retranscrite.

MIT pour le code, les instructions et les exemples fictifs de ce dépôt. Bricolage Grotesque est distribuée sous SIL Open Font License, voir [template/fonts/OFL.txt](template/fonts/OFL.txt). Les compositions sont rendues avec HyperFrames, soumis à sa propre licence.

---

<div align="center">

<sub>Construit par [Gauthier Thiry](https://x.com/gauthierthiry)</sub>

</div>
