#!/usr/bin/env python3
"""show.py <projet> T05 [début fin] : mot à mot d'une prise, avec les blancs de 0,25 s et plus."""
import argparse

from common import Project, read_json


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("project")
    a.add_argument("take")
    a.add_argument("start", nargs="?", type=float, default=0)
    a.add_argument("end", nargs="?", type=float, default=1e9)
    args = a.parse_args(argv)
    P = Project(args.project)
    words = [x for x in read_json(P.transcripts / f"{args.take}.json")["words"] if args.start <= x["s"] <= args.end]
    line, last = [], None

    def flush():
        if line:
            print(" ".join(line))
        line.clear()

    for x in words:
        if last is not None and x["s"] - last >= .25:
            flush()
            print(f"      --- blanc {x['s'] - last:.2f}s  ({last:.2f} -> {x['s']:.2f})")
        if not line:
            line.append(f"[{x['s']:7.2f}]")
        line.append(x["w"])
        last = x["e"]
        if len(line) > 14:
            flush()
    flush()


if __name__ == "__main__":
    main()
