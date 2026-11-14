#!/usr/bin/env python3
"""extract_audio.py <projet> : numérote les prises (T01, T02...) dans work/takes.json et extrait leur audio 16 kHz."""
import fnmatch

from common import Project, cli, ff, probe_video, read_json, write_json


def discover(rushes, include, exclude):
    """Fichiers vidéo triés par chemin, sans les captures d'écran ou sorties programme exclues."""
    found = []
    for p in sorted(rushes.rglob("*")):
        if not p.is_file() or p.name.startswith("."):
            continue
        rel = p.relative_to(rushes).as_posix().lower()
        if any(fnmatch.fnmatch(p.name.lower(), g.lower()) for g in include) and not any(fnmatch.fnmatch(rel, g.lower()) for g in exclude):
            found.append(p)
    return found


def main(argv=None):
    args = cli(__doc__).parse_args(argv)
    P = Project(args.project)
    cfg = P.config["takes"]
    files = discover(P.rushes, cfg["include"], cfg["exclude"])
    old = read_json(P.takes_file) if P.takes_file.is_file() else {}
    known = {v["file"]: k for k, v in old.items()}
    n = max([int(k[1:]) for k in old] or [0])
    takes = dict(old)
    for f in files:
        rel = f.relative_to(P.rushes).as_posix()
        tid = known.get(rel)
        if tid is None:
            n += 1
            tid = f"T{n:02d}"
        print(tid, rel, flush=True)
        if args.dry_run:
            continue
        if tid not in takes:
            takes[tid] = {"file": rel, **probe_video(f)}
        wav = P.audio / f"{tid}.wav"
        if not wav.exists():
            ff("-i", f, "-vn", "-ar", "16000", "-ac", "1", wav)
    if args.dry_run:
        print(f"{len(files)} prises trouvées dans {P.rushes} (rien écrit)")
        return
    write_json(P.takes_file, takes, indent=1)
    print(f"{len(takes)} prises dans work/takes.json")


if __name__ == "__main__":
    main()
