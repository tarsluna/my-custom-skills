#!/usr/bin/env python3
"""caps.py <projet> A01 : transcrit build/voice.wav (faster-whisper, langue forcée) et écrit captions.json, groupes de sous-titres à relire."""
import re

from common import Project, cli, read_json, whisper_model, write_json


def merge_tokens(raw):
    """Recolle les élisions et traits d'union que Whisper sort en jetons séparés."""
    words = []
    for tok, start, end in raw:
        tok = tok.strip()
        if not tok:
            continue
        if words and tok[0] in "'’-":
            words[-1]["text"] += tok
            words[-1]["end"] = round(end, 3)
        else:
            words.append({"id": f"w{len(words)}", "text": tok, "start": round(start, 3), "end": round(end, 3)})
    return words


def group_words(words, duration, max_words=4, max_chars=22, gap=.25):
    """Groupes d'une ligne : coupés au nombre de mots, à la largeur, aux blancs et à la ponctuation."""
    groups, cur = [], []

    def flush():
        if not cur:
            return
        text = re.sub(r"[.,;:]+$", "", " ".join(x["text"].strip() for x in cur))
        groups.append({"t0": round(cur[0]["start"], 3), "t1": round(min(cur[-1]["end"], duration), 3), "text": text})
        cur.clear()

    for w in words:
        if not w["text"].strip():
            continue
        n = len(" ".join(x["text"].strip() for x in cur + [w]))
        if cur and (len(cur) >= max_words or n > max_chars or w["start"] - cur[-1]["end"] >= gap):
            flush()
        cur.append(w)
        if re.search(r"[.?!,;:]$", w["text"].strip()):
            flush()
    flush()
    return groups


def main(argv=None):
    args = cli(__doc__, ad=True).parse_args(argv)
    P = Project(args.project)
    A = P.ads / args.ad
    limits = P.style["captions"]
    if args.dry_run:
        print(f"Transcrirait {A / 'build/voice.wav'} ({P.config['transcription']['captions']}, {P.language}), {limits['max_words']} mots et {limits['max_chars']} caractères max par groupe")
        return
    out = A / "build/caps"
    out.mkdir(parents=True, exist_ok=True)
    model = whisper_model(P.config["transcription"]["captions"])
    segs, _ = model.transcribe(str(A / "build/voice.wav"), language=P.language, word_timestamps=True, vad_filter=False, beam_size=5, condition_on_previous_text=False)
    words = merge_tokens((w.word, w.start, w.end) for s in segs for w in s.words or [])
    write_json(out / "transcript.json", words)
    duration = read_json(A / "build/timeline.json")["duration"]
    groups = group_words(words, duration, limits["max_words"], limits["max_chars"])
    write_json(A / "captions.json", groups)
    print(f"{args.ad}: {len(groups)} sous-titres, {len(words)} mots -> {A / 'captions.json'}")


if __name__ == "__main__":
    main()
