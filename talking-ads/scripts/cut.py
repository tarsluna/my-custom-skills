#!/usr/bin/env python3
"""cut.py <projet> A01 : lit ads/A01/edit.json, écrit build/{vert,horiz,bg}.mp4, voice.wav, words.json, timeline.json."""
import subprocess

from common import FFMPEG, FPS, Project, cli, ff, read_json, write_json


def snap(audio, sr, x, reach=.06):
    """Recale x au creux d'énergie le plus proche (fenêtre 20 ms, pas de 5 ms)."""
    hop, n, c = int(sr * .005), int(sr * .02), int(x * sr)
    best, best_v = c, float("inf")
    for k in range(int(-reach * sr), int(reach * sr), hop):
        i = max(0, c + k)
        seg = audio[i: i + n]
        if len(seg):
            v = float((seg ** 2).mean())
            if v < best_v:
                best_v, best = v, i
    return (best + n / 2) / sr


def resolve(segments, snap_fn=None):
    """Passe les segments en images sur la grille 30 i/s, après recalage éventuel."""
    res = []
    for s in segments:
        ss = s["s"] if s.get("nosnap") or not snap_fn else snap_fn(s["take"], s["s"])
        ee = s["e"] if s.get("nosnap") or not snap_fn else snap_fn(s["take"], s["e"])
        a, b = round(ss * FPS), round(ee * FPS)
        if b <= a:
            raise SystemExit(f"Segment vide ou inversé : {s}")
        res.append({**s, "a": a, "b": b})
    return res


def graph(P, res, vcrop):
    """Construit les entrées et le filtergraph, et place chaque segment sur la nouvelle timeline."""
    inputs, idx, fc, pos = [], {}, [], 0
    mirror = P.mirror()
    for i, s in enumerate(res):
        t = s["take"]
        if t not in idx:
            idx[t] = len(inputs) // 2
            inputs += ["-i", P.cam(t)]
        k, a, b = idx[t], s["a"], s["b"]
        n = b - a
        L = n / FPS
        (vw, vh, vx, vy), (hw, hh, hx, hy), (bw, bh, bx, by) = P.crops(t, vcrop)
        fc.append(f"[{k}:v]trim=start={a / FPS:.6f}:end={b / FPS:.6f},setpts=PTS-STARTPTS,fps={FPS},{mirror}split=3[s{i}a][s{i}b][s{i}c]")
        xval = vx
        if s.get("vx"):
            keys = s["vx"]
            e = str(keys[-1][1])
            for (t0, x0), (t1, x1) in reversed(list(zip(keys, keys[1:]))):
                e = f"if(lt(t,{t1:.3f}),{x0}+({x1}-{x0})*(t-{t0:.3f})/{t1 - t0:.3f},{e})"
            xval = "'" + e + "'"
        fc.append(f"[s{i}a]crop={vw}:{vh}:{xval}:{vy},scale=1080:1920:flags=lanczos,setsar=1[v{i}]")
        fc.append(f"[s{i}b]crop={hw}:{hh}:{hx}:{hy},scale=1920:1080:flags=lanczos,setsar=1[h{i}]")
        fc.append(f"[s{i}c]crop={bw}:{bh}:{bx}:{by},scale=270:480:flags=bilinear,gblur=sigma=11,eq=saturation=1.05:brightness=-0.04,scale=540:960:flags=bicubic,noise=alls=3:allf=t,setsar=1[b{i}]")
        fc.append(f"[{k}:a]atrim=start={a / FPS:.6f}:end={b / FPS:.6f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,pan=mono|c0=.5*c0+.5*c1,aformat=sample_fmts=fltp,afade=t=in:st=0:d=0.012,afade=t=out:st={max(0, L - .012):.6f}:d=0.012[a{i}]")
        s["start"], s["end"] = pos / FPS, (pos + n) / FPS
        pos += n
    N = len(res)
    for c in "vhb":
        fc.append("".join(f"[{c}{i}]" for i in range(N)) + f"concat=n={N}:v=1:a=0[{c}o]")
    fc.append("".join(f"[a{i}]" for i in range(N)) + f"concat=n={N}:v=0:a=1[ao]")
    return inputs, fc, pos


