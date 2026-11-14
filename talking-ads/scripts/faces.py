#!/usr/bin/env python3
"""faces.py <projet> : position médiane du visage dans chaque prise, écrite dans work/faces.json."""
import statistics as st
import tempfile

from common import FFMPEG, Project, cli, run, write_json


def main(argv=None):
    args = cli(__doc__).parse_args(argv)
    P = Project(args.project)
    if args.dry_run:
        print(f"Mesurerait {len(P.takes)} prises, miroir {'oui' if P.config['mirror'] else 'non'}")
        return
    import cv2
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    scale = "scale='if(gt(iw,ih),1280,-2)':'if(gt(iw,ih),-2,1280)'"
    out = dict(P.faces)
    for t, info in P.takes.items():
        pts = []
        for k in range(1, 9):
            with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
                run([FFMPEG, "-nostdin", "-v", "error", "-y", "-ss", f"{info['dur'] * k / 9:.2f}", "-i", P.cam(t), "-frames:v", "1",
                     "-vf", f"{P.mirror()}{scale}", "-q:v", "3", tmp.name])
                im = cv2.imread(tmp.name, cv2.IMREAD_GRAYSCALE)
            H, W = im.shape
            side = int(min(H, W) / 6)
            fs = cas.detectMultiScale(im, 1.08, 6, minSize=(side, side))
            if len(fs):
                x, y, w, h = max(fs, key=lambda b: b[2] * b[3])
                pts.append((float((x + w / 2) / W), float((y + h / 2) / H), float(h / H)))
        if pts:
            out[t] = {"cx": round(st.median(p[0] for p in pts), 4), "cy": round(st.median(p[1] for p in pts), 4), "h": round(st.median(p[2] for p in pts), 4), "n": len(pts)}
        print(t, out.get(t, "aucun visage : recadrage au centre"), flush=True)
    write_json(P.faces_file, out)


if __name__ == "__main__":
    main()
