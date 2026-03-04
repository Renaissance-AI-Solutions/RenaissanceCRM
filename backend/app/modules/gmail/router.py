"""Gmail integration router — test connection and status endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.models import Tenant, User
from app.modules.gmail.service import _build_credentials, _refresh_if_needed

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gmail", tags=["Gmail"])


class GmailStatus(BaseModel):
    connected: bool
    email: str | None = None
    last_polled_at: str | None = None
    poll_enabled: bool = False
    error: str | None = None


@router.get("/status", response_model=GmailStatus)
async def gmail_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return current Gmail connection status for the tenant."""
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    s = tenant.settings or {}
    creds = _build_credentials(s)
    if not creds:
        return GmailStatus(connected=False, poll_enabled=bool(s.get("gmail_poll_enabled")))

    try:
        creds = _refresh_if_needed(creds)
        from googleapiclient.discovery import build
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        profile = service.users().getProfile(userId="me").execute()
        email = profile.get("emailAddress", "")

        # Persist refreshed access token
        tenant.settings = {**s, "gmail_access_token": creds.token}
        await db.commit()

        return GmailStatus(
            connected=True,
            email=email,
            last_polled_at=s.get("gmail_last_polled_at"),
            poll_enabled=bool(s.get("gmail_poll_enabled")),
        )
    except Exception as exc:
        logger.error("Gmail status check failed: %s", exc)
        return GmailStatus(
            connected=False,
            poll_enabled=bool(s.get("gmail_poll_enabled")),
            error=str(exc)[:200],
        )


@router.post("/test")
async def test_gmail_connection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test Gmail connection using stored credentials."""
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    s = tenant.settings or {}
    creds = _build_credentials(s)
    if not creds:
        raise HTTPException(status_code=400, detail="Gmail credentials not configured")

    try:
        creds = _refresh_if_needed(creds)
        from googleapiclient.discovery import build
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        profile = service.users().getProfile(userId="me").execute()

        tenant.settings = {**s, "gmail_access_token": creds.token}
        await db.commit()

        return {
            "success": True,
            "email": profile.get("emailAddress", ""),
            "messages_total": profile.get("messagesTotal", 0),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gmail connection failed: {exc}")
