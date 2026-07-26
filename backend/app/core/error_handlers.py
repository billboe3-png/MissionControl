"""
Mission Control Consistent Error Handling

Provides standardized error response format and exception handlers
for all API endpoints.
"""

import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger("missioncontrol.errors")


# ------------------------------------------------------------------ #
# Error Response Format                                                 #
# ------------------------------------------------------------------ #


class ErrorResponse:
    """Standardized error response structure."""

    @staticmethod
    def create(
        status_code: int,
        message: str,
        details: Any = None,
        error_code: str = "",
        path: str = "",
    ) -> dict:
        return {
            "error": {
                "status_code": status_code,
                "message": message,
                "error_code": error_code or _error_code_for_status(status_code),
                "details": details,
                "path": path,
            }
        }


def _error_code_for_status(code: int) -> str:
    """Map HTTP status code to a machine-readable error code."""
    mapping = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limit_exceeded",
        500: "internal_error",
        502: "bad_gateway",
        503: "service_unavailable",
    }
    return mapping.get(code, "error")


# ------------------------------------------------------------------ #
# Exception Handlers                                                    #
# ------------------------------------------------------------------ #


async def http_exception_handler(request: Request, exc) -> JSONResponse:
    """Handle HTTPException with consistent format."""
    status_code = exc.status_code
    detail = exc.detail if hasattr(exc, "detail") else str(exc)

    logger.warning(
        "HTTP %s %s -> %s: %s",
        request.method,
        request.url.path,
        status_code,
        detail,
    )

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse.create(
            status_code=status_code,
            message=detail,
            path=request.url.path,
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors with consistent format."""
    errors = exc.errors()
    messages = []
    for err in errors:
        loc = " -> ".join(str(part) for part in err.get("loc", []))
        msg = err.get("msg", "validation error")
        messages.append(f"{loc}: {msg}")

    logger.warning(
        "Validation error on %s %s: %s",
        request.method,
        request.url.path,
        "; ".join(messages),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse.create(
            status_code=422,
            message="Validation error",
            details=messages,
            error_code="validation_error",
            path=request.url.path,
        ),
    )


async def pydantic_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = [str(e) for e in exc.errors()]

    logger.warning(
        "Pydantic error on %s %s: %s",
        request.method,
        request.url.path,
        "; ".join(errors),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse.create(
            status_code=422,
            message="Invalid request data",
            details=errors,
            error_code="validation_error",
            path=request.url.path,
        ),
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle uncaught exceptions — never expose stack traces."""
    logger.error(
        "Unhandled exception on %s %s: %s\n%s",
        request.method,
        request.url.path,
        exc,
        traceback.format_exc(),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse.create(
            status_code=500,
            message="An internal error occurred. Check server logs for details.",
            error_code="internal_error",
            path=request.url.path,
        ),
    )


async def not_found_handler(request: Request, exc) -> JSONResponse:
    """Handle 404 Not Found."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse.create(
            status_code=404,
            message=f"Endpoint not found: {request.url.path}",
            error_code="not_found",
            path=request.url.path,
        ),
    )


# ------------------------------------------------------------------ #
# Registration                                                          #
# ------------------------------------------------------------------ #


def register_error_handlers(app: FastAPI) -> None:
    """Register all error handlers on the FastAPI app."""
    from fastapi.exceptions import HTTPException

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    app.add_exception_handler(ValidationError, pydantic_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
