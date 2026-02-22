"""Reporting module — pipeline stats, activity summaries, forecast, CSV export."""

import csv
import io
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.models import Activity, Contact, Deal, PipelineStage, User

router = APIRouter(prefix="/api/reports", tags=["Reporting"])


@router.get("/pipeline")
async def pipeline_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pipeline report with stage-by-stage breakdown."""
    stages_result = await db.execute(
        select(PipelineStage)
        .where(PipelineStage.tenant_id == current_user.tenant_id)
        .order_by(PipelineStage.order)
    )
    stages = stages_result.scalars().all()

    deals_result = await db.execute(
        select(Deal).where(Deal.tenant_id == current_user.tenant_id)
    )
    all_deals = deals_result.scalars().all()

    open_deals = [d for d in all_deals if d.closed_at is None]
    won_deals = [d for d in all_deals if d.closed_at and any(s.is_won and s.id == d.stage_id for s in stages)]
    lost_deals = [d for d in all_deals if d.closed_at and any(s.is_lost and s.id == d.stage_id for s in stages)]

    stage_breakdown = []
    for stage in stages:
        stage_deals = [d for d in open_deals if d.stage_id == stage.id]
        stage_breakdown.append({
            "stage": stage.name,
            "color": stage.color,
            "count": len(stage_deals),
            "value": sum(d.value for d in stage_deals),
            "weighted_value": sum(d.value * d.probability / 100 for d in stage_deals),
        })

    return {
        "total_open_deals": len(open_deals),
        "total_open_value": sum(d.value for d in open_deals),
        "weighted_pipeline": sum(d.value * d.probability / 100 for d in open_deals),
        "won_count": len(won_deals),
        "won_value": sum(d.value for d in won_deals),
        "lost_count": len(lost_deals),
        "win_rate": len(won_deals) / (len(won_deals) + len(lost_deals)) * 100 if (won_deals or lost_deals) else 0,
        "stages": stage_breakdown,
    }


@router.get("/forecast")
async def forecast_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Probability-weighted revenue forecast."""
    deals_result = await db.execute(
        select(Deal).where(Deal.tenant_id == current_user.tenant_id, Deal.closed_at.is_(None))
    )
    deals = deals_result.scalars().all()

    total_value = sum(d.value for d in deals)
    weighted = sum(d.value * d.probability / 100 for d in deals)
    high_confidence = sum(d.value for d in deals if d.probability >= 75)
    medium_confidence = sum(d.value for d in deals if 25 <= d.probability < 75)
    low_confidence = sum(d.value for d in deals if d.probability < 25)

    return {
        "total_pipeline_value": total_value,
        "weighted_forecast": weighted,
        "high_confidence_value": high_confidence,
        "medium_confidence_value": medium_confidence,
        "low_confidence_value": low_confidence,
        "deal_count": len(deals),
    }


@router.get("/activity-summary")
async def activity_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Activity summary for the past N days."""
    from datetime import datetime, timedelta, timezone

    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(Activity)
        .where(Activity.tenant_id == current_user.tenant_id, Activity.created_at >= since)
    )
    activities = result.scalars().all()

    by_type = {}
    for a in activities:
        key = a.type.value
        by_type[key] = by_type.get(key, 0) + 1

    by_source = {}
    for a in activities:
        by_source[a.source] = by_source.get(a.source, 0) + 1

    return {
        "period_days": days,
        "total_activities": len(activities),
        "by_type": by_type,
        "by_source": by_source,
    }


@router.get("/contacts/export")
async def export_contacts_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export all contacts as CSV."""
    result = await db.execute(
        select(Contact).where(Contact.tenant_id == current_user.tenant_id).order_by(Contact.created_at)
    )
    contacts = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "First Name", "Last Name", "Email", "Phone", "Title", "Source", "Status", "Tags", "Created"])

    for c in contacts:
        writer.writerow([
            str(c.id), c.first_name, c.last_name, c.email or "", c.phone or "",
            c.title or "", c.source or "", c.status,
            ";".join(c.tags) if c.tags else "", c.created_at.isoformat(),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts_export.csv"},
    )
