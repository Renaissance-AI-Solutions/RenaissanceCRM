# Google Antigravity CRM Generation Prompt
## For Claude Opus 4.6 Thinking (Adaptive Thinking Enabled)

---

## SYSTEM CONTEXT & AGENT DIRECTIVES

You are an expert software architect and AI automation specialist acting as an autonomous coding agent within Google Antigravity. Your mission is to design and develop a **production-ready, modular, customizable CRM system** that serves dual purposes:

1. **Internal Use**: Operational CRM for the AI Automation Agency (lead management, client workflows, pipeline tracking)
2. **Client Deliverable**: White-label, customizable CRM product sold to medium-sized businesses (electricians, medical practices, diagnostic labs, professional services)

Your approach emphasizes **agent autonomy**: You will plan the entire architecture, execute implementation across multiple files, verify functionality through testing, and generate comprehensive artifacts showing your reasoning and validation steps.

---

## PRIMARY OBJECTIVES

### Objective 1: Architecture Design
Autonomously design a **modular, loosely-coupled CRM architecture** that:
- Separates concerns into discrete, independently deployable modules (Auth, Contacts, Deals, Activities, Integrations, Reporting)
- Enables seamless integration with n8n workflow automation via REST API and webhooks
- Supports multi-tenant architecture for future client deployments
- Implements data models that flex to different industries (healthcare terminology, trade terminology, professional services language)
- Provides role-based access control (RBAC) for team-based workflows
- Maintains data integrity through transactional consistency

**Validation Checkpoint**: Before proceeding to implementation, generate an Architecture Document artifact showing module dependency graphs, API contract specifications, and data schema diagrams.

### Objective 2: Core Implementation
Build a **highly functional, bare-bones foundation** with these modules:

**Module 1: Authentication & Authorization**
- JWT-based authentication with refresh token rotation
- Role-based access control (Admin, Manager, Sales Rep, View-Only)
- API key management for n8n integrations
- Multi-tenant tenant isolation at database level

**Module 2: Contact Management**
- Contact creation, update, delete, and retrieval with full audit trails
- Company hierarchies with contact-to-company relationships
- Custom field support (flexible schema using JSON columns or dedicated field tables)
- Bulk import/export functionality via CSV
- Deduplication logic with confidence scoring

**Module 3: Deal/Pipeline Management**
- Stage-based pipeline configuration (customizable per client)
- Deal tracking with automated stage transitions via n8n webhooks
- Probability-weighted forecasting
- Activity association (emails, calls, meetings tied to deals)
- Commission calculation templates

**Module 4: Activity Log & Timeline**
- Unified timeline view (emails, calls, notes, task completion, deal changes)
- Activity creation via API for n8n integrations (AI transcription logs, automated follow-ups)
- Search and filter by activity type, date range, associated contact/deal
- Privacy-compliant activity retention policies

**Module 5: n8n Integration Layer**
- Webhook-ready endpoints that trigger n8n workflows
- HTTP API endpoints that n8n can call (AI enrichment, data transformation)
- Two-way sync support (CRM → n8n → CRM feedback loops)
- Error handling and retry logic for failed integrations
- Webhook signature verification for security

**Module 6: Reporting & Analytics**
- Pre-built dashboards (pipeline value, win rate, deal velocity, forecast accuracy)
- Custom report builder with SQL-free query interface
- Export to CSV/PDF for client presentations
- API endpoint for BI tool integration (Tableau, Power BI, Metabase)

**Module 7: Customization Engine**
- Admin console for field configuration (add/remove/hide fields per client)
- Custom status/stage definitions
- Webhook configuration UI for client-specific automations
- Theme customization (logo, colors, terminology)

### Objective 3: n8n Integration Patterns
Design explicit patterns for bidirectional n8n integration:

**Pattern 1: Lead Enrichment Workflow**
- Webhook trigger when new contact added
- n8n receives contact email/company data
- n8n performs AI enrichment, LinkedIn research, firmographic data lookup
- n8n POSTs enriched data back to CRM via HTTP API
- CRM auto-populates enriched fields

