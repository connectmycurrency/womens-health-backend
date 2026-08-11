import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, Text, Boolean

from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Lead(Base):
    """
    One row per person who completes the quiz.

    status moves through:
      pending_review -> the report has been generated but a practitioner
                         has not yet checked it
      reviewed        -> a practitioner has approved (and optionally
                          edited) the report
      sent             -> the report-ready email (teaser + signup link)
                          has been sent
    """
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)

    name = Column(String, nullable=True)
    email = Column(String, nullable=False, index=True)
    marketing_consent = Column(Boolean, default=False)
    partner_share_consent = Column(Boolean, default=False)

    life_stage = Column(String, nullable=False)
    answers = Column(JSON, nullable=False)
    report = Column(JSON, nullable=False)

    status = Column(String, default="pending_review")
    practitioner_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    booking_clicked = Column(Boolean, default=False)


class User(Base):
    """
    An account created when someone signs up from the report-ready
    email to view or download their full report. Linked back to the
    Lead that generated the report via lead_id.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)

    lead_id = Column(String, nullable=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    phone = Column(String, nullable=True)
    bio = Column(Text, nullable=True)

    password_hash = Column(String, nullable=False)

    whatsapp_clicked = Column(Boolean, default=False)
