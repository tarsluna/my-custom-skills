"""Un seul point de sortie HTTP, en bibliothèque standard. Aucune erreur ne contient l'URL : certaines portent la clé."""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional, Tuple

# (méthode, url, en-têtes, corps, délai) -> (statut, corps)
Http = Callable[[str, str, Dict[str, str], Optional[bytes], float], Tuple[int, bytes]]


class NetworkError(RuntimeError):
    """Délai dépassé ou connexion coupée : on ne sait pas si la requête est arrivée."""


def urllib_http(method: str, url: str, headers: Dict[str, str], body: Optional[bytes], timeout: float) -> Tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, method=method, headers={"user-agent": "cold-email-replies/1.0", **headers})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read() or b""
    except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as exc:
        raise NetworkError(type(exc).__name__) from None


def send_json(http: Http, method: str, url: str, payload: Any = None, headers: Optional[Dict[str, str]] = None, timeout: float = 30) -> Tuple[int, bytes]:
    all_headers = dict(headers or {})
    body = None
    if payload is not None:
        all_headers["content-type"] = "application/json; charset=utf-8"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return http(method, url, all_headers, body, timeout)


def parse_json(body: bytes) -> Any:
    try:
        return json.loads(body.decode("utf-8")) if body else None
    except (ValueError, UnicodeDecodeError):
        return None
