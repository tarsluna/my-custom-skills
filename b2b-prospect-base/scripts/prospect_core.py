#!/usr/bin/env python3
"""Socle commun : schema, configuration et garde-fous.

Toute requete reseau du projet passe par `Client`. C'est volontaire : les garde-fous
ne dependent pas de la discipline de chaque script.

- Une source sans relecture de ses conditions (`reviews/<source>.json`) ne part pas.
- robots.txt est lu avant la premiere page de chaque origine, redirections comprises.
- 1 requete par seconde et par hote au maximum, plus si robots.txt le demande.
- 401, 403, 429, 503, anti-bot ou page derriere un compte : arret definitif de l'hote.
- Pas de faux User-Agent, pas de LinkedIn, Facebook ni Instagram.
- Aucune sonde SMTP : le seul controle de delivrabilite est le MX en DNS, dans merge.py.
"""
import csv
import datetime as dt
import html
import http.client
import json
import re
import socket
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

SCHEMA = [
    "prenom", "nom", "email", "entreprise", "segment", "ville", "code_postal",
    "site", "siren", "email_type", "source_url", "collected_at",
]

# Plancher non configurable. La configuration peut ralentir, jamais accelerer.
MIN_INTERVAL = 1.0
DEFAULT_INTERVAL = 1.1
MAX_CRAWL_DELAY = 15
# Au-dela, une ligne partagee sature et un echec reseau ressemble a un site absent.
MAX_CONNECTIONS = 40
DEFAULT_CONNECTIONS = 30
BLOCK_STATUS = {401, 403, 429, 503}
REDIRECT_STATUS = {301, 302, 303, 307, 308}
MAX_REDIRECTS = 5
MAX_BYTES = 1_500_000

FORBIDDEN_HOSTS = ("linkedin.com", "lnkd.in", "facebook.com", "fb.com", "instagram.com")
BROWSER_UA = re.compile(r"mozilla|chrome|safari|firefox|edg/|opera", re.I)
# Page de defi seulement : un reCAPTCHA sur un formulaire n'empeche pas de lire la page.
ANTIBOT = re.compile(
    r"cf-chl|<title>[^<]*(just a moment|attention required|captcha|access denied|are you (a )?human)"
    r"|verify you are human|ddos-guard",
    re.I,
)
LOGIN_PATH = re.compile(r"/(login|log-in|signin|sign-in|connexion|se-connecter|mon-compte|my-account)(/|$)", re.I)

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
MAILTO = re.compile(r"""href\s*=\s*["']mailto:([^"'?]+)""", re.I)
DROP = re.compile(r"<(script|style|noscript|template)\b.*?</\1>", re.I | re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)
TAG = re.compile(r"<[^>]+>")
ASSET = re.compile(r"\.(png|jpe?g|gif|svg|webp|avif|css|js|ico|pdf)$", re.I)
PHONE = re.compile(r"(?:\+33|0)[\s.\-]?[1-9](?:[\s.\-]?\d{2}){4}")
TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
DESCRIPTION = re.compile(r"""<meta[^>]+name=["']description["'][^>]*content=["']([^"']*)""", re.I)
OG_DESCRIPTION = re.compile(r"""<meta[^>]+property=["']og:description["'][^>]*content=["']([^"']*)""", re.I)

FREEMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "hotmail.com", "hotmail.fr", "outlook.com", "outlook.fr",
    "live.fr", "live.com", "msn.com", "yahoo.fr", "yahoo.com", "ymail.com", "icloud.com",
    "me.com", "mac.com", "orange.fr", "wanadoo.fr", "free.fr", "sfr.fr", "neuf.fr",
    "cegetel.net", "laposte.net", "bbox.fr", "aol.com", "aol.fr", "numericable.fr",
    "club-internet.fr", "aliceadsl.fr", "noos.fr", "voila.fr", "tele2.fr",
    "protonmail.com", "proton.me", "gmx.fr", "gmx.com", "tutanota.com",
}
LEGAL_WORDS = {
    "sarl", "sas", "sasu", "eurl", "scp", "selarl", "selas", "selafa", "sa", "ei", "eirl", "sci",
    "snc", "sca", "societe", "ste", "et", "de", "du", "des", "la", "le", "les", "l", "d", "and", "en",
}
MULTI_LEVEL_SUFFIXES = ("gouv.fr", "asso.fr", "nom.fr", "com.fr", "co.uk", "ac.uk", "com.au")

