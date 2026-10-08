"""Render one readable PDF per completed Customer-to-Cash Markdown module."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "knowledge" / "prospect_to_cash"
DESTINATION = ROOT / "output" / "pdf"
MODULES = ("customer", "customer_order", "customer_order_line")
NAVY = colors.HexColor("#173451")
TEAL = colors.HexColor("#087F8C")
INK = colors.HexColor("#253649")
MUTED = colors.HexColor("#63788B")
PALE = colors.HexColor("#EAF2F6")


def register_fonts() -> tuple[str, str]:
    normal = Path(r"C:\Windows\Fonts\arial.ttf")
    bold = Path(r"C:\Windows\Fonts\arialbd.ttf")
    if normal.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("GuideArial", str(normal)))
        pdfmetrics.registerFont(TTFont("GuideArial-Bold", str(bold)))
        pdfmetrics.registerFontFamily("GuideArial", normal="GuideArial", bold="GuideArial-Bold")
        return "GuideArial", "GuideArial-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()
STYLES = {
    "title": ParagraphStyle("GuideTitle", fontName=FONT_BOLD, fontSize=19, leading=23, textColor=NAVY, spaceAfter=12),
    "intro": ParagraphStyle("GuideIntro", fontName=FONT, fontSize=9.8, leading=15, textColor=INK, spaceAfter=8),
    "h2": ParagraphStyle("GuideH2", fontName=FONT_BOLD, fontSize=12.1, leading=16, textColor=NAVY, spaceBefore=17, spaceAfter=7, keepWithNext=True),
    "body": ParagraphStyle("GuideBody", fontName=FONT, fontSize=9.1, leading=13.5, textColor=INK, spaceAfter=5),
    "list": ParagraphStyle("GuideList", fontName=FONT, fontSize=9, leading=13.1, leftIndent=17, firstLineIndent=-13, textColor=INK, spaceAfter=4),
    "meta": ParagraphStyle("GuideMeta", fontName=FONT, fontSize=8.5, leading=12.3, textColor=INK, spaceAfter=2),
    "summary": ParagraphStyle("GuideSummary", fontName=FONT, fontSize=8.7, leading=12.5, textColor=TEAL, spaceBefore=3, spaceAfter=5),
    "keywords": ParagraphStyle("GuideKeywords", fontName=FONT, fontSize=8, leading=11.5, textColor=MUTED, spaceAfter=7),
    "cell": ParagraphStyle("GuideCell", fontName=FONT, fontSize=8.1, leading=11, textColor=INK),
    "cellhead": ParagraphStyle("GuideCellHead", fontName=FONT_BOLD, fontSize=8.1, leading=11, textColor=NAVY),
}


def inline(text: str) -> str:
    escaped = html.escape(text.strip())
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<font color='#087F8C'>\1</font>", escaped)
    return escaped.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")


def footer(canvas, document):
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#D7E3E9"))
    canvas.line(45, 42, width - 45, 42)
    canvas.setFont(FONT, 7.8)
    canvas.setFillColor(MUTED)
    canvas.drawString(46, 29, "General CSI/SyteLine guide | Draft for local SME review")
    canvas.drawRightString(width - 46, 29, f"Page {document.page}")
    canvas.restoreState()


def parse_table(lines: list[str], width: float) -> Table:
    parsed = [[part.strip() for part in line.strip().strip("|").split("|")] for line in lines]
    parsed = [row for row in parsed if not all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in row)]
    count = max(len(row) for row in parsed)
    parsed = [row + [""] * (count - len(row)) for row in parsed]
    columns = [width / count] * count
    if count == 2:
        columns = [width * 0.34, width * 0.66]
    cells = []
    for index, row in enumerate(parsed):
        style = STYLES["cellhead"] if index == 0 else STYLES["cell"]
        cells.append([Paragraph(inline(cell), style) for cell in row])
    table = Table(cells, colWidths=columns, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#B7CBD6")),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, colors.HexColor("#E1E9ED")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def flowables(markdown: str, width: float):
    lines = markdown.splitlines()
    story = []
    index = 0
    inside_metadata = False
    inside_keywords = False
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("# "):
            story.append(Paragraph(inline(line[2:]), STYLES["title"]))
            story.append(HRFlowable(width=width, thickness=1.5, color=TEAL, spaceAfter=8))
            index += 1
            continue
        if line.startswith("## "):
            heading = line[3:]
            inside_metadata = heading == "Document Metadata"
            inside_keywords = False
            story.append(Paragraph(inline(heading), STYLES["h2"]))
            index += 1
            continue
        if line.startswith("### Keywords"):
            inside_keywords = True
            index += 1
            continue
        if line.startswith("### "):
            inside_keywords = False
            story.append(Paragraph(inline(line[4:]), STYLES["h2"]))
            index += 1
            continue
        if line.startswith("|"):
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            story.append(parse_table(table_lines, width))
            story.append(Spacer(1, 6))
            continue
        if line.startswith("**Section Summary:**"):
            story.append(Paragraph(inline(line), STYLES["summary"]))
        elif inside_keywords:
            story.append(Paragraph("<b>Keywords:</b> " + inline(line), STYLES["keywords"]))
            inside_keywords = False
        elif re.match(r"^\d+\. ", line):
            number, body = line.split(". ", 1)
            story.append(Paragraph(f"<b>{number}.</b> {inline(body)}", STYLES["list"]))
        elif line.startswith("- "):
            style = STYLES["meta"] if inside_metadata else STYLES["list"]
            prefix = "" if inside_metadata else "<b>\u2022</b> "
            story.append(Paragraph(prefix + inline(line[2:]), style))
        else:
            style = STYLES["meta"] if inside_metadata else STYLES["intro"] if not story or len(story) < 3 else STYLES["body"]
            story.append(Paragraph(inline(line), style))
        index += 1
    return story


def build(module: str) -> Path:
    article = SOURCE / f"{module}.md"
    output = DESTINATION / f"{module}.pdf"
    page_width, _ = A4
    margin = 46
    document = SimpleDocTemplate(
        str(output), pagesize=A4, leftMargin=margin, rightMargin=margin,
        topMargin=48, bottomMargin=55, title=module.replace("_", " ").title(),
        author="SyteLine Chatbot Knowledge Base",
    )
    document.build(flowables(article.read_text(encoding="utf-8"), page_width - 2 * margin), onFirstPage=footer, onLaterPages=footer)
    return output


if __name__ == "__main__":
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for name in MODULES:
        print(build(name))