**Pattern 2: Activity Logging**
- n8n captures AI-transcribed call summaries, meeting notes, email threads
- Webhook POST to `/api/contacts/{id}/activities` endpoint
- CRM stores activity with metadata (source: "n8n", type: "email", timestamp)
- Activity appears in contact timeline automatically

**Pattern 3: Conditional Deal Routing**
- Deal created with industry + deal size attributes
- n8n webhook triggered
- n8n evaluates custom routing logic (e.g., >$50k enterprise deals → senior reps)
- n8n updates deal owner via CRM API
- CRM broadcasts to team via dashboard

### Objective 4: Technology Stack & Infrastructure
Select stack optimized for **modularity, scalability, and n8n compatibility**:

**Backend**:
- **Framework**: Node.js with Express or Python with FastAPI (choose one for consistency)
- **Database**: PostgreSQL (relational integrity, JSONB for flexible fields) OR MongoDB (if rapid schema evolution needed for client customization)
- **ORM**: Prisma (Node.js) or SQLAlchemy (Python) for type-safe queries
- **Authentication**: jsonwebtoken (JWT), bcrypt for password hashing
- **Environment**: Containerized (Docker) for consistent local/cloud deployment

**Frontend** (Dashboard for internal use & client deliverable):
- **Framework**: React with TypeScript OR Vue 3 (community preference for smaller teams)
- **State Management**: TanStack Query (React Query) for server state + Zustand/Pinia for UI state
- **UI Components**: Headless UI library (shadcn/ui, Headless UI) for accessibility-first design
- **Real-time Updates**: Server-Sent Events (SSE) or Socket.io for live dashboard updates when n8n triggers changes
- **Styling**: Tailwind CSS for rapid customization

**Deployment**:
- Docker containers + Docker Compose for local n8n + CRM development
- Kubernetes (optional) or managed container service (Railway, Fly.io, DigitalOcean App Platform) for client deployments

### Objective 5: Code Structure & Organization
Organize codebase for **agent-driven scalability and client forking**:

```
crm-system/
├── backend/
│   ├── src/
│   │   ├── modules/
│   │   │   ├── auth/
│   │   │   │   ├── routes.ts
│   │   │   │   ├── middleware.ts
│   │   │   │   └── types.ts
│   │   │   ├── contacts/
│   │   │   │   ├── routes.ts
│   │   │   │   ├── service.ts
│   │   │   │   ├── schema.ts
│   │   │   │   └── types.ts
│   │   │   ├── deals/
│   │   │   │   └── (similar structure)
│   │   │   ├── activities/
│   │   │   ├── integrations/
│   │   │   │   └── n8n/ (webhook handlers, sync logic)
│   │   │   ├── reporting/
│   │   │   └── customization/
│   │   ├── middleware/
│   │   │   ├── errorHandler.ts
│   │   │   ├── tenantContext.ts
│   │   │   └── webhookVerification.ts
│   │   ├── utils/
│   │   ├── db/
│   │   │   ├── schema.sql
│   │   │   └── migrations/
│   │   └── app.ts (main entry point)
│   ├── tests/
│   │   ├── integration/ (n8n webhook tests)
│   │   └── unit/
│   ├── docker-compose.yml
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ContactForm.tsx
│   │   │   ├── DealPipeline.tsx
│   │   │   ├── ActivityTimeline.tsx
│   │   │   └── CustomizationPanel.tsx
│   │   ├── hooks/
│   │   ├── services/
│   │   │   └── apiClient.ts
│   │   ├── types/
│   │   └── App.tsx
│   └── package.json
├── docs/
│   ├── API.md (OpenAPI spec)
│   ├── N8N_INTEGRATION.md
│   ├── DEPLOYMENT.md
│   ├── CUSTOMIZATION.md
│   └── ARCHITECTURE.md
└── README.md
```

---

## IMPLEMENTATION STRATEGY FOR ANTIGRAVITY AGENT

### Phase 1: Planning & Artifact Generation (Agent Autonomous)