def denoise(P, raw, out):
    """DPDFNet (sherpa-onnx) si le modèle est fourni, sinon le débruiteur de ffmpeg."""
    model = P.tool_path("denoiser_model", "DPDFNET_MODEL")
    if not model:
        print("Pas de modèle DPDFNet : débruitage ffmpeg afftdn, plus faible. Voir README, section prérequis.")
        ff("-i", raw, "-af", "afftdn=nf=-25", "-c:a", "pcm_f32le", out)
        return
    import numpy as np
    import sherpa_onnx as so
    import soundfile as sf
    x, sr = sf.read(str(raw), dtype="float32")
    d = so.OfflineSpeechDenoiser(so.OfflineSpeechDenoiserConfig(model=so.OfflineSpeechDenoiserModelConfig(num_threads=4, dpdfnet=so.OfflineSpeechDenoiserDpdfNetModelConfig(model=str(model)))))
    r = d.run(x, sr)
    y = np.array(r.samples, dtype=np.float32)
    n = min(len(x), len(y))
    y = np.pad(y[:n], (0, len(x) - n))
    # 10 % de signal d'origine : la voix garde son grain.
    sf.write(str(out), np.clip(y + 10 ** (-20 / 20) * x, -1, 1), sr, subtype="FLOAT")


def level_voice(den, out, target):
    """Compression légère puis gain vers la cible de loudness. Renvoie (LUFS mesuré, gain appliqué)."""
    pre = "highpass=f=70,acompressor=threshold=-30dB:ratio=2.5:attack=8:release=140"
    err = subprocess.run([FFMPEG, "-nostdin", "-hide_banner", "-i", str(den), "-af", pre + ",ebur128=framelog=quiet", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    measured = float([l for l in err.splitlines() if "I:" in l][-1].split("I:")[1].split()[0])
    gain = target - measured
    ff("-i", den, "-af", f"{pre},volume={gain:.2f}dB,alimiter=limit=0.84:attack=2:release=60:level=0", "-ar", "48000", "-c:a", "pcm_s16le", out)
    return measured, gain


def main(argv=None):
    args = cli(__doc__, ad=True).parse_args(argv)
    P = Project(args.project)
    A = P.ads / args.ad
    B = A / "build"
    E = read_json(A / "edit.json")
    vcrop = E.get("vcrop")
    if args.dry_run:
        res = resolve(E["segments"])
        inputs, fc, pos = graph(P, res, vcrop)
        print(f"{args.ad}: {len(res)} segments, {pos / FPS:.2f}s, {len(inputs) // 2} prises, recadrages {P.crops(res[0]['take'], vcrop)}, {len(fc)} filtres (rien écrit)")
        return

    import soundfile as sf
    B.mkdir(parents=True, exist_ok=True)
    cache = {}

    def snap_at(t, x):
        if t not in cache:
            cache[t] = sf.read(str(P.audio / f"{t}.wav"), dtype="float32")
        return snap(*cache[t], x)

    res = resolve(E["segments"], snap_at)
    inputs, fc, pos = graph(P, res, vcrop)
    enc = ["-c:v", "libx264", "-preset", "fast", "-g", "30", "-keyint_min", "30", "-sc_threshold", "0", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", "-an"]
    ff(*inputs, "-filter_complex", ";".join(fc),
       "-map", "[vo]", *enc, "-crf", "15", B / "vert.mp4",
       "-map", "[ho]", *enc, "-crf", "15", B / "horiz.mp4",
       "-map", "[bo]", *enc, "-crf", "24", B / "bg.mp4",
       "-map", "[ao]", "-c:a", "pcm_f32le", B / "raw.wav")
    denoise(P, B / "raw.wav", B / "den.wav")
    measured, gain = level_voice(B / "den.wav", B / "voice.wav", P.config["audio"]["voice_lufs"])
    (B / "raw.wav").unlink()
    (B / "den.wav").unlink()

    # Les mots de chaque prise, replacés sur la nouvelle timeline.
    words = []
    for s in res:
        for w in read_json(P.transcripts / f"{s['take']}.json")["words"]:
            if s["a"] / FPS - .02 <= w["s"] < s["b"] / FPS:
                words.append({"w": w["w"], "s": round(w["s"] - s["a"] / FPS + s["start"], 3), "e": round(w["e"] - s["a"] / FPS + s["start"], 3)})
    write_json(B / "words.json", words)
    write_json(B / "timeline.json", {"duration": pos / FPS, "frames": pos, "seams": [s["end"] for s in res[:-1]], "segments": res,
                                     "voice_input_lufs": measured, "gain_db": round(gain, 2)}, indent=1)
    print(f"{args.ad}: {len(res)} segments, {pos / FPS:.2f}s, source {measured} LUFS, gain {gain:+.1f} dB")


if __name__ == "__main__":
    main()
