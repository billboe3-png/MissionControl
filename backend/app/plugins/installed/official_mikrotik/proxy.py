"""
MikroTik WebFig Proxy
"""
import base64
import logging

import httpx
from fastapi import Request
from fastapi.responses import Response

from app.plugins.installed.official_mikrotik.models import MikroTikServer

logger = logging.getLogger("plugin.mikrotik.proxy")


class WebFigProxy:
    """Proxy MikroTik WebFig UI through Mission Control."""

    async def handle_request(
        self, server_id: int, path: str, request: Request, db_session
    ) -> Response:
        server = db_session.get(MikroTikServer, server_id)
        if server is None:
            return Response("Server not found", status_code=404)

        target_url = f"http://{server.host}:{server.webfig_port or 80}/{path}"
        auth_header = None
        if server.username and server.password_encrypted:
            credentials = base64.b64encode(
                f"{server.username}:{server.password_encrypted}".encode()
            ).decode()
            auth_header = f"Basic {credentials}"

        async with httpx.AsyncClient(follow_redirects=False, timeout=60) as client:
            req = client.build_request(
                method=request.method,
                url=target_url,
                headers={
                    key: value
                    for key, value in request.headers.items()
                    if key.lower() not in {"host", "connection"}
                },
                content=await request.body(),
            )
            if auth_header:
                req.headers["Authorization"] = auth_header

            resp = await client.send(req, stream=True)
            body = await resp.aread()

        excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
        headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}
        return Response(
            content=body,
            status_code=resp.status_code,
            headers=headers,
            media_type=resp.headers.get("content-type"),
        )


proxy = WebFigProxy()