# Clauses qui interdisent de collecter : la citation exacte part dans BLOCKED.md.
ACTS = (
    r"extraction|extraire|aspiration|aspirer|moissonnage|scraping|crawling"
    r"|collecte automatis\w+|collecter automatiquement|collecte (?:des|d.)\s*(?:adresses|e-?mails?|courriels?)"
)
BANS = r"interdit\w*|prohib\w*|n.?est pas autoris\w+|ne sont pas autoris\w+|forbidden|not permitted|strictly prohibited"
TERMS_FORBID = re.compile(r"(?:(?:%s)\b.{0,120}?\b(?:%s))|(?:(?:%s)\b.{0,120}?\b(?:%s))" % (ACTS, BANS, BANS, ACTS), re.I | re.S)

_blocked_write = threading.Lock()


class GuardrailError(Exception):
    """Un garde-fou empeche de continuer. Le message dit quoi faire."""


class ConfigError(GuardrailError):
    pass


class TermsNotReviewed(GuardrailError):
    pass


class TermsForbidden(GuardrailError):
    pass


class ForbiddenHost(GuardrailError):
    pass


class Blocked(Exception):
    """Le site a refuse (403, 429, anti-bot...). On s'arrete pour cet hote."""

    def __init__(self, host, reason):
        super().__init__(f"{reason}:{host}")
        self.host, self.reason = host, reason


class Disallowed(Exception):
    """robots.txt interdit cette URL."""


class Unreachable(Exception):
    """Reseau, DNS, delai depasse. Ce n'est pas un refus, et ce n'est pas un site absent."""


class Response:
    def __init__(self, status, headers, body, url):
        self.status = status
        self.headers = {str(k).lower(): v for k, v in (headers or {}).items()}
        self.body = body or b""
        self.url = url

    def text(self):
        match = re.search(r"charset=([\w-]+)", self.headers.get("content-type", ""), re.I)
        try:
            return self.body.decode(match.group(1) if match else "utf-8", "replace")
        except LookupError:
            return self.body.decode("utf-8", "replace")


class Page:
    def __init__(self, url, status, content):
        self.url, self.status, self.html = url, status, content
        self.text = visible_text(content)


class UrllibTransport:
    """Transport reel. Ne suit jamais une redirection : le client decide, apres robots.txt."""

    def __init__(self, timeout=15, max_bytes=MAX_BYTES):
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None

        self._opener = urllib.request.build_opener(NoRedirect)
        self.timeout = timeout
        self.max_bytes = max_bytes

    def request(self, method, url, headers, data=None):
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=self.timeout) as resp:
                return Response(resp.status, dict(resp.headers.items()), resp.read(self.max_bytes), resp.geturl())
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read(self.max_bytes)
            except Exception:
                body = b""
            return Response(exc.code, dict(exc.headers.items()) if exc.headers else {}, body, url)
        except (urllib.error.URLError, socket.timeout, TimeoutError, OSError, ValueError,
                http.client.HTTPException) as exc:
            raise Unreachable(repr(exc)[:120])


class HostThrottle:
    """Un creneau par hote, partage par tous les fils d'execution."""

    def __init__(self, interval=DEFAULT_INTERVAL, clock=time.monotonic, sleep=time.sleep):
        self.interval = max(MIN_INTERVAL, float(interval))
        self.clock, self.sleep = clock, sleep
        self._guard = threading.Lock()
        self._slots = {}

    def wait(self, host, delay=0):
        interval = max(self.interval, float(delay or 0))
        with self._guard:
            slot = self._slots.setdefault(host, [threading.Lock(), None])
        with slot[0]:
            if slot[1] is not None:
                gap = slot[1] + interval - self.clock()
                if gap > 0:
                    self.sleep(gap)
            slot[1] = self.clock()


