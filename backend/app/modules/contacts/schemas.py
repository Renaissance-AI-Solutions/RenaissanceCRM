"""Pydantic schemas for contacts module."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ContactCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, max_length=150)
    company_id: uuid.UUID | None = None
    source: str | None = Field(default=None, max_length=100)
    status: str = Field(default="new", max_length=50)
    tags: list[str] = []
    custom_fields: dict = {}
    notes: str | None = None


class ContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, max_length=150)
    company_id: uuid.UUID | None = None
    source: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=50)
    tags: list[str] | None = None
    custom_fields: dict | None = None
    notes: str | None = None


class ContactResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    title: str | None
    linkedin_url: str | None = None
    departments: list = []
    seniorities: list = []
    is_primary_contact: bool = False
    enrichment_status: str | None = None
    personal_emails: list = []
    company_id: uuid.UUID | None
    source: str | None
    status: str
    tags: list
    custom_fields: dict
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactListResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    per_page: int


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    domain: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=100)
    size: str | None = Field(default=None, max_length=50)
    address: str | None = None
    phone: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None, max_length=500)
    custom_fields: dict = {}


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    domain: str | None = None
    industry: str | None = None
    size: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    custom_fields: dict | None = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    domain: str | None
    industry: str | None
    size: str | None
    address: str | None
    phone: str | None
    website: str | None
    google_maps_url: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    custom_fields: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
