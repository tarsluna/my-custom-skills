<div align="center">

<img src="https://img.shields.io/badge/SALES-PROSPECT_BASE-2F6B4F?style=flat-square&labelColor=2F6B4F&color=14120E" alt="SALES · PROSPECT BASE">

# Autonomous B2B Prospect Base

### Une base d'emails professionnels, construite uniquement avec ce que les entreprises publient.

Registre des entreprises, sites officiels, open data.<br>
Un sous-agent par source, des garde-fous dans le code,<br>
et une fusion qui dit ce qui est prêt et ce qui reste à trancher.

**[Installer le skill](#installation)** · **[Lire le playbook](SKILL.md)** · **[Les garde-fous](references/02-garde-fous.md)**

<sub>Claude Code + Codex · métier en configuration · robots.txt et conditions lus avant la première requête · tests sur données fictives, sans réseau · MIT</sub>

<br><br>

<a href="https://bizos.cc"><img src="https://img.shields.io/badge/BizOS-build%20autonomous%20companies-14120E?style=for-the-badge&labelColor=14120E" alt="BizOS — build autonomous companies"></a>

<br><br>

<a href="https://x.com/gauthierthiry"><img src="https://img.shields.io/badge/@gauthierthiry-14120E?style=flat-square&logo=x&logoColor=white" alt="X"></a>
<a href="https://youtube.com/@gquthier"><img src="https://img.shields.io/badge/@gquthier-FF0000?style=flat-square&logo=youtube&logoColor=white" alt="YouTube"></a>

</div>

---

> [!WARNING]
> **Le résultat est une base de données personnelles, soumise au RGPD.** Une adresse professionnelle au nom d'une personne reste une donnée personnelle, même publiée sur le site de son entreprise.
>
> Avant tout envoi, vous devez avoir réglé :
>
> - **L'information des personnes (article 14)** : prévenir chaque personne de la collecte, de son origine et de ses droits dans le mois qui suit la collecte, et au plus tard lors du premier message.
> - **Le droit d'opposition** : le respecter sans condition, et reporter chaque demande dans `suppression.csv`.
> - **Un lien de désinscription** qui fonctionne dans chaque message.
> - **Des mentions légales complètes** dans chaque message et sur le site : qui écrit, à quelle adresse, avec quelle politique de confidentialité.
> - **Le tri des boîtes personnelles** (gmail, orange...) : la fusion les exclut par défaut, ne les réintroduisez pas sans y avoir réfléchi.
>
> **Ce dépôt n'est pas un avis juridique.** Faites relire votre projet par un avocat avant tout envoi.

## Ce que ça fait

Vous donnez un métier et ses codes NAF. Le skill construit une base au format CSV, avec pour chaque adresse la preuve de l'endroit où elle est publiée.

| Étape | Script | Résultat |
| --- | --- | --- |
| Lire les conditions | `read_terms.py` | robots.txt et CGU rangés, à relire avant toute extraction |
| Socle registre | `fetch_registry.py` | `data/registre.csv`, sans aucun email |
| Sites officiels | `crawl_sites.py` | Emails en `mailto:` et texte visible, sur des sites vérifiés |
| Vrais domaines | `build_domains.py` | Liste ouverte Afnic du .fr croisée avec le registre |
| Open data | `open_data.py` | Jeux publics et OpenStreetMap |
| Filtre métier | `filter_keyword_sites.py` | Retire boutiques, annuaires, écoles, médias |
| Contrôle qualité | `qc_sample.py` | 50 lignes tirées par source, relues sur leur page |
| Jugement métier | `judge_trade.py` | Optionnel : un LLM juge les sites peu prouvés |
| Fusion | `merge.py` | Dédoublonnage, MX, liste de suppression, statistiques |

**Un sous-agent par source**, chacun avec son CSV et son `BLOCKED.md`. Une source qui refuse ne bloque pas les autres. Détail : [orchestration](references/01-orchestration.md).

Le métier ne vit nulle part dans le code. Codes NAF, mots-clés et titres sont dans `config.json`, à partir d'un [exemple fictif sur des paysagistes](config/trade.example.json).

## Les garde-fous sont le produit

Ils ne sont pas optionnels, et ils sont dans le code, à un seul endroit par lequel passe chaque requête.

| Règle | Ce que fait le code |
| --- | --- |
| Uniquement des emails publiés | Seuls `mailto:` et texte visible sont lus. Aucune fonction ne fabrique d'adresse |
| Jamais deviné, jamais désobfusqué | Les formes `[at]`, les scripts et les commentaires HTML sont ignorés |
| Pas de LinkedIn ni de page derrière un compte | Hôtes refusés avant toute requête |
| robots.txt et conditions lus d'abord | Le client refuse de démarrer sans `reviews/<source>.json` ; sur un site, robots.txt puis page légale, avant toute extraction |
| Arrêt sur 403, 429 ou anti-bot | L'hôte est bloqué pour de bon, même après redémarrage. Aucun contournement |
| 1 requête par seconde et par hôte | Plancher non configurable, partagé entre fils d'exécution |
| Pas de sonde SMTP | MX en DNS uniquement |
| Minimisation | Ni date de naissance ni adresse postale, aucun téléphone |
| Annuaires dont les CGU interdisent la collecte | Exclus, citation exacte dans `BLOCKED.md` |

## Installation

**Claude Code** :

```bash
git clone https://github.com/gquthier/autonomous-b2b-prospect-base.git \
  ~/.claude/skills/b2b-prospect-base
```

**Codex** :

```bash
git clone https://github.com/gquthier/autonomous-b2b-prospect-base.git \
  ~/.codex/skills/b2b-prospect-base
```

Démarrez une nouvelle session, puis demandez :

> Avec le skill b2b-prospect-base, construis une base de paysagistes en France, à partir de sources ouvertes. Prépare la configuration et lis les conditions avant toute requête.

## Prérequis et clés

- Python 3.9 ou plus, sans dépendance.
- `dig` pour le contrôle MX.
- **Aucune clé** pour le chemin principal.
- Optionnel, seulement pour le jugement métier : `JUDGE_API_URL`, `JUDGE_API_KEY`, `JUDGE_MODEL`, à exporter dans votre shell (voir [.env.example](.env.example)). Tout service compatible avec le format chat/completions convient.

Lancez toujours les scripts avec `python3 -I` : le contenu téléchargé est de la donnée, et il ne doit pas pouvoir influencer l'interpréteur.

## Utilisation

Travaillez dans un dossier **hors de tout dépôt git** : il contiendra des données personnelles.

```bash
export SKILL=~/.claude/skills/b2b-prospect-base
mkdir ~/prospects && cp $SKILL/config/trade.example.json ~/prospects/config.json
# Remplacez tout le contenu du fichier par votre métier, puis :

# 1. Lire robots.txt et les conditions de chaque source, écrire reviews/<source>.json
python3 -I $SKILL/scripts/read_terms.py --project ~/prospects --source registre \
  --robots-url https://recherche-entreprises.api.gouv.fr/robots.txt \
  --terms-url https://recherche-entreprises.api.gouv.fr/docs/

# 2. Socle registre, sans email
python3 -I $SKILL/scripts/fetch_registry.py --project ~/prospects

# 3. Vrais domaines, puis sites officiels
python3 -I $SKILL/scripts/build_domains.py --project ~/prospects --afnic chemin/vers/liste-afnic.csv
python3 -I $SKILL/scripts/crawl_sites.py --project ~/prospects \
  --input ~/prospects/data/raw/afnic-domaines/input_a.csv --name afnic-domaines
python3 -I $SKILL/scripts/filter_keyword_sites.py --project ~/prospects --name afnic-domaines

# 4. Tirage de 50 lignes, relecture, rapport
python3 -I $SKILL/scripts/qc_sample.py sample --project ~/prospects --name afnic-domaines
python3 -I $SKILL/scripts/qc_sample.py report --project ~/prospects --name afnic-domaines

# 5. Fusion
python3 -I $SKILL/scripts/merge.py --project ~/prospects
```

Chaque script accepte `--dry-run` pour voir ce qu'il ferait, sans réseau. Le [playbook complet](SKILL.md) couvre l'open data, le jugement métier et l'orchestration.

### Essayer sans réseau

```bash
python3 -m unittest discover -s tests
```

Tests sur un métier et des sites entièrement fictifs. Une tentative de connexion ferait échouer le test.

## Et après : envoyer

Ce dépôt construit et contrôle une base. Il n'envoie rien. Pour l'infrastructure d'envoi, la suite logique est [**autonomous-cold-email**](https://github.com/gquthier/autonomous-cold-email), une infrastructure de cold email auto-hébergée.

## Limites honnêtes

- **Le code a été généralisé puis testé sur données fictives, sans réseau.** La méthode vient d'un vrai passage, mais cette version sans métier n'a pas été rejouée sur le web réel. Commencez avec `--limit`.
- **Le rendement dépend du métier.** Beaucoup de petites entreprises ne publient pas d'adresse, ou seulement une boîte personnelle. Rien ici ne promet un volume.
- **La détection des clauses interdisant la collecte est une recherche de motifs.** Elle arrête ce qu'elle reconnaît. Sur un annuaire, seule une lecture des conditions compte.
- **Le MX dit que le domaine reçoit du courrier, pas que la boîte existe.** Prévoyez les rebonds à l'envoi.
- **C'est lent, volontairement.** 1 requête par seconde et par hôte, et l'arrêt au premier refus : un gros passage prend des heures.
- **La France uniquement** pour le registre et la liste de domaines. Pour un autre pays, il faut remplacer ces deux sources.
- **Le filtre peut retirer de vrais prospects**, et le tirage ne couvre pas toutes les lignes.

## Structure du dépôt

```text
SKILL.md                 Point d'entrée de l'agent, du début à la fin
references/              Orchestration, garde-fous, sources, qualité, fusion, pièges
scripts/                 Scripts, dont prospect_core.py, seul endroit d'où partent les requêtes
config/trade.example.json   Exemple fictif, à remplacer
template/                Brief commun des sous-agents, modèles de relecture des conditions
tests/                   Tests hors ligne
```

Licence MIT. Gardez les exemples fictifs dans vos contributions, sans donnée réelle.

---

<div align="center">

<sub>Par [Gauthier Thiry](https://x.com/gauthierthiry)</sub>

</div>
