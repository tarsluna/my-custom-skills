<div align="center">

<img src="https://img.shields.io/badge/MARKETING-META%20ADS-1877F2?style=flat-square&labelColor=1877F2&color=0A0A0A" alt="MARKETING · META ADS">

# Autonomous Meta Launch

### De vos vidéos montées aux pubs actives, sans ouvrir le Gestionnaire de publicités.

Un import qui reprend où il s'est arrêté.<br>
Des textes qui parlent à la bonne audience.<br>
Une activation qui vérifie tout, puis relit ce que Meta a vraiment fait.

**[Installer le skill](#installation)** · **[Lire le playbook](SKILL.md)** · **[Créer son token avec un agent](references/token-meta-computer-use.md)**

<sub>Claude Code · Marketing API · reprise avec state.json · 5 textes et 5 titres par pub · passage vers un formulaire instantané · simulation complète sans clé · MIT</sub>

<br><br>

<a href="https://bizos.cc"><img src="https://img.shields.io/badge/BizOS-build%20autonomous%20companies-0A0A0A?style=for-the-badge&labelColor=0A0A0A" alt="BizOS — build autonomous companies"></a>

<br><br>

<a href="https://x.com/gauthierthiry"><img src="https://img.shields.io/badge/@gauthierthiry-0A0A0A?style=flat-square&logo=x&logoColor=white" alt="X"></a>
<a href="https://youtube.com/@gquthier"><img src="https://img.shields.io/badge/@gquthier-FF0000?style=flat-square&logo=youtube&logoColor=white" alt="YouTube"></a>

</div>

---

## Ce que ça fait

Vous avez des vidéos prêtes, en vertical et en horizontal, et plusieurs audiences. Importer tout ça à la main prend des heures, et l'erreur arrive vite : le mauvais texte sur la mauvaise audience, une version périmée, une pub oubliée.

Ce skill donne à un agent de code le chemin complet :

- **Une reprise après interruption.** Chaque identifiant est inscrit dans `state.json` dès que Meta le renvoie. Relancez la même commande après une coupure : rien n'est créé en double.
- **Des textes corrélés par adset.** 5 textes et 5 titres par pub. Le premier texte vient de la vidéo, le reste vient de l'audience, et un contrôle bloque les mélanges.
- **Le rendez-vous des formats.** Une pub n'est complète qu'avec son vertical et son horizontal. Tant qu'il en manque un, rien ne part.
- **La conversion sur page merci.** Les adsets optimisent sur les personnes qui ont terminé l'action.
- **Un contrôle avant activation.** Nombre de pubs, budget confirmé par un humain et relu chez Meta, pages en ligne, textes relus sur chaque pub.
- **La relecture après activation.** Le décompte vient de l'état réel chez Meta, pas de la réponse à la demande.
- **Le passage vers un formulaire instantané.** Une campagne tourne déjà vers un site ? Ses pubs sont recréées à l'identique dans une nouvelle campagne, vers un formulaire, sans toucher l'ancienne. Le formulaire est relu avant, chaque copie est comparée champ par champ après.

Tout est créé en pause. La campagne est activée en dernier.

## Il complète autonomous-ad-publishing

[**autonomous-ad-publishing**](https://github.com/gquthier/autonomous-ad-publishing) publie une campagne complète et laisse tout en pause. Partez de lui pour découvrir l'API, créer des formulaires instantanés ou lancer des pubs image.

| | autonomous-ad-publishing | autonomous-meta-launch |
|---|---|---|
| Créer un formulaire instantané | Oui | Non |
| Recopier une campagne existante vers un formulaire, pubs à l'identique | Non décrit | Oui |
| Pubs image | Oui | Non |
| Pubs vidéo, vertical et horizontal appariés | Non | Oui |
| Reprise après interruption | Non | Oui |
| 5 textes et 5 titres par pub, corrélés à l'adset | Non | Oui |
| Conversion personnalisée sur page merci | Non | Oui |
| Activation contrôlée et relecture | Non, activation manuelle | Oui |

## Installation

```bash
git clone https://github.com/gquthier/autonomous-meta-launch.git ~/.claude/skills/autonomous-meta-launch
```

Puis demandez à Claude Code : *« Lance mes pubs Meta à partir de ce dossier de vidéos. »*

## Prérequis et clés

- Python 3.9 ou plus, sans dépendance à installer.
- `curl` et `ffmpeg`, pour le mode réel.
- Un compte publicitaire avec un moyen de paiement, une Page, un pixel installé.
- Quatre variables d'environnement, listées dans [`.env.example`](.env.example) :

| Variable | Contenu |
|---|---|
| `META_ACCESS_TOKEN` | Token d'utilisateur système |
| `META_AD_ACCOUNT` | Compte publicitaire, `act_...` |
| `META_PAGE_ID` | Page qui porte les pubs |
| `META_PIXEL_ID` | Pixel présent sur la page merci |

`META_GRAPH_VERSION` est facultative. La version par défaut est `v23.0`, celle du lancement d'origine. Meta proposait déjà la `v26.0` au moment de la publication.

**Vous n'avez jamais créé de token ?** [`references/token-meta-computer-use.md`](references/token-meta-computer-use.md) contient un prompt à coller dans un agent qui pilote votre écran. Il s'arrête pour vous rendre la main à chaque étape sensible : mot de passe, double authentification, carte bancaire, vérification d'identité, conditions. Le token ne passe jamais par le chat.

## Utilisation

Essayez d'abord la simulation, sans clé ni vidéo, sur un exemple fictif de pépinière qui s'adresse à des paysagistes :

```bash
cd ~/.claude/skills/autonomous-meta-launch
python3 scripts/meta_launch.py --config examples/paysagistes/campagne.json --dry-run --fresh run --confirm-budget 3000
```

```text
controle avant activation : 12 pubs conformes
campagne : ACTIVE ACTIVE budget 3000
adset : Paysagistes indépendants ACTIVE
adset : Entreprises d'espaces verts ACTIVE
pubs : {'PENDING_REVIEW': 12}
etat relu chez Meta : conforme
```

Pour voir la reprise, simulez une coupure, puis relancez :

```bash
python3 scripts/meta_launch.py --config examples/paysagistes/campagne.json --dry-run --fresh structure
python3 scripts/meta_launch.py --config examples/paysagistes/campagne.json --dry-run --simulate-crash-after 6 ads
python3 scripts/meta_launch.py --config examples/paysagistes/campagne.json --dry-run rendezvous
python3 scripts/meta_launch.py --config examples/paysagistes/campagne.json --dry-run ads
```

En réel, dans l'ordre :

| Commande | Effet |
|---|---|
| `copy` | Contrôle les textes, écrit le fichier à relire |
| `check` | Contrôle le token, le compte, la Page, le pixel, les pages |
| `structure` | Crée campagne, conversion et adsets, en pause |
| `ads --only P01` | Teste une pub de bout en bout |
| `ads` | Importe le reste, relançable à volonté |
| `rendezvous` | Montre les formats encore manquants |
| `relink` | Remplace un texte ou une page sur des pubs existantes |
| `go --confirm-budget N` | Contrôle, active, relit |
| `status` | Relit l'état réel |
| `cleanup --yes` | Supprime uniquement ce que `state.json` a enregistré |

Le détail est dans [le playbook](SKILL.md), les écueils dans [les pièges](references/pieges.md).

### Passer une campagne vers un formulaire instantané

Le cas est détaillé dans [`references/lead-form.md`](references/lead-form.md). À blanc, sur les objets fictifs de l'exemple :

```bash
python3 scripts/lead_form.py check-form --file examples/paysagistes/formulaire/formulaire-a-corriger.json
python3 scripts/lead_form.py diff-adsets --files examples/paysagistes/formulaire/adset-site.json examples/paysagistes/formulaire/adset-formulaire.json
python3 scripts/lead_form.py --dry-run copy-ad --file examples/paysagistes/formulaire/pubs-ancienne-campagne.json --form-id 000000000900 --adset 000000000402
```

```text
[a blanc] P01 devis-perdus Vertical : video simple, 5 textes, 5 titres, statut source ACTIVE, controle 0 ecart(s)
[a blanc] P02 plantes-en-retard Emplacements : video par emplacement (3 videos), 1 textes, 1 titres, statut source ACTIVE, controle 0 ecart(s)
ignoree, refusee par Meta dans l'ancienne campagne : P03 refusee Vertical
2 a copier, 0 deja la, 1 refusee(s) non recopiee(s)
```

Les deux premières commandes s'arrêtent volontairement : le formulaire de l'exemple est en anglais avec des tranches qui se chevauchent, et l'ad set fait main n'a pas les réglages de l'ancien.

| Commande | Effet |
|---|---|
| `check-form` | Relit langue, libellés et tranches du formulaire, avant d'y diriger les pubs |
| `copy-adset` | Copie un ad set sans ses pubs, en pause, puis le renomme |
| `diff-adsets` | Signale pays, âges, langues, placements et intérêts qui diffèrent |
| `copy-ad` | Recrée les pubs vers le formulaire, en pause, et compare chaque copie |
| `diff` | Compare deux créatives champ par champ |

```bash
python3 -m unittest discover -s tests
```

## Limites honnêtes

- **Ce dépôt n'a pas été exécuté contre la vraie API Meta sous sa forme publiée.** Il généralise des scripts qui ont réellement importé une campagne. Sa version publique a été testée en simulation et contre un serveur local. Testez sur une seule pub d'abord.
- **Le passage vers un formulaire a tourné le 12 novembre 2026 sous forme de scripts ponctuels.** `lead_form.py` les généralise. Il a été testé à blanc et contre un faux client en mémoire, pas contre l'API. Il ne couvre que les pubs vidéo, et l'activation reste manuelle.
- **L'activation est l'étape la moins éprouvée.** Les notes du lancement d'origine ne confirment pas l'exécution finale de ce contrôle. Vérifiez le premier `go` dans le Gestionnaire de publicités.
- **La simulation imite Meta, elle ne le remplace pas.** Elle valide l'enchaînement, les identifiants et les contrôles. Elle ne dira pas qu'un texte sera refusé par l'examen des publicités.
- **Le pixel reste à vérifier à la main**, et une vraie réservation de bout en bout reste le meilleur test.
- **Les contrôles de texte sont mécaniques.** Une promesse commerciale, une garantie, un chiffre relèvent de la personne qui les publie.
- **Pas d'identité Instagram dédiée.** Pour diffuser sous un compte Instagram précis, ajoutez `instagram_user_id` à la créative.
- **Le verrou sur `state.json` n'existe que sur macOS et Linux.** Sous Windows, n'exécutez pas d'envois en parallèle.
- **L'interface et les règles de Meta évoluent.** Les écrans du guide token ont été relevés dans la documentation officielle en novembre 2026.

## Licence

MIT
