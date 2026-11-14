#!/usr/bin/env python3
"""text_pass.py <projet> [--ad A01] : texte fidèle des prises, ou du build/voice.wav d'une pub (contrôle final).

whisper.cpp si project.json ou l'environnement donne le binaire et le modèle, sinon faster-whisper.
Résultat : un JSON au format whisper.cpp, champ "transcription", liste de {"text": ...}.
"""
import subprocess

from common import Project, cli, read_json, run, whisper_model, write_json


def faithful(P, wav, base):
    """Transcrit wav vers <base>.json et renvoie le texte."""
    binary, model = P.tool_path("whisper_cpp_bin", "WHISPER_CPP_BIN"), P.tool_path("whisper_cpp_model", "WHISPER_CPP_MODEL")
    if binary and model:
        run([binary, "-m", model, "-f", wav, "-l", P.language, "-mc", "0", "-oj", "-of", base, "-np", "-t", "4"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        data = read_json(f"{base}.json")
    else:
        segs, _ = whisper_model(P.config["transcription"]["words"]).transcribe(str(wav), language=P.language, beam_size=5, condition_on_previous_text=False)
        data = {"transcription": [{"text": s.text} for s in segs]}
        write_json(f"{base}.json", data)
    return " ".join(x["text"].strip() for x in data["transcription"])


def main(argv=None):
    a = cli(__doc__)
    a.add_argument("--ad", help="ne traite que build/voice.wav de cette pub")
    args = a.parse_args(argv)
    P = Project(args.project)
    if args.ad:
        B = P.ads / args.ad / "build"
        if args.dry_run:
            print(f"Retranscrirait {B / 'voice.wav'}")
            return
        print(faithful(P, B / "voice.wav", B / "voice_text"))
        return
    out = P.transcripts / "text"
    todo = [t for t in P.takes if not (out / f"{t}.json").exists()]
    if args.dry_run:
        print(f"À passer : {' '.join(todo) or 'rien'}")
        return
    out.mkdir(parents=True, exist_ok=True)
    for t in todo:
        faithful(P, P.audio / f"{t}.wav", out / t)
        print(t, "fait", flush=True)


if __name__ == "__main__":
    main()
