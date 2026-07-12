#!/usr/bin/env python3
"""
the platform — Générateur PDF brandé pour les rapports Deep Search.

Usage :
    python3 build_deep_search_pdf.py <input.md> <output.pdf> \
        --client "Nom Client" \
        --report-type "market-awareness|competitors|psychographic" \
        [--logo path/to/logo.png] [--date "2026-04-10"]

Génère un PDF brandé the platform (même charte que build_proposal.py)
à partir d'un rapport Deep Search en markdown.
"""
import re
import sys
import argparse
from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    HRFlowable, Image as RLImage,
)
from reportlab.pdfgen.canvas import Canvas


# ── Brand colors ──────────────────────────────────────────────────────
BLUE_PRIMARY = HexColor("#4A7FD4")
BLUE_DARK = HexColor("#1E2A4A")
GREY_TEXT = HexColor("#2D2D2D")
GREY_LIGHT = HexColor("#666666")

# ── Default logo path (relative to this script) ──────────────────────
DEFAULT_LOGO = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "Projects" / "the platform" / "logo.png"
)

# ── Report type → cover title mapping ────────────────────────────────
REPORT_TITLES = {
    "market-awareness": "Étude de Conscience de Marché",
    "competitors": "Recherche Concurrentielle Approfondie",
    "psychographic": "Recherche Psychographique",
}

REPORT_SUBTITLES = {
    "market-awareness": "Analyse du niveau de conscience marché selon le modèle Schwartz",
    "competitors": "Paysage concurrentiel, positionnement et opportunités stratégiques",
    "psychographic": "Profil psychographique, douleurs et croyances de l'avatar cible",
}


# =====================================================================
# Watermark on every page
# =====================================================================

class WatermarkCanvas(Canvas):
    """Canvas subclass that draws a centered watermark logo on every page."""

    def __init__(self, *args, logo_path=None, **kw):
        self._logo_path = logo_path
        super().__init__(*args, **kw)

    def showPage(self):
        self._draw_watermark()
        self._draw_footer()
        super().showPage()

    def _draw_watermark(self):
        if not self._logo_path or not Path(self._logo_path).exists():
            return
        self.saveState()
        self.setFillAlpha(0.04)
        w, h = A4
        logo_size = 14 * cm
        x = (w - logo_size) / 2
        y = (h - logo_size) / 2
        self.drawImage(
            str(self._logo_path), x, y, logo_size, logo_size,
            preserveAspectRatio=True, mask="auto",
        )
        self.restoreState()

    def _draw_footer(self):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(GREY_LIGHT)
        w, _ = A4
        self.drawCentredString(w / 2, 1.2 * cm, "the platform — Confidentiel")
        self.restoreState()


# =====================================================================
# Markdown parser → ReportLab flowables
# =====================================================================

def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "LF_H1", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=16, leading=22,
        textColor=BLUE_DARK, spaceBefore=24, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        "LF_H2", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=13, leading=18,
        textColor=BLUE_PRIMARY, spaceBefore=18, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "LF_H3", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=11, leading=15,
        textColor=BLUE_DARK, spaceBefore=12, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "LF_Body", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, leading=15,
        textColor=GREY_TEXT, spaceBefore=2, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "LF_Bullet", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, leading=15,
        textColor=GREY_TEXT, leftIndent=18, spaceBefore=1, spaceAfter=3,
        bulletIndent=6,
    ))
    styles.add(ParagraphStyle(
        "LF_Quote", parent=styles["Normal"],
        fontName="Helvetica-Oblique", fontSize=10, leading=14,
        textColor=GREY_LIGHT, leftIndent=24, rightIndent=12,
        spaceBefore=4, spaceAfter=6,
        borderColor=BLUE_PRIMARY, borderWidth=0, borderPadding=0,
    ))
    return styles


def md_inline(text):
    """Convert **bold** and *italic* markers to ReportLab tags."""
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    return text


def parse_markdown(md_text, styles):
    """Parse markdown text into a list of ReportLab flowables."""
    flowables = []
    lines = md_text.splitlines()
    i = 0

    while i < len(lines):
        ln = lines[i].rstrip()

        if not ln:
            i += 1
            continue

        # Horizontal rule
        if ln.strip() in ("---", "***", "___"):
            flowables.append(Spacer(1, 6))
            flowables.append(HRFlowable(
                width="100%", thickness=0.5, color=BLUE_PRIMARY,
                spaceBefore=4, spaceAfter=10,
            ))
            i += 1
            continue

        # H1 = # Title (top-level from the report)
        if ln.startswith("# ") and not ln.startswith("## "):
            flowables.append(Paragraph(md_inline(ln[2:].strip()), styles["LF_H1"]))
            flowables.append(HRFlowable(
                width="100%", thickness=1.5, color=BLUE_PRIMARY,
                spaceBefore=0, spaceAfter=8,
            ))
            i += 1
            continue

        # H2 = ## Section
        if ln.startswith("## "):
            flowables.append(Paragraph(md_inline(ln[3:].strip()), styles["LF_H1"]))
            flowables.append(HRFlowable(
                width="100%", thickness=1.5, color=BLUE_PRIMARY,
                spaceBefore=0, spaceAfter=8,
            ))
            i += 1
            continue

        # H3 = ### Sous-section
        if ln.startswith("### "):
            flowables.append(Paragraph(md_inline(ln[4:].strip()), styles["LF_H2"]))
            i += 1
            continue

        # H4 = #### or #####
        if ln.startswith("##### "):
            flowables.append(Paragraph(md_inline(ln[6:].strip()), styles["LF_H3"]))
            i += 1
            continue
        if ln.startswith("#### "):
            flowables.append(Paragraph(md_inline(ln[5:].strip()), styles["LF_H3"]))
            i += 1
            continue

        # Blockquote (for prospect quotes)
        if ln.startswith("> "):
            content = ln[2:].strip()
            flowables.append(Paragraph(
                f"<i>\u00ab {md_inline(content)} \u00bb</i>",
                styles["LF_Quote"],
            ))
            i += 1
            continue

        # Bullet (- or *)
        if ln.lstrip().startswith(("- ", "* ")):
            content = ln.lstrip()[2:].strip()
            flowables.append(Paragraph(
                f"<bullet>&bull;</bullet> {md_inline(content)}",
                styles["LF_Bullet"],
            ))
            i += 1
            continue

        # Numbered list (1. 2. etc.)
        m = re.match(r"^\d+\.\s+(.*)", ln.lstrip())
        if m:
            content = m.group(1).strip()
            flowables.append(Paragraph(
                f"<bullet>&bull;</bullet> {md_inline(content)}",
                styles["LF_Bullet"],
            ))
            i += 1
            continue

        # Regular paragraph
        flowables.append(Paragraph(md_inline(ln), styles["LF_Body"]))
        i += 1

    return flowables


