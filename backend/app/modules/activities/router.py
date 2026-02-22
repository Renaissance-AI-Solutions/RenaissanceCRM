"""Activities module — CRUD, timeline, and filtering."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.models import Activity, ActivityType, User
from app.modules.activities.schemas import (
    ActivityCreate,
    ActivityListResponse,
    ActivityResponse,
    ActivityUpdate,
)

router = APIRouter(prefix="/api/activities", tags=["Activities"])


@router.get("", response_model=ActivityListResponse)
async def list_activities(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    contact_id: uuid.UUID | None = None,
    deal_id: uuid.UUID | None = None,
    type: ActivityType | None = None,
    source: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List activities with filters."""
    query = select(Activity).where(Activity.tenant_id == current_user.tenant_id)
    count_q = select(func.count(Activity.id)).where(Activity.tenant_id == current_user.tenant_id)

    if contact_id:
        query = query.where(Activity.contact_id == contact_id)
        count_q = count_q.where(Activity.contact_id == contact_id)
    if deal_id:
        query = query.where(Activity.deal_id == deal_id)
        count_q = count_q.where(Activity.deal_id == deal_id)
    if type:
        query = query.where(Activity.type == type)
        count_q = count_q.where(Activity.type == type)
    if source:
        query = query.where(Activity.source == source)
        count_q = count_q.where(Activity.source == source)

    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(Activity.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)

    return ActivityListResponse(items=result.scalars().all(), total=total, page=page, per_page=per_page)


@router.get("/timeline/{contact_id}", response_model=list[ActivityResponse])
async def contact_timeline(
    contact_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get unified timeline for a contact (all activity types)."""
    result = await db.execute(
        select(Activity)
        .where(Activity.tenant_id == current_user.tenant_id, Activity.contact_id == contact_id)
        .order_by(Activity.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    req: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new activity."""
    activity = Activity(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        type=req.type,
        subject=req.subject,
        body=req.body,
        contact_id=req.contact_id,
        deal_id=req.deal_id,
        metadata_=req.metadata_,
        source=req.source,
        is_pinned=req.is_pinned,
    )
    db.add(activity)
    await db.flush()
    return activity


@router.patch("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: uuid.UUID,
    req: ActivityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Activity).where(Activity.id == activity_id, Activity.tenant_id == current_user.tenant_id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(activity, field, value)
    return activity


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Activity).where(Activity.id == activity_id, Activity.tenant_id == current_user.tenant_id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    await db.delete(activity)
