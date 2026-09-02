#!/usr/bin/env python3
"""
Campaign Proposal PDF Builder.

Reads a markdown source and renders a branded PDF with:
- cover page (agency logo + title + client + date)
- small low-opacity agency logo on every content page (watermark)
- brand colors (primary for H2 / accent lines, dark for H1, body black)
- Helvetica, light/clean layout
- footer "<AGENCY_NAME> — Confidentiel" on every page

Branding is fully configurable (defaults are neutral):
  --agency  / env AGENCY_NAME     agency name (footer + replaces {{AGENCY_NAME}} in the markdown)
  --logo    / env AGENCY_LOGO     path to a PNG/JPG logo (cover + watermark); none → no logo
  --brand   / env AGENCY_BRAND    "#PRIMARY[,#DARK]" hex colors (default "#4A7FD4,#1E2A4A")
  --tagline / env AGENCY_TAGLINE  baseline printed at the bottom of the cover (default: none)

Dependencies: reportlab, pillow  →  pip install reportlab pillow

Markdown subset supported: H1 (#), H2 (##), H3 (###), paragraphs,
bullet lists (- ), pipe tables, **bold**, *italic*, horizontal rule (---),
trailing italic line.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    print("Missing dependency: pillow. Install it with:  pip install pillow", file=sys.stderr)
    sys.exit(2)

try:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas
except ImportError:  # pragma: no cover
    print("Missing dependency: reportlab. Install it with:  pip install reportlab", file=sys.stderr)
    sys.exit(2)

PAGE_W, PAGE_H = A4
MARGIN_L = 2.0 * cm
MARGIN_R = 2.0 * cm
MARGIN_T = 2.2 * cm
MARGIN_B = 2.0 * cm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

# Neutral default palette — override with --brand / AGENCY_BRAND.
DEFAULT_PRIMARY = "#4A7FD4"
DEFAULT_DARK = "#1E2A4A"

TEXT = HexColor("#111111")
MUTED = HexColor("#5A6480")
TABLE_BG = HexColor("#F4F7FC")
TABLE_BORDER = HexColor("#D9E1F1")
HR = HexColor("#E2E8F2")

FONT = "Helvetica"
FONT_B = "Helvetica-Bold"
FONT_I = "Helvetica-Oblique"

AGENCY_PLACEHOLDER = "{{AGENCY_NAME}}"


def parse_inline(text: str) -> list[tuple[str, str]]:
    """Return list of (font_token, text) segments. font_token in {n,b,i,bi}."""
    out: list[tuple[str, str]] = []
    pattern = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*)")
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            out.append(("n", text[pos:m.start()]))
        seg = m.group(0)
        if seg.startswith("**"):
            out.append(("b", seg[2:-2]))
        else:
            out.append(("i", seg[1:-1]))
        pos = m.end()
    if pos < len(text):
        out.append(("n", text[pos:]))
    return out


def font_for(tok: str) -> str:
    return {"n": FONT, "b": FONT_B, "i": FONT_I}.get(tok, FONT)


def measure(segments: list[tuple[str, str]], size: float) -> float:
    return sum(stringWidth(t, font_for(tok), size) for tok, t in segments)


def wrap_segments(segments: list[tuple[str, str]], size: float, max_w: float) -> list[list[tuple[str, str]]]:
    """Word-wrap rich segments preserving formatting."""
    lines: list[list[tuple[str, str]]] = [[]]
    cur_w = 0.0
    for tok, text in segments:
        words = re.split(r"(\s+)", text)
        for w in words:
            if not w:
                continue
            w_width = stringWidth(w, font_for(tok), size)
            if cur_w + w_width > max_w and lines[-1]:
                lines.append([])
                cur_w = 0.0
                if w.isspace():
                    continue
            lines[-1].append((tok, w))
            cur_w += w_width
    return [ln for ln in lines if ln]


def make_faded_logo(src: Path, opacity: float = 0.06) -> Path | None:
    """Bake a low-opacity copy of the logo for use as a watermark. Returns None if the image can't be read."""
    try:
        img = Image.open(src).convert("RGBA")
    except Exception as exc:  # unreadable / unsupported image
        print(f"warning: cannot read logo '{src}' ({exc}) — continuing without watermark", file=sys.stderr)
        return None
    r, g, b, a = img.split()
    a = a.point(lambda v: int(v * opacity))
    img.putalpha(a)
    out = Path(tempfile.gettempdir()) / f"proposal_watermark_{src.stem}.png"
    img.save(out)
    return out


