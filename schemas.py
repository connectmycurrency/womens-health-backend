from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, EmailStr


class LeadCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    marketing_consent: bool = False
    partner_share_consent: bool = False
    life_stage: str
    answers: Dict[str, Any]


class LeadReviewUpdate(BaseModel):
    practitioner_notes: Optional[str] = None
    reviewed_by: str
    # If the practitioner wants to change the report text before it goes
    # out, they can pass an edited version here. If omitted, the
    # server-generated report is approved as-is.
    edited_report: Optional[Dict[str, Any]] = None


class LeadOut(BaseModel):
    id: str
    created_at: datetime
    name: Optional[str]
    email: str
    life_stage: str
    answers: Dict[str, Any]
    report: Dict[str, Any]
    status: str
    practitioner_notes: Optional[str]
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    sent_at: Optional[datetime]
    booking_clicked: bool

    class Config:
        from_attributes = True
