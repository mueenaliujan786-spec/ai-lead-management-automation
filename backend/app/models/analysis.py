import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LeadAIAnalysis(Base):
    """The AI's analysis of a lead. A recommendation, not a verified fact."""

    __tablename__ = "lead_ai_analyses"
    __table_args__ = (
        CheckConstraint("status IN ('success', 'failed')", name="ck_analyses_status"),
        CheckConstraint(
            "priority IS NULL OR priority IN ('High', 'Medium', 'Low')",
            name="ck_analyses_priority",
        ),
        # Only ONE successful analysis per lead, enforced by the database itself.
        Index(
            "uq_one_success_per_lead",
            "lead_id",
            unique=True,
            postgresql_where=text("status = 'success'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str | None] = mapped_column(String(100))
    priority: Mapped[str | None] = mapped_column(String(10))
    intent: Mapped[str | None] = mapped_column(String(300))
    summary: Mapped[str | None] = mapped_column(String(1000))
    recommended_action: Mapped[str | None] = mapped_column(String(500))
    ai_model: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))
    error_message: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class EmailDraft(Base):
    """A draft email waiting for a human to approve, edit, or reject it."""

    __tablename__ = "email_drafts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'sent')",
            name="ck_drafts_status",
        ),
        Index("ix_email_drafts_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )
    # unique=True: one draft per analysis, so a retry can't create a second one.
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lead_ai_analyses.id", ondelete="CASCADE"), unique=True
    )
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), server_default="pending")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )