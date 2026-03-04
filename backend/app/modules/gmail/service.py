"""Gmail polling service — polls Gmail API for inbound replies and auto-drafts AI responses.

Flow:
1. APScheduler calls poll_all_tenants() every 2 minutes
2. For each tenant with gmail configured: fetch new messages via Gmail API historyId
3. Match reply to existing EmailThread by X-CRM-Thread-ID header or contact email
4. Save inbound Activity linked to thread
5. If no pending draft for thread: auto-draft AI reply via LMStudio
"""

import base64
import logging
import re
import uuid
from datetime import datetime, timezone
from email import message_from_bytes

import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.models import (
    Activity,
    ActivityType,
    Contact,
    DraftEmail,
    DraftEmailStatus,
    EmailThread,
    EmailThreadStatus,
    Tenant,
)

logger = logging.getLogger(__name__)

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


# ---------------------------------------------------------------------------
# Credential helpers
# ---------------------------------------------------------------------------

def _build_credentials(s: dict) -> Credentials | None:
    """Build Google Credentials from tenant settings dict. Returns None if not configured."""
    client_id = s.get("gmail_client_id", "")
    client_secret = s.get("gmail_client_secret", "")
    refresh_token = s.get("gmail_refresh_token", "")
    if not (client_id and client_secret and refresh_token):
        return None
    creds = Credentials(
        token=s.get("gmail_access_token") or None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=GMAIL_SCOPES,
    )
    return creds


def _refresh_if_needed(creds: Credentials) -> Credentials:
    """Refresh access token if expired."""
    if not creds.valid:
        creds.refresh(Request())
    return creds


# ---------------------------------------------------------------------------
# Parse Gmail message headers
# ---------------------------------------------------------------------------

def _get_header(headers: list[dict], name: str) -> str:
    """Extract a header value by name (case-insensitive)."""
    name_lower = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name_lower:
            return h.get("value", "")
    return ""


def _decode_body(payload: dict) -> str:
    """Recursively decode message body from Gmail payload."""
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    if mime_type.startswith("multipart/"):
        for part in payload.get("parts", []):
            text = _decode_body(part)
            if text:
                return text
    return ""


# ---------------------------------------------------------------------------
# Thread matching
# ---------------------------------------------------------------------------

async def _find_or_create_thread(
    db,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    company_id: uuid.UUID | None,
    subject: str,
    gmail_thread_id: str | None,
    crm_thread_id: str | None,
) -> EmailThread:
    """Find existing thread or create one."""
    thread = None

    # Priority 1: explicit CRM thread ID from X-CRM-Thread-ID header
    if crm_thread_id:
        try:
            t_uuid = uuid.UUID(crm_thread_id)
            result = await db.execute(
                select(EmailThread).where(
                    EmailThread.id == t_uuid,
                    EmailThread.tenant_id == tenant_id,
                )
            )
            thread = result.scalar_one_or_none()
        except (ValueError, AttributeError):
            pass

    # Priority 2: match by Gmail thread ID
    if not thread and gmail_thread_id:
        result = await db.execute(
            select(EmailThread).where(
                EmailThread.gmail_thread_id == gmail_thread_id,
                EmailThread.tenant_id == tenant_id,
            )
        )
        thread = result.scalar_one_or_none()

    # Priority 3: most recent active thread for this contact
    if not thread:
        result = await db.execute(
            select(EmailThread).where(
                EmailThread.contact_id == contact_id,
                EmailThread.tenant_id == tenant_id,
                EmailThread.status == EmailThreadStatus.ACTIVE,
            ).order_by(EmailThread.last_activity_at.desc()).limit(1)
        )
        thread = result.scalar_one_or_none()

    # Create new thread if still not found
    if not thread:
        clean_subject = re.sub(r"^(Re|Fwd?):\s*", "", subject, flags=re.IGNORECASE).strip()
        thread = EmailThread(
            tenant_id=tenant_id,
            contact_id=contact_id,
            company_id=company_id,
            subject=clean_subject or subject,
            gmail_thread_id=gmail_thread_id,
            status=EmailThreadStatus.ACTIVE,
            last_activity_at=datetime.now(timezone.utc),
        )
        db.add(thread)
        await db.flush()

    # Update Gmail thread ID if we didn't have it
    if gmail_thread_id and not thread.gmail_thread_id:
        thread.gmail_thread_id = gmail_thread_id

    thread.last_activity_at = datetime.now(timezone.utc)
    return thread


