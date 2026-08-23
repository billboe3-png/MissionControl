"""
Mission Control Rate Limiter Tests

Verifies that authenticated traffic is keyed per-user (not per shared proxy
IP) so normal page loads never lock every logged-in user out with 429s, while
login stays rate-limited per account.
"""

import starlette.responses
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.routing import Route

from app.main import RateLimitMiddleware
from app.services.auth_service import create_access_token


def _make_client(monkeypatch, default=2, auth=1, authenticated=3):
    """Build a small app with a RateLimitMiddleware using tiny budgets."""
    monkeypatch.setattr("app.main._TESTING", False)

    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        default_limit=default,
        auth_limit=auth,
        authenticated_limit=authenticated,
        window=60,
    )

    async def ping(_):
        return starlette.responses.JSONResponse({"ok": True})

    async def fake_login(_):
        return starlette.responses.JSONResponse({"ok": True})

    app.router.routes = [
        Route("/api/v1/ping", ping),
        Route("/api/v1/auth/login", fake_login, methods=["POST"]),
    ]
    return TestClient(app)


def test_anonymous_traffic_rate_limited_per_ip(monkeypatch) -> None:
    client = _make_client(monkeypatch, default=2)
    assert client.get("/api/v1/ping").status_code == 200
    assert client.get("/api/v1/ping").status_code == 200
    assert client.get("/api/v1/ping").status_code == 429


def test_authenticated_traffic_not_blocked_by_shared_ip(monkeypatch) -> None:
    client = _make_client(monkeypatch)
    token_a = create_access_token(user_id=1, company_id=None, site_id=None, role="operator")
    token_b = create_access_token(user_id=2, company_id=None, site_id=None, role="operator")

    # User A burns their own budget (limit 3/min)…
    for _ in range(3):
        response = client.get(
            "/api/v1/ping",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert response.status_code == 200
    assert (
        client.get(
            "/api/v1/ping",
            headers={"Authorization": f"Bearer {token_a}"},
        ).status_code
        == 429
    )

    # …but User B behind the same IP is unaffected.
    response = client.get(
        "/api/v1/ping",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 200


def test_login_rate_limited_per_account(monkeypatch) -> None:
    client = _make_client(monkeypatch, auth=1)
    login_a = {"email": "a@example.com", "password": "x"}
    login_b = {"email": "b@example.com", "password": "x"}

    assert client.post("/api/v1/auth/login", json=login_a).status_code == 200
    assert client.post("/api/v1/auth/login", json=login_a).status_code == 429
    # A different account keeps its own budget.
    assert client.post("/api/v1/auth/login", json=login_b).status_code == 200


def test_auth_identity_keys_per_user(monkeypatch) -> None:
    token = create_access_token(
        user_id=42, company_id=None, site_id=None, role="operator"
    )
    middleware = RateLimitMiddleware.__new__(RateLimitMiddleware)

    assert middleware._auth_identity(_req({"authorization": f"Bearer {token}"})) == "user:42"
    assert middleware._auth_identity(_req({})) is None
    assert (
        middleware._auth_identity(_req({"authorization": "Bearer garbage-token"})) is None
    )


def _req(headers: dict[str, str]):
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/ping",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)