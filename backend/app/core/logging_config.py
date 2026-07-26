"""
Mission Control Structured Logging

Provides structured JSON logging with request IDs, agent IDs,
plugin IDs, and correlation IDs for production observability.
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Context variables for request-scoped data
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
agent_id_var: ContextVar[str] = ContextVar("agent_id", default="")
plugin_id_var: ContextVar[str] = ContextVar("plugin_id", default="")
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter for production."""

    def __init__(self, json_format: bool = True):
        super().__init__()
        self.json_format = json_format

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context variables
        req_id = request_id_var.get("")
        if req_id:
            log_entry["request_id"] = req_id

        agt_id = agent_id_var.get("")
        if agt_id:
            log_entry["agent_id"] = agt_id

        plug_id = plugin_id_var.get("")
        if plug_id:
            log_entry["plugin_id"] = plug_id

        corr_id = correlation_id_var.get("")
        if corr_id:
            log_entry["correlation_id"] = corr_id

        uid = user_id_var.get("")
        if uid:
            log_entry["user_id"] = uid

        # Add source location for non-production debugging
        if record.levelno >= logging.WARNING:
            log_entry["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Add exception info
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        if self.json_format:
            return json.dumps(log_entry, default=str)
        else:
            # Fallback to human-readable format
            parts = [
                log_entry["timestamp"],
                log_entry["level"].ljust(8),
                log_entry["logger"],
                log_entry["message"],
            ]
            if req_id:
                parts.insert(1, f"[{req_id}]")
            return " ".join(parts)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    def format(self, record: logging.LogRecord) -> str:
        parts = [
            record.levelname.ljust(8),
            record.name,
            record.getMessage(),
        ]

        req_id = request_id_var.get("")
        if req_id:
            parts.insert(1, f"[{req_id}]")

        return " ".join(parts)


def setup_logging(
    level: str = "INFO",
    json_format: bool | None = None,
) -> None:
    """
    Configure structured logging for Mission Control.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_format: Use JSON format. None = auto-detect (JSON in production).
    """
    if json_format is None:
        import os
        env = os.environ.get("ENVIRONMENT", "development")
        json_format = env == "production"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        StructuredFormatter(json_format=json_format)
        if json_format
        else HumanReadableFormatter()
    )

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return uuid.uuid4().hex[:12]


def get_request_id() -> str:
    """Get the current request ID."""
    return request_id_var.get("")


def set_request_id(request_id: str) -> None:
    """Set the current request ID."""
    request_id_var.set(request_id)


def set_agent_id(agent_id: str) -> None:
    """Set the current agent ID for logging context."""
    agent_id_var.set(str(agent_id))


def set_plugin_id(plugin_id: str) -> None:
    """Set the current plugin ID for logging context."""
    plugin_id_var.set(plugin_id)


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for distributed tracing."""
    correlation_id_var.set(correlation_id)


def set_user_id(user_id: str) -> None:
    """Set the user ID for logging context."""
    user_id_var.set(str(user_id))


def clear_context() -> None:
    """Clear all logging context (call at end of request)."""
    request_id_var.set("")
    agent_id_var.set("")
    plugin_id_var.set("")
    correlation_id_var.set("")
    user_id_var.set("")


class RequestLoggingMiddleware:
    """ASGI middleware for structured request logging with timing."""

    def __init__(self, app, log_level: int = logging.INFO):
        self.app = app
        self.log_level = log_level
        self.logger = logging.getLogger("missioncontrol.request")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = generate_request_id()
        set_request_id(request_id)

        start = time.perf_counter()
        method = scope.get("method", "?")
        path = scope.get("path", "/")

        response_status = 500

        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message.get("status", 500)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            response_status = 500
            raise
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

            # Log slow requests at WARNING level
            actual_level = logging.WARNING if elapsed_ms > 1000 else self.log_level

            self.logger.log(
                actual_level,
                "%s %s %s %sms",
                method,
                path,
                response_status,
                elapsed_ms,
            )

            # Add headers to response
            clear_context()
