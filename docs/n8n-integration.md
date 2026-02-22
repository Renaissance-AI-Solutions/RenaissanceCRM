# n8n Integration Guide

Connect your n8n workflows to the Antigravity CRM to automatically import leads, log activities, and update deals.

## Authentication

All n8n endpoints require an API key. Create one in **Settings → API Keys**.

In every n8n HTTP Request node, set:
- **Header**: `x-api-key: <your-api-key>`
- **Content-Type**: `application/json`

For HMAC signature verification (optional), add:
- **Header**: `x-webhook-signature: <hmac-sha256-hex>`
- The signature is computed over the raw body using your `WEBHOOK_SECRET`

---

## Endpoints

### 1. Upsert Lead / Contact

**`POST /api/n8n/lead`**

Creates a new contact or updates an existing one (matched by email).

```json
{
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1-555-0123",
  "source": "website-form",
  "tags": ["inbound", "enterprise"],
  "custom_fields": {
    "company_size": "50-100",
    "industry": "SaaS"
  },
  "notes": "Downloaded whitepaper on AI automation",
  "create_deal": true,
  "deal_title": "John Doe — Enterprise Plan",
  "deal_value": 25000
}
```

**Response**: The created/updated contact object with `is_new: true/false`.

### 2. Log Activity

**`POST /api/n8n/activity`**

Logs an activity (email, call, note, meeting, system) to a contact's timeline.

```json
{
  "contact_email": "john@example.com",
  "type": "email",
  "subject": "Follow-up: AI Automation Proposal",
  "body": "Hi John, just following up on our conversation...",
  "metadata": {
    "email_id": "msg-123",
    "direction": "outbound"
  }
}
```

### 3. Import Email History

**`POST /api/n8n/email-history`**

Imports a batch of email threads to a contact's timeline.

```json
{
  "contact_email": "john@example.com",
  "emails": [
    {
      "subject": "Re: Project Proposal",
      "body": "Thanks for sending over the proposal...",
      "direction": "inbound",
      "sent_at": "2025-01-15T10:30:00Z",
      "message_id": "msg-456",
      "thread_id": "thread-789"
    },
    {
      "subject": "Project Proposal",
      "body": "Hi John, please find our proposal attached...",
      "direction": "outbound",
      "sent_at": "2025-01-14T09:00:00Z",
      "message_id": "msg-455",
      "thread_id": "thread-789"
    }
  ]
}
```

### 4. Update Deal

**`POST /api/n8n/deal-update`**

Updates a deal's stage, value, or probability.

```json
{
  "contact_email": "john@example.com",
  "deal_title": "John Doe — Enterprise Plan",
  "stage_name": "Proposal",
  "value": 30000,
  "probability": 60,
  "notes": "Sent revised proposal with volume discount"
}
```

---

### 5. Company + Draft Email (Combined)

**`POST /api/webhooks/n8n/company-with-draft`**

Creates/upserts a company and all contacts from Clay data, **plus** stores an AI-generated draft email linked to the primary contact. The draft email is saved with `status: "draft"` for user review before sending.

**Payload structure:**

```json
{
  "body": {
    "company": "Acme Corp",
    "address": "123 Main St, City, ST 12345",
    "phone": "+1 555-0100",
    "website": "https://acme.example.com",
    "google_maps_url": "https://www.google.com/maps/place/...",
    "rating": 4.5,
    "reviews_count": 200,
    "source": "clay",
    "people": [
      {
        "firstName": "Jane",
        "lastName": "Smith",
        "fullName": "Jane Smith",
        "jobTitle": "CEO",
        "companyDomain": "acme.example.com",
        "linkedInUrl": "https://linkedin.com/in/janesmith",
        "departments": ["Management"],
        "seniorities": ["C-Level"]
      }
    ],
    "personal_emails": {
      "full_name": "Jane Smith",
      "linkedin_url": "https://linkedin.com/in/janesmith",
      "emails": [{ "email": "jane@personal.com", "domain": "personal.com", "tags": ["b2c"] }]
    }
  },
  "ai_output": [
    {
      "model_instance_id": "qwen/qwen3-32b",
      "output": [
        { "type": "reasoning", "content": "Chain of thought..." },
        { "type": "tool_call", "tool": "browser_navigate", "arguments": {"url": "..."}, "output": "..." },
        { "type": "message", "content": "**Subject:** Your subject here\n\nDear Jane,\n\nEmail body..." }
      ]
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "message": "Company 'Acme Corp' processed with 1 contacts and draft email",
  "data": {
    "company_id": "uuid",
    "contacts": [{ "contact_id": "uuid", "name": "Jane Smith", "action": "created", "is_primary": true }],
    "draft_email_id": "uuid",
    "draft_email_status": "draft"
  }
}
```

**Draft email lifecycle:** `draft` → `approved` → `sent` (or `rejected`)

---

## Example n8n Workflows

### New Lead from Web Form
1. **Webhook Trigger** (receives form submission)
2. **Set** node (map form fields to CRM schema)
3. **HTTP Request** → `POST /api/n8n/lead` with `create_deal: true`
4. **IF** node (check `is_new`)
5. **Send Email** (welcome email if new) / **Slack** (notify team)

### Gmail → CRM Activity Sync
1. **Gmail Trigger** (new email)
2. **Set** node (extract sender, subject, body)
3. **HTTP Request** → `POST /api/n8n/activity` with type `email`

### Scheduled Email History Import
1. **Schedule Trigger** (daily at 2am)
2. **Gmail** node (get last 24h of emails)
3. **Code** node (group by contact, format as `emails` array)
4. **Loop Over Items**
5. **HTTP Request** → `POST /api/n8n/email-history`

---

## Webhook Security (HMAC)

If `WEBHOOK_SECRET` is set, verify payloads:

```python
import hmac, hashlib

signature = hmac.new(
    WEBHOOK_SECRET.encode(),
    request_body_bytes,
    hashlib.sha256
).hexdigest()

# Send as header: x-webhook-signature: <signature>
```

In n8n, use a **Code** node before the HTTP Request to compute the HMAC.
