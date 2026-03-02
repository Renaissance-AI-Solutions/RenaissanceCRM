"""Pydantic schemas for n8n webhook payloads."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.models import ActivityType


class N8nLeadPayload(BaseModel):
    """Payload from n8n to create or update a contact (lead)."""
    email: EmailStr
    first_name: str = Field(default="", max_length=100)
    last_name: str = Field(default="", max_length=100)
    phone: str | None = None
    title: str | None = None
    company_name: str | None = None
    company_domain: str | None = None
    source: str = Field(default="n8n", max_length=100)
    status: str = Field(default="new", max_length=50)
    tags: list[str] = []
    custom_fields: dict = {}
    notes: str | None = None


class N8nActivityPayload(BaseModel):
    """Payload from n8n to log an activity against a contact."""
    contact_email: EmailStr | None = None
    contact_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None
    type: ActivityType = ActivityType.EMAIL
    subject: str = Field(min_length=1, max_length=500)
    body: str | None = None
    metadata: dict = {}
    timestamp: datetime | None = None


class N8nDealUpdatePayload(BaseModel):
    """Payload from n8n to update a deal's stage or owner."""
    deal_id: uuid.UUID
    stage_name: str | None = None
    assigned_to_email: str | None = None
    value: float | None = None
    probability: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class N8nEmailHistoryPayload(BaseModel):
    """Payload from n8n containing email thread history for a contact."""
    contact_email: EmailStr
    contact_id: uuid.UUID | None = None
    emails: list["EmailEntry"]


class EmailEntry(BaseModel):
    """A single email in a thread history."""
    subject: str
    body: str
    from_address: str
    to_addresses: list[str] = []
    cc_addresses: list[str] = []
    date: datetime
    direction: str = Field(default="inbound", pattern="^(inbound|outbound)$")
    thread_id: str | None = None
    message_id: str | None = None
    labels: list[str] = []


# ---------------------------------------------------------------------------
# Clay webhook schemas
# ---------------------------------------------------------------------------
class ClayPersonEntry(BaseModel):
    """A single person/employee from the Clay people array."""
    companyDomain: str | None = None
    companyName: str | None = None
    country: str | None = None
    departments: list[str] = []
    firstName: str
    fullName: str
    jobTitle: str | None = None
    lastName: str
    linkedInUrl: str | None = None
    seniorities: list[str] = []


class ClayPersonalEmail(BaseModel):
    """A single email entry from Clay's personal_emails."""
    email: EmailStr
    domain: str | None = None
    tags: list[str] = []


class ClayPersonalEmails(BaseModel):
    """Personal emails block from Clay — matched to one person."""
    model_config = {"extra": "ignore"}
    emails: list[ClayPersonalEmail] = []
    full_name: str | None = None
    linkedin_url: str | None = None


class ClayWebhookBody(BaseModel):
    """The body of a Clay webhook payload."""
    address: str | None = None
    company: str
    google_maps_url: str | None = None
    people: list[ClayPersonEntry]
    personal_emails: ClayPersonalEmails | None = None
    phone: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    source: str = "clay"
    website: str | None = None


class ClayWebhookPayload(BaseModel):
    """Top-level envelope for Clay webhook data."""
    body: ClayWebhookBody


# ---------------------------------------------------------------------------
# Enrichment schemas
# ---------------------------------------------------------------------------
class EnrichContactPayload(BaseModel):
    """Payload to update a contact with enriched email data."""
    contact_id: uuid.UUID | None = None
    linkedin_url: str | None = None  # alternative lookup
    email: EmailStr
    enrichment_source: str = "clay"


class WebhookResponse(BaseModel):
    success: bool
    message: str
    data: dict = {}


# ---------------------------------------------------------------------------
# Company-with-Draft schemas (combined Clay + AI output)
# ---------------------------------------------------------------------------
class AiOutputBlock(BaseModel):
    """A single block from the AI output array (reasoning, message, or tool_call)."""
    type: str  # "reasoning", "message", "tool_call"
    content: str | None = None
    tool: str | None = None
    arguments: dict | None = None
    output: str | None = None  # tool call result (raw string)


class AiOutputEntry(BaseModel):
    """One element from the AI response array — maps to JSON 1's structure."""
    model_instance_id: str | None = None
    output: list[AiOutputBlock] = []


class CompanyWithDraftPayload(BaseModel):
    """Top-level payload for the combined company + draft email endpoint.

    N8N sends this as a single POST containing:
    - body: the Clay webhook body (company + people + personal_emails)
    - ai_output: the AI-generated draft email data (array of model responses)
    """
    body: ClayWebhookBody
    ai_output: list[AiOutputBlock] = []


# ---------------------------------------------------------------------------
# Draft-email-sent callback schema
# ---------------------------------------------------------------------------
class DraftEmailSentPayload(BaseModel):
    """Payload from n8n after it successfully sends a draft email."""
    draft_email_id: uuid.UUID
