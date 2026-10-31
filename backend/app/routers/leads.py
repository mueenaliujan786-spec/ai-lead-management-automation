import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead, LeadStatusHistory
from app.schemas.lead import LeadCreate, LeadCreated
from app.security import require_api_key

router = APIRouter(
    prefix="/leads", tags=["leads"], dependencies=[Depends(require_api_key)]
)


def make_content_hash(email: str, message: str) -> str:
    """A fingerprint of email + message, used to detect duplicates."""
    normalized = " ".join(message.lower().split())
    raw = f"{email.lower()}|{normalized}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@router.post("", response_model=LeadCreated, status_code=201)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    email = payload.email.lower()
    content_hash = make_content_hash(email, payload.message)

    already_exists = db.scalar(
        select(Lead.id).where(Lead.email == email, Lead.content_hash == content_hash)
    )
    if already_exists:
        raise HTTPException(status_code=409, detail="Duplicate lead")

    lead = Lead(
        full_name=payload.full_name,
        email=email,
        phone=payload.phone,
        company=payload.company,
        service_interest=payload.service_interest,
        message=payload.message,
        source=payload.source,
        content_hash=content_hash,
    )
    db.add(lead)

    try:
        db.flush()  # sends the INSERT so the lead's id is ready
        db.add(LeadStatusHistory(lead_id=lead.id, old_status=None, new_status="new"))
        db.commit()
    except IntegrityError:
        # Two identical requests at the same moment: the database blocks the second.
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate lead")

    db.refresh(lead)
    return lead