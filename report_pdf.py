"""
Builds a downloadable PDF of someone's full Women's Health Check
report from the stored report JSON. Uses reportlab, which is pure
Python and installs cleanly on Render without any compiled
dependencies, same reasoning as the password hashing choice in
auth_utils.py.
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT

PURPLE_DARK = HexColor("#2E0854")
PURPLE = HexColor("#7C2AE8")
INK = HexColor("#241933")
INK_SOFT = HexColor("#5B4E6D")


def build_report_pdf(user_name: str, life_stage: str, report: dict, reviewed: bool, reviewed_by: str = None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=24 * mm, bottomMargin=20 * mm, leftMargin=22 * mm, rightMargin=22 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], textColor=PURPLE_DARK, fontSize=22, spaceAfter=4)
    meta_style = ParagraphStyle("MetaStyle", parent=styles["Normal"], textColor=INK_SOFT, fontSize=10, spaceAfter=16)
    track_title_style = ParagraphStyle("TrackTitle", parent=styles["Heading2"], textColor=PURPLE_DARK, fontSize=14, spaceBefore=18, spaceAfter=4)
    band_style = ParagraphStyle("BandStyle", parent=styles["Normal"], textColor=PURPLE, fontSize=11, fontName="Helvetica-Bold", spaceAfter=6)
    body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], textColor=INK, fontSize=10.5, leading=15, spaceAfter=8, alignment=TA_LEFT)
    next_style = ParagraphStyle("NextStyle", parent=styles["Normal"], textColor=INK, fontSize=10.5, leading=15, leftIndent=12, spaceAfter=3)
    specialist_style = ParagraphStyle("SpecialistStyle", parent=styles["Normal"], textColor=PURPLE_DARK, fontSize=10, fontName="Helvetica-Bold", spaceBefore=6)
    footer_style = ParagraphStyle("FooterStyle", parent=styles["Normal"], textColor=INK_SOFT, fontSize=9, spaceBefore=20)

    story = []
    story.append(Paragraph("Your Women's Health Check", title_style))
    story.append(Paragraph(f"{user_name} · {life_stage} · generated {datetime.utcnow().strftime('%d %B %Y')}", meta_style))
    story.append(HRFlowable(width="100%", color=HexColor("#E4D9F0"), thickness=1))

    if reviewed:
        review_note = f"Reviewed by {reviewed_by}." if reviewed_by else "Reviewed by a qualified practitioner."
    else:
        review_note = "This report is awaiting practitioner review. Treat it as provisional until reviewed."
    story.append(Paragraph(review_note, meta_style))

    tracks = report.get("tracks", {})
    for key in tracks:
        t = tracks[key]
        story.append(Paragraph(t["title"], track_title_style))
        story.append(Paragraph(t["label"], band_style))
        story.append(Paragraph(t["text"], body_style))
        for step in t.get("next", []):
            story.append(Paragraph(f"&bull; {step}", next_style))
        if t.get("specialist"):
            story.append(Paragraph(t["specialist"], specialist_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", color=HexColor("#E4D9F0"), thickness=1))
    story.append(Paragraph(
        "This report is for informational purposes and does not replace medical advice. "
        "If anything here concerns you, please speak with a GP or qualified practitioner.",
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