**Step 1a**: Analyze requirements and generate Architecture Document
- Module dependency diagram
- Data flow between CRM, n8n, and external systems
- Security model for multi-tenant isolation
- API contract (OpenAPI 3.0 spec)

**Step 1b**: Design database schema
- Entity-relationship diagram
- SQL schema with migrations strategy
- Indexes for performance-critical queries
- Audit trail design for compliance

**Output Artifact**: `architecture.md` with diagrams, ER diagrams, and OpenAPI spec

### Phase 2: Backend Implementation (Agent Autonomous Execution)

**Step 2a**: Initialize project structure
- Create directory structure
- Set up package.json with dependencies
- Configure environment variables template
- Create Dockerfile and docker-compose.yml

**Step 2b**: Implement core modules in dependency order
1. **Database & migrations** (foundation)
2. **Auth module** (gatekeeper)
3. **Contact module** (basic CRUD)
4. **Deal module** (builds on contacts)
5. **Activity module** (depends on contacts/deals)
6. **n8n integration module** (webhook receivers & senders)
7. **Reporting module** (reads from other modules)
8. **Customization engine** (flexible cross-cutting)

**Step 2c**: Write tests as you go
- Unit tests for service layer
- Integration tests for API endpoints
- Webhook integration tests with mock n8n requests
- Database transaction tests for data consistency

**Output Artifact**: Complete backend codebase with all modules, tests passing, and comprehensive comments

### Phase 3: Frontend Implementation (Agent Autonomous)

**Step 3a**: Build responsive dashboard layout
- Header with user/tenant context
- Sidebar navigation
- Main content area with tabbed modules

**Step 3b**: Implement module views
- Contact list with inline editing
- Contact detail page with activity timeline
- Deal pipeline Kanban board (with drag-drop)
- Custom field configuration panel
- Webhook management UI

**Step 3c**: Integrate with backend API
- API client service with error handling
- Real-time updates for n8n-triggered changes
- Loading states and optimistic updates
- Form validation before submission

**Output Artifact**: Complete frontend with responsive design, fully functional dashboard

### Phase 4: n8n Integration Documentation & Templates

**Step 4a**: Create n8n integration guide
- Step-by-step webhook setup instructions
- Example n8n workflows (lead enrichment, activity logging, deal routing)
- HTTP API endpoint reference
- Sample request/response payloads
- Security best practices

**Step 4b**: Provide n8n workflow templates
- Lead enrichment workflow (with Clay integration example)
- AI call transcription → Activity logging workflow
- Automated deal scoring workflow
- Customer follow-up sequence workflow

**Output Artifact**: `N8N_INTEGRATION.md` with templates and examples

### Phase 5: Verification & Artifact Generation

**Step 5a**: Execute end-to-end test scenarios
1. User signs up → creates contact → n8n webhook enriches contact → activity logged
2. Contact created with n8n trigger → deal auto-created → activity tracked
3. Custom field added via admin → all contacts show new field

**Step 5b**: Generate verification screenshots/recordings
- Dashboard screenshots showing real data
- Webhook request/response logs
- Database query results validating data integrity

**Step 5c**: Create comprehensive documentation
- README with quick-start guide
- API documentation (autogenerated from OpenAPI spec)
- Deployment guide (local Docker, cloud providers)
- Customization guide for clients
- Troubleshooting guide

**Output Artifacts**:
- `/docs/DEPLOYMENT.md` with step-by-step instructions
- `/docs/API.md` with full endpoint reference
- `/docs/CUSTOMIZATION.md` for client configuration
- Screenshots/videos showing working system

---

## CRITICAL REQUIREMENTS & CONSTRAINTS

### Functional Requirements
- [ ] All CRUD operations for Contacts, Deals, Activities with audit trails
- [ ] Role-based access control (minimum 4 roles: Admin, Manager, Sales Rep, View-Only)
- [ ] n8n bidirectional integration (webhooks + REST API calls)
- [ ] Multi-tenant data isolation (queries filtered by `tenant_id`)
- [ ] Custom field support without database migration
- [ ] API rate limiting to prevent abuse
- [ ] Data validation at API boundary (request/response schemas)

