import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

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
                          edited) the report, but it has not been sent
      sent             -> the report has been emailed to the person
    """
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Contact details captured at the end of the quiz
    name = Column(String, nullable=True)
    email = Column(String, nullable=False, index=True)
    marketing_consent = Column(Boolean, default=False)
    partner_share_consent = Column(Boolean, default=False)

    # Raw quiz answers, exactly as submitted by the front end
    life_stage = Column(String, nullable=False)
    answers = Column(JSON, nullable=False)

    # Computed per-track results (bands + copy), generated server-side
    # from the answers so scoring logic lives in one place, not
    # duplicated between the front end and the backend.
    report = Column(JSON, nullable=False)

    status = Column(String, default="pending_review")
    practitioner_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    booking_clicked = Column(Boolean, default=False)
