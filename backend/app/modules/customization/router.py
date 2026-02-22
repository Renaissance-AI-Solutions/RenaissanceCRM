"""Customization module — custom fields, pipeline stages, tenant settings, webhook configs."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.models import (
    CustomFieldDefinition,
    CustomFieldType,
    PipelineStage,
    Tenant,
    User,
    UserRole,
    WebhookConfig,
)

router = APIRouter(prefix="/api/customization", tags=["Customization"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CustomFieldCreate(BaseModel):
    entity_type: str = Field(pattern="^(contact|company|deal)$")
    field_name: str = Field(min_length=1, max_length=100)
    field_label: str = Field(min_length=1, max_length=150)
    field_type: CustomFieldType
    options: dict = {}
    is_required: bool = False
    sort_order: int = 0


class CustomFieldResponse(BaseModel):
    id: uuid.UUID
    entity_type: str
    field_name: str
    field_label: str
    field_type: CustomFieldType
    options: dict
    is_required: bool
    is_visible: bool
    sort_order: int
    model_config = {"from_attributes": True}


class PipelineStageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    order: int = 0
    color: str = Field(default="#6366f1", max_length=7)
    is_won: bool = False
    is_lost: bool = False


class PipelineStageUpdate(BaseModel):
    name: str | None = None
    order: int | None = None
    color: str | None = None
    is_won: bool | None = None
    is_lost: bool | None = None


class TenantSettingsUpdate(BaseModel):
    settings: dict


class WebhookConfigCreate(BaseModel):
    event: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=500)
    secret: str | None = None
    headers: dict = {}


class WebhookConfigResponse(BaseModel):
    id: uuid.UUID
    event: str
    url: str
    is_active: bool
    headers: dict
    created_at: str | None = None
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Custom Field Definitions
# ---------------------------------------------------------------------------
@router.get("/fields", response_model=list[CustomFieldResponse])
async def list_custom_fields(
    entity_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(CustomFieldDefinition).where(
        CustomFieldDefinition.tenant_id == current_user.tenant_id
    )
    if entity_type:
        query = query.where(CustomFieldDefinition.entity_type == entity_type)
    query = query.order_by(CustomFieldDefinition.sort_order)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/fields", response_model=CustomFieldResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_field(
    req: CustomFieldCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    field = CustomFieldDefinition(tenant_id=current_user.tenant_id, **req.model_dump())
    db.add(field)
    await db.flush()
    return field


@router.delete("/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_field(
    field_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CustomFieldDefinition).where(
            CustomFieldDefinition.id == field_id,
            CustomFieldDefinition.tenant_id == current_user.tenant_id,
        )
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail="Custom field not found")
    await db.delete(field)


# ---------------------------------------------------------------------------
# Pipeline Stages
# ---------------------------------------------------------------------------
@router.post("/stages", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_stage(
    req: PipelineStageCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    stage = PipelineStage(tenant_id=current_user.tenant_id, **req.model_dump())
    db.add(stage)
    await db.flush()
    return {"id": str(stage.id), "name": stage.name, "order": stage.order, "color": stage.color}


@router.patch("/stages/{stage_id}", response_model=dict)
async def update_stage(
    stage_id: uuid.UUID,
    req: PipelineStageUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PipelineStage).where(
            PipelineStage.id == stage_id, PipelineStage.tenant_id == current_user.tenant_id,
        )
    )
    stage = result.scalar_one_or_none()
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(stage, field, value)
    return {"id": str(stage.id), "name": stage.name, "order": stage.order, "color": stage.color}


# ---------------------------------------------------------------------------
# Tenant Settings
# ---------------------------------------------------------------------------
@router.get("/settings")
async def get_tenant_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one()
    return {"tenant_id": str(tenant.id), "name": tenant.name, "slug": tenant.slug, "settings": tenant.settings}


@router.patch("/settings")
async def update_tenant_settings(
    req: TenantSettingsUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one()
    merged = {**tenant.settings, **req.settings}
    tenant.settings = merged
    return {"tenant_id": str(tenant.id), "settings": tenant.settings}


# ---------------------------------------------------------------------------
# Webhook Configs
# ---------------------------------------------------------------------------
@router.get("/webhooks", response_model=list[WebhookConfigResponse])
async def list_webhooks(
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookConfig).where(WebhookConfig.tenant_id == current_user.tenant_id)
    )
    return result.scalars().all()


@router.post("/webhooks", response_model=WebhookConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    req: WebhookConfigCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    webhook = WebhookConfig(tenant_id=current_user.tenant_id, **req.model_dump())
    db.add(webhook)
    await db.flush()
    return webhook


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookConfig).where(
            WebhookConfig.id == webhook_id, WebhookConfig.tenant_id == current_user.tenant_id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook config not found")
    await db.delete(webhook)
