"""Contacts module — CRUD with audit trail, search, dedup, and company management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.models import AuditAction, AuditLog, Company, Contact, User, UserRole
from app.modules.contacts.schemas import (
    CompanyCreate,
    CompanyResponse,
    CompanyUpdate,
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)

router = APIRouter(prefix="/api/contacts", tags=["Contacts"])
company_router = APIRouter(prefix="/api/companies", tags=["Companies"])


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------
async def _audit(db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID | None,
                 entity_type: str, entity_id: uuid.UUID, action: AuditAction, changes: dict):
    db.add(AuditLog(
        tenant_id=tenant_id, user_id=user_id,
        entity_type=entity_type, entity_id=entity_id,
        action=action, changes=changes,
    ))


# ---------------------------------------------------------------------------
# Contact CRUD
# ---------------------------------------------------------------------------
@router.get("", response_model=ContactListResponse)
async def list_contacts(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    search: str | None = Query(None, max_length=200),
    status_filter: str | None = Query(None, alias="status", max_length=50),
    source: str | None = Query(None, max_length=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List contacts with pagination, search, and filters."""
    query = select(Contact).where(Contact.tenant_id == current_user.tenant_id)
    count_query = select(func.count(Contact.id)).where(Contact.tenant_id == current_user.tenant_id)

    if search:
        like = f"%{search}%"
        search_filter = or_(
            Contact.first_name.ilike(like),
            Contact.last_name.ilike(like),
            Contact.email.ilike(like),
            Contact.phone.ilike(like),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if status_filter:
        query = query.where(Contact.status == status_filter)
        count_query = count_query.where(Contact.status == status_filter)

    if source:
        query = query.where(Contact.source == source)
        count_query = count_query.where(Contact.source == source)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Contact.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)

    return ContactListResponse(
        items=result.scalars().all(),
        total=total, page=page, per_page=per_page,
    )


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single contact by ID."""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.tenant_id == current_user.tenant_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    req: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new contact with audit trail."""
    contact = Contact(tenant_id=current_user.tenant_id, **req.model_dump())
    db.add(contact)
    await db.flush()

    await _audit(db, current_user.tenant_id, current_user.id, "contact", contact.id, AuditAction.CREATE, req.model_dump())
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: uuid.UUID,
    req: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a contact. Only provided fields are changed."""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.tenant_id == current_user.tenant_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    changes = {}
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old_val = getattr(contact, field)
        if old_val != value:
            changes[field] = {"old": str(old_val), "new": str(value)}
            setattr(contact, field, value)

    if changes:
        await _audit(db, current_user.tenant_id, current_user.id, "contact", contact.id, AuditAction.UPDATE, changes)

    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a contact (admin/manager only)."""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.tenant_id == current_user.tenant_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    await _audit(db, current_user.tenant_id, current_user.id, "contact", contact.id, AuditAction.DELETE, {})
    await db.delete(contact)


@router.get("/search/dedup", response_model=list[ContactResponse])
async def dedup_search(
    email: str | None = Query(None),
    phone: str | None = Query(None),
    first_name: str | None = Query(None),
    last_name: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search for potential duplicate contacts by email, phone, or name."""
    filters = [Contact.tenant_id == current_user.tenant_id]
    conditions = []
    if email:
        conditions.append(Contact.email == email)
    if phone:
        conditions.append(Contact.phone == phone)
    if first_name and last_name:
        conditions.append((Contact.first_name.ilike(first_name)) & (Contact.last_name.ilike(last_name)))

    if not conditions:
        raise HTTPException(status_code=400, detail="Provide at least one search parameter")

    query = select(Contact).where(*filters, or_(*conditions)).limit(20)
    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Company CRUD
# ---------------------------------------------------------------------------
@company_router.get("", response_model=list[CompanyResponse])
async def list_companies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Company).where(Company.tenant_id == current_user.tenant_id).order_by(Company.name)
    )
    return result.scalars().all()


@company_router.get("/{company_id}/contacts", response_model=list[ContactResponse])
async def list_company_contacts(
    company_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all contacts that belong to a company."""
    result = await db.execute(
        select(Contact)
        .where(Contact.company_id == company_id, Contact.tenant_id == current_user.tenant_id)
        .order_by(Contact.is_primary_contact.desc(), Contact.created_at.desc())
    )
    return result.scalars().all()


@company_router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    req: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = Company(tenant_id=current_user.tenant_id, **req.model_dump())
    db.add(company)
    await db.flush()
    await _audit(db, current_user.tenant_id, current_user.id, "company", company.id, AuditAction.CREATE, req.model_dump())
    return company


@company_router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: uuid.UUID,
    req: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Company).where(Company.id == company_id, Company.tenant_id == current_user.tenant_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    return company


@company_router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Company).where(Company.id == company_id, Company.tenant_id == current_user.tenant_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    await db.delete(company)
