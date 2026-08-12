import os
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import Base, engine, get_db, SessionLocal
from models import Lead, User
from schemas import (
    LeadCreate, LeadOut, LeadReviewUpdate,
    SignupRequest, LoginRequest, TokenOut, MeReportOut,
)
from scoring import build_report
from auth_utils import hash_password, verify_password, create_access_token, decode_access_token
from emailer import send_report_ready_email
from report_pdf import build_report_pdf

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Women's Health Check API")

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN") or "*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/admin", StaticFiles(directory="static", html=True), name="admin")
app.mount("/portal", StaticFiles(directory="static/portal", html=True), name="portal")

PRACTITIONER_API_KEY = os.environ.get("PRACTITIONER_API_KEY", "change-me-before-deploying")

WHATSAPP_COMMUNITY_URL = os.environ.get("WHATSAPP_COMMUNITY_URL", "https://chat.whatsapp.com/replace-with-your-invite-link")


def require_practitioner(x_api_key: Optional[str] = Header(default=None)):
    if not x_api_key or x_api_key != PRACTITIONER_API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")


def get_current_user(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.get("/")
def health_check():
    return {"status": "ok", "service": "womens-health-check-api"}


# ---------- Lead submission (called by the quiz) ----------

def _send_lead_email_background(lead_id: str):
    """Runs after the response has already gone back to the client. Opens
    its own DB session since the request's session is closed by then.
    Sending via Resend was previously done inline before responding, which
    added several seconds (sometimes much more, on top of Render free-tier
    cold starts) to every quiz submission. Moving it here means the client
    gets its response as soon as the lead is saved, not after the email
    round-trip finishes too."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return
        send_report_ready_email(lead)
        lead.sent_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


@app.post("/api/leads", response_model=LeadOut)
def create_lead(payload: LeadCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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

    # Email is teaser + a link to the signup/portal page, never the full
    # report content itself, so nothing detailed leaves via email. Sent in
    # the background so the quiz doesn't sit waiting on it.
    background_tasks.add_task(_send_lead_email_background, lead.id)

    return lead


# ---------- Practitioner review queue ----------

@app.get("/api/leads", response_model=List[LeadOut])
def list_leads(status: Optional[str] = None, db: Session = Depends(get_db), _: None = Depends(require_practitioner)):
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
def review_lead(lead_id: str, payload: LeadReviewUpdate, db: Session = Depends(get_db), _: None = Depends(require_practitioner)):
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


@app.post("/api/leads/{lead_id}/book-click")
def track_booking_click(lead_id: str, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.booking_clicked = True
    db.commit()
    return {"ok": True}


# ---------- Account signup / login (from the report-ready email) ----------

@app.post("/api/signup", response_model=TokenOut)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists. Try logging in instead.")

    user = User(
        lead_id=payload.lead_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        bio=payload.bio,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="An account with this email already exists. Try logging in instead.")
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenOut(access_token=token)


@app.post("/api/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(user.id)
    return TokenOut(access_token=token)


# ---------- The logged-in person's own report ----------

def _effective_report(lead: Lead) -> dict:
    """Reports are computed once at signup and frozen into lead.report so
    a practitioner's edits survive. But before a practitioner has reviewed
    a lead, nothing has been intentionally edited yet, so serving the
    frozen snapshot means content/scoring updates in scoring.py never
    reach accounts that signed up before the update, even after a
    redesign ships. Recompute from the stored answers on every read until
    the lead is reviewed; once reviewed, the stored value (possibly
    hand-edited by a practitioner) is authoritative and must not be
    overwritten."""
    if lead.status == "reviewed":
        return lead.report
    return build_report(lead.life_stage, lead.answers)


@app.get("/api/me/report", response_model=MeReportOut)
def get_my_report(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.lead_id:
        return MeReportOut(has_report=False)
    lead = db.query(Lead).filter(Lead.id == user.lead_id).first()
    if not lead:
        return MeReportOut(has_report=False)
    return MeReportOut(
        life_stage=lead.life_stage,
        report=_effective_report(lead),
        status=lead.status,
        reviewed_by=lead.reviewed_by,
        has_report=True,
    )


@app.get("/api/me/report/pdf")
def download_my_report_pdf(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.lead_id:
        raise HTTPException(status_code=404, detail="No report linked to this account")
    lead = db.query(Lead).filter(Lead.id == user.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="No report linked to this account")

    pdf_bytes = build_report_pdf(
        user_name=user.name,
        life_stage=lead.life_stage,
        report=_effective_report(lead),
        reviewed=(lead.status == "reviewed"),
        reviewed_by=lead.reviewed_by,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=womens-health-check-report.pdf"},
    )


@app.get("/api/whatsapp-link")
def get_whatsapp_link():
    return {"url": WHATSAPP_COMMUNITY_URL}


@app.post("/api/me/whatsapp-click")
def track_whatsapp_click(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.whatsapp_clicked = True
    db.commit()
    return {"ok": True}
