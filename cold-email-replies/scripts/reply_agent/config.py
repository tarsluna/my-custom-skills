"""Configuration : le métier dans un fichier JSON, les secrets dans l'environnement. Jamais de clé dans le JSON."""
from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

INTENTS = ("yes", "meeting_request", "question", "later", "no", "out_of_office", "other")

INTENT_LABELS = {
    "yes": "oui",
    "meeting_request": "demande de rendez-vous",
    "question": "question",
    "later": "pas maintenant",
    "no": "non",
    "out_of_office": "absence",
    "other": "non classée",
}

DEFAULTS: Dict[str, Any] = {
    "brand": {"name": "Votre agence", "sender_name": "Votre prénom"},
    # Le lien de réservation envoyé avec le livrable. Un événement dédié au cold email permet de savoir d'où vient le rendez-vous.
    "booking_url": None,
    "deliverable": {
        "name": "audit",
        # static : un même lien pour tous (guide, vidéo). webhook : votre générateur crée un livrable par prospect.
        "mode": "static",
        "static_url": None,
        # Un livrable par prospect se fabrique à partir d'un domaine. Un guide commun n'en a pas besoin.
        "requires_domain": None,
        "max_per_day": 10,
        "reuse_days": 30,
        "stuck_hours": 36,
    },
    "reply": {
        "greeting": "Bonjour {first_name},",
        "greeting_without_name": "Bonjour,",
        "company_fallback": "votre entreprise",
        "lines": [
            "{greeting}",
            "",
            "Votre {deliverable_name} est prêt : {link}",
            "",
            "On vous propose de vous présenter le reste lors d'un appel. Si vous trouvez ça pertinent, réservez votre créneau ici : {booking_url}",
            "",
            "{sender_name}",
            "{brand_name}",
        ],
    },
    "classifier": {
        # rules : mots-clés, hors ligne, pour tester. claude : un appel au modèle par réponse, pour la production.
        "mode": "rules",
        "model": "claude-opus-5-5",
        "min_confidence": 0.8,
        "max_attempts": 5,
        "offer_context": "The prospect received a cold email offering a free personalised audit of their business, and was asked to reply \"ok\" to receive it, or \"non\" to stop receiving emails.",
        # Mots-clés du mode rules, sans accents et en minuscules. Un mot finissant par * est un préfixe.
        "keywords": {
            "no": [
                "non", "non merci", "pas interesse*", "stop", "desinscri*", "desabonn*", "retirez", "supprimez",
                "ne plus recevoir", "ne m'ecrivez plus", "arretez", "unsubscribe", "remove me", "not interested", "no thanks",
            ],
            "out_of_office": [
                "absent*", "en conge*", "out of office", "de retour le", "back on", "reponse automatique", "automatic reply",
                "auto-reply", "ne fait plus partie", "a quitte", "no longer with",
            ],
            "later": [
                "pas maintenant", "plus tard", "pas pour le moment", "pas le moment", "l'annee prochaine", "recontactez-moi",
                "revenez vers moi", "not now", "maybe later", "next year",
            ],
            "meeting_request": [
                "rendez-vous", "rdv", "appel", "appelez-moi", "creneau*", "visio", "telephone", "dispo", "disponible*",
                "call", "meeting", "book a time",
            ],
            "yes": [
                "ok", "okay", "oui", "go", "volontiers", "avec plaisir", "envoyez*", "je veux bien", "interesse*", "d'accord",
                "partant*", "yes", "sure", "send it", "sounds good", "interested",
            ],
            "question": ["combien", "c'est quoi", "qui etes", "comment ca marche", "how much", "what is", "who are"],
        },
    },
    "tool_categories": {
        # Catégories de la classification native de l'outil d'envoi qui valent un oui. Vérifiez les numéros dans votre compte.
        "positive": {"1": "Interested", "2": "Meeting Request"},
        # La catégorie de l'outil peut confirmer un oui quand l'agent hésite. Faut-il aussi lui laisser transformer une question en oui ?
        "upgrade_questions": False,
    },
    "alerts": {"new_lead_title": "NOUVEAU LEAD", "sent_title": "audit envoyé"},
    "crm": {"stages": {"new_lead": None, "sent": "Audit envoyé", "booked": "Appel booké"}},
    "consumer_mailboxes": [
        "gmail", "googlemail", "hotmail", "outlook", "live", "msn", "yahoo", "ymail", "aol", "icloud", "me", "proton",
        "protonmail", "gmx", "orange", "wanadoo", "free", "sfr", "laposte", "neuf", "bbox",
    ],
    "timezone": "Europe/Paris",
    "poll_interval_seconds": 180,
    "smartlead": {"pace_seconds": 1.1, "page_size": 100, "max_pages": 50},
}

