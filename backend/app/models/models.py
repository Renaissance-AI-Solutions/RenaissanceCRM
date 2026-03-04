"""SQLAlchemy models for the CRM system.

All models include `tenant_id` for multi-tenant data isolation.
JSONB columns are used for custom fields and flexible configuration.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"
    VIEW_ONLY = "view_only"


class ActivityType(str, enum.Enum):
    EMAIL = "email"
    CALL = "call"
    NOTE = "note"
    MEETING = "meeting"
    SYSTEM = "system"


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class EnrichmentStatus(str, enum.Enum):
    NOT_NEEDED = "not_needed"    # already has email
    PENDING = "pending"          # waiting for primary to fail
    QUEUED = "queued"            # enrichment requested
    ENRICHED = "enriched"        # email found via enrichment
    FAILED = "failed"            # enrichment failed to find email


class DraftEmailStatus(str, enum.Enum):
    DRAFT = "draft"              # AI-generated, awaiting review
    APPROVED = "approved"        # user approved, ready to send
    SENT = "sent"                # sent via n8n callback
    REJECTED = "rejected"        # user rejected the draft


class EmailThreadStatus(str, enum.Enum):
    ACTIVE = "active"            # conversation ongoing
    CLOSED = "closed"            # conversation closed


class CustomFieldType(str, enum.Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    BOOLEAN = "boolean"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"


# ---------------------------------------------------------------------------
# Tenant
# ---------------------------------------------------------------------------
class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    contacts: Mapped[list["Contact"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    companies: Mapped[list["Company"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    deals: Mapped[list["Deal"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    pipeline_stages: Mapped[list["PipelineStage"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    email_threads: Mapped[list["EmailThread"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# User / Auth
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", "tenant_id", name="uq_user_email_tenant"),
        Index("ix_users_tenant", "tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.SALES_REP)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")
    activities: Mapped[list["Activity"]] = relationship(back_populates="user")
    assigned_deals: Mapped[list["Deal"]] = relationship(back_populates="assigned_user", foreign_keys="Deal.assigned_to")


class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = (Index("ix_api_keys_tenant", "tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)  # First 8 chars for identification
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="api_keys")


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------
class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("domain", "tenant_id", name="uq_company_domain_tenant"),
        Index("ix_companies_tenant", "tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_maps_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="companies")
    contacts: Mapped[list["Contact"]] = relationship(back_populates="company")
    draft_emails: Mapped[list["DraftEmail"]] = relationship(back_populates="company")
    email_threads: Mapped[list["EmailThread"]] = relationship(back_populates="company")


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------
class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        Index("ix_contacts_tenant", "tenant_id"),
        Index("ix_contacts_email", "email"),
        Index("ix_contacts_tenant_email", "tenant_id", "email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    departments: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    seniorities: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    enrichment_status: Mapped[EnrichmentStatus | None] = mapped_column(
        Enum(EnrichmentStatus), nullable=True, default=None,
    )
    personal_emails: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="new")
    tags: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="contacts")
    company: Mapped["Company | None"] = relationship(back_populates="contacts")
    deals: Mapped[list["Deal"]] = relationship(back_populates="contact")
    activities: Mapped[list["Activity"]] = relationship(back_populates="contact")
    draft_emails: Mapped[list["DraftEmail"]] = relationship(back_populates="contact")
    email_threads: Mapped[list["EmailThread"]] = relationship(back_populates="contact")


# ---------------------------------------------------------------------------
# Pipeline & Deals
# ---------------------------------------------------------------------------
class PipelineStage(Base):
    __tablename__ = "pipeline_stages"
    __table_args__ = (
        UniqueConstraint("name", "tenant_id", name="uq_stage_name_tenant"),
        Index("ix_pipeline_stages_tenant", "tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    color: Mapped[str] = mapped_column(String(7), default="#6366f1")  # Hex color
    is_won: Mapped[bool] = mapped_column(Boolean, default=False)
    is_lost: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="pipeline_stages")
    deals: Mapped[list["Deal"]] = relationship(back_populates="stage")


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = (
        Index("ix_deals_tenant", "tenant_id"),
        Index("ix_deals_stage", "stage_id"),
        Index("ix_deals_contact", "contact_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    stage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=False)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[float] = mapped_column(Float, default=0.0)
    probability: Mapped[int] = mapped_column(Integer, default=50)  # 0-100
    expected_close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="deals")
    contact: Mapped["Contact | None"] = relationship(back_populates="deals")
    stage: Mapped["PipelineStage"] = relationship(back_populates="deals")
    assigned_user: Mapped["User | None"] = relationship(back_populates="assigned_deals", foreign_keys=[assigned_to])
    activities: Mapped[list["Activity"]] = relationship(back_populates="deal")


# ---------------------------------------------------------------------------
# Activity
# ---------------------------------------------------------------------------
class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (
        Index("ix_activities_tenant", "tenant_id"),
        Index("ix_activities_contact", "contact_id"),
        Index("ix_activities_deal", "deal_id"),
        Index("ix_activities_created", "created_at"),
        Index("ix_activities_thread", "thread_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    thread_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("email_threads.id"), nullable=True)
    gmail_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type: Mapped[ActivityType] = mapped_column(Enum(ActivityType), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default="{}")
    source: Mapped[str] = mapped_column(String(50), default="manual")  # manual, n8n, system, gmail
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    contact: Mapped["Contact | None"] = relationship(back_populates="activities")
    deal: Mapped["Deal | None"] = relationship(back_populates="activities")
    user: Mapped["User | None"] = relationship(back_populates="activities")
    thread: Mapped["EmailThread | None"] = relationship(back_populates="activities")


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_tenant", "tenant_id"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False)
    changes: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ---------------------------------------------------------------------------
# Customization
# ---------------------------------------------------------------------------
class CustomFieldDefinition(Base):
    __tablename__ = "custom_field_definitions"
    __table_args__ = (
        UniqueConstraint("entity_type", "field_name", "tenant_id", name="uq_field_def_tenant"),
        Index("ix_custom_fields_tenant", "tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # contact, company, deal
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    field_label: Mapped[str] = mapped_column(String(150), nullable=False)
    field_type: Mapped[CustomFieldType] = mapped_column(Enum(CustomFieldType), nullable=False)
    options: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")  # For select types
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WebhookConfig(Base):
    __tablename__ = "webhook_configs"
    __table_args__ = (Index("ix_webhook_configs_tenant", "tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    event: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    headers: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# Email Thread
# ---------------------------------------------------------------------------
class EmailThread(Base):
    """Groups all inbound/outbound emails for a single conversation with a contact."""
    __tablename__ = "email_threads"
    __table_args__ = (
        Index("ix_email_threads_tenant", "tenant_id"),
        Index("ix_email_threads_contact", "contact_id"),
        Index("ix_email_threads_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)  # Subject of the first email
    gmail_thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Gmail's native thread ID
    status: Mapped[EmailThreadStatus] = mapped_column(
        Enum(EmailThreadStatus), default=EmailThreadStatus.ACTIVE, nullable=False
    )
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="email_threads")
    contact: Mapped["Contact"] = relationship(back_populates="email_threads")
    company: Mapped["Company | None"] = relationship(back_populates="email_threads")
    draft_emails: Mapped[list["DraftEmail"]] = relationship(back_populates="thread")
    activities: Mapped[list["Activity"]] = relationship(back_populates="thread")


# ---------------------------------------------------------------------------
# Draft Email
# ---------------------------------------------------------------------------
class DraftEmail(Base):
    __tablename__ = "draft_emails"
    __table_args__ = (
        Index("ix_draft_emails_tenant", "tenant_id"),
        Index("ix_draft_emails_company", "company_id"),
        Index("ix_draft_emails_contact", "contact_id"),
        Index("ix_draft_emails_status", "status"),
        Index("ix_draft_emails_thread", "thread_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    thread_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("email_threads.id"), nullable=True)
    gmail_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Gmail Message-ID after sending
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DraftEmailStatus] = mapped_column(
        Enum(DraftEmailStatus), default=DraftEmailStatus.DRAFT, nullable=False,
    )
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    company: Mapped["Company"] = relationship(back_populates="draft_emails")
    contact: Mapped["Contact"] = relationship(back_populates="draft_emails")
    thread: Mapped["EmailThread | None"] = relationship(back_populates="draft_emails")