def parse_brand(spec: str | None) -> tuple[HexColor, HexColor]:
    """Parse "#PRIMARY[,#DARK]" into two reportlab colors (defaults when missing)."""
    primary, dark = DEFAULT_PRIMARY, DEFAULT_DARK
    if spec:
        parts = [p.strip() for p in spec.split(",") if p.strip()]
        for p in parts:
            if not re.fullmatch(r"#?[0-9A-Fa-f]{6}", p):
                print(f"error: invalid brand color '{p}' — expected hex like #4A7FD4", file=sys.stderr)
                sys.exit(1)
        parts = [p if p.startswith("#") else f"#{p}" for p in parts]
        if len(parts) >= 1:
            primary = parts[0]
        if len(parts) >= 2:
            dark = parts[1]
    return HexColor(primary), HexColor(dark)


class ProposalPDF:
    def __init__(
        self,
        output: Path,
        client: str,
        date: str,
        logo: Path | None,
        agency: str = "",
        tagline: str = "",
        primary: HexColor | None = None,
        dark: HexColor | None = None,
    ):
        self.c = canvas.Canvas(str(output), pagesize=A4)
        self.client = client
        self.date = date
        self.logo = logo
        self.agency = agency.strip()
        self.tagline = tagline.strip()
        self.primary = primary or HexColor(DEFAULT_PRIMARY)
        self.dark = dark or HexColor(DEFAULT_DARK)
        self.watermark_logo = make_faded_logo(logo) if (logo and logo.exists()) else None
        self.y = PAGE_H - MARGIN_T
        self.page_num = 0
        self._cover_done = False

    # ---- page lifecycle ---------------------------------------------------
    def _watermark(self):
        if not self.watermark_logo or not self.watermark_logo.exists():
            return
        try:
            img = ImageReader(str(self.watermark_logo))
            iw, ih = img.getSize()
        except Exception:
            return
        # small logo, bottom-right corner, very low opacity (already baked in)
        target_w = 2.4 * cm
        scale = target_w / iw
        target_h = ih * scale
        x = PAGE_W - MARGIN_R - target_w
        y = 1.0 * cm
        self.c.drawImage(
            str(self.watermark_logo), x, y, width=target_w, height=target_h,
            mask="auto", preserveAspectRatio=True,
        )

    def _footer_text(self) -> str:
        return f"{self.agency} — Confidentiel" if self.agency else "Confidentiel"

    def _footer(self):
        self.c.setFillColor(MUTED)
        self.c.setFont(FONT, 8)
        self.c.drawString(MARGIN_L, 1.2 * cm, self._footer_text())
        # page number centered, watermark logo in right corner
        self.c.drawCentredString(PAGE_W / 2, 1.2 * cm, f"{self.page_num}")
        # top thin accent
        self.c.setStrokeColor(self.primary)
        self.c.setLineWidth(0.6)
        self.c.line(MARGIN_L, PAGE_H - 1.5 * cm, MARGIN_L + 1.5 * cm, PAGE_H - 1.5 * cm)

    def new_content_page(self):
        if self.page_num > 0:
            self.c.showPage()
        self.page_num += 1
        self._watermark()
        self._footer()
        self.y = PAGE_H - MARGIN_T

    def ensure_space(self, needed: float):
        if self.y - needed < MARGIN_B + 0.5 * cm:
            self.new_content_page()

    # ---- cover ------------------------------------------------------------
    def draw_cover(self):
        # logo top-center
        if self.logo and self.logo.exists():
            try:
                img = ImageReader(str(self.logo))
                iw, ih = img.getSize()
                target_w = 5.5 * cm
                scale = target_w / iw
                target_h = ih * scale
                self.c.drawImage(
                    str(self.logo),
                    (PAGE_W - target_w) / 2,
                    PAGE_H - 5 * cm,
                    width=target_w,
                    height=target_h,
                    mask="auto",
                    preserveAspectRatio=True,
                )
            except Exception as exc:
                print(f"warning: cannot draw logo '{self.logo}' ({exc}) — cover without logo", file=sys.stderr)

        # title block
        self.c.setFillColor(self.dark)
        self.c.setFont(FONT_B, 30)
        title = "Proposition de Campagne"
        tw = stringWidth(title, FONT_B, 30)
        self.c.drawString((PAGE_W - tw) / 2, PAGE_H / 2 + 1.0 * cm, title)

        self.c.setFillColor(self.primary)
        self.c.setFont(FONT_B, 18)
        cw = stringWidth(self.client, FONT_B, 18)
        self.c.drawString((PAGE_W - cw) / 2, PAGE_H / 2 - 0.2 * cm, self.client)

        # accent line
        self.c.setStrokeColor(self.primary)
        self.c.setLineWidth(1.5)
        self.c.line(
            (PAGE_W - 6 * cm) / 2, PAGE_H / 2 - 1.0 * cm,
            (PAGE_W + 6 * cm) / 2, PAGE_H / 2 - 1.0 * cm,
        )

        self.c.setFillColor(MUTED)
        self.c.setFont(FONT, 11)
        dw = stringWidth(self.date, FONT, 11)
        self.c.drawString((PAGE_W - dw) / 2, PAGE_H / 2 - 1.9 * cm, self.date)

        # footer brand: "<agency> — <tagline>" (either part optional)
        foot = " — ".join(p for p in (self.agency, self.tagline) if p)
        if foot:
            self.c.setFillColor(MUTED)
            self.c.setFont(FONT, 9)
            fw = stringWidth(foot, FONT, 9)
            self.c.drawString((PAGE_W - fw) / 2, 2.0 * cm, foot)
        self._cover_done = True
        # close cover page so subsequent content starts fresh
        self.c.showPage()

    # ---- text blocks ------------------------------------------------------
    def draw_h1(self, text: str):
        self.ensure_space(1.5 * cm)
        self.c.setFillColor(self.dark)
        self.c.setFont(FONT_B, 18)
        self.y -= 0.2 * cm
        self.c.drawString(MARGIN_L, self.y, text)
        self.y -= 0.35 * cm
        self.c.setStrokeColor(self.primary)
        self.c.setLineWidth(1.2)
        self.c.line(MARGIN_L, self.y, MARGIN_L + 2.0 * cm, self.y)
        self.y -= 0.5 * cm

    def draw_h2(self, text: str):
        self.ensure_space(1.1 * cm)
        self.c.setFillColor(self.primary)
        self.c.setFont(FONT_B, 13)
        self.y -= 0.1 * cm
        self.c.drawString(MARGIN_L, self.y, text)
        self.y -= 0.55 * cm

    def draw_h3(self, text: str):
        self.ensure_space(0.9 * cm)
        self.c.setFillColor(self.dark)
        self.c.setFont(FONT_B, 11)
        self.c.drawString(MARGIN_L, self.y, text)
        self.y -= 0.45 * cm

    def draw_paragraph(self, text: str, size: float = 10.5, leading: float = 0.50 * cm, italic: bool = False, color=TEXT, indent: float = 0.0):
        segments = parse_inline(text)
        if italic:
            segments = [("i", t) for _, t in segments]
        lines = wrap_segments(segments, size, CONTENT_W - indent)
        for line in lines:
            self.ensure_space(leading)
            x = MARGIN_L + indent
            self.c.setFillColor(color)
            for tok, t in line:
                self.c.setFont(font_for(tok), size)
                self.c.drawString(x, self.y, t)
                x += stringWidth(t, font_for(tok), size)
            self.y -= leading
        self.y -= 0.05 * cm

    def draw_bullet(self, text: str):
        size = 10.5
        leading = 0.48 * cm
        indent = 0.55 * cm
        segments = parse_inline(text)
        lines = wrap_segments(segments, size, CONTENT_W - indent)
        first = True
        for line in lines:
            self.ensure_space(leading)
            if first:
                self.c.setFillColor(self.primary)
                self.c.setFont(FONT_B, size)
                self.c.drawString(MARGIN_L + 0.15 * cm, self.y, "•")
                first = False
            x = MARGIN_L + indent
            self.c.setFillColor(TEXT)
            for tok, t in line:
                self.c.setFont(font_for(tok), size)
                self.c.drawString(x, self.y, t)
                x += stringWidth(t, font_for(tok), size)
            self.y -= leading

    def draw_hr(self):
        self.ensure_space(0.6 * cm)
        self.y -= 0.1 * cm
        self.c.setStrokeColor(HR)
        self.c.setLineWidth(0.6)
        self.c.line(MARGIN_L, self.y, PAGE_W - MARGIN_R, self.y)
        self.y -= 0.5 * cm

    def draw_table(self, rows: list[list[str]]):
        if not rows:
            return
        header, body = rows[0], rows[1:]
        n_cols = len(header)
        size = 9.5
        pad_x = 0.18 * cm
        pad_y = 0.18 * cm
        line_h = 0.42 * cm

        # column widths proportional to longest cell content (clamped)
        raw_widths = []
        for j in range(n_cols):
            longest = max(
                [stringWidth(header[j], FONT_B, size)] +
                [stringWidth(r[j] if j < len(r) else "", FONT, size) for r in body]
            )
            raw_widths.append(longest + 2 * pad_x)
        total_raw = sum(raw_widths)
        scale = CONTENT_W / total_raw
        col_w = [w * scale for w in raw_widths]

        def cell_lines(text, w, font):
            segs = parse_inline(text)
            if font == FONT_B:
                segs = [("b", t) for _, t in segs]
            return wrap_segments(segs, size, w - 2 * pad_x)

        def row_height(row, font):
            h = 0
            for j in range(n_cols):
                cell = row[j] if j < len(row) else ""
                lines = cell_lines(cell, col_w[j], font)
                h = max(h, len(lines) * line_h + 2 * pad_y)
            return max(h, line_h + 2 * pad_y)

        def render_row(row, font, bg=None):
            h = row_height(row, font)
            self.ensure_space(h + 0.05 * cm)
            x = MARGIN_L
            top_y = self.y
            if bg:
                self.c.setFillColor(bg)
                self.c.rect(x, top_y - h, CONTENT_W, h, stroke=0, fill=1)
            for j in range(n_cols):
                cell = row[j] if j < len(row) else ""
                lines = cell_lines(cell, col_w[j], font)
                cy = top_y - pad_y - line_h * 0.75
                for line in lines:
                    tx = x + pad_x
                    for tok, t in line:
                        font_name = FONT_B if (font == FONT_B or tok == "b") else (FONT_I if tok == "i" else FONT)
                        self.c.setFont(font_name, size)
                        self.c.setFillColor(self.dark if font == FONT_B else TEXT)
                        self.c.drawString(tx, cy, t)
                        tx += stringWidth(t, font_name, size)
                    cy -= line_h
                x += col_w[j]
            # borders
            self.c.setStrokeColor(TABLE_BORDER)
            self.c.setLineWidth(0.4)
            self.c.line(MARGIN_L, top_y - h, PAGE_W - MARGIN_R, top_y - h)
            self.y = top_y - h

        # top border
        self.ensure_space(0.4 * cm)
        self.c.setStrokeColor(TABLE_BORDER)
        self.c.setLineWidth(0.4)
        self.c.line(MARGIN_L, self.y, PAGE_W - MARGIN_R, self.y)
        # header
        render_row(header, FONT_B, bg=TABLE_BG)
        # body
        for r in body:
            render_row(r, FONT)
        self.y -= 0.25 * cm

    # ---- finalize ---------------------------------------------------------
    def save(self):
        self.c.save()


