import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Lead(Base):
    """A potential customer who contacted the business."""

    __tablename__ = "leads"
    __table_args__ = (
        # Stops the same person from submitting the exact same message twice.
        UniqueConstraint("email", "content_hash", name="uq_leads_email_content"),
        CheckConstraint(
            "status IN ('new', 'analyzed', 'awaiting_approval', "
            "'contacted', 'closed', 'opted_out')",
            name="ck_leads_status",
        ),
        Index("ix_leads_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    company: Mapped[str | None] = mapped_column(String(160))
    service_interest: Mapped[str | None] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), server_default="new")
    follow_up_paused: Mapped[bool] = mapped_column(Boolean, server_default="false")
    # Fingerprint of the message, used to detect duplicates.
    content_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LeadStatusHistory(Base):
    """One row for every time a lead's status changes."""

    __tablename__ = "lead_status_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )
    old_status: Mapped[str | None] = mapped_column(String(30))
    new_status: Mapped[str] = mapped_column(String(30))
    # Empty when the system changed the status automatically.
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )