"""FastAPI application — main entry point with all routers registered."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import CRMException, crm_exception_handler, generic_exception_handler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle manager."""
    # Start Gmail polling scheduler
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from app.modules.gmail.service import poll_all_tenants

        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            poll_all_tenants,
            "interval",
            minutes=2,
            id="gmail_poll",
            max_instances=1,  # Prevent overlapping runs
            coalesce=True,
        )
        scheduler.start()
        logger.info("Gmail polling scheduler started (every 2 minutes)")
        app.state.scheduler = scheduler
    except Exception as exc:
        logger.warning("Could not start Gmail scheduler: %s", exc)
        app.state.scheduler = None

    yield

    # Shutdown scheduler
    if getattr(app.state, "scheduler", None):
        app.state.scheduler.shutdown(wait=False)
        logger.info("Gmail polling scheduler stopped")


app = FastAPI(
    title="Antigravity CRM",
    description="Modular CRM with n8n webhook integration",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
app.add_exception_handler(CRMException, crm_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------
from app.modules.auth.router import router as auth_router
from app.modules.contacts.router import company_router, router as contacts_router
from app.modules.deals.router import router as deals_router, stages_router
from app.modules.activities.router import router as activities_router
from app.modules.integrations.n8n.router import router as n8n_router
from app.modules.reporting.router import router as reporting_router
from app.modules.customization.router import router as customization_router
from app.modules.draft_emails.router import router as draft_emails_router
from app.modules.email_threads.router import router as email_threads_router
from app.modules.gmail.router import router as gmail_router

app.include_router(auth_router)
app.include_router(contacts_router)
app.include_router(company_router)
app.include_router(deals_router)
app.include_router(stages_router)
app.include_router(activities_router)
app.include_router(n8n_router)
app.include_router(reporting_router)
app.include_router(customization_router)
app.include_router(draft_emails_router)
app.include_router(email_threads_router)
app.include_router(gmail_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health", tags=["Health"])
async def health_check():
    scheduler = getattr(app.state, "scheduler", None)
    return {
        "status": "healthy",
        "version": "1.0.0",
        "gmail_scheduler": "running" if (scheduler and scheduler.running) else "stopped",
    }
