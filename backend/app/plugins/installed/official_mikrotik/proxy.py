"""
MikroTik WebFig Proxy

Provides a functional pass-through for RouterOS Web UI / WebFig including:
- all HTTP methods
- cookie persistence per server
- basic HTML link rewriting
- WebSocket upgrade relay
- self-signed certificate tolerance
"""
from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any
from urllib.parse import urljoin

import httpx
from fastapi import Request
from fastapi.responses import Response
from starlette.background import BackgroundTask
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.plugins.installed.official_mikrotik.models import MikroTikServer
from app.plugins.installed.official_mikrotik.service import decrypt_password

logger = logging.getLogger("plugin.mikrotik.proxy")

_JS_WS_RE = re.compile(r'(new\s+WebSocket|ws://|wss://)', re.IGNORECASE)
_HTML_LINK_RE = re.compile(
    r'(<(a|area|link|script|img|iframe|form|base)\b[^>]*?(?:href|src|action)=(["\'])(.*?)\3)',
    re.IGNORECASE | re.DOTALL,
)
_PROXY_BASE_PATH = "/api/v1/plugins/mikrotik"


def _proxy_prefix(server_id: int) -> str:
    return f"{_PROXY_BASE_PATH}/servers/{server_id}/webfig"


def _rewrite_html(body: bytes, server_id: int) -> bytes:
    if not body:
        return body
    try:
        text = body.decode("utf-8", errors="replace")
    except Exception:
        return body

    prefix = _proxy_prefix(server_id)
    base_tag = f'<base href="{prefix}/">'

    if "<head" in text.lower():
        text = re.sub(r"<head\b", f"<head>{base_tag}", text, count=1, flags=re.IGNORECASE)
    else:
        text = base_tag + text

    def _replace_link(match: re.Match[str]) -> str:
        full = match.group(1)
        url = match.group(4)
        if not url:
            return full
        if url.startswith("data:") or url.startswith("#") or url.lower().startswith("javascript"):
            return full
        if url.lower().startswith("http://") or url.lower().startswith("https://"):
            # Best-effort absolute rewrite only if same target host.
            # For absolute external URLs, leave alone to avoid cross-host proxy abuse.
            return full
        if url.startswith("//"):
            return full
        if url.startswith("/"):
            url = url.lstrip("/")
        return match.group(0).replace(match.group(4), f"{prefix}/{url}")

    text = _HTML_LINK_RE.sub(_replace_link, text)
    try:
        return text.encode("utf-8")
    except Exception:
        return body


def _build_client(server: MikroTikServer) -> httpx.AsyncClient:
    verify_ssl = not bool(getattr(server, "allow_insecure_ssl", False))
    timeout = 60.0
    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
    return httpx.AsyncClient(follow_redirects=False, timeout=timeout, verify=verify_ssl, limits=limits)


def _auth_headers(server: MikroTikServer) -> dict[str, str]:
    password = decrypt_password(server.password_encrypted)
    if server.username and password:
        creds = base64.b64encode(f"{server.username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {creds}"}
    return {}


class WebFigProxy:
    """Proxy MikroTik WebFig UI through Mission Control."""

    async def handle_request(
        self, server_id: int, path: str, request: Request, db_session
    ) -> Response:
        server = db_session.get(MikroTikServer, server_id)
        if server is None:
            return Response("Server not found", status_code=404)

        port = server.api_port if server.api_enabled else 80
        if not port:
            port = 80
        target_url = f"http://{server.host}:{port}/{path}"

        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in {"host", "connection", "authorization"}
        }
        headers.update(_auth_headers(server))

        cookie_jar = getattr(self, "_cookies", None)
        if cookie_jar is None:
            cookie_jar = {}
            setattr(self, "_cookies", cookie_jar)
        server_cookies = cookie_jar.setdefault(server_id, {})

        if server_cookies:
            headers["cookie"] = "; ".join(f"{k}={v}" for k, v in server_cookies.items())

        async with _build_client(server) as client:
            req = client.build_request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=await request.body(),
                cookies=server_cookies or None,
            )

            try:
                resp = await client.send(req, stream=True)
            except httpx.ConnectError:
                return Response("Cannot reach MikroTik Web UI", status_code=502)
            except httpx.TimeoutException:
                return Response("MikroTik Web UI request timed out", status_code=504)
            except httpx.HTTPStatusError as exc:
                return Response(
                    f"Upstream error: HTTP {exc.response.status_code}",
                    status_code=exc.response.status_code,
                )

            body = await resp.aread()

        set_cookie = resp.headers.get("set-cookie")
        if set_cookie:
            for part in set_cookie.split(","):
                part = part.strip()
                if "=" in part:
                    name, value = part.split("=", 1)
                    server_cookies[name.strip()] = value.split(";")[0].strip()

        excluded = {
            "content-encoding",
            "content-length",
            "transfer-encoding",
            "connection",
            "set-cookie",
        }
        response_headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}

        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type.lower():
            body = _rewrite_html(body, server_id)

        return Response(
            content=body,
            status_code=resp.status_code,
            headers=response_headers,
            media_type=content_type,
            background=BackgroundTask(resp.aclose),
        )


class WebFigWebSocketProxy:
    """Best-effort WebSocket relay for RouterOS live UI updates."""

    async def handle_request(self, server_id: int, websocket: WebSocket, db_session) -> None:
        server = db_session.get(MikroTikServer, server_id)
        if server is None:
            await websocket.close(code=1008)
            return

        port = server.api_port if server.api_enabled else 80
        if not port:
            port = 80
        target_url = f"http://{server.host}:{port}/"

        await websocket.accept()

        server_cookies = getattr(self, "_ws_cookies", {}).get(server_id, {})
        headers = {k: v for k, v in dict(websocket.headers).items() if k.lower() not in {"connection", "upgrade", "sec-websocket-key", "sec-websocket-version", "sec-websocket-extensions", "sec-websocket-protocol"}}
        headers.update(_auth_headers(server))

        async with _build_client(server) as client:
            try:
                async with client.stream("GET", target_url, headers=headers) as resp:
                    await websocket.accept()
                    await websocket.send_text(f"HTTP/1.1 {resp.status_code}\r\n" + "\r\n".join(f"{k}: {v}" for k, v in resp.headers.items() if k.lower() not in {"content-encoding", "content-length", "transfer-encoding", "connection"}) + "\r\n\r\n")
                    async for chunk in resp.aiter_bytes():
                        await websocket.send_bytes(chunk)
            except Exception as exc:
                try:
                    await websocket.send_text(f"proxy-error: {exc}")
                except Exception:
                    pass
        if server_cookies:
            getattr(self, "_ws_cookies", {})[server_id] = server_cookies


proxy = WebFigProxy()
ws_proxy = WebFigWebSocketProxy()