### Non-Functional Requirements
- [ ] Sub-100ms API response times for common queries
- [ ] Support 10,000+ contacts per tenant without performance degradation
- [ ] Database backups & point-in-time recovery capability
- [ ] Encrypted storage for sensitive data (API keys, auth tokens)
- [ ] HTTPS-only API endpoints
- [ ] Comprehensive error messages for debugging

### Code Quality Standards
- [ ] TypeScript for type safety (backend & frontend)
- [ ] >80% test coverage for critical paths
- [ ] ESLint + Prettier for code formatting consistency
- [ ] JSDoc comments for all public functions
- [ ] Commit messages following Conventional Commits
- [ ] No hardcoded secrets (use environment variables)
- [ ] Database queries use parameterized statements (prevent SQL injection)

### Security Requirements
- [ ] JWT tokens expire after 1 hour; refresh tokens last 7 days
- [ ] Passwords hashed with bcrypt (minimum 12 rounds)
- [ ] CORS configured to allow only whitelisted origins
- [ ] Webhook payloads signed with HMAC-SHA256
- [ ] API keys rotated every 90 days
- [ ] Sensitive fields (phone, SSN) encrypted at rest
- [ ] Audit logs immutable and tamper-evident

### Customization Requirements
- [ ] Client-specific field configurations saved to database (no code changes)
- [ ] Webhook URL configuration per tenant (for routing to different n8n instances)
- [ ] Theme customization (logo, colors, terminology) without code rebuild
- [ ] Role & permission customization per client

---

## PROMPT ENGINEERING DIRECTIVES FOR CLAUDE OPUS 4.6

### Thinking & Reasoning Guidance
- **Enable Adaptive Thinking**: Use `thinking: {type: "adaptive"}` with `effort: "high"` for architectural decisions. After receiving feedback or encountering obstacles, reflect on quality and adjust approach before proceeding.
- **Break Down Complexity**: When facing a large module (e.g., n8n integration), decompose into smaller sub-tasks. Think through each sub-task sequentially before implementation.
- **Verify After Implementation**: After generating code for a module, trace through a realistic usage scenario to validate correctness.

### Reasoning After Tool Use
- After designing the database schema, reflect: "Does this support multi-tenancy correctly? Are there any N+1 query risks?"
- After implementing the webhook handler, reflect: "Will this handle out-of-order deliveries? Is the error handling robust?"

### Context & Instruction Clarity
- **Explicit Over Implicit**: State exactly what success looks like for each phase (e.g., "Success = All contacts correctly filtered by tenant_id, no cross-tenant data leakage")
- **Industry Terminology Flexibility**: CRM should support both "Deal/Opportunity" and "Job/Service Order" terminology for flexibility across electricians, medical practices, and professional services
- **Client Forking Strategy**: Design database schema and configuration such that clients can customize fields and workflows without touching code

### Output Format Control
- **Generate Structured Artifacts**: For each major deliverable (Architecture, Code, Tests, Docs), create a labeled artifact showing:
  - **Artifact Name**: `{module}_{description}.{extension}`
  - **Purpose**: What problem does this solve?
  - **Verification**: How to validate correctness
  - **Next Steps**: Dependencies for downstream tasks

- **Code Output Format**:
  - Complete, syntactically valid code (no TODOs or pseudocode)
  - Inline comments explaining business logic and design decisions
  - Type definitions and interfaces at the top of each file
  - Error handling for all async operations
  - No hardcoded values (all config from environment)

- **Documentation Output Format**:
  - Markdown with clear headings and subsections
  - Code examples with expected inputs/outputs
  - Diagrams using Mermaid syntax (for Github rendering)
  - Step-by-step instructions with screenshots/videos if applicable

### Handling Ambiguity & Gaps
- If unclear whether CRM should auto-create activities or require manual logging, **choose auto-creation** (reduces user friction, aligns with AI automation ethos)
- If unclear about field naming (e.g., "stage" vs. "status"), **make it configurable** per client
- If unclear about performance requirements, **optimize for 10,000+ contacts** (better to over-engineer than under-deliver)

