# Brief de montage : une pub = un sous-agent

> L'agent principal remplit ce qui est entre crochets, fige ce fichier, puis le donne tel quel à chaque sous-agent. Le reste ne change pas d'une série à l'autre.

Tu montes **une seule** pub, à partir des prises du projet. Ta mission te donne son identifiant, sa ou ses prises, son slug et sa cible.

- **Projet** : `[chemin absolu du dossier de projet]`, noté `$P`.
- **Outils** : `[chemin absolu du dossier scripts du skill]`, noté `$S`. Lance-les ainsi : `python3 $S/<outil>.py $P ...`
- **Ce qu'on vend et à qui** : [deux lignes. Exemple fictif : un réseau de salles de sport propose 14 jours d'essai aux habitants du quartier.]
- **Offres admises dans le hook** : [liste courte, mot pour mot. Exemple fictif : « 14 jours d'essai offerts ».]

## Règles fermes

**Montage très simple et esthétique : du texte, rien d'autre.** Le visage, les sous-titres, les mots-clés, le hook, des effets sonores.

- **Pas d'animation de début ni de fin**, pas de carte, de logo, d'image, de b-roll, de motion design, de musique. N'ajoute rien qui n'est pas demandé ici.
- **Vidéo complète de A à Z** : du premier au dernier mot de la prise de parole, y compris le mot d'ouverture et la dernière phrase. Tu ne retires que le déchet évident : faux départs, phrases recommencées, rires, apartés hors texte. Dans le doute, tu gardes. Le dernier segment finit au moins 0,4 s après la fin réelle du dernier mot.
- **Zooms réguliers** : ils sont faits par `gen.py`, à chaque raccord et toutes les 3 à 4 s. Ne les retire pas, n'en ajoute pas.
- Tu ne touches qu'à `$P/ads/<ID>/`. Ni aux autres pubs, ni à `style.json`, ni aux outils. Tu ne publies rien.

## Ce que tu livres

Deux fichiers 1080×1920 dans `$P/out/` :

- **Vertical** : le visage recadré plein cadre, sous-titres et mots-clés.
- **Horizontal** : la vidéo 16:9 au milieu, fond = la même vidéo floutée, hook au-dessus pendant toute la durée, sous-titres et mots-clés.

## Étape 1 : couper proprement

Une pub est une seule prise de parole **propre**, sans répétition.

1. Lis la prise : texte fidèle dans `$P/transcripts/text/Txx.json` (champ `transcription`), temps mot à mot avec `show.py $P Txx`. Ces temps ont plusieurs dixièmes d'écart dans les deux sens : ne déduis pas un blanc des seuls temps, vérifie avec `seams.py`.
2. Écris `$P/ads/<ID>/edit.json` : `{"id":"A01","segments":[{"take":"T01","s":0.95,"e":12.4},{"take":"T01","s":13.0,"e":30.2}]}`. Temps en secondes dans la prise, recalés seuls au creux d'énergie à ±60 ms. `"nosnap":true` désactive le recalage sur un segment.
   - Quand une phrase est répétée, garde la meilleure, une seule fois.
   - Blancs de plus de 0,35 s ramenés à 0,18-0,25 s. Ne hache pas : garde les respirations naturelles. Jamais de coupe dans un mot.
3. `cut.py $P <ID>` puis `seams.py $P <ID>` : chaque raccord doit donner une phrase correcte, niveau **≤ −35 dB**. Sinon ajuste et recommence.
4. `text_pass.py $P --ad <ID>` retranscrit tout `build/voice.wav`. Relis : aucune répétition, aucune fin coupée, dernier mot présent.

Si la prise commence pendant que la personne s'installe et que le visage sort du cadre vertical : `track.py $P <ID>`, puis `cut.py` à nouveau.

## Étape 2 : sous-titres

`caps.py $P <ID>` crée `ads/<ID>/captions.json` (groupes `{"t0","t1","text"}`, mots détaillés dans `build/caps/transcript.json`, compte 1 à 3 min quand la machine est chargée). **Relis tout** et corrige le fichier à la main :

- Le texte doit être exactement ce qui est dit, sans faute. Corrige avec la transcription de l'étape 1, noms propres compris.
- Maximum 4 mots et 22 caractères par groupe, une seule ligne. Regroupe pour que chaque groupe se lise bien : ne finis pas sur un article, une préposition ou un pronom seul. Reprends les temps des mots de `transcript.json`.
- Pas de ponctuation finale, sauf « ? » et « ! ».

Le style vient de `style.json`, tu n'y touches pas.

## Étape 3 : plan.json

```json
{"id":"A01","h_target":"Salle de sport","h_goal":"14 jours d'essai offerts","hook_d":4.4,
 "keywords":[{"t":8.2,"d":1.5,"text":"14 JOURS"},{"t":21.4,"d":1.6,"text":"SANS\nENGAGEMENT"}]}
```

- **h_target** : la cible, en deux à quatre mots, donnée par ta mission. Laisse vide pour afficher l'offre seule.
- **h_goal** : une offre de la liste en tête de ce brief, mot pour mot. Rien d'absent de la prise.
- **hook_d** : temps réservé au début, sans mot-clé. Au moins 0,5 + 0,3 s par mot du hook.
- **keywords** : les mots importants **en gros au milieu de l'image** (la promesse, la garantie, le chiffre fort), tels qu'ils sont dits dans ta prise. Jamais un chiffre, un témoignage ou un nom inventé. 1 à 4 mots en capitales, `\n` pour couper la ligne. `t` au moment exact où c'est dit, `d` ≥ 0,5 + 0,3 s par mot, 1,1 s minimum. Environ un toutes les 7 à 10 s, pas plus : garde le plus fort. Aucun pendant `hook_d`, aucun dans la dernière seconde. Un effet sonore part automatiquement avec chacun. Le sous-titre s'efface tout seul pendant le mot-clé.

Le vertical ne porte pas de hook : sous-titres et mots-clés seulement.

## Étape 4 : assembler et vérifier

1. `gen.py $P <ID>`. Tout message « ATTENTION » se corrige avant d'aller plus loin.
2. `npx --yes hyperframes@0.9.23 check --json` dans `ads/<ID>/hf-v` et `ads/<ID>/hf-h` (rapport dans `.hyperframes/artifacts/checks/*.json`). Corrige toute erreur. `nested_structure_needs_subcomposition`, `timeline_track_too_dense`, `clip_media_fit` et `container_overflow` sont attendus.
3. `finish.py $P <ID> <slug>`. Le rendu attend si un autre est en cours. Vérifie la durée et le niveau (environ −14 LUFS), puis **regarde les planches** `ads/<ID>/qa/Vertical.jpg` et `qa/Horizontal.jpg` : sous-titre lisible, mot-clé qui ne déborde pas, hook entier.

## Ton rapport final (6 lignes maximum)

Identifiant, nom des deux fichiers, durée, nombre de raccords, hook retenu, mots-clés, ce que tu as retiré, et **ce qui reste douteux**. Ne dis pas « vérifié » pour ce que tu n'as pas vérifié : tu lis des transcriptions et tu regardes des planches, tu n'écoutes pas le film.
