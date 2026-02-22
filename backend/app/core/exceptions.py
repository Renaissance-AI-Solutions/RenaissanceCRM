"""Custom exception classes and FastAPI exception handlers."""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class CRMException(Exception):
    """Base exception for CRM application errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(CRMException):
    def __init__(self, entity: str, identifier: str | int):
        super().__init__(f"{entity} '{identifier}' not found", status_code=404)


class DuplicateError(CRMException):
    def __init__(self, entity: str, field: str, value: str):
        super().__init__(f"{entity} with {field} '{value}' already exists", status_code=409)


class ForbiddenError(CRMException):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message, status_code=403)


class WebhookVerificationError(CRMException):
    def __init__(self):
        super().__init__("Invalid webhook signature", status_code=401)


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# ---------------------------------------------------------------------------
async def crm_exception_handler(request: Request, exc: CRMException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "status_code": exc.status_code},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500},
    )
