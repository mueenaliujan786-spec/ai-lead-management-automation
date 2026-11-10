import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.analysis import EmailDraft, LeadAIAnalysis
from app.models.lead import Lead, LeadStatusHistory
from app.models.user import User

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(get_current_user)],
)


class DraftListItem(BaseModel):
    draft_id: uuid.UUID
    status: str
    subject: str
    lead_id: uuid.UUID
    lead_name: str
    lead_email: str
    company: str | None
    category: str | None
    priority: str | None
    created_at: datetime


class DraftDetail(DraftListItem):
    body: str
    service_interest: str | None
    lead_message: str
    lead_status: str
    intent: str | None
    summary: str | None
    recommended_action: str | None
    reviewed_at: datetime | None


class DraftEdit(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5000)


class ReviewRequest(BaseModel):
    decision: Literal["approved", "rejected"]


class ReviewResult(BaseModel):
    draft_id: uuid.UUID
    draft_status: str
    lead_status: str


def _base_query():
    return (
        select(EmailDraft, Lead, LeadAIAnalysis)
        .join(Lead, Lead.id == EmailDraft.lead_id)
        .join(LeadAIAnalysis, LeadAIAnalysis.id == EmailDraft.analysis_id)
    )


def _list_item(d: EmailDraft, lead: Lead, a: LeadAIAnalysis) -> dict:
    return dict(
        draft_id=d.id,
        status=d.status,
        subject=d.subject,
        lead_id=lead.id,
        lead_name=lead.full_name,
        lead_email=lead.email,
        company=lead.company,
        category=a.category,
        priority=a.priority,
        created_at=d.created_at,
    )


@router.get("/drafts", response_model=list[DraftListItem])
def list_drafts(
    status: Literal["pending", "approved", "rejected", "sent"] | None = None,
    db: Session = Depends(get_db),
):
    query = _base_query().order_by(EmailDraft.created_at.desc()).limit(100)
    if status is not None:
        query = query.where(EmailDraft.status == status)
    rows = db.execute(query).all()
    return [DraftListItem(**_list_item(d, lead, a)) for d, lead, a in rows]


@router.get("/drafts/{draft_id}", response_model=DraftDetail)
def get_draft(draft_id: uuid.UUID, db: Session = Depends(get_db)):
    row = db.execute(_base_query().where(EmailDraft.id == draft_id)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    d, lead, a = row
    return DraftDetail(
        **_list_item(d, lead, a),
        body=d.body,
        service_interest=lead.service_interest,
        lead_message=lead.message,
        lead_status=lead.status,
        intent=a.intent,
        summary=a.summary,
        recommended_action=a.recommended_action,
        reviewed_at=d.reviewed_at,
    )


@router.patch("/drafts/{draft_id}", response_model=DraftDetail)
def edit_draft(
    draft_id: uuid.UUID, payload: DraftEdit, db: Session = Depends(get_db)
):
    subject = payload.subject.strip()
    body = payload.body.strip()
    if not subject or not body:
        raise HTTPException(
            status_code=422, detail="Subject and body cannot be empty"
        )
    # Line breaks in a subject could be used to inject extra email headers.
    if "\r" in subject or "\n" in subject:
        raise HTTPException(
            status_code=422, detail="Subject cannot contain line breaks"
        )

    draft = db.get(EmailDraft, draft_id, with_for_update=True)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != "pending":
        raise HTTPException(
            status_code=409, detail="Only pending drafts can be edited"
        )
    draft.subject = subject
    draft.body = body
    db.commit()
    return get_draft(draft_id, db)


@router.post("/drafts/{draft_id}/review", response_model=ReviewResult)
def review_draft(
    draft_id: uuid.UUID,
    payload: ReviewRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # with_for_update locks the row, so two clicks at once cannot both succeed.
    draft = db.get(EmailDraft, draft_id, with_for_update=True)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != "pending":
        raise HTTPException(status_code=409, detail="Draft already reviewed")

    lead = db.get(Lead, draft.lead_id)
    draft.status = payload.decision
    draft.reviewed_by = user.id
    draft.reviewed_at = datetime.now(timezone.utc)

    if payload.decision == "rejected" and lead.status == "awaiting_approval":
        db.add(
            LeadStatusHistory(
                lead_id=lead.id,
                old_status="awaiting_approval",
                new_status="analyzed",
                changed_by=user.id,
            )
        )
        lead.status = "analyzed"

    db.commit()
    return ReviewResult(
        draft_id=draft.id, draft_status=draft.status, lead_status=lead.status
    )
