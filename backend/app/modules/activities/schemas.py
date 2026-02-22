"""Pydantic schemas for activities module."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.models import ActivityType


class ActivityCreate(BaseModel):
    type: ActivityType
    subject: str = Field(min_length=1, max_length=500)
    body: str | None = None
    contact_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None
    metadata_: dict = Field(default={}, alias="metadata")
    source: str = Field(default="manual", max_length=50)
    is_pinned: bool = False


class ActivityUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=500)
    body: str | None = None
    is_pinned: bool | None = None
    metadata_: dict | None = Field(default=None, alias="metadata")


class ActivityResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    contact_id: uuid.UUID | None
    deal_id: uuid.UUID | None
    user_id: uuid.UUID | None
    type: ActivityType
    subject: str
    body: str | None
    metadata_: dict
    source: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    page: int
    per_page: int
