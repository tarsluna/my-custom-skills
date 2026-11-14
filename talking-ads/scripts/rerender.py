#!/usr/bin/env python3
"""rerender.py <projet> [A01 A02...] [--deliver DOSSIER] : régénère et rend à la chaîne, après un changement de style.

Sans identifiant, prend toutes les pubs qui ont un build/timeline.json. La découpe n'est pas refaite.
"""
import pathlib
import subprocess
import sys

from common import Project, cli

HERE = pathlib.Path(__file__).resolve().parent


def main(argv=None):
    a = cli(__doc__)
    a.add_argument("ads", nargs="*", help="identifiants, tous par défaut")
    a.add_argument("--deliver")
    args = a.parse_args(argv)
    P = Project(args.project)
    ids = args.ads or sorted(d.name for d in P.ads.iterdir() if (d / "build/timeline.json").is_file())
    for ad in ids:
        slug_file = P.ads / ad / "slug.txt"
        slug = slug_file.read_text(encoding="utf-8").strip() if slug_file.is_file() else "pub"
        extra = ["--dry-run"] if args.dry_run else []
        subprocess.run([sys.executable, str(HERE / "gen.py"), str(P.root), ad, *extra], check=True)
        cmd = [sys.executable, str(HERE / "finish.py"), str(P.root), ad, slug, *extra]
        if args.deliver:
            cmd += ["--deliver", args.deliver]
        subprocess.run(cmd, check=True)
    print(f"{len(ids)} pubs traitées")


if __name__ == "__main__":
    main()
