"""Email Threads router — list threads and get full thread message history."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.models import (
    Activity,
    ActivityType,
    Contact,
    DraftEmail,
    DraftEmailStatus,
    EmailThread,
    EmailThreadStatus,
    User,
)

router = APIRouter(prefix="/api/email-threads", tags=["Email Threads"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ThreadMessage(BaseModel):
    id: str
    type: str          # "draft" | "inbound" | "outbound"
    direction: str     # "inbound" | "outbound"
    subject: str
    body: str | None
    from_addr: str | None = None
    status: str | None = None  # for drafts: draft/approved/sent/rejected
    ai_model: str | None = None
    ai_reasoning: str | None = None
    gmail_message_id: str | None = None
    created_at: datetime
    source: str | None = None


class ThreadDetail(BaseModel):
    id: str
    contact_id: str
    company_id: str | None
    subject: str
    status: str
    last_activity_at: datetime
    created_at: datetime
    messages: list[ThreadMessage]
    contact_name: str | None = None
    contact_email: str | None = None
    has_pending_draft: bool = False


class ThreadSummary(BaseModel):
    id: str
    contact_id: str
    subject: str
    status: str
    last_activity_at: datetime
    created_at: datetime
    contact_name: str | None = None
    contact_email: str | None = None
    message_count: int = 0
    has_pending_draft: bool = False


# ---------------------------------------------------------------------------
# List threads
# ---------------------------------------------------------------------------

@router.get("", response_model=list[ThreadSummary])
async def list_threads(
    contact_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List email threads, optionally filtered by contact_id or status."""
    query = select(EmailThread).where(EmailThread.tenant_id == current_user.tenant_id)

    if contact_id:
        query = query.where(EmailThread.contact_id == contact_id)
    if status:
        try:
            status_enum = EmailThreadStatus(status)
            query = query.where(EmailThread.status == status_enum)
        except ValueError:
            pass

    query = query.order_by(EmailThread.last_activity_at.desc()).limit(limit)
    result = await db.execute(query)
    threads = result.scalars().all()

    summaries = []
    for thread in threads:
        # Get contact name/email
        contact_result = await db.execute(select(Contact).where(Contact.id == thread.contact_id))
        contact = contact_result.scalar_one_or_none()

        # Count messages
        drafts_result = await db.execute(
            select(DraftEmail).where(DraftEmail.thread_id == thread.id)
        )
        drafts = drafts_result.scalars().all()

        activities_result = await db.execute(
            select(Activity).where(
                Activity.thread_id == thread.id,
                Activity.type == ActivityType.EMAIL,
            )
        )
        activities = activities_result.scalars().all()

        has_pending = any(d.status == DraftEmailStatus.DRAFT for d in drafts)

        summaries.append(ThreadSummary(
            id=str(thread.id),
            contact_id=str(thread.contact_id),
            subject=thread.subject,
            status=thread.status.value,
            last_activity_at=thread.last_activity_at,
            created_at=thread.created_at,
            contact_name=f"{contact.first_name} {contact.last_name}".strip() if contact else None,
            contact_email=contact.email if contact else None,
            message_count=len(drafts) + len(activities),
            has_pending_draft=has_pending,
        ))

    return summaries


# ---------------------------------------------------------------------------
# Get full thread
# ---------------------------------------------------------------------------

@router.get("/{thread_id}", response_model=ThreadDetail)
async def get_thread(
    thread_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full thread with all messages interleaved chronologically."""
    result = await db.execute(
        select(EmailThread).where(
            EmailThread.id == thread_id,
            EmailThread.tenant_id == current_user.tenant_id,
        )
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Contact info
    contact_result = await db.execute(select(Contact).where(Contact.id == thread.contact_id))
    contact = contact_result.scalar_one_or_none()

    # Draft emails (outbound — both sent and pending)
    drafts_result = await db.execute(
        select(DraftEmail).where(DraftEmail.thread_id == thread.id)
        .order_by(DraftEmail.created_at)
    )
    drafts = drafts_result.scalars().all()

    # Email activities (inbound from Gmail)
    activities_result = await db.execute(
        select(Activity).where(
            Activity.thread_id == thread.id,
            Activity.type == ActivityType.EMAIL,
        ).order_by(Activity.created_at)
    )
    activities = activities_result.scalars().all()

    # Build interleaved message list
    messages: list[ThreadMessage] = []

    for draft in drafts:
        messages.append(ThreadMessage(
            id=str(draft.id),
            type="draft",
            direction="outbound",
            subject=draft.subject,
            body=draft.body,
            status=draft.status.value,
            ai_model=draft.ai_model,
            ai_reasoning=draft.ai_reasoning,
            gmail_message_id=draft.gmail_message_id,
            created_at=draft.created_at,
            source="crm",
        ))

    for act in activities:
        meta = act.metadata_ or {}
        direction = meta.get("direction", "inbound")
        messages.append(ThreadMessage(
            id=str(act.id),
            type=direction,
            direction=direction,
            subject=act.subject,
            body=act.body,
            from_addr=meta.get("from"),
            gmail_message_id=act.gmail_message_id,
            created_at=act.created_at,
            source=act.source,
        ))

    # Sort chronologically
    messages.sort(key=lambda m: m.created_at)

    has_pending = any(
        m.type == "draft" and m.status == "draft" for m in messages
    )

    return ThreadDetail(
        id=str(thread.id),
        contact_id=str(thread.contact_id),
        company_id=str(thread.company_id) if thread.company_id else None,
        subject=thread.subject,
        status=thread.status.value,
        last_activity_at=thread.last_activity_at,
        created_at=thread.created_at,
        messages=messages,
        contact_name=f"{contact.first_name} {contact.last_name}".strip() if contact else None,
        contact_email=contact.email if contact else None,
        has_pending_draft=has_pending,
    )


# ---------------------------------------------------------------------------
# Update thread status
# ---------------------------------------------------------------------------

class ThreadUpdate(BaseModel):
    status: str  # "active" | "closed"


@router.patch("/{thread_id}")
async def update_thread(
    thread_id: uuid.UUID,
    update: ThreadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update thread status (e.g., close a thread)."""
    result = await db.execute(
        select(EmailThread).where(
            EmailThread.id == thread_id,
            EmailThread.tenant_id == current_user.tenant_id,
        )
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    try:
        thread.status = EmailThreadStatus(update.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {update.status}")

    await db.commit()
    return {"id": str(thread.id), "status": thread.status.value}
