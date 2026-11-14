#!/usr/bin/env python3
"""gen.py <projet> A01 : plan.json + captions.json + build/ -> hf-v (9:16 plein cadre) et hf-h (16:9 sur fond flou).

Montage texte seul : sous-titres, mots-clés en gros au centre, hook sur l'horizontal, zooms réguliers, effets sonores.
Tout ce qui se voit se règle dans style.json.
"""
import html
import json
import os
import shutil
from itertools import combinations

from common import TEMPLATE, Project, cli, probe, read_json


def esc(s):
    return html.escape(str(s), quote=False)


def link(src, dst):
    """Lien dur quand c'est possible : les vidéos intermédiaires pèsent lourd."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def clamp_i(v, a, b):
    return int(max(a, min(b, v)))


def kw_lines(text):
    """Coupe un mot-clé long en 2 ou 3 lignes équilibrées pour qu'il reste très gros."""
    if "\n" in text:
        return text.split("\n")
    w = text.split()
    if len(text) <= 13 or len(w) == 1:
        return [text]
    best = None
    for n in (2, 3):
        if len(w) < n:
            continue
        for cut in combinations(range(1, len(w)), n - 1):
            parts = [" ".join(w[a:b]) for a, b in zip((0,) + cut, cut + (len(w),))]
            score = max(map(len, parts)) + (n - 2) * 1.5
            if best is None or score < best[0]:
                best = (score, parts)
    return best[1]


