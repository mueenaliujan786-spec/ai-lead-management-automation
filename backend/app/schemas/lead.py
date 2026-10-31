import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Invisible control characters (except normal tab and new lines) are removed.
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# Very basic detection of script injection attempts.
SUSPICIOUS = re.compile(r"<\s*script|javascript:|onerror\s*=", re.IGNORECASE)


def clean_text(value: str) -> str:
    """Remove control characters, trim spaces, reject suspicious content."""
    value = CONTROL_CHARS.sub("", value).strip()
    if SUSPICIOUS.search(value):
        raise ValueError("Input contains disallowed content")
    return value


class LeadCreate(BaseModel):
    """What a customer (or n8n) must send to create a lead."""

    # Unknown fields are rejected instead of silently ignored.
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    company: str | None = Field(default=None, max_length=160)
    service_interest: str | None = Field(default=None, max_length=160)
    message: str = Field(min_length=1, max_length=5000)
    source: str = Field(default="api", min_length=1, max_length=50)

    @field_validator(
        "full_name",
        "phone",
        "company",
        "service_interest",
        "message",
        "source",
        mode="before",
    )
    @classmethod
    def sanitize(cls, value):
        # mode="before" runs this cleaning first, then length rules are checked.
        if isinstance(value, str):
            return clean_text(value)
        return value


class LeadCreated(BaseModel):
    """What the API sends back after a lead is saved (no message text)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    status: str
    created_at: datetime