# -------- markdown parser ---------------------------------------------------

def parse_markdown(md: str) -> list[tuple[str, object]]:
    """Yield blocks as (kind, payload). Tables become ('table', rows)."""
    blocks: list[tuple[str, object]] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("# "):
            blocks.append(("h1", stripped[2:].strip()))
            i += 1
            continue
        if stripped.startswith("## "):
            blocks.append(("h2", stripped[3:].strip()))
            i += 1
            continue
        if stripped.startswith("### "):
            blocks.append(("h3", stripped[4:].strip()))
            i += 1
            continue
        if stripped == "---":
            blocks.append(("hr", None))
            i += 1
            continue
        # table: line starts with | and next line is separator |---|
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*[-:|\s]+\|", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = lines[i].strip().strip("|")
                cells = [c.strip() for c in row.split("|")]
                rows.append(cells)
                i += 1
            # drop separator row (index 1)
            if len(rows) >= 2:
                separator = rows[1]
                if all(set(c.replace(" ", "")) <= set("-:") for c in separator):
                    del rows[1]
            blocks.append(("table", rows))
            continue
        # bullet list
        if stripped.startswith("- "):
            while i < len(lines) and lines[i].strip().startswith("- "):
                blocks.append(("bullet", lines[i].strip()[2:].strip()))
                i += 1
            continue
        # italic trailing line
        if stripped.startswith("*") and stripped.endswith("*") and stripped.count("*") == 2:
            blocks.append(("italic_p", stripped.strip("*").strip()))
            i += 1
            continue
        # paragraph (gather until blank line / next block marker)
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith(("#", "- ", "|", "---", "*")):
                break
            para_lines.append(nxt)
            i += 1
        blocks.append(("p", " ".join(para_lines)))
    return blocks


