"""Texte d'une réponse : ce que le prospect a écrit, sans le fil cité, puis le mail qu'on lui renvoie."""
from __future__ import annotations

import re
import unicodedata
from html.parser import HTMLParser
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urlsplit

LOOKS_LIKE_HTML = re.compile(r"</?(?:html|body|div|p|br|span|table|blockquote|a|b|i|font)\b[^>]*>", re.I)

# Blocs de citation connus : Gmail, Yahoo, Thunderbird, Proton, Outlook.
QUOTE_CLASSES = {"gmail_quote", "gmail_quote_container", "gmail_attr", "yahoo_quoted", "moz-cite-prefix", "protonmail_quote", "outlookmessageheader"}
# Outlook web place le message cité après ces blocs, au même niveau : tout ce qui suit est du fil cité.
QUOTE_START_IDS = {"appendonsend", "divrplyfwdmsg", "mail-editor-reference-message-container"}
SKIP_TAGS = {"script", "style", "head", "blockquote", "title"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
BLOCK_TAGS = {"p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0
        self.stopped = False

    def handle_starttag(self, tag, attrs):
        if self.stopped:
            return
        if self.skip:
            if tag not in VOID_TAGS:
                self.skip += 1
            return
        attributes = dict(attrs)
        if (attributes.get("id") or "").lower() in QUOTE_START_IDS:
            self.stopped = True
            return
        classes = {c.lower() for c in (attributes.get("class") or "").split()}
        if tag in SKIP_TAGS or classes & QUOTE_CLASSES:
            if tag not in VOID_TAGS:
                self.skip = 1
            return
        if tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.stopped:
            return
        if self.skip:
            if tag not in VOID_TAGS:
                self.skip -= 1
            return
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.stopped and not self.skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    return "".join(parser.parts)


QUOTE_MARKERS = [
    re.compile(r"^[ \t]*On\b[^\n]{0,300}(?:\n[^\n]{0,300})?\bwrote\s*:[ \t]*$", re.I | re.M),
    re.compile(r"^[ \t]*Le\b[^\n]{0,300}(?:\n[^\n]{0,300})?\ba\s+[ée]crit\s*:[ \t]*$", re.I | re.M),
    re.compile(r"^[ \t]*-{2,}[ \t]*(?:original message|message d['’]origine|message original|forwarded message|message transf[ée]r[ée])", re.I | re.M),
    re.compile(r"^[ \t]*_{5,}[ \t]*$", re.M),
    re.compile(r"^[ \t]*(?:de|from)[ \t]*:[^\n]*\n(?:[^\n]*\n){0,2}?[ \t]*(?:envoy[ée]|sent|date|[àa]|to|objet|subject)[ \t]*:", re.I | re.M),
]


def strip_quoted_lines(text: str) -> str:
    unquoted = "\n".join(line for line in text.split("\n") if not re.match(r"^\s*>", line))
    cut = len(unquoted)
    for marker in QUOTE_MARKERS:
        hit = marker.search(unquoted)
        if hit and hit.start() < cut:
            cut = hit.start()
    return unquoted[:cut]


def reply_text(body: str, max_length: int = 20_000) -> str:
    """Le texte écrit par le prospect, sans le fil cité. C'est ce qui est gardé, classé et montré à l'équipe."""
    plain = html_to_text(body) if LOOKS_LIKE_HTML.search(body or "") else (body or "")
    plain = plain.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in strip_quoted_lines(plain).split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()[:max_length]


EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")
PHONE_FR = re.compile(r"(?:\+33|0033|0)[\s.\-]?(?:\(0\)[\s.\-]?)?[1-9](?:[\s.\-]?\d{2}){4}")
PHONE_ANY = re.compile(r"\+?\d[\d\s.\-()]{7,}\d")


def collapse(value: Optional[str]) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def redact_contacts(text: str) -> str:
    """Retire adresses et numéros : seul ce texte part chez le modèle qui classe."""
    without = PHONE_FR.sub(" ", EMAIL.sub(" ", text))
    without = PHONE_ANY.sub(lambda m: " " if len(re.sub(r"\D", "", m.group(0))) >= 9 else m.group(0), without)
    return collapse(without)


def normalize_for_match(text: str) -> str:
    """Minuscules, sans accents, apostrophes droites : la forme sous laquelle on cherche les mots-clés."""
    decomposed = unicodedata.normalize("NFKD", (text or "").replace("’", "'").lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


UNSAFE_NAME = re.compile("[@{}<>!☀-➿\U0001f000-\U0001faff]")


def _clean_name(value: Optional[str], max_length: int) -> Optional[str]:
    name = collapse(value)
    if not name or len(name) > max_length or UNSAFE_NAME.search(name):
        return None
    return name


def clean_first_name(value: Optional[str]) -> Optional[str]:
    """Un prénom n'entre dans le mail que s'il est propre ; sinon le gabarit prend sa formule neutre."""
    name = _clean_name(value, 40)
    return name if name and not re.search(r"\d", name) else None


def clean_company_name(value: Optional[str]) -> Optional[str]:
    return _clean_name(value, 80)


def _shouts(name: Optional[str]) -> bool:
    return bool(name and re.search(r"[^\W\d_]{3}", name) and name == name.upper())


def pick_company_name(from_deliverable: Optional[str], from_lead: Optional[str]) -> Optional[str]:
    """Un nom tout en capitales crie dans un mail : on lui préfère l'autre source, sinon la formule neutre du gabarit."""
    for name in (clean_company_name(from_deliverable), clean_company_name(from_lead)):
        if name and not _shouts(name):
            return name
    return None


DOMAIN = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{1,62}$")


def domain_from_free_text(value: Optional[str]) -> Optional[str]:
    raw = (value or "").strip().lower()
    if not raw:
        return None
    if "://" not in raw:
        raw = "http://" + raw
    try:
        host = urlsplit(raw).hostname
    except ValueError:
        return None
    if not host:
        return None
    host = host.rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host if DOMAIN.match(host) else None


def domain_from_email(email: Optional[str]) -> Optional[str]:
    if not email or "@" not in email:
        return None
    return domain_from_free_text(email.rsplit("@", 1)[1])


def company_domain(website: Optional[str], email: Optional[str], consumer_mailboxes: Iterable[str]) -> Optional[str]:
    """Le champ site du contact d'abord, sinon le domaine de son adresse s'il est professionnel. Jamais le texte de la réponse."""
    from_website = domain_from_free_text(website)
    if from_website:
        return from_website
    from_email = domain_from_email(email)
    if not from_email:
        return None
    consumer = set(consumer_mailboxes)
    # gmail.com, yahoo.de, orange.fr : quelle que soit l'extension, le domaine ne dit rien de l'entreprise.
    return None if any(label in consumer for label in from_email.split(".")[:-1]) else from_email


class _Strict(dict):
    def __missing__(self, key):
        raise KeyError(key)


def render_reply(cfg: Dict[str, Any], *, first_name: Optional[str], company: Optional[str], link: str, booking_url: Optional[str]) -> str:
    reply = cfg["reply"]
    values = _Strict(
        first_name=first_name or "",
        company=company or reply["company_fallback"],
        link=link,
        booking_url=booking_url or "",
        sender_name=cfg["brand"]["sender_name"],
        brand_name=cfg["brand"]["name"],
        deliverable_name=cfg["deliverable"]["name"],
    )
    values["greeting"] = reply["greeting"].format_map(values) if first_name else reply["greeting_without_name"]
    lines = []
    for line in reply["lines"]:
        if "{booking_url}" in line and not booking_url:
            continue  # sans lien de réservation configuré, la phrase qui le propose disparaît
        lines.append(line.format_map(values))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def escape_slack(text: str) -> str:
    """Slack lit <!channel>, <@U…> et <lien|texte> : une réponse de prospect ne doit ni prévenir tout un canal ni cacher un lien."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
