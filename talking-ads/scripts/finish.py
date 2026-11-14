#!/usr/bin/env python3
"""finish.py <projet> A01 slug [--deliver DOSSIER] : rend V et H, contrôle durée et son, écrit les planches QA."""
import pathlib
import shutil
import subprocess

from common import FFMPEG, FPS, Project, cli, ff, probe, read_json, run


def render_cmd(P, hf, out):
    r = P.config["render"]
    return ["npx", "--yes", f"hyperframes@{r['hyperframes']}", "render", hf, "-o", out, "-f", FPS, "-q", r["quality"], "--sdr", "-w", r["workers"], "--quiet"]


def loudness(f):
    err = subprocess.run([FFMPEG, "-nostdin", "-hide_banner", "-i", str(f), "-af", "ebur128=framelog=quiet:peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr.splitlines()
    return [l for l in err if " I:" in l][-1].split()[1], [l for l in err if "Peak:" in l][-1].split()[1]


def main(argv=None):
    a = cli(__doc__, ad=True)
    a.add_argument("slug")
    a.add_argument("--deliver", help="copie aussi les deux fichiers dans ce dossier")
    args = a.parse_args(argv)
    P = Project(args.project)
    A = P.ads / args.ad
    name = P.config["name"]
    targets = [("Vertical", "hf-v"), ("Horizontal", "hf-h")]
    if args.dry_run:
        for fmt, sub in targets:
            print(" ".join(str(c) for c in render_cmd(P, A / sub, P.out / f"{name}-{args.ad}-{args.slug}-{fmt}.mp4")))
        return
    P.out.mkdir(exist_ok=True)
    Q = A / "qa"
    Q.mkdir(exist_ok=True)
    (A / "slug.txt").write_text(args.slug + "\n", encoding="utf-8")
    deliver = pathlib.Path(args.deliver).expanduser() if args.deliver else None
    if deliver:
        deliver.mkdir(parents=True, exist_ok=True)
    expected = read_json(A / "build/timeline.json")["duration"]
    for fmt, sub in targets:
        f = P.out / f"{name}-{args.ad}-{args.slug}-{fmt}.mp4"
        run(render_cmd(P, A / sub, f), stdout=subprocess.DEVNULL)  # HyperFrames attend seul si un autre rendu tourne
        dur = float(probe(f))
        I, TP = loudness(f)
        n = 12
        ff("-i", f, "-vf", f"fps={n}/{dur:.3f},scale=270:-2,tile={n}x1", "-frames:v", "1", Q / f"{fmt}.jpg")
        if deliver:
            shutil.copy2(f, deliver / f.name)
        gap = "" if abs(dur - expected) < .15 else f"  ECART : montage {expected:.2f}s"
        print(f"{f.name}: {dur:.2f}s{gap}  {I} LUFS  peak {TP} dBFS  {f.stat().st_size / 1e6:.0f} Mo  planche {Q / (fmt + '.jpg')}")


if __name__ == "__main__":
    main()
