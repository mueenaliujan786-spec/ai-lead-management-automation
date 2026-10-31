import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EmailDraft, Lead, LeadAIAnalysis, LeadStatusHistory
from app.schemas.analysis import AnalysisCreate, AnalysisSaved
from app.security import require_api_key

router = APIRouter(
    prefix="/leads", tags=["analysis"], dependencies=[Depends(require_api_key)]
)


@router.post("/{lead_id}/analysis", response_model=AnalysisSaved, status_code=201)
def save_analysis(
    lead_id: uuid.UUID, payload: AnalysisCreate, db: Session = Depends(get_db)
):
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    if payload.status == "success":
        already_done = db.scalar(
            select(LeadAIAnalysis.id).where(
                LeadAIAnalysis.lead_id == lead_id, LeadAIAnalysis.status == "success"
            )
        )
        if already_done:
            raise HTTPException(status_code=409, detail="Analysis already exists")

    data = payload.analysis
    record = LeadAIAnalysis(
        lead_id=lead_id,
        status=payload.status,
        ai_model=payload.ai_model,
        error_message=payload.error_message,
        category=data.category if data else None,
        priority=data.priority if data else None,
        intent=data.intent if data else None,
        summary=data.summary if data else None,
        recommended_action=data.recommended_action if data else None,
    )
    db.add(record)

    draft = None
    try:
        db.flush()
        if data is not None:
            draft = EmailDraft(
                lead_id=lead_id,
                analysis_id=record.id,
                subject=data.email_subject,
                body=data.email_draft,
            )
            db.add(draft)
            if lead.status == "new":
                db.add(
                    LeadStatusHistory(
                        lead_id=lead.id,
                        old_status="new",
                        new_status="awaiting_approval",
                    )
                )
                lead.status = "awaiting_approval"
        db.commit()
    except IntegrityError:
        # Two identical requests at the same moment: the database blocks the second.
        db.rollback()
        raise HTTPException(status_code=409, detail="Analysis already exists")

    return AnalysisSaved(
        analysis_id=record.id,
        draft_id=draft.id if draft else None,
        lead_status=lead.status,
    )