"""FastAPI application — main entry point with all routers registered."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import CRMException, crm_exception_handler, generic_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle manager."""
    yield


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

app.include_router(auth_router)
app.include_router(contacts_router)
app.include_router(company_router)
app.include_router(deals_router)
app.include_router(stages_router)
app.include_router(activities_router)
app.include_router(n8n_router)
app.include_router(reporting_router)
app.include_router(customization_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
