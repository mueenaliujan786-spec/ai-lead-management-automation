import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.lead import clean_text


class AnalysisFields(BaseModel):
    """The 7 fields the AI must return. Checked again here: never trust the AI."""

    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1, max_length=100)
    priority: Literal["High", "Medium", "Low"]
    intent: str = Field(min_length=1, max_length=300)
    summary: str = Field(min_length=1, max_length=1000)
    recommended_action: str = Field(min_length=1, max_length=500)
    email_subject: str = Field(min_length=1, max_length=200)
    email_draft: str = Field(min_length=1, max_length=3000)

    @field_validator(
        "category",
        "intent",
        "summary",
        "recommended_action",
        "email_subject",
        "email_draft",
        mode="before",
    )
    @classmethod
    def sanitize(cls, value):
        if isinstance(value, str):
            return clean_text(value)
        return value


class AnalysisCreate(BaseModel):
    """What n8n sends to save an analysis (success) or a failure."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "failed"]
    ai_model: str = Field(min_length=1, max_length=100)
    analysis: AnalysisFields | None = None
    error_message: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def check_consistency(self):
        if self.status == "success" and self.analysis is None:
            raise ValueError("analysis is required when status is success")
        if self.status == "failed":
            if not self.error_message:
                raise ValueError("error_message is required when status is failed")
            if self.analysis is not None:
                raise ValueError("analysis must be empty when status is failed")
        return self


class AnalysisSaved(BaseModel):
    analysis_id: uuid.UUID
    draft_id: uuid.UUID | None
    lead_status: str