"""
Builds a downloadable PDF of someone's full Women's Health Check
report. Pure Python (reportlab), no compiled dependencies.
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
from reportlab.lib.enums import TA_LEFT

PURPLE_DARK = HexColor("#2E0854")
PURPLE = HexColor("#7C2AE8")
GOLD = HexColor("#C9A227")
INK = HexColor("#241933")
INK_SOFT = HexColor("#5B4E6D")


def build_report_pdf(user_name: str, life_stage: str, report: dict, reviewed: bool, reviewed_by: str = None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=24 * mm, bottomMargin=20 * mm, leftMargin=22 * mm, rightMargin=22 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], textColor=PURPLE_DARK, fontSize=24, spaceAfter=4)
    meta_style = ParagraphStyle("MetaStyle", parent=styles["Normal"], textColor=INK_SOFT, fontSize=10, spaceAfter=14)
    overview_style = ParagraphStyle("OverviewStyle", parent=styles["Normal"], textColor=INK, fontSize=11.5, leading=17, spaceAfter=10)
    section_h1 = ParagraphStyle("SectionH1", parent=styles["Heading1"], textColor=PURPLE_DARK, fontSize=13.5, spaceBefore=0, spaceAfter=8)
    track_title_style = ParagraphStyle("TrackTitle", parent=styles["Heading1"], textColor=PURPLE_DARK, fontSize=19, spaceBefore=0, spaceAfter=6)
    band_style = ParagraphStyle("BandStyle", parent=styles["Normal"], textColor=PURPLE, fontSize=12, fontName="Helvetica-Bold", spaceAfter=10)
    summary_style = ParagraphStyle("SummaryStyle", parent=styles["Normal"], textColor=INK, fontSize=12, leading=17, fontName="Helvetica-Bold", spaceAfter=10)
    subhead_style = ParagraphStyle("SubheadStyle", parent=styles["Heading2"], textColor=PURPLE_DARK, fontSize=12, spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], textColor=INK, fontSize=10.5, leading=15.5, spaceAfter=8, alignment=TA_LEFT)
    bullet_style = ParagraphStyle("BulletStyle", parent=styles["Normal"], textColor=INK, fontSize=10.5, leading=15.5, leftIndent=14, spaceAfter=5)
    specialist_box_style = ParagraphStyle("SpecialistBox", parent=styles["Normal"], textColor=INK, fontSize=10.5, leading=15.5, spaceAfter=4)
    specialist_name_style = ParagraphStyle("SpecialistName", parent=styles["Normal"], textColor=PURPLE_DARK, fontSize=11.5, fontName="Helvetica-Bold", spaceAfter=4)
    footer_style = ParagraphStyle("FooterStyle", parent=styles["Normal"], textColor=INK_SOFT, fontSize=9, spaceBefore=20, leading=13)
    toc_item_style = ParagraphStyle("TocItem", parent=styles["Normal"], textColor=INK, fontSize=11.5, leading=20)

    story = []

    # ---------- Cover / intro page ----------
    story.append(Paragraph("Your Women's Health Check", title_style))
    story.append(Paragraph(f"{user_name} &middot; {life_stage} &middot; generated {datetime.utcnow().strftime('%d %B %Y')}", meta_style))
    story.append(HRFlowable(width="100%", color=HexColor("#E4D9F0"), thickness=1))
    story.append(Spacer(1, 14))

    if reviewed:
        review_note = f"This report has been reviewed by {reviewed_by}." if reviewed_by else "This report has been reviewed by a qualified practitioner."
    else:
        review_note = "This report is awaiting practitioner review. Treat it as provisional until reviewed."
    story.append(Paragraph(review_note, meta_style))

    if report.get("overview"):
        story.append(Paragraph("Where you are right now", section_h1))
        story.append(Paragraph(report["overview"], overview_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("What's in this report", section_h1))
    tracks = report.get("tracks", {})
    for key in tracks:
        story.append(Paragraph(f"&bull; {tracks[key]['title']}, {tracks[key]['label']}", toc_item_style))
    story.append(Paragraph("&bull; Your action plan", toc_item_style))

    story.append(PageBreak())

    # ---------- One full section per track ----------
    for key in tracks:
        t = tracks[key]
        story.append(Paragraph(t["title"], track_title_style))
        story.append(Paragraph(t["label"], band_style))
        story.append(Paragraph(t["summary"], summary_style))

        if t.get("why_it_matters"):
            story.append(Paragraph("Why this matters", subhead_style))
            story.append(Paragraph(t["why_it_matters"], body_style))

        if t.get("next_steps"):
            story.append(Paragraph("Your next steps", subhead_style))
            for step in t["next_steps"]:
                story.append(Paragraph(f"&bull; {step}", bullet_style))

        if t.get("lifestyle_tips"):
            story.append(Paragraph("Lifestyle tips", subhead_style))
            for tip in t["lifestyle_tips"]:
                story.append(Paragraph(f"&bull; {tip}", bullet_style))

        if t.get("when_to_seek_help"):
            story.append(Paragraph("When to seek help", subhead_style))
            story.append(Paragraph(t["when_to_seek_help"], body_style))

        if t.get("specialist"):
            story.append(Paragraph("Recommended specialist", subhead_style))
            story.append(Paragraph(t["specialist"], specialist_name_style))
            if t.get("specialist_expect"):
                story.append(Paragraph(t["specialist_expect"], specialist_box_style))

        story.append(PageBreak())

    # ---------- Action plan summary ----------
    story.append(Paragraph("Your action plan", track_title_style))
    story.append(Paragraph("A short summary pulling together the single most useful next step from each area above.", body_style))
    for key in tracks:
        t = tracks[key]
        first_step = t["next_steps"][0] if t.get("next_steps") else ""
        story.append(Paragraph(t["title"], subhead_style))
        story.append(Paragraph(f"&bull; {first_step}", bullet_style))

    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", color=HexColor("#E4D9F0"), thickness=1))
    story.append(Paragraph(
        "This report is for informational purposes and does not replace medical advice. "
        "If anything here concerns you, please speak with a GP or qualified practitioner. "
        "In an emergency, or if you ever feel unsafe, contact your GP, midwife, or NHS 111 immediately.",
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