# --- Texte et adresses ---------------------------------------------------------------

def normalize(text):
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def tokens(name):
    return [t for t in re.split(r"[^a-z0-9]+", normalize(name)) if t and t not in LEGAL_WORDS]


def visible_text(page):
    """Ce qu'un visiteur lit : ni script, ni style, ni commentaire."""
    return html.unescape(TAG.sub(" ", DROP.sub(" ", COMMENT.sub(" ", page or ""))))


def registrable(domain):
    parts = (domain or "").lower().rstrip(".").split(".")
    if ".".join(parts[-2:]) in MULTI_LEVEL_SUFFIXES:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def host_of(url):
    url = (url or "").strip().lower()
    if not url:
        return ""
    try:
        host = urllib.parse.urlsplit(url if "://" in url else "http://" + url).hostname or ""
    except ValueError:
        return ""
    return re.sub(r"^www\d?\.", "", host)


def is_under(domain, parents):
    return any(domain == parent or domain.endswith("." + parent) for parent in parents)


def published_emails(page_html, text):
    """Adresses en mailto ou en clair. Aucune forme [at], aucun motif reconstitue."""
    found = set()
    for raw in list(MAILTO.findall(page_html or "")) + EMAIL.findall(text or ""):
        email = urllib.parse.unquote(raw).strip().strip(".,;:'\"").lower()
        if EMAIL.fullmatch(email) and not ASSET.search(email):
            found.add(email)
    return found


def mask_contacts(text):
    return re.sub(r"\s+", " ", PHONE.sub("[tel]", EMAIL.sub("[mail]", text or ""))).strip()


def first_match(pattern, page):
    match = pattern.search(page or "")
    return html.unescape(TAG.sub(" ", match.group(1))).strip()[:200] if match else ""


def terms_forbid(text):
    """Renvoie la phrase qui interdit la collecte, ou chaine vide."""
    flat = re.sub(r"\s+", " ", text or "")
    found = TERMS_FORBID.search(flat)
    return flat[max(0, found.start() - 60): found.end() + 60].strip()[:400] if found else ""


# --- Configuration et chemins --------------------------------------------------------

def load_config(project, path=None):
    config_path = Path(path) if path else Path(project) / "config.json"
    if not config_path.exists():
        raise ConfigError(f"Configuration absente : {config_path}. Copie config/trade.example.json.")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    missing = [key for key in ("user_agent", "segments") if not config.get(key)]
    if missing:
        raise ConfigError("Configuration incomplete, cles manquantes : " + ", ".join(missing))
    check_user_agent(config["user_agent"])
    for segment in config["segments"]:
        if not segment.get("name") or not segment.get("title_regex"):
            raise ConfigError("Chaque segment doit avoir `name` et `title_regex`.")
        re.compile(segment["title_regex"])
    return config


def check_user_agent(agent):
    if not agent or BROWSER_UA.search(agent):
        raise ConfigError(
            "User-Agent refuse : il doit nommer ce projet, jamais imiter un navigateur. "
            "Exemple : mon-projet/1.0 (+https://mon-site.example/contact)"
        )
    return agent


def check_workers(count):
    if count > MAX_CONNECTIONS:
        raise ConfigError(
            f"{count} connexions refusees (maximum {MAX_CONNECTIONS}). Au-dela, une ligne partagee "
            "sature et des sites vivants passent pour absents."
        )
    return max(1, count)


def raw_dir(project, source):
    path = Path(project) / "data" / "raw" / source
    path.mkdir(parents=True, exist_ok=True)
    return path


def record_blocked(project, source, host, reason, quote=""):
    """Une ligne par refus dans data/raw/<source>/BLOCKED.md, citation exacte comprise."""
    path = raw_dir(project, source) / "BLOCKED.md"
    with _blocked_write:
        fresh = not path.exists()
        with path.open("a", encoding="utf-8") as handle:
            if fresh:
                handle.write(f"# BLOCKED : {source}\n\nDate | Hote | Raison | Citation\n--- | --- | --- | ---\n")
            clean = re.sub(r"\s+", " ", quote).replace("|", "/")
            handle.write(f"{dt.date.today().isoformat()} | {host} | {reason} | {clean}\n")