# =====================================================================
# Cover page
# =====================================================================

def build_cover(client, report_type, doc_date, logo_path, styles):
    """Build a cover page as a list of flowables."""
    elements = []
    elements.append(Spacer(1, 3.5 * cm))

    # Logo centered
    if logo_path and Path(logo_path).exists():
        logo = RLImage(str(logo_path), width=5 * cm, height=5 * cm)
        logo.hAlign = "CENTER"
        elements.append(logo)
        elements.append(Spacer(1, 1.5 * cm))

    # Report category label
    label_style = ParagraphStyle(
        "CoverLabel", fontName="Helvetica", fontSize=11, leading=14,
        textColor=BLUE_PRIMARY, alignment=TA_CENTER,
    )
    elements.append(Paragraph("Deep Search — Rapport de Recherche", label_style))
    elements.append(Spacer(1, 0.6 * cm))

    # Title
    title = REPORT_TITLES.get(report_type, "Rapport Deep Search")
    title_style = ParagraphStyle(
        "CoverTitle", fontName="Helvetica-Bold", fontSize=24, leading=30,
        textColor=BLUE_DARK, alignment=TA_CENTER,
    )
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.5 * cm))

    # Subtitle
    subtitle = REPORT_SUBTITLES.get(report_type, "")
    if subtitle:
        sub_style = ParagraphStyle(
            "CoverSub", fontName="Helvetica", fontSize=11, leading=15,
            textColor=GREY_LIGHT, alignment=TA_CENTER,
        )
        elements.append(Paragraph(subtitle, sub_style))
    elements.append(Spacer(1, 1.2 * cm))

    # Client name
    client_style = ParagraphStyle(
        "CoverClient", fontName="Helvetica", fontSize=18, leading=24,
        textColor=BLUE_PRIMARY, alignment=TA_CENTER,
    )
    elements.append(Paragraph(client, client_style))
    elements.append(Spacer(1, 1 * cm))

    # Date
    date_style = ParagraphStyle(
        "CoverDate", fontName="Helvetica", fontSize=12, leading=16,
        textColor=GREY_LIGHT, alignment=TA_CENTER,
    )
    elements.append(Paragraph(doc_date, date_style))
    elements.append(Spacer(1, 2.5 * cm))

    # Subtle line
    elements.append(HRFlowable(
        width="40%", thickness=1, color=BLUE_PRIMARY,
        spaceBefore=0, spaceAfter=20,
    ))

    # Footer text
    footer_style = ParagraphStyle(
        "CoverFooter", fontName="Helvetica", fontSize=9, leading=12,
        textColor=GREY_LIGHT, alignment=TA_CENTER,
    )
    elements.append(Paragraph("the platform — Document confidentiel", footer_style))

    elements.append(PageBreak())
    return elements


# =====================================================================
# Main build
# =====================================================================

def build(md_path, out_path, client, report_type, logo_path=None, doc_date=None):
    if doc_date is None:
        doc_date = date.today().strftime("%d/%m/%Y")

    md = Path(md_path).read_text(encoding="utf-8")
    styles = build_styles()

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    title = REPORT_TITLES.get(report_type, "Deep Search")

    def make_canvas(filename, pagesize=A4, **kwargs):
        return WatermarkCanvas(filename, pagesize=pagesize, logo_path=logo_path, **kwargs)

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        title=f"the platform — {title} — {client}",
        author="the platform",
    )

    elements = []
    elements.extend(build_cover(client, report_type, doc_date, logo_path, styles))
    elements.extend(parse_markdown(md, styles))

    doc.build(elements, canvasmaker=make_canvas)
    print(f"\u2713 {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="Markdown source file")
    parser.add_argument("output", help="Output .pdf path")
    parser.add_argument("--client", required=True, help="Nom du client")
    parser.add_argument(
        "--report-type", required=True,
        choices=["market-awareness", "competitors", "psychographic"],
        help="Type de rapport Deep Search",
    )
    parser.add_argument("--logo", default=str(DEFAULT_LOGO), help="Path to logo PNG")
    parser.add_argument("--date", default=None, help="Date du document (DD/MM/YYYY)")
    args = parser.parse_args()
    build(
        args.input, args.output, args.client, args.report_type,
        logo_path=args.logo, doc_date=args.date,
    )
