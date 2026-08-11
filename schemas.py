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


class SignupRequest(BaseModel):
    lead_id: Optional[str] = None
    name: str
    email: EmailStr
    phone: Optional[str] = None
    bio: Optional[str] = None
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeReportOut(BaseModel):
    life_stage: Optional[str] = None
    report: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    reviewed_by: Optional[str] = None
    has_report: bool
