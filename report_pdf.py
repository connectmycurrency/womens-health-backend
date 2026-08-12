"""
Builds a formal, magazine-style PDF report for the Women's Health
Check. Pure Python (reportlab), no compiled dependencies.

Structure: cover page, about-this-report page, results-at-a-glance
page, one detailed section per track (with a running header bar and
page number on every content page), a resources page, and a closing
disclaimer. Uses our own purple/gold brand system throughout.
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    HRFlowable, PageBreak, Table, TableStyle, NextPageTemplate, FrameBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import Flowable


class SectionMarker(Flowable):
    """Invisible flowable that updates the running header label at the
    exact point it's actually drawn, so headers stay correct even when
    a section spans more than one page (unlike guessing page numbers
    in advance, which breaks as soon as content length varies).

    When state contains a "marks" list, also records the real
    (page_number, label) pair there, used by build_report_pdf's
    discovery pass to build a verified page-to-label map."""
    def __init__(self, label, state):
        Flowable.__init__(self)
        self.label = label
        self.state = state

    def draw(self):
        self.state["label"] = self.label
        marks = self.state.get("marks")
        if marks is not None:
            marks.append((self.canv.getPageNumber(), self.label))

    def wrap(self, availWidth, availHeight):
        return (0, 0)

PURPLE_DARK = HexColor("#2E0854")
PURPLE = HexColor("#7C2AE8")
PURPLE_PALE = HexColor("#F1E7FB")
GOLD = HexColor("#C9A227")
GOLD_PALE = HexColor("#FBF3DE")
MAGENTA = HexColor("#C2367B")
MAGENTA_PALE = HexColor("#FBE7F1")
INK = HexColor("#241933")
INK_SOFT = HexColor("#5B4E6D")
WHITE = HexColor("#FFFFFF")
BORDER = HexColor("#E4D9F0")

BAND_ACCENT = {"low": GOLD, "mid": MAGENTA, "high": PURPLE}
BAND_ACCENT_PALE = {"low": GOLD_PALE, "mid": MAGENTA_PALE, "high": PURPLE_PALE}

PAGE_W, PAGE_H = A4
MARGIN = 22 * mm


def _draw_wave(c, y_base, height, color):
    """A simple curved band across the top of the cover page."""
    c.setFillColor(color)
    path = c.beginPath()
    path.moveTo(0, y_base + height)
    path.lineTo(0, y_base)
    path.curveTo(PAGE_W * 0.3, y_base + height * 0.6, PAGE_W * 0.7, y_base - height * 0.4, PAGE_W, y_base)
    path.lineTo(PAGE_W, y_base + height)
    path.close()
    c.drawPath(path, fill=1, stroke=0)


def _draw_cover(c, doc, user_name, life_stage):
    c.saveState()
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    _draw_wave(c, PAGE_H - 95 * mm, 55 * mm, PURPLE_DARK)
    # wave trough dips to roughly (PAGE_H - 95mm) - 22mm from the bottom edge,
    # so the title sits clear of it with room to spare.
    title_y = PAGE_H - 118 * mm
    subtitle_y = title_y - 10 * mm
    date_y = subtitle_y - 7 * mm

    c.setFillColor(PURPLE_DARK)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(PAGE_W / 2, title_y, "Your Women's Health Check")
    c.setFont("Helvetica", 12)
    c.setFillColor(INK_SOFT)
    c.drawCentredString(PAGE_W / 2, subtitle_y, f"{user_name}  |  {life_stage}")
    c.drawCentredString(PAGE_W / 2, date_y, datetime.utcnow().strftime("%d %B %Y"))

    # abstract "whole person" graphic, positioned well clear of the text above it
    cx, cy = PAGE_W / 2, 90 * mm
    rings = [(42 * mm, PURPLE_PALE), (32 * mm, MAGENTA_PALE), (23 * mm, GOLD_PALE), (14 * mm, PURPLE)]
    for radius, color in rings:
        c.setFillColor(color)
        c.circle(cx, cy, radius, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.circle(cx, cy, 7 * mm, fill=1, stroke=0)

    # bottom brand strip
    c.setFillColor(PURPLE_DARK)
    c.rect(0, 0, PAGE_W, 16 * mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(PAGE_W / 2, 6 * mm, "WOMENSHEALTHCHECK.ONLINE")
    c.restoreState()


def _draw_header_footer(c, doc, label):
    c.saveState()
    c.setFillColor(PURPLE_DARK)
    c.rect(0, PAGE_H - 14 * mm, PAGE_W, 14 * mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN, PAGE_H - 9 * mm, label.upper())
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 9 * mm, str(doc.page))
    c.setFillColor(INK_SOFT)
    c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_W / 2, 10 * mm, "This report is informational and does not replace medical advice.")
    c.restoreState()


def _boxed_table(rows, col_widths, header_bg=None, zebra=False):
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
    ]
    if header_bg:
        style_cmds.append(("BACKGROUND", (0, 0), (-1, 0), header_bg))
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle(style_cmds))
    return t


def _render(user_name, life_stage, report, reviewed, reviewed_by, page_label_map, header_state):
    """Builds the full document once. header_state is used only to
    record markers during the discovery pass; page_label_map, once
    populated, is used to draw the real header text."""
    buffer = io.BytesIO()
    tracks = report.get("tracks", {})

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=PURPLE_DARK, fontSize=18, spaceBefore=0, spaceAfter=10)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=PURPLE_DARK, fontSize=13, spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["Normal"], textColor=INK, fontSize=10.5, leading=15.5, spaceAfter=8)
    body_soft = ParagraphStyle("BodySoft", parent=styles["Normal"], textColor=INK_SOFT, fontSize=10, leading=14.5, spaceAfter=6)
    bullet = ParagraphStyle("Bullet", parent=styles["Normal"], textColor=INK, fontSize=10.5, leading=15, leftIndent=6, spaceAfter=4)
    band_label_style = ParagraphStyle("BandLabel", parent=styles["Normal"], fontSize=12, fontName="Helvetica-Bold", spaceAfter=8)
    summary_style = ParagraphStyle("Summary", parent=styles["Normal"], textColor=INK, fontSize=11.5, leading=16.5, fontName="Helvetica-Bold", spaceAfter=10)
    box_title = ParagraphStyle("BoxTitle", parent=styles["Normal"], fontSize=10.5, fontName="Helvetica-Bold", textColor=PURPLE_DARK, spaceAfter=3)
    box_body = ParagraphStyle("BoxBody", parent=styles["Normal"], fontSize=10, leading=14.5, textColor=INK)
    toc_style = ParagraphStyle("Toc", parent=styles["Normal"], fontSize=11.5, leading=20, textColor=INK)
    glance_track = ParagraphStyle("GlanceTrack", parent=styles["Normal"], fontSize=10.5, fontName="Helvetica-Bold", textColor=INK)

    doc = BaseDocTemplate(buffer, pagesize=A4)
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, id="cover", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    content_frame = Frame(MARGIN, 18 * mm, PAGE_W - 2 * MARGIN, PAGE_H - 14 * mm - 22 * mm, id="content")

    def on_cover(c, d):
        _draw_cover(c, d, user_name, life_stage)

    def on_content(c, d):
        label = page_label_map.get(d.page, header_state["label"])
        _draw_header_footer(c, d, label)

    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[cover_frame], onPage=on_cover),
        PageTemplate(id="Content", frames=[content_frame], onPage=on_content),
    ])

    story = []
    story.append(NextPageTemplate("Content"))
    story.append(PageBreak())

    if reviewed:
        review_line = f"Reviewed by {reviewed_by}." if reviewed_by else "Reviewed by a qualified practitioner."
    else:
        review_line = "Awaiting practitioner review. Treat this report as provisional until reviewed."

    story.append(SectionMarker("About this report", header_state))
    story.append(Paragraph("About this report", h1))
    story.append(Paragraph(
        "This report was generated from your answers to the Women's Health Check, a short questionnaire "
        "covering the areas most relevant to your current life stage. It combines your specific answers with "
        "general, well-evidenced guidance to give you a clear starting point, not a diagnosis.",
        body
    ))
    info_rows = [
        [Paragraph("Prepared for", box_title), Paragraph(user_name, box_body)],
        [Paragraph("Life stage", box_title), Paragraph(life_stage, box_body)],
        [Paragraph("Date generated", box_title), Paragraph(datetime.utcnow().strftime("%d %B %Y"), box_body)],
        [Paragraph("Review status", box_title), Paragraph(review_line, box_body)],
    ]
    story.append(_boxed_table(info_rows, [40 * mm, None]))
    story.append(Spacer(1, 14))

    if report.get("overview"):
        story.append(Paragraph("Where you are right now", h2))
        story.append(Paragraph(report["overview"], body))

    story.append(Spacer(1, 10))
    story.append(Paragraph("What's in this report", h2))
    for key in tracks:
        story.append(Paragraph(f"&bull; {tracks[key]['title']}, {tracks[key]['label']}", toc_style))
    story.append(Paragraph("&bull; Results at a glance", toc_style))
    story.append(Paragraph("&bull; Resources", toc_style))

    story.append(PageBreak())

    story.append(SectionMarker("Results at a glance", header_state))
    story.append(Paragraph("Results at a glance", h1))
    story.append(Paragraph(
        "A quick visual summary before the detail. Each bar shows how much attention that area is worth "
        "right now, based on your answers.",
        body
    ))
    story.append(Spacer(1, 8))

    band_width = {"low": 0.35, "mid": 0.65, "high": 1.0}
    bar_total = 90
    for key in tracks:
        t = tracks[key]
        accent = BAND_ACCENT[t["band"]]
        fraction = band_width[t["band"]]
        fill_w = bar_total * fraction
        empty_w = bar_total - fill_w
        cells = [Paragraph(t["title"], glance_track)]
        widths = [55 * mm]
        if fill_w > 0:
            cells.append("")
            widths.append(fill_w)
        if empty_w > 0:
            cells.append("")
            widths.append(empty_w)
        cells.append(Paragraph(t["label"], ParagraphStyle("bandsm", fontSize=9.5, fontName="Helvetica-Bold", textColor=accent)))
        widths.append(40 * mm)

        row = Table([cells], colWidths=widths, rowHeights=[14])
        style_cmds = [("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
        col = 1
        if fill_w > 0:
            style_cmds.append(("BACKGROUND", (col, 0), (col, 0), accent))
            col += 1
        if empty_w > 0:
            style_cmds.append(("BACKGROUND", (col, 0), (col, 0), HexColor("#F0EAF7")))
        row.setStyle(TableStyle(style_cmds))
        story.append(row)
        story.append(Spacer(1, 12))

    story.append(PageBreak())

    for i, key in enumerate(tracks):
        t = tracks[key]
        accent = BAND_ACCENT[t["band"]]
        pale = BAND_ACCENT_PALE[t["band"]]

        story.append(SectionMarker(t["title"], header_state))
        story.append(Paragraph(t["title"], h1))
        story.append(Paragraph(t["label"], ParagraphStyle("bandlbl", parent=band_label_style, textColor=accent)))
        story.append(Paragraph(t["summary"], summary_style))

        if t.get("education"):
            edu_table = _boxed_table(
                [[Paragraph("Understanding this stage", box_title)],
                 [Paragraph(t["education"], box_body)]],
                [None]
            )
            edu_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PURPLE_PALE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
            ]))
            story.append(Spacer(1, 4))
            story.append(edu_table)
            story.append(Spacer(1, 12))

        if t.get("why_it_matters"):
            story.append(Paragraph("Why this matters for you", h2))
            story.append(Paragraph(t["why_it_matters"], body))

        if t.get("next_steps"):
            story.append(Paragraph("Your next steps", h2))
            rows = []
            for n, step in enumerate(t["next_steps"], start=1):
                num = Paragraph(str(n), ParagraphStyle("num", fontSize=10, fontName="Helvetica-Bold", textColor=WHITE, alignment=TA_CENTER))
                rows.append([num, Paragraph(step, box_body)])
            step_table = Table(rows, colWidths=[9 * mm, None])
            step_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (1, 0), (1, -1), 8),
            ]))
            for r in range(len(rows)):
                step_table.setStyle(TableStyle([("BACKGROUND", (0, r), (0, r), accent)]))
            story.append(step_table)
            story.append(Spacer(1, 10))

        if t.get("lifestyle_tips"):
            story.append(Paragraph("Lifestyle tips", h2))
            for tip in t["lifestyle_tips"]:
                story.append(Paragraph(f"&bull; {tip}", bullet))

        if t.get("when_to_seek_help"):
            help_table = _boxed_table(
                [[Paragraph("When to seek help", box_title)],
                 [Paragraph(t["when_to_seek_help"], box_body)]],
                [None]
            )
            help_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), pale),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 0.75, accent),
            ]))
            story.append(Spacer(1, 6))
            story.append(help_table)
            story.append(Spacer(1, 10))

        if t.get("specialist"):
            story.append(Paragraph("Recommended specialist", h2))
            story.append(Paragraph(t["specialist"], ParagraphStyle("specname", fontSize=11, fontName="Helvetica-Bold", textColor=PURPLE_DARK, spaceAfter=3)))
            if t.get("specialist_expect"):
                story.append(Paragraph(t["specialist_expect"], body_soft))

        story.append(PageBreak())

    story.append(SectionMarker("Resources", header_state))
    story.append(Paragraph("Resources", h1))
    story.append(Paragraph(
        "A few starting points if you want to read further or need support beyond this report.",
        body
    ))
    resource_rows = [
        [Paragraph("NHS", box_title), Paragraph("General health information and how to contact your GP, midwife, or health visitor.", box_body)],
        [Paragraph("NHS 111", box_title), Paragraph("For urgent, non-emergency support any time, day or night.", box_body)],
        [Paragraph("British Menopause Society", box_title), Paragraph("Independent, evidence-based information specifically on menopause.", box_body)],
        [Paragraph("Local health visiting service", box_title), Paragraph("Ongoing postnatal support, usually contactable directly without needing a GP appointment first.", box_body)],
    ]
    story.append(_boxed_table(resource_rows, [50 * mm, None]))
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=BORDER, thickness=1))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "This report is for informational purposes and does not replace medical advice. If anything here "
        "concerns you, please speak with a GP or qualified practitioner. In an emergency, or if you ever feel "
        "unsafe, contact your GP, midwife, or NHS 111 immediately.",
        body_soft
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def build_report_pdf(user_name: str, life_stage: str, report: dict, reviewed: bool, reviewed_by: str = None) -> bytes:
    # Pass 1 (discovery, discarded): render once so every SectionMarker
    # records the real page number it lands on. The header text drawn
    # in this pass is thrown away, headers lag a page behind here since
    # onPage fires before that page's content, which is exactly the bug
    # this two-pass approach exists to avoid in the real output.
    discovery_state = {"label": "YOUR WOMEN'S HEALTH CHECK", "marks": []}
    _render(user_name, life_stage, report, reviewed, reviewed_by, {}, discovery_state)

    # Build a page -> label map from the real page numbers captured above,
    # forward-filling so pages a section spills onto also get its label.
    marks = sorted(discovery_state["marks"], key=lambda m: m[0])
    page_label_map = {}
    if marks:
        max_page = marks[-1][0] + 3  # generous headroom
        current_label = marks[0][1]
        mark_idx = 0
        for page in range(1, max_page + 1):
            while mark_idx < len(marks) and marks[mark_idx][0] == page:
                current_label = marks[mark_idx][1]
                mark_idx += 1
            page_label_map[page] = current_label

    # Pass 2 (real): render using the verified page -> label map, so
    # every page's header matches what's actually on it.
    header_state = {"label": "YOUR WOMEN'S HEALTH CHECK"}
    return _render(user_name, life_stage, report, reviewed, reviewed_by, page_label_map, header_state)
