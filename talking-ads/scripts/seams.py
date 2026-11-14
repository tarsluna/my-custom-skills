#!/usr/bin/env python3
"""seams.py <projet> A01 : réécoute chaque raccord du voice.wav (±1,8 s) et donne le niveau juste au raccord."""
from common import Project, cli, read_json, whisper_model


def main(argv=None):
    args = cli(__doc__, ad=True).parse_args(argv)
    P = Project(args.project)
    B = P.ads / args.ad / "build"
    T = read_json(B / "timeline.json")
    points = [0.0] + T["seams"] + [T["duration"]]
    if args.dry_run:
        print(f"{args.ad}: {len(T['seams'])} raccords à réécouter : {T['seams']}")
        return
    import numpy as np
    import soundfile as sf
    a, sr = sf.read(str(B / "voice.wav"), dtype="float32")
    m = whisper_model(P.config["transcription"]["captions"])
    limit = P.config["audio"]["seam_max_db"]
    for i, t in enumerate(points):
        lo, hi = max(0, t - 1.8), min(T["duration"], t + 1.8)
        x = a[int(lo * sr): int(hi * sr)]
        k, w = int((t - lo) * sr), int(.03 * sr)
        db = 20 * np.log10(np.sqrt(np.mean(x[max(0, k - w): k + w] ** 2)) + 1e-9)
        y = np.interp(np.arange(0, len(x), sr / 16000), np.arange(len(x)), x).astype(np.float32)
        s, _ = m.transcribe(y, language=P.language, beam_size=5, condition_on_previous_text=False, vad_filter=False)
        flag = "  A REVOIR" if 0 < i < len(points) - 1 and db > limit else ""
        print(f"[{i:02d}] t={t:7.2f}  niveau raccord {db:6.1f} dB{flag} | " + " ".join(z.text.strip() for z in s), flush=True)


if __name__ == "__main__":
    main()