REVIEW_FIELDS = ("source", "kind", "robots_url", "terms_url", "read_at", "verdict", "licence", "quote")


def review_path(project, source):
    return Path(project) / "reviews" / f"{source}.json"


def require_terms_review(project, source):
    """Bloque tant que robots.txt et les conditions de la source n'ont pas ete lus."""
    path = review_path(project, source)
    if not path.exists():
        raise TermsNotReviewed(
            f"Aucune requete pour `{source}` : {path} est absent. Lis d'abord robots.txt et les conditions "
            "(scripts/read_terms.py), puis ecris la relecture (voir template/reviews/)."
        )
    review = json.loads(path.read_text(encoding="utf-8"))
    empty = [field for field in REVIEW_FIELDS if not str(review.get(field, "")).strip()]
    if empty:
        raise TermsNotReviewed(f"{path} incomplet : " + ", ".join(empty))
    try:
        read_at = dt.date.fromisoformat(str(review["read_at"])[:10])
    except ValueError:
        raise TermsNotReviewed(f"{path} : read_at doit etre une date ISO.")
    if read_at > dt.date.today():
        raise TermsNotReviewed(f"{path} : read_at est dans le futur.")
    if review["verdict"] == "interdit":
        record_blocked(project, source, review.get("terms_url", "?"), "conditions", review["quote"])
        raise TermsForbidden(f"`{source}` interdit la collecte : voir BLOCKED.md. Ne pas y retourner sans accord ecrit.")
    if review["verdict"] != "autorise":
        raise TermsNotReviewed(f"{path} : verdict doit valoir `autorise` ou `interdit`.")
    return review


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="", errors="replace") as handle:
        return list(csv.DictReader(handle))


# --- Client HTTP unique --------------------------------------------------------------

