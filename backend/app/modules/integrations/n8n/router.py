"""n8n Integration module — webhook endpoints for leads, activities, deals, and email history.

All endpoints authenticate via API key (x-api-key header) rather than JWT,
since n8n workflows call these endpoints programmatically.
"""

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import api_key_auth
from app.db.session import get_db
from app.models.models import (
    Activity,
    ActivityType,
    ApiKey,
    AuditAction,
    AuditLog,
    Company,
    Contact,
    Deal,
    DraftEmail,
    DraftEmailStatus,
    EnrichmentStatus,
    PipelineStage,
    User,
)
from app.modules.integrations.n8n.schemas import (
    ClayWebhookBody,
    ClayWebhookPayload,
    CompanyWithDraftPayload,
    DraftEmailSentPayload,
    EnrichContactPayload,
    N8nActivityPayload,
    N8nDealUpdatePayload,
    N8nEmailHistoryPayload,
    N8nLeadPayload,
    WebhookResponse,
)

router = APIRouter(prefix="/api/webhooks/n8n", tags=["n8n Webhooks"])


# ---------------------------------------------------------------------------
# Lead ingestion — upserts contact based on email
# ---------------------------------------------------------------------------
@router.post("/lead", response_model=WebhookResponse)
async def receive_lead(
    payload: N8nLeadPayload,
    api_key: ApiKey = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """Receive a lead from n8n. Upserts by email within the tenant."""
    tenant_id = api_key.tenant_id

    # Check for existing contact by email
    existing = None
    if payload.email:
        result = await db.execute(
            select(Contact).where(Contact.tenant_id == tenant_id, Contact.email == payload.email)
        )
        existing = result.scalar_one_or_none()

    # Handle company creation/lookup
    company_id = None
    if payload.company_name:
        result = await db.execute(
            select(Company).where(
                Company.tenant_id == tenant_id,
                Company.name == payload.company_name,
            )
        )
        company = result.scalar_one_or_none()
        if not company:
            company = Company(
                tenant_id=tenant_id,
                name=payload.company_name,
                domain=payload.company_domain,
            )
            db.add(company)
            await db.flush()
        company_id = company.id

    if existing:
        # Update existing contact with new data (merge, don't overwrite blanks)
        if payload.first_name:
            existing.first_name = payload.first_name
        if payload.last_name:
            existing.last_name = payload.last_name
        if payload.phone:
            existing.phone = payload.phone
        if payload.title:
            existing.title = payload.title
        if company_id:
            existing.company_id = company_id
        if payload.tags:
            existing.tags = list(set(existing.tags + payload.tags))
        if payload.custom_fields:
            merged = {**existing.custom_fields, **payload.custom_fields}
            existing.custom_fields = merged
        if payload.notes:
            existing.notes = (existing.notes or "") + "\n---\n" + payload.notes

        db.add(AuditLog(
            tenant_id=tenant_id, entity_type="contact", entity_id=existing.id,
            action=AuditAction.UPDATE, changes={"source": "n8n", "operation": "lead_update"},
        ))

        # Log activity
        db.add(Activity(
            tenant_id=tenant_id, contact_id=existing.id,
            type=ActivityType.SYSTEM, subject="Contact updated via n8n webhook",
            source="n8n", metadata_={"payload_source": payload.source},
        ))

        return WebhookResponse(
            success=True, message="Contact updated",
            data={"contact_id": str(existing.id), "action": "updated"},
        )
    else:
        # Create new contact
        contact = Contact(
            tenant_id=tenant_id,
            first_name=payload.first_name or payload.email.split("@")[0],
            last_name=payload.last_name or "",
            email=payload.email,
            phone=payload.phone,
            title=payload.title,
            company_id=company_id,
            source=payload.source,
            status=payload.status,
            tags=payload.tags,
            custom_fields=payload.custom_fields,
            notes=payload.notes,
        )
        db.add(contact)
        await db.flush()

        db.add(AuditLog(
            tenant_id=tenant_id, entity_type="contact", entity_id=contact.id,
            action=AuditAction.CREATE, changes={"source": "n8n"},
        ))
        db.add(Activity(
            tenant_id=tenant_id, contact_id=contact.id,
            type=ActivityType.SYSTEM, subject="Lead created via n8n webhook",
            source="n8n", metadata_={"payload_source": payload.source},
        ))

        return WebhookResponse(
            success=True, message="Contact created",
            data={"contact_id": str(contact.id), "action": "created"},
        )


# ---------------------------------------------------------------------------
# Activity logging from n8n
# ---------------------------------------------------------------------------
@router.post("/activity", response_model=WebhookResponse)
async def receive_activity(
    payload: N8nActivityPayload,
    api_key: ApiKey = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """Log an activity from n8n (email, call, note, meeting)."""
    tenant_id = api_key.tenant_id

    # Resolve contact by email if no ID provided
    contact_id = payload.contact_id
    if not contact_id and payload.contact_email:
        result = await db.execute(
            select(Contact).where(
                Contact.tenant_id == tenant_id, Contact.email == payload.contact_email,
            )
        )
        contact = result.scalar_one_or_none()
        if contact:
            contact_id = contact.id

    activity = Activity(
        tenant_id=tenant_id,
        contact_id=contact_id,
        deal_id=payload.deal_id,
        type=payload.type,
        subject=payload.subject,
        body=payload.body,
        metadata_=payload.metadata,
        source="n8n",
    )
    db.add(activity)
    await db.flush()

    return WebhookResponse(
        success=True, message="Activity logged",
        data={"activity_id": str(activity.id)},
    )


# ---------------------------------------------------------------------------
# Deal update from n8n
# ---------------------------------------------------------------------------
@router.post("/deal-update", response_model=WebhookResponse)
async def receive_deal_update(
    payload: N8nDealUpdatePayload,
    api_key: ApiKey = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """Update a deal's stage, owner, or value from n8n."""
    tenant_id = api_key.tenant_id

    result = await db.execute(
        select(Deal).where(Deal.id == payload.deal_id, Deal.tenant_id == tenant_id)
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    changes = []

    if payload.stage_name:
        stage_result = await db.execute(
            select(PipelineStage).where(
                PipelineStage.tenant_id == tenant_id, PipelineStage.name == payload.stage_name,
            )
        )
        stage = stage_result.scalar_one_or_none()
        if stage:
            old_stage_result = await db.execute(
                select(PipelineStage).where(PipelineStage.id == deal.stage_id)
            )
            old_stage = old_stage_result.scalar_one()
            deal.stage_id = stage.id
            changes.append(f"Stage: {old_stage.name} → {stage.name}")

    if payload.assigned_to_email:
        user_result = await db.execute(
            select(User).where(User.email == payload.assigned_to_email, User.tenant_id == tenant_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            deal.assigned_to = user.id
            changes.append(f"Assigned to: {user.first_name} {user.last_name}")

    if payload.value is not None:
        deal.value = payload.value
        changes.append(f"Value updated to ${payload.value:,.2f}")

    if payload.probability is not None:
        deal.probability = payload.probability

    if payload.notes:
        deal.notes = (deal.notes or "") + "\n---\n" + payload.notes

    if changes:
        db.add(Activity(
            tenant_id=tenant_id, deal_id=deal.id, contact_id=deal.contact_id,
            type=ActivityType.SYSTEM, subject="Deal updated via n8n: " + "; ".join(changes),
            source="n8n",
        ))

    return WebhookResponse(
        success=True, message="Deal updated", data={"deal_id": str(deal.id), "changes": changes},
    )


# ---------------------------------------------------------------------------
# Email history import from n8n
# ---------------------------------------------------------------------------
@router.post("/email-history", response_model=WebhookResponse)
async def receive_email_history(
    payload: N8nEmailHistoryPayload,
    api_key: ApiKey = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """Import email thread history from n8n and log as activities."""
    tenant_id = api_key.tenant_id

    # Resolve contact
    contact_id = payload.contact_id
    if not contact_id:
        result = await db.execute(
            select(Contact).where(
                Contact.tenant_id == tenant_id, Contact.email == payload.contact_email,
            )
        )
        contact = result.scalar_one_or_none()
        if contact:
            contact_id = contact.id
        else:
            # Auto-create contact from email
            contact = Contact(
                tenant_id=tenant_id,
                first_name=payload.contact_email.split("@")[0],
                last_name="",
                email=payload.contact_email,
                source="n8n-email-import",
                status="new",
            )
            db.add(contact)
            await db.flush()
            contact_id = contact.id

    created_count = 0
    for email_entry in payload.emails:
        activity = Activity(
            tenant_id=tenant_id,
            contact_id=contact_id,
            type=ActivityType.EMAIL,
            subject=email_entry.subject,
            body=email_entry.body,
            source="n8n",
            metadata_={
                "from": email_entry.from_address,
                "to": email_entry.to_addresses,
                "cc": email_entry.cc_addresses,
                "direction": email_entry.direction,
                "thread_id": email_entry.thread_id,
                "message_id": email_entry.message_id,
                "labels": email_entry.labels,
                "original_date": email_entry.date.isoformat(),
            },
        )
        db.add(activity)
        created_count += 1

    await db.flush()

    return WebhookResponse(
        success=True,
        message=f"Imported {created_count} email(s) for contact",
        data={"contact_id": str(contact_id), "emails_imported": created_count},
    )


# ---------------------------------------------------------------------------
# Shared helper — upsert company + contacts from Clay data
# ---------------------------------------------------------------------------
async def _upsert_company_and_contacts(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    body: ClayWebhookBody,
) -> tuple[Company, list[dict]]:
    """Upsert a Company and its Contacts from Clay data.

    Returns (company, created_contacts_list).
    """
    # ---- 1. Upsert Company (match by domain + tenant) --------------------
    company_domain = None
    if body.people:
        company_domain = body.people[0].companyDomain

    company = None
    if company_domain:
        result = await db.execute(
            select(Company).where(
                Company.tenant_id == tenant_id,
                Company.domain == company_domain,
            )
        )
        company = result.scalar_one_or_none()

    if company:
        # Update with latest Clay data
        company.name = body.company
        if body.address:
            company.address = body.address
        if body.phone:
            company.phone = body.phone
        if body.website:
            company.website = body.website
        if body.google_maps_url:
            company.google_maps_url = body.google_maps_url
        if body.rating is not None:
            company.rating = body.rating
        if body.reviews_count is not None:
            company.reviews_count = body.reviews_count
    else:
        company = Company(
            tenant_id=tenant_id,
            name=body.company,
            domain=company_domain,
            address=body.address,
            phone=body.phone,
            website=body.website,
            google_maps_url=body.google_maps_url,
            rating=body.rating,
            reviews_count=body.reviews_count,
        )
        db.add(company)

    await db.flush()

    db.add(AuditLog(
        tenant_id=tenant_id, entity_type="company", entity_id=company.id,
        action=AuditAction.CREATE, changes={"source": "clay"},
    ))

    # ---- 2. Identify the primary contact (the one with personal_emails) --
    primary_full_name = None
    primary_linkedin = None
    primary_email = None
    personal_emails_data = []

    if body.personal_emails:
        primary_full_name = body.personal_emails.full_name
        primary_linkedin = body.personal_emails.linkedin_url
        if body.personal_emails.emails:
            primary_email = body.personal_emails.emails[0].email
            personal_emails_data = [
                e.model_dump() for e in body.personal_emails.emails
            ]

    # ---- 3. Create/upsert contacts for each person ----------------------
    created_contacts: list[dict] = []
    for person in body.people:
        # Determine if this person is the primary contact
        is_primary = False
        if primary_full_name and person.fullName == primary_full_name:
            is_primary = True
        elif primary_linkedin and person.linkedInUrl and \
                primary_linkedin.rstrip("/") == person.linkedInUrl.rstrip("/"):
            is_primary = True

        # Dedup by linkedin_url within tenant
        existing_contact = None
        if person.linkedInUrl:
            result = await db.execute(
                select(Contact).where(
                    Contact.tenant_id == tenant_id,
                    Contact.linkedin_url == person.linkedInUrl,
                )
            )
            existing_contact = result.scalar_one_or_none()

        # Clean up lastName — Clay sometimes appends credentials
        last_name = person.lastName
        if "," in last_name:
            last_name = last_name.split(",")[0].strip()

        if existing_contact:
            # Update existing contact
            existing_contact.first_name = person.firstName
            existing_contact.last_name = last_name
            existing_contact.title = person.jobTitle
            existing_contact.company_id = company.id
            existing_contact.departments = person.departments
            existing_contact.seniorities = person.seniorities
            if is_primary:
                existing_contact.email = primary_email
                existing_contact.is_primary_contact = True
                existing_contact.enrichment_status = EnrichmentStatus.NOT_NEEDED
                existing_contact.personal_emails = personal_emails_data
            created_contacts.append({
                "contact_id": str(existing_contact.id),
                "name": person.fullName,
                "action": "updated",
                "is_primary": is_primary,
            })
        else:
            contact = Contact(
                tenant_id=tenant_id,
                first_name=person.firstName,
                last_name=last_name,
                email=primary_email if is_primary else None,
                title=person.jobTitle,
                linkedin_url=person.linkedInUrl,
                departments=person.departments,
                seniorities=person.seniorities,
                is_primary_contact=is_primary,
                enrichment_status=(
                    EnrichmentStatus.NOT_NEEDED if is_primary
                    else EnrichmentStatus.PENDING
                ),
                personal_emails=personal_emails_data if is_primary else [],
                company_id=company.id,
                source="clay",
                status="new",
            )
            db.add(contact)
            await db.flush()

            db.add(AuditLog(
                tenant_id=tenant_id, entity_type="contact", entity_id=contact.id,
                action=AuditAction.CREATE, changes={"source": "clay"},
            ))

            db.add(Activity(
                tenant_id=tenant_id, contact_id=contact.id,
                type=ActivityType.SYSTEM,
                subject=f"Contact created via Clay webhook — {'primary' if is_primary else 'pending enrichment'}",
                source="clay",
                metadata_={"company": body.company, "job_title": person.jobTitle},
            ))

            created_contacts.append({
                "contact_id": str(contact.id),
                "name": person.fullName,
                "action": "created",
                "is_primary": is_primary,
            })

    return company, created_contacts


# ---------------------------------------------------------------------------
# Clay lead ingestion — company + multiple employees
# ---------------------------------------------------------------------------
@router.post("/clay-lead", response_model=WebhookResponse)
async def receive_clay_lead(
    payload: ClayWebhookPayload,
    api_key: ApiKey = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """Receive a Clay webhook with company data and multiple employees.

    Creates/upserts a Company, then creates Contact records for each person.
    The person matched by personal_emails is marked as the primary contact
    with their email populated. Others are set to enrichment_status=PENDING.
    """
    company, created_contacts = await _upsert_company_and_contacts(
        db, api_key.tenant_id, payload.body,
    )

    return WebhookResponse(
        success=True,
        message=f"Company '{payload.body.company}' processed with {len(created_contacts)} contacts",
        data={
            "company_id": str(company.id),
            "contacts": created_contacts,
        },
    )


# ---------------------------------------------------------------------------
# Contact enrichment — receive enriched email for a pending contact
# ---------------------------------------------------------------------------
@router.post("/enrich-contact", response_model=WebhookResponse)
async def enrich_contact(
    payload: EnrichContactPayload,
    api_key: ApiKey = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """Receive enriched email data for a contact that was pending enrichment.

    Looks up the contact by ID or LinkedIn URL, sets their email, and updates
    enrichment_status to ENRICHED so outreach can target them.
    """
    tenant_id = api_key.tenant_id

    contact = None
    if payload.contact_id:
        result = await db.execute(
            select(Contact).where(
                Contact.id == payload.contact_id,
                Contact.tenant_id == tenant_id,
            )
        )
        contact = result.scalar_one_or_none()

    if not contact and payload.linkedin_url:
        result = await db.execute(
            select(Contact).where(
                Contact.tenant_id == tenant_id,
                Contact.linkedin_url == payload.linkedin_url,
            )
        )
        contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact.email = payload.email
    contact.enrichment_status = EnrichmentStatus.ENRICHED

    db.add(AuditLog(
        tenant_id=tenant_id, entity_type="contact", entity_id=contact.id,
        action=AuditAction.UPDATE,
        changes={"source": payload.enrichment_source, "operation": "email_enrichment"},
    ))

    db.add(Activity(
        tenant_id=tenant_id, contact_id=contact.id,
        type=ActivityType.SYSTEM,
        subject=f"Contact enriched with email via {payload.enrichment_source}",
        source=payload.enrichment_source,
        metadata_={"enriched_email": payload.email},
    ))

    return WebhookResponse(
        success=True,
        message="Contact enriched with email",
        data={
            "contact_id": str(contact.id),
            "email": payload.email,
            "enrichment_status": EnrichmentStatus.ENRICHED.value,
        },
    )


# ---------------------------------------------------------------------------
# Company + Draft Email — combined Clay data + AI-generated email
# ---------------------------------------------------------------------------
def _parse_ai_draft(ai_output: list) -> dict:
    """Extract subject, body, reasoning, model, and website snapshot from AI output.

    Scans the AI output array for the last entry's message-type blocks
    to get the email content, reasoning blocks for chain-of-thought,
    and tool_call output for the website snapshot.
    """
    subject = ""
    body = ""
    reasoning_parts: list[str] = []
    model_id = None
    website_snapshot = None

    for block in ai_output:
        if block.type == "reasoning" and block.content:
            reasoning_parts.append(block.content.strip())
        elif block.type == "message" and block.content and block.content.strip():
            raw = block.content.strip()
            # Try to extract a Subject: line from the email
            subject_match = re.search(r"\*\*Subject:\*\*\s*(.+?)(?:\n|$)", raw)
            if subject_match:
                subject = subject_match.group(1).strip()
            body = raw
        elif block.type == "tool_call" and block.output:
            website_snapshot = block.output
    return {
        "subject": subject,
        "body": body,
        "reasoning": "\n\n---\n\n".join(reasoning_parts) if reasoning_parts else None,
        "model_id": model_id,
        "website_snapshot": website_snapshot,
    }


@router.post("/company-with-draft", response_model=WebhookResponse)
async def receive_company_with_draft(
    payload: CompanyWithDraftPayload,
    api_key: ApiKey = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """Receive Clay company data + AI-generated draft email in a single call.

    1. Upserts the Company and all Contacts (same as /clay-lead).
    2. Parses the AI output to extract the draft email subject, body,
       reasoning, and website snapshot.
    3. Creates a DraftEmail record linked to the company and primary contact
       with status=DRAFT for user review.
    """
    tenant_id = api_key.tenant_id

    # ---- 1. Upsert company + contacts -----------------------------------
    company, created_contacts = await _upsert_company_and_contacts(
        db, tenant_id, payload.body,
    )

    # ---- 2. Parse AI output to extract the draft email ------------------
    draft_data = _parse_ai_draft(payload.ai_output)

    if not draft_data["body"]:
        return WebhookResponse(
            success=True,
            message=f"Company '{payload.body.company}' processed (no draft email in AI output)",
            data={
                "company_id": str(company.id),
                "contacts": created_contacts,
                "draft_email_id": None,
            },
        )

    # ---- 3. Resolve primary contact for the draft email -----------------
    primary_contact_id = None
    for c in created_contacts:
        if c.get("is_primary"):
            primary_contact_id = c["contact_id"]
            break

    # Fallback: grab the first contact if no primary was identified
    if not primary_contact_id and created_contacts:
        primary_contact_id = created_contacts[0]["contact_id"]

    if not primary_contact_id:
        raise HTTPException(
            status_code=422,
            detail="No contacts found to associate the draft email with",
        )

    # ---- 4. Create DraftEmail record ------------------------------------
    draft_email = DraftEmail(
        tenant_id=tenant_id,
        company_id=company.id,
        contact_id=uuid.UUID(primary_contact_id),
        subject=draft_data["subject"] or f"Draft email for {payload.body.company}",
        body=draft_data["body"],
        status=DraftEmailStatus.DRAFT,
        ai_model=draft_data["model_id"],
        ai_reasoning=draft_data["reasoning"],
        website_snapshot=draft_data["website_snapshot"],
    )
    db.add(draft_email)
    await db.flush()

    db.add(AuditLog(
        tenant_id=tenant_id, entity_type="draft_email", entity_id=draft_email.id,
        action=AuditAction.CREATE,
        changes={"source": "n8n", "ai_model": draft_data["model_id"]},
    ))

    db.add(Activity(
        tenant_id=tenant_id,
        contact_id=uuid.UUID(primary_contact_id),
        type=ActivityType.SYSTEM,
        subject=f"AI draft email generated for {payload.body.company}",
        source="n8n",
        metadata_={
            "draft_email_id": str(draft_email.id),
            "ai_model": draft_data["model_id"],
            "email_subject": draft_data["subject"],
        },
    ))

    return WebhookResponse(
        success=True,
        message=f"Company '{payload.body.company}' processed with {len(created_contacts)} contacts and draft email",
        data={
            "company_id": str(company.id),
            "contacts": created_contacts,
            "draft_email_id": str(draft_email.id),
            "draft_email_status": DraftEmailStatus.DRAFT.value,
        },
    )


# ---------------------------------------------------------------------------
# n8n callback — mark draft email as SENT after n8n sends it
# ---------------------------------------------------------------------------
@router.post("/draft-email-sent", response_model=WebhookResponse)
async def mark_draft_email_sent(
    payload: DraftEmailSentPayload,
    api_key: ApiKey = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """Called by n8n after it successfully sends a draft email.

    Marks the DraftEmail status as SENT so the CRM reflects the send.
    Payload: { "draft_email_id": "uuid" }
    """
    from datetime import datetime, timezone

    result = await db.execute(
        select(DraftEmail).where(
            DraftEmail.id == payload.draft_email_id,
            DraftEmail.tenant_id == api_key.tenant_id,
        )
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft email not found")

    draft.status = DraftEmailStatus.SENT
    draft.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return WebhookResponse(
        success=True,
        message="Draft email marked as sent",
        data={"draft_email_id": str(draft.id), "status": "sent"},
    )
