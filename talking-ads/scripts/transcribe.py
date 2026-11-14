#!/usr/bin/env python3
"""transcribe.py <projet> [--model NOM] : transcription mot à mot de chaque prise (faster-whisper, langue forcée)."""
from common import Project, cli, whisper_model, write_json


def main(argv=None):
    a = cli(__doc__)
    a.add_argument("--model", help="modèle faster-whisper, défaut : transcription.words dans project.json")
    args = a.parse_args(argv)
    P = Project(args.project)
    name = args.model or P.config["transcription"]["words"]
    todo = [t for t in P.takes if not (P.transcripts / f"{t}.json").exists()]
    if args.dry_run:
        print(f"Modèle {name}, langue {P.language}, à transcrire : {' '.join(todo) or 'rien'}")
        return
    if not todo:
        print("Tout est déjà transcrit.")
        return
    model = whisper_model(name, threads=8)
    for t in todo:
        segs, _ = model.transcribe(str(P.audio / f"{t}.wav"), language=P.language, word_timestamps=True, vad_filter=False,
                                   beam_size=5, condition_on_previous_text=False)
        words, text = [], []
        for s in segs:
            text.append(s.text.strip())
            for w in s.words or []:
                words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)})
        write_json(P.transcripts / f"{t}.json", {"id": t, "file": P.takes[t]["file"], "text": " ".join(text), "words": words})
        print(t, " ".join(text)[:90], flush=True)


if __name__ == "__main__":
    main()