class Composer:
    def __init__(self, P, ad):
        self.P, self.ad = P, ad
        self.A = P.ads / ad
        self.B = self.A / "build"
        self.plan = read_json(self.A / "plan.json")
        self.timeline = read_json(self.B / "timeline.json")
        self.D = self.timeline["duration"]
        self.caps = read_json(self.A / "captions.json")
        self.kw = sorted(self.plan.get("keywords", []), key=lambda k: k["t"])
        self.s = P.style

    # ---- ce qui se voit ----
    def css(self):
        s, f, c = self.s, self.s["font"], self.s["colors"]
        cap = s["captions"]
        fam = f"'{f['family']}',sans-serif"
        return f"""@font-face{{font-family:'{f['family']}';src:url('assets/fonts/{os.path.basename(f['file'])}');font-weight:{f['weight_range']}}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;background:{c['background']};overflow:hidden}}
#root{{position:absolute;left:0;top:0;width:1080px;height:1920px;background:{c['background']};overflow:hidden}}
.capw{{position:absolute;left:40px;width:1000px;height:140px;display:flex;align-items:center;justify-content:center}}
.cap{{color:{c['caption']};font:{f['weight']} {cap['size']}px/{cap['line_height']} {fam};letter-spacing:{f['tracking_em']}em;text-align:center;white-space:nowrap}}
.kw{{position:absolute;left:0;top:0;width:1080px;height:1920px}}
.kdim{{position:absolute;left:0;top:0;width:1080px;height:1920px;background:{c['keyword_dim']}}}
.kt{{position:absolute;left:60px;top:0;width:960px;height:1920px;display:flex;align-items:center;justify-content:center;text-align:center;color:{c['keyword']};font-family:{fam};font-weight:{f['weight']};line-height:.98;letter-spacing:{f['tracking_em']}em;text-transform:uppercase}}
"""

    def css_vertical(self):
        s, f = self.s, self.s["font"]
        return f"""#cam{{position:absolute;left:0;top:0;width:1080px;height:1920px;transform-origin:50% 62%}}
#base{{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}}
.capw{{top:{s['captions']['top_vertical']}px}}
.hv{{position:absolute;left:80px;right:80px;bottom:{s['hook']['bottom_vertical']}px;color:{s['colors']['hook']};font-family:'{f['family']}',sans-serif;font-weight:{f['weight']};line-height:1.04;letter-spacing:{f['tracking_em']}em;text-align:center;text-wrap:balance}}
"""

    def css_horizontal(self):
        s, f = self.s, self.s["font"]
        return f"""#bg{{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}}
.scrim{{position:absolute;left:0;top:0;width:1080px;height:1920px;background:{s['colors']['scrim']}}}
#hwin{{position:absolute;left:0;top:656px;width:1080px;height:608px;overflow:hidden}}
#hcam{{position:absolute;left:0;top:0;width:1080px;height:608px;transform-origin:50% 56%}}
#hv{{position:absolute;left:0;top:0;width:1080px;height:608px;object-fit:cover}}
.capw{{top:{s['captions']['top_horizontal']}px}}
.hh{{position:absolute;left:60px;right:60px;bottom:{s['hook']['bottom_horizontal']}px;color:{s['colors']['hook']};font-family:'{f['family']}',sans-serif;font-weight:{f['weight']};line-height:1.04;letter-spacing:{f['tracking_em']}em;text-align:center;text-wrap:balance}}
.hh .tg{{line-height:1}}
.hh .go{{margin-top:16px;line-height:1.08}}
"""

    def kept_captions(self):
        """Sous-titres sans chevauchement, retirés pendant les mots-clés au centre."""
        res = []
        for i, c in enumerate(self.caps):
            t0, t1 = float(c["t0"]), float(c["t1"])
            nxt = float(self.caps[i + 1]["t0"]) if i + 1 < len(self.caps) else self.D
            t1 = min(max(t1 + .18, t0 + .42), nxt, self.D)
            skip = False
            for k in self.kw:
                a, b = float(k["t"]), float(k["t"]) + float(k["d"])
                ov = min(t1, b) - max(t0, a)
                if ov <= 0:
                    continue
                if ov >= .4 * (t1 - t0):
                    skip = True
                    break
                if t0 < a:
                    t1 = a
                else:
                    t0 = b
            if not skip and t1 - t0 >= .12:
                res.append((t0, t1, c["text"]))
        return res

    def captions_html(self):
        return "\n".join(f'<div id="c{i}" class="clip capw" data-start="{a:.3f}" data-duration="{b - a:.3f}" data-track-index="5" data-track-kind="captions"><div class="cap">{esc(t)}</div></div>'
                         for i, (a, b, t) in enumerate(self.kept_captions()))

    def keywords_html(self):
        k_s, out = self.s["keywords"], []
        for i, k in enumerate(self.kw):
            lines = kw_lines(str(k["text"]))
            n = max(len(l) for l in lines)
            size = clamp_i(950 / (k_s["char_width_em"] * max(n, 1)), k_s["min_size"], k_s["max_size"])
            body = "<br>".join(esc(l) for l in lines)
            out.append(f'<div id="k{i}" class="clip kw" data-start="{float(k["t"]):.3f}" data-duration="{float(k["d"]):.3f}" data-track-index="6" data-track-kind="graphics"><div class="kdim"></div><div class="kt" style="font-size:{size}px">{body}</div></div>')
        return "\n".join(out)

    def hook_text(self):
        return self.plan.get("h_goal") or self.plan.get("hook") or ""

    def hook_h_html(self):
        """Hook horizontal : la cible en gros et l'offre dessous, ou l'offre seule."""
        h, tg, go = self.s["hook"], self.plan.get("h_target", ""), self.hook_text()
        if tg:
            st = clamp_i(940 / (h["char_width_em"] * len(tg)), h["target_min"], h["target_max"])
            sg = clamp_i(h["goal_max"] * 46 / max(46, len(go)), h["goal_min"], h["goal_max"])
            return f'<div class="hh"><div class="tg" style="font-size:{st}px">{esc(tg)}</div><div class="go" style="font-size:{sg}px">{esc(go)}</div></div>'
        if not go:
            return ""
        return f'<div class="hh"><div class="tg" style="font-size:{clamp_i(h["alone_max"] * 46 / max(46, len(go)), h["alone_min"], h["alone_max"])}px">{esc(go)}</div></div>'

    def hook_v_html(self):
        """Désactivé par défaut (hook.on_vertical) : le vertical ne porte que les sous-titres et les mots-clés."""
        text = self.hook_text()
        if not self.s["hook"]["on_vertical"] or not text:
            return ""
        size = clamp_i(84 * 34 / max(34, len(text) + 6), 72, 84)
        d = min(float(self.plan.get("hook_d", 4.4)), self.D)
        return f'<div id="hook" class="clip hv" data-start="0" data-duration="{d:.3f}" data-track-index="7" style="font-size:{size}px">{esc(text)}</div>'

    # ---- le rythme ----
    def beats(self):
        """Plans de zoom : chaque raccord, chaque fin de mot-clé, puis un changement sur un début de groupe quand le plan dure."""
        z = self.s["zoom"]
        seams = sorted(float(x) for x in self.timeline.get("seams", []))
        ends = {round(float(k["t"]) + float(k["d"]), 3) for k in self.kw if float(k["t"]) + float(k["d"]) < self.D - .8}
        fixed = sorted({0.0, *seams, *ends})
        starts = [float(c["t0"]) for c in self.caps]
        pts = []
        for p in fixed:
            if pts and p - pts[-1] < 1.0 and p not in seams:
                continue
            if pts and p - pts[-1] < 1.0 and pts[-1] not in seams and pts[-1] > 0:
                pts.pop()
            pts.append(p)
        out = []
        for a, b in zip(pts, pts[1:] + [self.D]):
            out.append(a)
            last = a
            while b - last > z["max_shot"]:
                c = [s for s in starts if last + z["min_shot"] <= s <= b - 1.6]
                if not c:
                    break
                last = c[0]
                out.append(last)
        return out

    def zoom_js(self, sel, levels):
        pts, z = self.beats(), self.s["zoom"]
        js = []
        for i, (a, b) in enumerate(zip(pts, pts[1:] + [self.D])):
            level = levels[i % len(levels)]
            drift = round(level * (1 + min(z["drift_max"], z["drift_per_s"] * (b - a))), 4)
            js.append(f"tl.fromTo('{sel}',{{scale:{level}}},{{scale:{drift},duration:{b - a:.3f},ease:'none',immediateRender:false}},{a:.3f});")
        return "\n".join(js)

    # ---- le son ----
    def sfx_table(self):
        """Fichiers disponibles dans <projet>/<sfx.dir>, avec leur durée. Un son absent est ignoré, pas bloquant."""
        cfg, table = self.s["sfx"], {}
        wanted = [x["file"] for x in cfg["keyword"]] + ([cfg["zoom"]["file"]] if cfg.get("zoom") else [])
        for name in wanted:
            f = self.P.root / cfg["dir"] / name
            if not f.is_file():
                print(f"Son absent, ignoré : {cfg['dir']}/{name}")
            elif name not in table:
                table[name] = (f, float(probe(f)))
        return table

    def audio_tags(self, table):
        D, cfg = self.D, self.s["sfx"]
        tags = [f'<audio id="voice" class="clip" src="assets/voice.wav" data-start="0" data-duration="{D:.3f}" data-volume="1" data-track-index="40"></audio>']
        n = 0

        def add(at, name, volume, track):
            nonlocal n
            d = table[name][1]
            tags.append(f'<audio id="sfx{n}" class="clip" src="assets/sfx/{name}" data-start="{max(0, at):.3f}" data-duration="{d:.3f}" data-volume="{volume}" data-track-index="{track}"></audio>')
            n += 1

        for k in self.kw:
            t = float(k["t"])
            for x in cfg["keyword"]:
                if x["file"] in table and t + x["offset"] + table[x["file"]][1] < D:
                    add(t + x["offset"], x["file"], x["volume"], 41 + (n % 2))
        z = cfg.get("zoom")
        if z and z["file"] in table:
            near = [float(k["t"]) for k in self.kw] + [float(k["t"]) + float(k["d"]) for k in self.kw]
            for i, t in enumerate(self.beats()):
                if i % z["every"] == 0 or t + table[z["file"]][1] >= D or any(abs(t - x) < .5 for x in near):
                    continue
                add(t + z["offset"], z["file"], z["volume"], 43)
        return "\n".join(tags)

    # ---- l'assemblage ----
    def page(self, css, body, js):
        return f"""<!doctype html>
<html lang="{self.P.language}"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>{self.css()}{css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{self.D:.3f}" data-width="1080" data-height="1920">
{body}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{js}
window.__timelines["main"]=tl;
</script>
</body></html>
"""

    def setup(self, hf, table):
        if hf.exists():
            shutil.rmtree(hf)
        hf.mkdir()
        for n in ("hyperframes.json", "package.json"):
            shutil.copy(TEMPLATE / "hf" / n, hf / n)
        (hf / "meta.json").write_text(json.dumps({"id": f"{self.ad}-{hf.name}", "name": f"{self.ad} {hf.name}"}))
        font = self.P.root / self.s["font"]["file"]
        if not font.is_file():
            raise SystemExit(f"Police introuvable : {font}. Corrige font.file dans style.json.")
        link(font, hf / "assets/fonts" / font.name)
        link(self.B / "voice.wav", hf / "assets/voice.wav")
        for name, (f, _) in table.items():
            link(f, hf / "assets/sfx" / name)

    def warnings(self):
        """Contrôles non bloquants, pour que chaque sous-agent voie ses écarts au brief."""
        out, cap = [], self.s["captions"]
        for c in self.caps:
            if len(c["text"].split()) > cap["max_words"] or len(c["text"]) > cap["max_chars"]:
                out.append(f"Sous-titre trop long : {c['text']}")
        for k in self.kw:
            if float(k["t"]) + float(k["d"]) > self.D:
                out.append(f"Mot-clé qui dépasse la fin : {k['text']}")
        return out

    def build(self):
        Z = self.s["zoom"]
        table = self.sfx_table()
        audio = self.audio_tags(table)
        hfv = self.A / "hf-v"
        self.setup(hfv, table)
        link(self.B / "vert.mp4", hfv / "assets/vert.mp4")
        body = [f'<div id="cam"><video id="base" class="clip" src="assets/vert.mp4" data-start="0" data-duration="{self.D:.3f}" muted playsinline data-track-index="0"></video></div>',
                self.hook_v_html(), self.captions_html(), self.keywords_html(), audio]
        (hfv / "index.html").write_text(self.page(self.css_vertical(), "\n".join(x for x in body if x), self.zoom_js("#cam", Z["levels_vertical"])), encoding="utf-8")

        hfh = self.A / "hf-h"
        self.setup(hfh, table)
        link(self.B / "horiz.mp4", hfh / "assets/horiz.mp4")
        link(self.B / "bg.mp4", hfh / "assets/bg.mp4")
        body = [f'<video id="bg" class="clip" src="assets/bg.mp4" data-start="0" data-duration="{self.D:.3f}" muted playsinline data-track-index="0"></video>',
                '<div class="scrim"></div>',
                f'<div id="hwin"><div id="hcam"><video id="hv" class="clip" src="assets/horiz.mp4" data-start="0" data-duration="{self.D:.3f}" muted playsinline data-track-index="1"></video></div></div>',
                self.hook_h_html(), self.captions_html(), self.keywords_html(), audio]
        (hfh / "index.html").write_text(self.page(self.css_horizontal(), "\n".join(x for x in body if x), self.zoom_js("#hcam", Z["levels_horizontal"])), encoding="utf-8")


def main(argv=None):
    args = cli(__doc__, ad=True).parse_args(argv)
    P = Project(args.project)
    c = Composer(P, args.ad)
    for w in c.warnings():
        print("ATTENTION :", w)
    if args.dry_run:
        print(f"{args.ad}: {c.D:.2f}s  {len(c.kept_captions())} sous-titres  {len(c.kw)} mots-clés  {len(c.beats())} plans de zoom (rien écrit)")
        return
    c.build()
    print(f"{args.ad}: {c.D:.2f}s  {len(c.kept_captions())} sous-titres  {len(c.kw)} mots-clés")


if __name__ == "__main__":
    main()
