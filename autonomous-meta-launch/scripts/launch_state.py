"""state.json : la memoire du lancement.

Chaque identifiant est ecrit des que Meta le renvoie. Plusieurs envois peuvent
tourner en parallele : on fusionne avec le disque sous verrou, puis on remplace
le fichier d'un coup pour qu'une coupure ne le laisse jamais a moitie ecrit.
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile

try:
    import fcntl
except ImportError:  # Windows : pas de verrou, donc pas d'envois en parallele
    fcntl = None

BUCKETS = ("adsets", "videos", "video_files", "images", "creatives", "ads", "revisions")
LISTS = ("retired_creatives", "cleanup_failed")


class StateError(RuntimeError):
    pass


class State:
    def __init__(self, path, mode):
        self.path = pathlib.Path(path)
        self.lock_path = pathlib.Path(str(self.path) + ".lock")
        self.data = self._read()
        if self.data.get("mode") not in (None, mode):
            raise StateError("%s appartient au mode %s, pas %s" % (self.path, self.data.get("mode"), mode))
        self.data["mode"] = mode
        self._normalize(self.data)

    @staticmethod
    def _normalize(data):
        for bucket in BUCKETS:
            data.setdefault(bucket, {})
        for name in LISTS:
            data.setdefault(name, [])

    def _read(self):
        return json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, bucket, key, value):
        if key is None:
            self.data[bucket] = value
        else:
            self.data[bucket][key] = value
        self.save()

    def _write(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle, tmp = tempfile.mkstemp(prefix=".state-", dir=str(self.path.parent))
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            json.dump(data, out, ensure_ascii=False, indent=1)
        os.replace(tmp, str(self.path))

    def _locked(self, action):
        with open(str(self.lock_path), "w") as lock:
            if fcntl:
                fcntl.flock(lock, fcntl.LOCK_EX)
            return action()

    def save(self):
        def merge():
            disk = self._read()
            self._normalize(disk)
            for key, value in self.data.items():
                if isinstance(value, dict):
                    disk.setdefault(key, {}).update(value)
                elif isinstance(value, list):
                    disk[key] = disk.get(key, []) + [v for v in value if v not in disk.get(key, [])]
                else:
                    disk[key] = value
            self._write(disk)
            self.data = disk
        self._locked(merge)

    def replace(self):
        """Ecrit l'etat tel quel : seul un nettoyage retire des cles."""
        self._locked(lambda: self._write(self.data))
