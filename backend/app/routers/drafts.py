import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EmailDraft, Lead, LeadStatusHistory
from app.security import require_api_key

router = APIRouter(
    prefix="/drafts", tags=["drafts"], dependencies=[Depends(require_api_key)]
)


class ReviewRequest(BaseModel):
    decision: Literal["approved", "rejected"]


class ReviewResult(BaseModel):
    draft_id: uuid.UUID
    draft_status: str
    lead_status: str


class ApprovedDraft(BaseModel):
    draft_id: uuid.UUID
    lead_id: uuid.UUID
    to_email: str
    to_name: str
    subject: str
    body: str


@router.get("/approved", response_model=list[ApprovedDraft])
def list_approved(db: Session = Depends(get_db)):
    rows = db.execute(
        select(EmailDraft, Lead)
        .join(Lead, Lead.id == EmailDraft.lead_id)
        .where(EmailDraft.status == "approved", Lead.status != "opted_out")
        .order_by(EmailDraft.created_at)
        .limit(20)
    ).all()
    return [
        ApprovedDraft(
            draft_id=d.id,
            lead_id=l.id,
            to_email=l.email,
            to_name=l.full_name,
            subject=d.subject,
            body=d.body,
        )
        for d, l in rows
    ]


@router.post("/{draft_id}/review", response_model=ReviewResult)
def review_draft(
    draft_id: uuid.UUID, payload: ReviewRequest, db: Session = Depends(get_db)
):
    # with_for_update locks the row, so two clicks at once cannot both succeed.
    draft = db.get(EmailDraft, draft_id, with_for_update=True)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != "pending":
        raise HTTPException(status_code=409, detail="Draft already reviewed")

    lead = db.get(Lead, draft.lead_id)

    draft.status = payload.decision
    draft.reviewed_at = datetime.now(timezone.utc)

    if payload.decision == "rejected" and lead.status == "awaiting_approval":
        db.add(
            LeadStatusHistory(
                lead_id=lead.id,
                old_status="awaiting_approval",
                new_status="analyzed",
            )
        )
        lead.status = "analyzed"

    db.commit()

    return ReviewResult(
        draft_id=draft.id, draft_status=draft.status, lead_status=lead.status
    )


@router.post("/{draft_id}/sent", response_model=ReviewResult)
def mark_sent(draft_id: uuid.UUID, db: Session = Depends(get_db)):
    draft = db.get(EmailDraft, draft_id, with_for_update=True)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != "approved":
        raise HTTPException(status_code=409, detail="Draft is not approved")

    lead = db.get(Lead, draft.lead_id)

    draft.status = "sent"

    if lead.status in ("awaiting_approval", "analyzed"):
        db.add(
            LeadStatusHistory(
                lead_id=lead.id,
                old_status=lead.status,
                new_status="contacted",
            )
        )
        lead.status = "contacted"

    db.commit()

    return ReviewResult(
        draft_id=draft.id, draft_status=draft.status, lead_status=lead.status
    )