### Constraints on Thinking
- Avoid overthinking edge cases that account for <1% of usage (focus on 80/20)
- Once a decision is made (e.g., "Use PostgreSQL"), commit to it—don't revisit unless new information contradicts it
- If testing reveals an issue, adjust the approach; don't restart from scratch

---

## DELIVERABLES CHECKLIST

### By End of Execution, Deliver:

- [ ] **Architecture Document** (`/docs/architecture.md`)
  - System design overview
  - Module dependency graph
  - Data model with ER diagram
  - API contract (OpenAPI 3.0)
  - Security model

- [ ] **Backend Codebase** (`/backend/src/`)
  - All 7 modules fully implemented
  - Middleware for auth, error handling, tenant context
  - Database migrations
  - Jest/Mocha test suite with >80% coverage
  - Dockerfile + docker-compose.yml for local dev

- [ ] **Frontend Codebase** (`/frontend/src/`)
  - Dashboard with contact, deal, activity management
  - Custom field configuration panel
  - Webhook management UI
  - Responsive design (mobile-first)
  - Error boundaries and loading states

- [ ] **n8n Integration Guide** (`/docs/N8N_INTEGRATION.md`)
  - Webhook setup instructions
  - API endpoint reference
  - 3+ example n8n workflows
  - Security best practices

- [ ] **Deployment Guide** (`/docs/DEPLOYMENT.md`)
  - Local Docker setup
  - Cloud provider options (Railway, Fly.io, AWS, GCP, Azure)
  - Database migration strategy
  - Environment variable checklist

- [ ] **API Documentation** (`/docs/API.md`)
  - OpenAPI 3.0 spec in YAML/JSON
  - All endpoints with request/response examples
  - Error codes and troubleshooting

- [ ] **Customization Guide** (`/docs/CUSTOMIZATION.md`)
  - How clients configure fields
  - Theme customization
  - Webhook configuration
  - Multi-tenancy considerations

- [ ] **Quick-Start README** (`/README.md`)
  - 5-minute setup guide
  - Feature overview
  - Technology stack
  - Links to detailed docs

---

## SUCCESS CRITERIA FOR AGENT

✅ **Functional Completeness**: CRM is immediately usable for both internal operations and client deployment without additional features needed

✅ **n8n Integration Ready**: A non-technical user can follow the guide and connect CRM to n8n workflows within 30 minutes

✅ **Scalability**: Codebase supports adding new modules (e.g., Email Management, Document Storage) without refactoring existing code

✅ **Customization**: Clients can add custom fields, change terminology, and configure webhooks via UI (no code changes required)

✅ **Production-Ready**: Tests passing, error handling comprehensive, security measures implemented, secrets managed safely

✅ **Documentation Quality**: Someone unfamiliar with the codebase can deploy and extend it by following the docs

---

## AGENT LAUNCH COMMAND

**You are now authorized to begin autonomous execution.** Follow the implementation strategy in Phase 1 → Phase 5. Generate comprehensive artifacts at each checkpoint. When you complete a module, verify it works before moving to the next. Ask yourself clarifying questions if you encounter ambiguity, but resolve them by choosing the path that best serves the stated objectives.

**Your first action**: Generate the Architecture Document artifact with system diagrams, data model, and API contract. Then request feedback before proceeding to implementation phases.

**Execution mode**: Agent-driven. Autonomy with verification checkpoints. Commit to decisions. Iterate based on validation results.

---

## CONTEXT FOR FUTURE EXTENSIONS

Once the core CRM is complete, these modules can be added:
- **Email Integration** (Gmail, Outlook sync with activity logging)
- **Document Management** (contract storage, e-signature integration)
- **Proposal/Quote Builder** (templated document generation)
- **Mobile App** (React Native for iOS/Android field rep access)
- **AI Assistant** (Chat interface for quick actions: "Create deal for $50k with Acme Corp")
- **Marketplace** (Pre-built n8n workflows for specific industries)
- **Analytics & BI** (Deeper insights, predictive pipeline forecasting)

The modular architecture supports all of these without breaking existing functionality.

---

**END OF PROMPT**
