#!/usr/bin/env python3
"""init_project.py <projet> [--rushes DOSSIER] [--name PREFIXE] [--language fr] : crée le dossier de projet."""
import argparse
import pathlib
import shutil
import sys

from common import TEMPLATE, read_json, write_json

DIRS = ("rushes", "audio", "transcripts/text", "work", "ads", "out", "sounds")


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("project")
    a.add_argument("--rushes", help="dossier des prises, s'il n'est pas <projet>/rushes")
    a.add_argument("--name", help="préfixe des fichiers livrés")
    a.add_argument("--language", help="langue parlée dans les prises, code ISO (fr, en, es...)")
    args = a.parse_args(argv)
    root = pathlib.Path(args.project).expanduser().resolve()
    if (root / "project.json").exists():
        sys.exit(f"{root} contient déjà un project.json : rien n'a été modifié.")
    for d in DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
    for f in ("BRIEF.md", "project.json", "style.json", "topup.example.json"):
        shutil.copy(TEMPLATE / f, root / f)
    shutil.copytree(TEMPLATE / "fonts", root / "fonts", dirs_exist_ok=True)
    cfg = read_json(root / "project.json")
    if args.rushes:
        cfg["rushes"] = str(pathlib.Path(args.rushes).expanduser().resolve())
    if args.name:
        cfg["name"] = args.name
    if args.language:
        cfg["language"] = args.language
    write_json(root / "project.json", cfg, indent=2)
    print(f"Projet prêt : {root}\nÀ remplir : project.json, style.json, BRIEF.md. Sons à poser dans sounds/ (voir references/03-sons.md).")


if __name__ == "__main__":
    main()
