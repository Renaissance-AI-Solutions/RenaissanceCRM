"""Deals module — CRUD, stage transitions, pipeline stats, forecasting."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.models import (
    Activity,
    ActivityType,
    AuditAction,
    AuditLog,
    Deal,
    PipelineStage,
    User,
    UserRole,
)
from app.modules.deals.schemas import (
    DealCreate,
    DealListResponse,
    DealResponse,
    DealUpdate,
    PipelineStats,
    StageResponse,
)

router = APIRouter(prefix="/api/deals", tags=["Deals"])
stages_router = APIRouter(prefix="/api/pipeline-stages", tags=["Pipeline Stages"])


# ---------------------------------------------------------------------------
# Deal CRUD
# ---------------------------------------------------------------------------
@router.get("", response_model=DealListResponse)
async def list_deals(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    stage_id: uuid.UUID | None = None,
    assigned_to: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List deals with optional stage and assignee filters."""
    query = select(Deal).where(Deal.tenant_id == current_user.tenant_id)
    count_q = select(func.count(Deal.id)).where(Deal.tenant_id == current_user.tenant_id)

    if stage_id:
        query = query.where(Deal.stage_id == stage_id)
        count_q = count_q.where(Deal.stage_id == stage_id)
    if assigned_to:
        query = query.where(Deal.assigned_to == assigned_to)
        count_q = count_q.where(Deal.assigned_to == assigned_to)

    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(Deal.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)

    return DealListResponse(items=result.scalars().all(), total=total, page=page, per_page=per_page)


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Deal).where(Deal.id == deal_id, Deal.tenant_id == current_user.tenant_id)
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.post("", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    req: DealCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new deal."""
    deal = Deal(tenant_id=current_user.tenant_id, **req.model_dump())
    db.add(deal)
    await db.flush()

    # Auto-log creation activity
    db.add(Activity(
        tenant_id=current_user.tenant_id, deal_id=deal.id,
        contact_id=deal.contact_id, user_id=current_user.id,
        type=ActivityType.SYSTEM, subject=f"Deal created: {deal.title}",
        source="system",
    ))

    db.add(AuditLog(
        tenant_id=current_user.tenant_id, user_id=current_user.id,
        entity_type="deal", entity_id=deal.id,
        action=AuditAction.CREATE, changes=req.model_dump(mode="json"),
    ))
    return deal


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: uuid.UUID,
    req: DealUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a deal. Logs stage transitions as activities."""
    result = await db.execute(
        select(Deal).where(Deal.id == deal_id, Deal.tenant_id == current_user.tenant_id)
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    update_data = req.model_dump(exclude_unset=True)
    changes = {}

    # Detect stage transition
    if "stage_id" in update_data and update_data["stage_id"] != deal.stage_id:
        old_stage = await db.execute(select(PipelineStage).where(PipelineStage.id == deal.stage_id))
        new_stage = await db.execute(select(PipelineStage).where(PipelineStage.id == update_data["stage_id"]))
        old_name = old_stage.scalar_one().name if old_stage else "Unknown"
        new_obj = new_stage.scalar_one_or_none()
        if not new_obj:
            raise HTTPException(status_code=400, detail="Invalid stage ID")
        new_name = new_obj.name

        db.add(Activity(
            tenant_id=current_user.tenant_id, deal_id=deal.id,
            contact_id=deal.contact_id, user_id=current_user.id,
            type=ActivityType.SYSTEM, subject=f"Deal moved from {old_name} → {new_name}",
            source="system",
        ))

        # Auto-close if moved to won/lost stage
        if new_obj.is_won or new_obj.is_lost:
            deal.closed_at = datetime.now(timezone.utc)

    for field, value in update_data.items():
        old_val = getattr(deal, field)
        if old_val != value:
            changes[field] = {"old": str(old_val), "new": str(value)}
            setattr(deal, field, value)

    if changes:
        db.add(AuditLog(
            tenant_id=current_user.tenant_id, user_id=current_user.id,
            entity_type="deal", entity_id=deal.id,
            action=AuditAction.UPDATE, changes=changes,
        ))
    return deal


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Deal).where(Deal.id == deal_id, Deal.tenant_id == current_user.tenant_id)
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    await db.delete(deal)


# ---------------------------------------------------------------------------
# Pipeline stats
# ---------------------------------------------------------------------------
@router.get("/stats/pipeline", response_model=PipelineStats)
async def pipeline_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pipeline statistics with per-stage breakdown."""
    deals_result = await db.execute(
        select(Deal).where(Deal.tenant_id == current_user.tenant_id, Deal.closed_at.is_(None))
    )
    open_deals = deals_result.scalars().all()

    stages_result = await db.execute(
        select(PipelineStage)
        .where(PipelineStage.tenant_id == current_user.tenant_id)
        .order_by(PipelineStage.order)
    )
    stages = stages_result.scalars().all()

    stage_stats = []
    for stage in stages:
        stage_deals = [d for d in open_deals if d.stage_id == stage.id]
        stage_stats.append({
            "id": str(stage.id),
            "name": stage.name,
            "color": stage.color,
            "order": stage.order,
            "deal_count": len(stage_deals),
            "total_value": sum(d.value for d in stage_deals),
            "weighted_value": sum(d.value * d.probability / 100 for d in stage_deals),
        })

    total_value = sum(d.value for d in open_deals)
    weighted_value = sum(d.value * d.probability / 100 for d in open_deals)
    avg_prob = sum(d.probability for d in open_deals) / len(open_deals) if open_deals else 0

    return PipelineStats(
        total_deals=len(open_deals),
        total_value=total_value,
        weighted_value=weighted_value,
        avg_probability=avg_prob,
        stages=stage_stats,
    )


# ---------------------------------------------------------------------------
# Pipeline stages CRUD
# ---------------------------------------------------------------------------
@stages_router.get("", response_model=list[StageResponse])
async def list_stages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PipelineStage)
        .where(PipelineStage.tenant_id == current_user.tenant_id)
        .order_by(PipelineStage.order)
    )
    return result.scalars().all()