PLACEHOLDERS = ("greeting", "first_name", "company", "link", "booking_url", "sender_name", "brand_name", "deliverable_name")


class ConfigError(ValueError):
    pass


def deep_merge(base: Dict[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if key.startswith("_"):
            continue  # commentaires du JSON d'exemple
        if isinstance(value, Mapping) and isinstance(out.get(key), dict) and key != "positive":
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _is_url(value: Any) -> bool:
    return isinstance(value, str) and re.match(r"^https?://[^\s/]+\.[^\s]+$", value) is not None


def validate(cfg: Dict[str, Any]) -> Dict[str, Any]:
    d = cfg["deliverable"]
    if d["mode"] not in ("static", "webhook"):
        raise ConfigError("deliverable.mode doit valoir static ou webhook")
    if d["mode"] == "static" and not _is_url(d.get("static_url")):
        raise ConfigError("deliverable.static_url doit être une URL en mode static")
    if d["requires_domain"] is None:
        d["requires_domain"] = d["mode"] == "webhook"
    for name in ("max_per_day", "reuse_days", "stuck_hours"):
        if not isinstance(d[name], (int, float)) or d[name] < 1:
            raise ConfigError("deliverable.%s doit être un nombre supérieur ou égal à 1" % name)
    c = cfg["classifier"]
    if c["mode"] not in ("rules", "claude"):
        raise ConfigError("classifier.mode doit valoir rules ou claude")
    if not (0 < float(c["min_confidence"]) <= 1):
        raise ConfigError("classifier.min_confidence doit être entre 0 et 1")
    unknown = set(c["keywords"]) - set(INTENTS)
    if unknown:
        raise ConfigError("classifier.keywords : intentions inconnues %s" % sorted(unknown))
    if cfg["booking_url"] is not None and not _is_url(cfg["booking_url"]):
        raise ConfigError("booking_url doit être une URL")
    template = "\n".join(cfg["reply"]["lines"]) + cfg["reply"]["greeting"]
    for field in re.findall(r"{([^{}]*)}", template):
        if field not in PLACEHOLDERS:
            raise ConfigError("reply : champ inconnu {%s}. Champs possibles : %s" % (field, ", ".join(PLACEHOLDERS)))
    if "{link}" not in template:
        raise ConfigError("reply.lines doit contenir {link}, sinon le prospect ne reçoit pas ce qu'il a demandé")
    cfg["tool_categories"]["positive"] = {str(k): str(v) for k, v in cfg["tool_categories"]["positive"].items()}
    return cfg


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    cfg = copy.deepcopy(DEFAULTS)
    if path:
        cfg = deep_merge(cfg, json.loads(Path(path).read_text(encoding="utf-8")))
    return validate(cfg)


def parse_campaign_ids(raw: str) -> List[str]:
    """Plusieurs campagnes séparées par des virgules ou des espaces. Tout ce qui n'est pas un numéro est ignoré."""
    return [part for part in re.split(r"[\s,;]+", raw or "") if part.isdigit()]


def env_settings(environ: Mapping[str, str] = os.environ) -> Dict[str, Any]:
    def opt(name: str) -> Optional[str]:
        value = (environ.get(name) or "").strip()
        return value or None

    return {
        "enabled": (environ.get("REPLY_AGENT_ENABLED") or "").strip().lower() in ("1", "true", "yes", "on"),
        "smartlead_api_key": opt("SMARTLEAD_API_KEY"),
        "campaign_ids": parse_campaign_ids(environ.get("SMARTLEAD_CAMPAIGN_IDS", "")),
        "slack_webhook_url": opt("SLACK_WEBHOOK_URL"),
        "crm_webhook_url": opt("CRM_WEBHOOK_URL"),
        "crm_webhook_secret": opt("CRM_WEBHOOK_SECRET"),
        "deliverable_api_url": opt("DELIVERABLE_API_URL"),
        "deliverable_api_key": opt("DELIVERABLE_API_KEY"),
        "booking_url": opt("BOOKING_URL"),
        "db_path": opt("REPLY_AGENT_DB") or "reply-agent.sqlite3",
    }
