import os
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Lead
from schemas import LeadCreate, LeadOut, LeadReviewUpdate
from scoring import build_report

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Women's Health Check API")

# Allow the quiz front end (wherever it's hosted) to call this API.
# Set FRONTEND_ORIGIN as an environment variable on Render once the
# front end has a real domain, e.g. https://yourclinic-quiz.netlify.app
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/admin", StaticFiles(directory="static", html=True), name="admin")

PRACTITIONER_API_KEY = os.environ.get("PRACTITIONER_API_KEY", "change-me-before-deploying")


def require_practitioner(x_api_key: Optional[str] = Header(default=None)):
    """
    Simple shared-secret auth for practitioner-only endpoints.

    This is intentionally minimal for the pilot stage. Before onboarding
    a real clinic, swap this for proper per-practitioner login (Clerk,
    matching how CMC Connect handles auth, is the natural fit once this
    needs multiple named users rather than one shared key).
    """
    if not x_api_key or x_api_key != PRACTITIONER_API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")


@app.get("/")
def health_check():
    return {"status": "ok", "service": "womens-health-check-api"}


@app.post("/api/leads", response_model=LeadOut)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    """
    Called by the quiz front end when someone finishes the quiz.
    Computes the report server-side (never trust a client-computed
    score) and stores it as pending_review.
    """
    report = build_report(payload.life_stage, payload.answers)

    lead = Lead(
        name=payload.name,
        email=payload.email,
        marketing_consent=payload.marketing_consent,
        partner_share_consent=payload.partner_share_consent,
        life_stage=payload.life_stage,
        answers=payload.answers,
        report=report,
        status="pending_review",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@app.get("/api/leads", response_model=List[LeadOut])
def list_leads(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: None = Depends(require_practitioner),
):
    """Practitioner review queue. Filter with ?status=pending_review to see what needs checking."""
    query = db.query(Lead).order_by(Lead.created_at.desc())
    if status:
        query = query.filter(Lead.status == status)
    return query.all()


@app.get("/api/leads/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: str, db: Session = Depends(get_db), _: None = Depends(require_practitioner)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.patch("/api/leads/{lead_id}/review", response_model=LeadOut)
def review_lead(
    lead_id: str,
    payload: LeadReviewUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_practitioner),
):
    """Practitioner approves the report, optionally editing it first."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if payload.edited_report is not None:
        lead.report = payload.edited_report
    lead.practitioner_notes = payload.practitioner_notes
    lead.reviewed_by = payload.reviewed_by
    lead.reviewed_at = datetime.utcnow()
    lead.status = "reviewed"

    db.commit()
    db.refresh(lead)
    return lead


@app.post("/api/leads/{lead_id}/send", response_model=LeadOut)
def send_lead_report(lead_id: str, db: Session = Depends(get_db), _: None = Depends(require_practitioner)):
    """
    Marks the report as sent. Wire this up to Resend (the same email
    provider CMC Connect already uses) once you have a template ready,
    see send_report_email() below for where that call goes.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.status != "reviewed":
        raise HTTPException(status_code=400, detail="Report must be reviewed before it can be sent")

    send_report_email(lead)

    lead.status = "sent"
    lead.sent_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return lead


@app.post("/api/leads/{lead_id}/book-click")
def track_booking_click(lead_id: str, db: Session = Depends(get_db)):
    """Public endpoint the front end calls when someone clicks 'Book a consultation'."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.booking_clicked = True
    db.commit()
    return {"ok": True}


def send_report_email(lead: Lead):
    """
    Stub for sending the final report by email via Resend.

    RESEND_API_KEY is not set yet, so this currently just prints to the
    log instead of sending. Once you have a Resend key and an email
    template, replace the body of this function with an actual API
    call, the same pattern CMC Connect already uses for its emails.
    """
    resend_key = os.environ.get("RESEND_API_KEY")
    if not resend_key:
        print(f"[email stub] Would send report to {lead.email} now (no RESEND_API_KEY set)")
        return

    # Example of what the real call will look like once a key exists:
    #
    # import resend
    # resend.api_key = resend_key
    # resend.Emails.send({
    #     "from": "reports@yourclinic.com",
    #     "to": lead.email,
    #     "subject": "Your Women's Health Check",
    #     "html": render_report_email_html(lead),
    # })
    print(f"[email stub] Sending report to {lead.email}")