# ---------------------------------------------------------------------------
# Auto-draft AI reply
# ---------------------------------------------------------------------------

async def _auto_draft_reply(
    db,
    thread: EmailThread,
    tenant_settings: dict,
) -> DraftEmail | None:
    """Draft an AI reply for the thread using LMStudio. Returns created DraftEmail or None."""
    lm_url = tenant_settings.get("lmstudio_url", "").rstrip("/")
    lm_key = tenant_settings.get("lmstudio_api_key", "")
    lm_model = tenant_settings.get("lmstudio_model", "openai/gpt-oss-20b")

    if not lm_url:
        logger.warning("LMStudio not configured — skipping auto-draft for thread %s", thread.id)
        return None

    # Fetch full thread: sent drafts + inbound activities in chronological order
    drafts_result = await db.execute(
        select(DraftEmail).where(
            DraftEmail.thread_id == thread.id,
            DraftEmail.status.in_([DraftEmailStatus.SENT, DraftEmailStatus.APPROVED]),
        ).order_by(DraftEmail.created_at)
    )
    sent_drafts = drafts_result.scalars().all()

    activities_result = await db.execute(
        select(Activity).where(
            Activity.thread_id == thread.id,
            Activity.type == ActivityType.EMAIL,
        ).order_by(Activity.created_at)
    )
    inbound_activities = activities_result.scalars().all()

    # Build conversation context (interleaved by timestamp)
    messages_ctx: list[tuple[datetime, str, str]] = []
    for d in sent_drafts:
        messages_ctx.append((d.created_at, "outbound", f"Subject: {d.subject}\n\n{d.body}"))
    for a in inbound_activities:
        direction = a.metadata_.get("direction", "inbound")
        if direction == "inbound":
            messages_ctx.append((a.created_at, "inbound", f"Subject: {a.subject}\n\n{a.body or ''}"))

    messages_ctx.sort(key=lambda x: x[0])

    if not messages_ctx:
        logger.warning("No thread context found for auto-draft, thread %s", thread.id)
        return None

    conversation = "\n\n---\n\n".join(
        f"[{'YOU' if direction == 'outbound' else 'LEAD'}]\n{text}"
        for _, direction, text in messages_ctx
    )

    system_prompt = (
        "You are an expert B2B sales email writer. "
        "You are given an ongoing email conversation with a lead. "
        "Your job is to draft the next reply from the salesperson. "
        "Be concise, professional, and natural. "
        "Continue the conversation appropriately based on what the lead said. "
        "Start your response with 'Subject: <subject line>' on the first line, "
        "followed by a blank line, then the email body. "
        "Do not include any preamble or explanation — only the email."
    )

    user_message = f"Here is the email thread so far:\n\n{conversation}\n\nDraft the next reply from YOU."

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            headers: dict = {"Content-Type": "application/json"}
            if lm_key:
                headers["Authorization"] = f"Bearer {lm_key}"
            resp = await client.post(
                f"{lm_url}/v1/chat/completions",
                json={
                    "model": lm_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "stream": False,
                },
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.error("LMStudio call failed for auto-draft thread %s: %s", thread.id, exc)
        return None

    raw = data["choices"][0]["message"]["content"].strip()

    # Strip <think> blocks from reasoning models
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    if "<think>" in raw:
        parts = raw.split("</think>")
        raw = parts[-1].strip() if len(parts) > 1 else ""
    if not raw:
        logger.warning("AI returned empty response for thread %s", thread.id)
        return None

    # Parse Subject: from first line
    subject = thread.subject
    body = raw
    subject_match = re.match(r"Subject:\s*(.+?)(?:\n|$)", raw, re.IGNORECASE)
    if subject_match:
        subject = subject_match.group(1).strip()
        body = raw[subject_match.end():].lstrip("\n")

    # Fetch contact for company_id
    contact_result = await db.execute(select(Contact).where(Contact.id == thread.contact_id))
    contact = contact_result.scalar_one_or_none()

    draft = DraftEmail(
        tenant_id=thread.tenant_id,
        contact_id=thread.contact_id,
        company_id=thread.company_id or (contact.company_id if contact else None),
        thread_id=thread.id,
        subject=subject,
        body=body,
        status=DraftEmailStatus.DRAFT,
        ai_model=lm_model,
    )
    db.add(draft)
    await db.flush()
    logger.info("Auto-drafted AI reply for thread %s (draft_id=%s)", thread.id, draft.id)
    return draft


# ---------------------------------------------------------------------------
# Core polling logic
# ---------------------------------------------------------------------------

async def _poll_tenant(db, tenant: Tenant) -> None:
    """Poll Gmail for new replies for a single tenant."""
    s = tenant.settings or {}
    if not s.get("gmail_poll_enabled"):
        return

    creds = _build_credentials(s)
    if not creds:
        logger.debug("Tenant %s: Gmail credentials not configured", tenant.id)
        return

    try:
        creds = _refresh_if_needed(creds)
    except Exception as exc:
        logger.error("Tenant %s: Failed to refresh Gmail token: %s", tenant.id, exc)
        return

    # Persist refreshed access token
    tenant.settings = {**s, "gmail_access_token": creds.token}

    try:
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    except Exception as exc:
        logger.error("Tenant %s: Failed to build Gmail service: %s", tenant.id, exc)
        return

    last_history_id = s.get("gmail_history_id")

    try:
        if last_history_id:
            # Incremental: only changes since last poll
            history_resp = service.users().history().list(
                userId="me",
                startHistoryId=last_history_id,
                historyTypes=["messageAdded"],
                labelId="INBOX",
            ).execute()
            new_message_ids = []
            for record in history_resp.get("history", []):
                for msg_added in record.get("messagesAdded", []):
                    msg = msg_added.get("message", {})
                    if "INBOX" in msg.get("labelIds", []):
                        new_message_ids.append(msg["id"])
            new_history_id = history_resp.get("historyId", last_history_id)
        else:
            # First run: fetch recent unread messages as baseline
            list_resp = service.users().messages().list(
                userId="me",
                q="in:INBOX is:unread",
                maxResults=20,
            ).execute()
            new_message_ids = [m["id"] for m in list_resp.get("messages", [])]
            # Get current historyId for future incremental polls
            profile = service.users().getProfile(userId="me").execute()
            new_history_id = profile.get("historyId", "")

    except Exception as exc:
        logger.error("Tenant %s: Gmail API error: %s", tenant.id, exc)
        return

    logger.info("Tenant %s: %d new message(s) to process", tenant.id, len(new_message_ids))

    for msg_id in new_message_ids:
        try:
            await _process_message(db, service, tenant, msg_id)
        except Exception as exc:
            logger.error("Tenant %s: Error processing message %s: %s", tenant.id, msg_id, exc)

    # Update poll state
    tenant.settings = {
        **tenant.settings,
        "gmail_history_id": new_history_id,
        "gmail_last_polled_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.commit()


async def _process_message(db, service, tenant: Tenant, msg_id: str) -> None:
    """Process a single Gmail message — save as inbound activity and auto-draft reply."""
    msg = service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()

    payload = msg.get("payload", {})
    headers = payload.get("headers", [])

    # Must be a reply (has In-Reply-To header)
    in_reply_to = _get_header(headers, "In-Reply-To")
    references = _get_header(headers, "References")
    if not in_reply_to and not references:
        return  # Not a reply — skip

    subject = _get_header(headers, "Subject") or "(no subject)"
    from_addr = _get_header(headers, "From")
    crm_thread_id = _get_header(headers, "X-CRM-Thread-ID")
    gmail_thread_id = msg.get("threadId")
    gmail_msg_id = _get_header(headers, "Message-ID") or msg_id

    # Extract sender email address
    sender_email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]+", from_addr)
    sender_email = sender_email_match.group(0).lower() if sender_email_match else ""

    if not sender_email:
        return

    # Look up contact by email
    result = await db.execute(
        select(Contact).where(
            Contact.tenant_id == tenant.id,
            Contact.email == sender_email,
        )
    )
    contact = result.scalar_one_or_none()

    # Also check personal_emails JSONB field if no match
    if not contact:
        result = await db.execute(
            select(Contact).where(
                Contact.tenant_id == tenant.id,
            )
        )
        all_contacts = result.scalars().all()
        for c in all_contacts:
            pe_list = c.personal_emails or []
            for pe in pe_list:
                email_val = pe if isinstance(pe, str) else pe.get("email", "")
                if email_val.lower() == sender_email:
                    contact = c
                    break
            if contact:
                break

    if not contact:
        logger.debug("Tenant %s: No contact found for sender %s", tenant.id, sender_email)
        return

    # Check for duplicate (already processed this Gmail message)
    dup_result = await db.execute(
        select(Activity).where(
            Activity.tenant_id == tenant.id,
            Activity.gmail_message_id == gmail_msg_id,
        )
    )
    if dup_result.scalar_one_or_none():
        return  # Already processed

    # Decode body
    body_text = _decode_body(payload)

    # Find or create thread
    thread = await _find_or_create_thread(
        db=db,
        tenant_id=tenant.id,
        contact_id=contact.id,
        company_id=contact.company_id,
        subject=subject,
        gmail_thread_id=gmail_thread_id,
        crm_thread_id=crm_thread_id or None,
    )

    # Save inbound activity
    activity = Activity(
        tenant_id=tenant.id,
        contact_id=contact.id,
        thread_id=thread.id,
        gmail_message_id=gmail_msg_id,
        type=ActivityType.EMAIL,
        subject=subject,
        body=body_text,
        source="gmail",
        metadata_={
            "direction": "inbound",
            "from": from_addr,
            "gmail_message_id": gmail_msg_id,
            "gmail_thread_id": gmail_thread_id,
        },
    )
    db.add(activity)
    await db.flush()

    logger.info(
        "Tenant %s: Saved inbound email from %s (thread=%s)",
        tenant.id, sender_email, thread.id,
    )

    # Auto-draft reply if no pending draft exists for this thread
    pending_result = await db.execute(
        select(DraftEmail).where(
            DraftEmail.thread_id == thread.id,
            DraftEmail.status == DraftEmailStatus.DRAFT,
        )
    )
    if not pending_result.scalar_one_or_none():
        await _auto_draft_reply(db, thread, tenant.settings or {})

    # Mark message as read in Gmail
    try:
        service.users().messages().modify(
            userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()
    except Exception:
        pass  # Non-fatal


# ---------------------------------------------------------------------------
# APScheduler entry point
# ---------------------------------------------------------------------------

async def poll_all_tenants() -> None:
    """Called by APScheduler every 2 minutes. Polls Gmail for all configured tenants."""
    logger.info("Gmail poll: starting")
    async with async_session_factory() as db:
        result = await db.execute(select(Tenant).where(Tenant.is_active == True))  # noqa: E712
        tenants = result.scalars().all()
        for tenant in tenants:
            try:
                await _poll_tenant(db, tenant)
            except Exception as exc:
                logger.error("Gmail poll error for tenant %s: %s", tenant.id, exc)
    logger.info("Gmail poll: complete")
