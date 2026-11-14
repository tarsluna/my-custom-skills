#!/usr/bin/env python3
"""track.py <projet> A17 [secondes] : fait suivre la tête au recadrage vertical au début de la pub (écrit "vx" dans edit.json).

Pour une prise qui démarre pendant que la personne s'installe. Relance cut.py ensuite.
"""
import subprocess

from common import FFMPEG, FPS, Project, cli, even, read_json, write_json


def main(argv=None):
    a = cli(__doc__, ad=True)
    a.add_argument("seconds", nargs="?", type=float, default=4.0)
    args = a.parse_args(argv)
    N = args.seconds
    P = Project(args.project)
    A = P.ads / args.ad
    E = read_json(A / "edit.json")
    T = read_json(A / "build/timeline.json")
    if args.dry_run:
        print(f"{args.ad}: segments concernés : {[k for k, s in enumerate(T['segments']) if s['start'] < N]} (rien écrit)")
        return
    import cv2
    import numpy as np
    vcrop = E.get("vcrop")
    front = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    prof = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
    FS = 10
    for k, seg in enumerate(T["segments"]):
        if seg["start"] >= N:
            E["segments"][k].pop("vx", None)
            continue
        sw, sh = P.size(seg["take"])
        W, H = 960, even(960 * sh / sw)
        side = int(min(W, H) * .13)
        start, dur = seg["a"] / FPS, (seg["b"] - seg["a"]) / FPS
        raw = subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(P.cam(seg["take"])),
                              "-vf", f"fps={FS},{P.mirror()}scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
        frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W)
        ts, xs = [], []
        for i, f in enumerate(frames):
            found = []
            for det, g, flipped in ((front, f, False), (prof, f, False), (prof, cv2.flip(f, 1), True)):
                for (x, y, w, h) in det.detectMultiScale(g, 1.08, 5, minSize=(side, side)):
                    found.append((w * h, (W - x - w / 2) if flipped else x + w / 2))
            if found:
                ts.append(i / FS)
                xs.append(max(found)[1] / W * sw)
        (vw, _, sx, _), _, _ = P.crops(seg["take"], vcrop)
        grid = np.arange(0, dur + .001, .1)
        if len(ts) < 3:
            print(k, "pas assez de visages")
            continue
        x = np.interp(grid, ts, xs)
        x = np.array([np.median(x[max(0, i - 3): i + 4]) for i in range(len(x))])
        x = np.convolve(np.pad(x, 4, mode="edge"), np.ones(9) / 9, "valid")
        px = x - vw / 2
        last = seg["end"] >= N or k == len(T["segments"]) - 1 or T["segments"][k + 1]["start"] >= N
        if last:  # retour en douceur sur le cadre fixe pendant la dernière seconde
            w = np.clip((grid - (dur - 1.0)) / 1.0, 0, 1)
            px = px * (1 - w) + sx * w
        px = np.clip(px, 0, sw - vw)
        step = max(1, int(round(len(grid) / 18)))
        keys = [[round(float(grid[i]), 3), int(px[i]) // 2 * 2] for i in range(0, len(grid), step)]
        if keys[-1][0] < grid[-1]:
            keys.append([round(float(grid[-1]), 3), int(px[-1]) // 2 * 2])
        E["segments"][k]["vx"] = keys
        print(f"seg {k}: {seg['take']} {dur:.2f}s, {len(ts)}/{len(frames)} visages, x {min(p for _, p in keys)}..{max(p for _, p in keys)} (fixe {sx})")
    write_json(A / "edit.json", E)


if __name__ == "__main__":
    main()