class Client:
    def __init__(self, project, source, config, transport=None, clock=time.monotonic, sleep=time.sleep,
                 terms_bootstrap=None):
        self.project, self.source, self.config = Path(project), source, config
        self.agent = check_user_agent(config["user_agent"])
        self.transport = transport or UrllibTransport()
        self.throttle = HostThrottle(config.get("min_interval_seconds", DEFAULT_INTERVAL), clock, sleep)
        # read_terms.py seul peut demander a lire robots.txt et la page des conditions avant relecture.
        self.bootstrap = set(terms_bootstrap or ())
        if not self.bootstrap:
            require_terms_review(self.project, source)
        self.excluded = tuple(FORBIDDEN_HOSTS) + tuple(h.lower() for h in config.get("excluded_hosts", []))
        self._robots, self._robots_guard = {}, threading.Lock()
        self._robots_locks = {}
        self._blocked_guard = threading.Lock()
        self._blocked_path = raw_dir(self.project, source) / "blocked_hosts.txt"
        self.blocked = set()
        if self._blocked_path.exists():
            self.blocked = {h for h in self._blocked_path.read_text(encoding="utf-8").split("\n") if h}

    # Garde-fous --------------------------------------------------------------------

    def _assert_allowed(self, url):
        parts = urllib.parse.urlsplit(url)
        host = host_of(url)
        if parts.scheme not in ("http", "https") or not host:
            raise ForbiddenHost(f"URL refusee : {url}")
        if is_under(host, self.excluded):
            raise ForbiddenHost(f"Hote exclu par les garde-fous : {host}")
        with self._blocked_guard:
            if host in self.blocked:
                raise Blocked(host, "deja_bloque")
        return host

    def _block(self, host, reason, quote=""):
        with self._blocked_guard:
            if host not in self.blocked:
                self.blocked.add(host)
                with self._blocked_path.open("a", encoding="utf-8") as handle:
                    handle.write(host + "\n")
        record_blocked(self.project, self.source, host, reason, quote)
        raise Blocked(host, reason)

    def block(self, url, reason, quote=""):
        """Arret decide par un script, par exemple une page legale qui interdit la collecte."""
        self._block(host_of(url), reason, quote)

    def _headers(self, accept):
        return {"User-Agent": self.agent, "Accept": accept}

    def _send(self, host, method, url, accept, data=None):
        response = self.transport.request(method, url, self._headers(accept), data)
        if response.status in BLOCK_STATUS:
            self._block(host, f"http_{response.status}")
        if ANTIBOT.search(response.body[:6000].decode("utf-8", "replace")):
            self._block(host, "anti-bot")
        return response

    def robots_for(self, url):
        """Lit robots.txt de l'origine une seule fois, avant toute page."""
        parts = urllib.parse.urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        host = self._assert_allowed(url)
        with self._robots_guard:
            cached = self._robots.get(origin)
            lock = self._robots_locks.setdefault(origin, threading.Lock())
        if cached is not None:
            return cached
        with lock:
            with self._robots_guard:
                cached = self._robots.get(origin)
            if cached is not None:
                return cached
            parser = urllib.robotparser.RobotFileParser()
            self.throttle.wait(host)
            robots_url = origin + "/robots.txt"
            response = self._send(host, "GET", robots_url, "text/plain,*/*")
            if response.status == 200:
                parser.parse(response.text().splitlines())
            elif response.status >= 500:
                raise Unreachable(f"robots.txt {response.status}")
            elif response.status in REDIRECT_STATUS:
                raise Unreachable("robots.txt redirige")
            else:  # 404 et autres 4xx : pas de robots.txt publie
                parser.parse([])
            delay = parser.crawl_delay(self.agent) if parser.last_checked else None
            if delay and float(delay) > MAX_CRAWL_DELAY:
                self._block(host, "crawl_delay_excessif")
            with self._robots_guard:
                self._robots[origin] = (parser, float(delay or 0))
            return self._robots[origin]

    def ensure_robots(self, url):
        self.robots_for(url)

    def _request(self, method, url, accept, data=None):
        host = self._assert_allowed(url)
        if self.bootstrap and url not in self.bootstrap:
            raise TermsNotReviewed(f"Avant relecture, seules les conditions peuvent etre lues : {url}")
        parser, delay = self.robots_for(url)
        if not parser.can_fetch(self.agent, url):
            raise Disallowed(url)
        self.throttle.wait(host, delay)
        return self._send(host, method, url, accept, data)

    # Lecture -----------------------------------------------------------------------

    def get(self, url, accept="text/html,*/*;q=0.5"):
        """Suit les redirections une par une, chacune repassant par tous les garde-fous."""
        current = url
        for _ in range(MAX_REDIRECTS + 1):
            response = self._request("GET", current, accept)
            if response.status in REDIRECT_STATUS and response.headers.get("location"):
                target = urllib.parse.urljoin(current, response.headers["location"])
                if LOGIN_PATH.search(urllib.parse.urlsplit(target).path):
                    self._block(host_of(target), "page_derriere_un_compte")
                current = target
                if self.bootstrap:
                    self.bootstrap.add(current)
                continue
            response.url = current
            return response
        raise Unreachable("trop de redirections")

    def page(self, url):
        """Une page HTML lisible, ou None."""
        response = self.get(url)
        ctype = response.headers.get("content-type", "text/html").lower()
        if response.status != 200 or ("html" not in ctype and "text" not in ctype):
            return None
        return Page(response.url, response.status, response.text())

    def get_json(self, url):
        response = self.get(url, "application/json")
        if response.status != 200:
            raise Unreachable(f"HTTP {response.status} sur {url}")
        try:
            return json.loads(response.body)
        except ValueError:
            raise Unreachable(f"Reponse JSON illisible sur {url}")

    def post_form(self, url, fields):
        body = urllib.parse.urlencode(fields).encode()
        response = self._request("POST", url, "application/json", body)
        if response.status != 200:
            raise Unreachable(f"HTTP {response.status} sur {url}")
        return json.loads(response.body)