def render(
    md_path: Path,
    out_path: Path,
    client: str,
    date: str,
    logo: Path | None,
    agency: str = "",
    tagline: str = "",
    brand: str | None = None,
):
    md = md_path.read_text(encoding="utf-8")
    # {{AGENCY_NAME}} in the markdown → agency name (or "l'agence" when none is configured)
    md = md.replace(AGENCY_PLACEHOLDER, agency.strip() or "l'agence")
    blocks = parse_markdown(md)
    primary, dark = parse_brand(brand)

    pdf = ProposalPDF(out_path, client, date, logo, agency=agency, tagline=tagline, primary=primary, dark=dark)
    pdf.draw_cover()
    pdf.new_content_page()

    # Skip the first H1 (already in cover) and the first 3 paragraphs of meta lines
    skipped_h1 = False
    for kind, payload in blocks:
        if not skipped_h1 and kind == "h1":
            skipped_h1 = True
            continue
        # skip cover meta lines like "**Client** : ...", "**Date** : ..."
        if kind == "p" and isinstance(payload, str):
            if re.match(r"^\*\*(Client|Date|Lancement campagne|Version)\*\*\s*:", payload):
                continue
        if kind == "h1":
            pdf.draw_h1(payload)
        elif kind == "h2":
            pdf.draw_h2(payload)
        elif kind == "h3":
            pdf.draw_h3(payload)
        elif kind == "p":
            pdf.draw_paragraph(payload)
        elif kind == "bullet":
            pdf.draw_bullet(payload)
        elif kind == "table":
            pdf.draw_table(payload)
        elif kind == "hr":
            pdf.draw_hr()
        elif kind == "italic_p":
            pdf.draw_paragraph(payload, size=9.0, italic=True, color=MUTED)

    pdf.save()


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def main():
    ap = argparse.ArgumentParser(
        description="Render a branded 'Proposition de Campagne' PDF from a markdown source.",
        epilog="Branding options fall back to env vars AGENCY_NAME, AGENCY_LOGO, AGENCY_BRAND, AGENCY_TAGLINE "
               "(see .env.example). Without any of them the PDF is generated with a neutral look and no logo.",
    )
    ap.add_argument("input", type=Path, help="markdown source (see templates/proposal-structure.md)")
    ap.add_argument("output", type=Path, help="output .pdf path")
    ap.add_argument("--client", required=True, help="client name printed on the cover")
    ap.add_argument("--date", required=True, help="date printed on the cover, e.g. 01/09/2026")
    ap.add_argument("--agency", default=None, help="agency name (footer, {{AGENCY_NAME}} placeholder). Env: AGENCY_NAME")
    ap.add_argument("--logo", type=Path, default=None, help="agency logo PNG/JPG (cover + watermark). Env: AGENCY_LOGO")
    ap.add_argument("--brand", default=None, help='brand colors "#PRIMARY[,#DARK]". Env: AGENCY_BRAND. Default "#4A7FD4,#1E2A4A"')
    ap.add_argument("--tagline", default=None, help="baseline under the cover. Env: AGENCY_TAGLINE")
    args = ap.parse_args()

    if not args.input.exists():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    agency = args.agency if args.agency is not None else _env("AGENCY_NAME")
    tagline = args.tagline if args.tagline is not None else _env("AGENCY_TAGLINE")
    brand = args.brand if args.brand is not None else (_env("AGENCY_BRAND") or None)

    logo: Path | None = args.logo
    if logo is None and _env("AGENCY_LOGO"):
        logo = Path(_env("AGENCY_LOGO"))
    if logo is not None:
        logo = Path(os.path.expanduser(str(logo)))
        if not logo.exists():
            print(f"warning: logo not found: {logo} — generating without logo", file=sys.stderr)
            logo = None

    args.output.parent.mkdir(parents=True, exist_ok=True)
    render(args.input, args.output, args.client, args.date, logo, agency=agency, tagline=tagline, brand=brand)
    print(str(args.output))


if __name__ == "__main__":
    main()
