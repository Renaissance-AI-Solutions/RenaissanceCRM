"""Pydantic schemas for deals module."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    value: float = Field(default=0.0, ge=0)
    probability: int = Field(default=50, ge=0, le=100)
    stage_id: uuid.UUID
    contact_id: uuid.UUID | None = None
    assigned_to: uuid.UUID | None = None
    expected_close_date: datetime | None = None
    notes: str | None = None
    custom_fields: dict = {}


class DealUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    value: float | None = Field(default=None, ge=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    stage_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    assigned_to: uuid.UUID | None = None
    expected_close_date: datetime | None = None
    notes: str | None = None
    custom_fields: dict | None = None


class StageResponse(BaseModel):
    id: uuid.UUID
    name: str
    order: int
    color: str
    is_won: bool
    is_lost: bool

    model_config = {"from_attributes": True}


class DealResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    title: str
    value: float
    probability: int
    stage_id: uuid.UUID
    contact_id: uuid.UUID | None
    assigned_to: uuid.UUID | None
    expected_close_date: datetime | None
    notes: str | None
    custom_fields: dict
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None

    model_config = {"from_attributes": True}


class DealListResponse(BaseModel):
    items: list[DealResponse]
    total: int
    page: int
    per_page: int


class PipelineStats(BaseModel):
    total_deals: int
    total_value: float
    weighted_value: float
    avg_probability: float
    stages: list[dict]
