# Les pièges rencontrés

Tout ce qui suit est arrivé pendant une vraie série tournée et montée en une journée.

## Le processus

**Le format a changé après le premier rendu.** Plusieurs montages étaient déjà partis quand les retours sont arrivés, et le format a encore bougé deux fois ensuite. Chaque fois, toute la série est repartie en rendu. Une pilote validée avant de lancer la série évite l'essentiel de ce coût.

**« Pas d'animation », dit après coup.** La première version avait des cartes, un logo, une animation de fin. Elle a été jetée. Le montage demandé tenait en trois éléments : le visage, le texte, le son. Ne rajoute rien.

**Vidéos coupées trop tôt.** Les premières pubs perdaient le mot d'ouverture et la dernière phrase. Le dernier segment doit finir au moins 0,4 s après le dernier mot, et la retranscription de `voice.wav` doit contenir ce mot.

**Un correctif d'outil ne se propage pas seul.** Un bug sur les pubs à deux prises a été corrigé en cours de route. Les pubs déjà montées gardaient l'ancienne version. Liste ce qui est touché, relance.

**Personne n'a écouté.** Les sous-agents contrôlent des transcriptions, des niveaux et des planches d'images. Une voix qui remonte à la jointure entre deux prises, ou un mot mangé mais retranscrit correctement, passent à travers. Il faut une écoute humaine avant diffusion.

## L'audio et la transcription

**Forcer la langue.** Un transcripteur qui détecte la langue seul est parti en anglais sur certaines prises françaises. Toutes les transcriptions passent par `language` de `project.json`.

**Les temps mot à mot mentent.** Plusieurs dixièmes d'écart, dans les deux sens. Un blanc déduit des seuls temps peut tomber en plein mot. Vise le blanc, puis laisse `seams.py` juger : le niveau au raccord doit rester sous −35 dB, et la phrase réécoutée doit être correcte.

**Deux transcriptions, deux usages.** faster-whisper donne les temps, whisper.cpp donne le texte le plus fidèle. Les sous-titres se corrigent avec le texte fidèle.

**Le gros modèle, sous charge.** `large-v3` a pris plus de 5 minutes sur 8 secondes quand plusieurs montages tournaient. D'où `medium` pour les sous-titres et les raccords.

**Deux prises collées.** Le niveau et le timbre de la voix peuvent changer à la jointure. À écouter en priorité.

## L'image

**Le miroir.** La sortie d'un logiciel de streaming peut être retournée alors que le fichier caméra ne l'est pas, ou l'inverse. Regarde un texte dans l'image et règle `mirror`.

**Les captures d'écran dans le dossier.** Un logiciel de streaming peut enregistrer l'écran à côté de la caméra. Elles montrent des fenêtres privées. `takes.exclude` les écarte par leur nom : relis la liste donnée par `extract_audio.py`.

**La prise commence pendant que la personne s'assoit.** Le visage sort du cadre vertical. `track.py` fait suivre la tête au début, puis revient au cadre fixe.

**Source en 1080p.** Le vertical agrandit l'image plus de deux fois. Filme en 4K, ou passe `framing.vcrop` à `1.0`.

**Face non détectée.** `faces.py` utilise un détecteur simple. Sans visage, le recadrage part du centre. Regarde la planche.

## Le texte à l'écran

**Mots-clés qui débordent.** Leur taille dépend de la largeur de la police. Après un changement de police, règle `keywords.char_width_em` et regarde les planches.

**Un mot-clé dont la voix ne parle pas.** Rejette-le : il doit être dit dans la prise, à ce moment-là.

**Le hook a changé trois fois.** Texte POV, puis cible et offre. Choisis-le à la pilote et fige-le dans le brief.

## La machine

**Disque.** Chaque pub produit trois vidéos intermédiaires à fort débit. `gen.py` utilise des liens durs pour ne pas les dupliquer. Après livraison, `ads/<ID>/build/*.mp4` se supprime sans perte tant que tu ne re-rends pas : `cut.py` les refait.

**Rendus simultanés.** Ils s'affament. HyperFrames les fait attendre par défaut, laisse faire.

**`check` qui signale `nested_structure_needs_subcomposition`, `timeline_track_too_dense`, `clip_media_fit` ou `container_overflow`.** Attendu avec cette composition, en version 0.9.23. `line_unread` sur un mot-clé proche de la fin mérite un coup d'œil.
