#!/usr/bin/env python3
"""Socle commun. Un projet est un dossier, donné en premier argument de chaque outil.

Aucune dépendance lourde ici : numpy, opencv, faster-whisper et sherpa-onnx sont importés
dans les fonctions qui s'en servent, pour que tout s'importe et tourne en --dry-run sans eux.
"""
import argparse
import json
import os
import pathlib
import subprocess

FPS = 30
SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "template"
FFMPEG = os.environ.get("FFMPEG_BIN") or "ffmpeg"
FFPROBE = os.environ.get("FFPROBE_BIN") or "ffprobe"


def read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def write_json(path, data, indent=0):
    pathlib.Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8")


def merged(base, over):
    """Fusion récursive : un fichier de projet partiel garde les valeurs par défaut du reste."""
    out = dict(base)
    for k, v in over.items():
        out[k] = merged(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def run(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def ff(*a):
    return run([FFMPEG, "-nostdin", "-v", "error", "-y", *a])


def probe(f, entry="format=duration"):
    return subprocess.check_output([FFPROBE, "-v", "error", "-show_entries", entry, "-of", "csv=p=0", str(f)]).decode().strip()


def probe_video(path):
    """Largeur, hauteur (rotation des téléphones comprise) et durée d'un fichier vidéo."""
    out = subprocess.check_output([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_streams", "-show_format", "-of", "json", str(path)])
    data = json.loads(out)
    st = data["streams"][0]
    w, h = int(st["width"]), int(st["height"])
    rotation = next((int(sd["rotation"]) for sd in st.get("side_data_list", []) if "rotation" in sd), 0)
    if abs(rotation) % 180 == 90:
        w, h = h, w
    return {"w": w, "h": h, "dur": round(float(data["format"]["duration"]), 3)}


def clamp(v, a, b):
    return max(a, min(b, v))


def even(v):
    return int(v) // 2 * 2


def whisper_model(name, threads=4):
    from faster_whisper import WhisperModel
    return WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=threads)


class Project:
    def __init__(self, root):
        self.root = pathlib.Path(root).expanduser().resolve()
        if not (self.root / "project.json").is_file():
            raise SystemExit(f"{self.root} n'est pas un projet : lance d'abord scripts/init_project.py")
        self.config = merged(read_json(TEMPLATE / "project.json"), read_json(self.root / "project.json"))
        style = self.root / "style.json"
        self.style = merged(read_json(TEMPLATE / "style.json"), read_json(style) if style.is_file() else {})
        self.audio = self.root / "audio"
        self.transcripts = self.root / "transcripts"
        self.work = self.root / "work"
        self.ads = self.root / "ads"
        self.out = self.root / "out"
        self._takes = None
        self._faces = None

    @property
    def language(self):
        return self.config["language"]

    @property
    def rushes(self):
        p = pathlib.Path(self.config["rushes"]).expanduser()
        return p if p.is_absolute() else self.root / p

    @property
    def takes_file(self):
        return self.work / "takes.json"

    @property
    def faces_file(self):
        return self.work / "faces.json"

    @property
    def takes(self):
        if self._takes is None:
            if not self.takes_file.is_file():
                raise SystemExit("work/takes.json manquant : lance d'abord extract_audio.py")
            self._takes = read_json(self.takes_file)
        return self._takes

    @property
    def faces(self):
        if self._faces is None:
            self._faces = read_json(self.faces_file) if self.faces_file.is_file() else {}
        return self._faces

    def tool_path(self, key, env):
        """Chemin d'un outil facultatif : variable d'environnement, sinon project.json (section tools)."""
        value = os.environ.get(env) or self.config["tools"].get(key) or ""
        if not value:
            return None
        p = pathlib.Path(value).expanduser()
        p = p if p.is_absolute() else self.root / p
        return p if p.exists() else None

    def cam(self, take):
        return self.rushes / self.takes[take]["file"]

    def size(self, take):
        t = self.takes[take]
        return t["w"], t["h"]

    def mirror(self):
        """Filtre à poser quand la caméra enregistre l'image retournée."""
        return "hflip," if self.config["mirror"] else ""

    def crops(self, take, vcrop=None):
        """Recadrages (l, h, x, y) dans la source : vertical, horizontal 16:9, fond flou."""
        W, H = self.size(take)
        face = self.faces.get(take) or {"cx": .5, "cy": .42}
        fx, fy = face["cx"] * W, face["cy"] * H
        fr = self.config["framing"]
        vh = even(round(H * (vcrop or fr["vcrop"])))
        vw = even(round(vh * 9 / 16))
        if vw > W:
            vw = even(W)
            vh = even(round(vw * 16 / 9))
        v = (vw, vh, even(clamp(round(fx - vw / 2), 0, W - vw)), even(clamp(round(fy - fr["v_face_y"] * vh), 0, H - vh)))
        hw = even(round(W * fr["h_width"]))
        hh = even(round(hw * 9 / 16))
        if hh > H:
            hh = even(H)
            hw = even(round(hh * 16 / 9))
        h = (hw, hh, even(clamp(round(fx - hw / 2), 0, W - hw)), even(clamp(round(fy - fr["h_face_y"] * hh), 0, H - hh)))
        bh = even(H)
        bw = min(even(round(H * 9 / 16)), even(W))
        b = (bw, bh, even(clamp(round(fx - bw / 2), 0, W - bw)), 0)
        return v, h, b


def cli(description, ad=False):
    """Analyseur commun : <projet> [ID] [--dry-run]."""
    p = argparse.ArgumentParser(description=description)
    p.add_argument("project", help="dossier du projet")
    if ad:
        p.add_argument("ad", help="identifiant de la pub, par exemple A01")
    p.add_argument("--dry-run", action="store_true", help="n'écrit rien, n'appelle ni ffmpeg ni modèle")
    return p
