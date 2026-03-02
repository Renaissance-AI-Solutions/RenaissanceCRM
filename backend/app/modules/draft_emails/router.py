"""Draft Emails module — list, update status/content, delete, send, and AI rewrite."""

import re
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.models import Company, Contact, DraftEmail, DraftEmailStatus, Tenant, User

router = APIRouter(prefix="/api/draft-emails", tags=["Draft Emails"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class DraftEmailUpdate(BaseModel):
    subject: str | None = None
    body: str | None = None
    status: DraftEmailStatus | None = None


class AiRewriteRequest(BaseModel):
    instruction: str
    model: str | None = None  # overrides tenant default if provided


# ---------------------------------------------------------------------------
# Helper: fetch LMStudio config from tenant settings
# ---------------------------------------------------------------------------
async def _get_lmstudio_config(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    settings = (tenant.settings or {}) if tenant else {}
    return {
        "url": settings.get("lmstudio_url", "").rstrip("/"),
        "api_key": settings.get("lmstudio_api_key", ""),
        "model": settings.get("lmstudio_model", "qwen/qwen3-14b"),
    }


# ---------------------------------------------------------------------------
# List draft emails (optionally filtered by contact_id and/or status)
# ---------------------------------------------------------------------------
@router.get("")
async def list_draft_emails(
    status_filter: str | None = Query(None, alias="status"),
    contact_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(DraftEmail, Company, Contact)
        .join(Company, DraftEmail.company_id == Company.id)
        .join(Contact, DraftEmail.contact_id == Contact.id)
        .where(DraftEmail.tenant_id == current_user.tenant_id)
    )
    if status_filter:
        try:
            query = query.where(DraftEmail.status == DraftEmailStatus(status_filter))
        except ValueError:
            pass
    if contact_id:
        query = query.where(DraftEmail.contact_id == contact_id)

    query = query.order_by(DraftEmail.created_at.desc())
    result = await db.execute(query)
    rows = result.all()

    items = []
    for draft, company, contact in rows:
        items.append({
            "id": str(draft.id),
            "company_id": str(draft.company_id),
            "contact_id": str(draft.contact_id),
            "subject": draft.subject,
            "body": draft.body,
            "status": draft.status.value,
            "ai_model": draft.ai_model,
            "ai_reasoning": draft.ai_reasoning,
            "website_snapshot": draft.website_snapshot,
            "created_at": draft.created_at.isoformat(),
            "updated_at": draft.updated_at.isoformat(),
            "company_name": company.name if company else None,
            "contact_name": f"{contact.first_name} {contact.last_name}".strip() if contact else None,
            "contact_email": contact.email if contact else None,
        })

    return {"items": items, "total": len(items)}


# ---------------------------------------------------------------------------
# Update draft email (edit subject/body, change status)
# ---------------------------------------------------------------------------
@router.patch("/{draft_id}")
async def update_draft_email(
    draft_id: uuid.UUID,
    data: DraftEmailUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DraftEmail).where(
            DraftEmail.id == draft_id,
            DraftEmail.tenant_id == current_user.tenant_id,
        )
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft email not found")

    if data.subject is not None:
        draft.subject = data.subject
    if data.body is not None:
        draft.body = data.body
    if data.status is not None:
        draft.status = data.status

    draft.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(draft)

    return {
        "id": str(draft.id),
        "subject": draft.subject,
        "body": draft.body,
        "status": draft.status.value,
        "updated_at": draft.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# AI Rewrite — call LMStudio to revise the email, return without saving
# ---------------------------------------------------------------------------
@router.post("/{draft_id}/ai-rewrite")
async def ai_rewrite_draft(
    draft_id: uuid.UUID,
    req: AiRewriteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Use LMStudio (via Tailscale) to rewrite the draft email.

    Returns { subject, body } with the AI-revised version.
    Does NOT save automatically — the frontend shows it for review first.
    """
    # Fetch the draft
    result = await db.execute(
        select(DraftEmail).where(
            DraftEmail.id == draft_id,
            DraftEmail.tenant_id == current_user.tenant_id,
        )
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft email not found")

    # Get LMStudio config
    cfg = await _get_lmstudio_config(db, current_user.tenant_id)
    if not cfg["url"]:
        raise HTTPException(
            status_code=400,
            detail="LMStudio URL not configured. Add it in Settings → General → AI Integration.",
        )

    model = req.model or cfg["model"]

    # Build the prompt
    system_prompt = (
        "You are an expert B2B sales email writer. "
        "When given an email and an instruction, rewrite the email following the instruction. "
        "Keep it concise, professional, and personalized. "
        "Return ONLY the rewritten email — start with 'Subject: ' on the first line, "
        "then a blank line, then the email body. "
        "Do not include any explanation, preamble, or commentary outside the email itself."
    )

    user_message = (
        f"Here is the original email:\n\n"
        f"Subject: {draft.subject}\n\n"
        f"{draft.body}\n\n"
        f"---\n\n"
        f"Instruction: {req.instruction}\n\n"
        f"Rewrite the email following the instruction:"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
        "max_tokens": 4096,  # Extra room for thinking models that emit <think>...</think> first
        "stream": False,
    }

    headers = {"Content-Type": "application/json"}
    if cfg["api_key"]:
        headers["Authorization"] = f"Bearer {cfg['api_key']}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{cfg['url']}/v1/chat/completions",
                json=payload,
                headers=headers,
            )
        resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LMStudio timed out. Is the model loaded and your machine reachable via Tailscale?")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"LMStudio returned {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not reach LMStudio: {str(e)}")

    raw = data["choices"][0]["message"]["content"].strip()

    # Strip <think>...</think> blocks emitted by reasoning/thinking models (e.g. qwen3, deepseek-r1)
    # Strategy 1: complete <think>...</think> blocks
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    # Strategy 2: if <think> is still present (truncated response), take everything after </think>
    if "<think>" in raw:
        parts = raw.split("</think>")
        if len(parts) > 1:
            raw = parts[-1].strip()
        else:
            # Incomplete think block — take everything after the last > char in what looks like a tag
            raw = re.sub(r"<think>.*", "", raw, flags=re.DOTALL).strip()
            if not raw:
                raise HTTPException(status_code=502, detail="Model response was all reasoning tokens. Try a non-thinking model.")

    # Parse "Subject: ..." from the first line, rest is the body
    subject = draft.subject
    body = raw

    # Try to extract Subject: line
    subject_match = re.match(r"Subject:\s*(.+?)(?:\n|$)", raw, re.IGNORECASE)
    if subject_match:
        subject = subject_match.group(1).strip()
        # Body is everything after the subject line + blank line
        after_subject = raw[subject_match.end():].lstrip("\n")
        if after_subject:
            body = after_subject

    return {
        "subject": subject,
        "body": body,
        "model_used": model,
    }


# ---------------------------------------------------------------------------
# Approve & Send — mark APPROVED and fire n8n send webhook
# ---------------------------------------------------------------------------
@router.post("/{draft_id}/send")
async def send_draft_email(
    draft_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a draft email and trigger n8n to send it."""
    row_result = await db.execute(
        select(DraftEmail, Company, Contact)
        .join(Company, DraftEmail.company_id == Company.id)
        .join(Contact, DraftEmail.contact_id == Contact.id)
        .where(DraftEmail.id == draft_id, DraftEmail.tenant_id == current_user.tenant_id)
    )
    row = row_result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Draft email not found")
    draft, company, contact = row

    # Get n8n send webhook URL from tenant settings
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    webhook_url = (tenant.settings or {}).get("n8n_email_send_webhook") if tenant else None

    webhook_status = None
    webhook_ok = False

    if webhook_url:
        payload = {
            "draft_email_id": str(draft.id),
            "contact_id": str(contact.id),
            "contact_name": f"{contact.first_name} {contact.last_name}".strip(),
            "contact_email": contact.email,
            "company_name": company.name,
            "subject": draft.subject,
            "body": draft.body,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(webhook_url, json=payload)
            webhook_status = resp.status_code
            webhook_ok = resp.is_success
        except Exception:
            webhook_status = None
            webhook_ok = False

    draft.status = DraftEmailStatus.APPROVED
    draft.updated_at = datetime.now(timezone.utc)
    await db.commit()

    if webhook_ok:
        message = "Email approved and n8n notified successfully."
    elif webhook_url:
        message = f"Email approved but webhook call failed (HTTP {webhook_status}). Check your n8n URL in Settings."
    else:
        message = "Email approved. No send webhook configured — add one in Settings → General → n8n Integrations."

    return {
        "success": True,
        "draft_email_id": str(draft.id),
        "status": "approved",
        "webhook_fired": webhook_url is not None,
        "webhook_status_code": webhook_status,
        "webhook_ok": webhook_ok,
        "message": message,
    }


# ---------------------------------------------------------------------------
# Delete draft email
# ---------------------------------------------------------------------------
@router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft_email(
    draft_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DraftEmail).where(
            DraftEmail.id == draft_id,
            DraftEmail.tenant_id == current_user.tenant_id,
        )
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft email not found")

    await db.delete(draft)
    await db.commit()
