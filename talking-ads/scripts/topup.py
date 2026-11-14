#!/usr/bin/env python3
"""topup.py <projet> ajouts.json : ajoute des mots-clés à des pubs déjà montées, calés sur leurs sous-titres.

ajouts.json : {"A01": [[17.3, "extrait du sous-titre", "MOT-CLÉ"]]}. Sauvegarde dans work/plan-bak/.
Relance rerender.py ensuite.
"""
import shutil

from common import Project, cli, read_json, write_json


def add_keywords(plan, captions, items, min_gap=1.6):
    """Renvoie (mots-clés ajoutés, refus). Un mot-clé part au début du sous-titre qui contient l'extrait."""
    hook = float(plan.get("hook_d", 0))
    kw = plan.setdefault("keywords", [])
    added, refused = [], []
    for at, sub, text in items:
        m = [c for c in captions if sub.lower() in c["text"].lower()]
        if not m:
            refused.append((text, "introuvable"))
            continue
        c = min(m, key=lambda x: abs(float(x["t0"]) - at))
        t = float(c["t0"])
        if abs(t - at) > 1.0:
            refused.append((text, f"sous-titre trop loin ({t:.1f}s)"))
        elif t < hook:
            refused.append((text, "pendant le hook"))
        elif any(abs(float(k["t"]) - t) < min_gap for k in kw):
            refused.append((text, "trop proche d'un autre"))
        else:
            k = {"t": t, "d": round(max(1.15, .5 + .3 * len(text.split())) + .1, 2), "text": text}
            kw.append(k)
            added.append(k)
    kw.sort(key=lambda k: float(k["t"]))
    return added, refused


def main(argv=None):
    a = cli(__doc__)
    a.add_argument("additions")
    args = a.parse_args(argv)
    P = Project(args.project)
    for ad, items in read_json(args.additions).items():
        path = P.ads / ad / "plan.json"
        plan = read_json(path)
        added, refused = add_keywords(plan, read_json(P.ads / ad / "captions.json"), items)
        for text, why in refused:
            print(f"!! {ad} {text} : {why}")
        print(ad, len(plan["keywords"]), ", ".join(f'{float(k["t"]):.1f}:{k["text"]}' for k in plan["keywords"]))
        if not args.dry_run:
            (P.work / "plan-bak").mkdir(exist_ok=True)
            shutil.copy(path, P.work / "plan-bak" / f"{ad}.plan.json")
            write_json(path, plan)


if __name__ == "__main__":
    main()
