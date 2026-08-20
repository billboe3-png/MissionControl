"""
Mission Control Agent Active Directory Provider Tests

Validates response shapes produced by AgentActiveDirectoryProvider match
the Pydantic response schemas (ADSummaryResponse, ADUsersResponse,
ADGroupsResponse, ADDevicesResponse, ADHealthResponse) and that write
operations dispatch correctly.
"""

import pytest

from app.providers.identity.agent_ad_provider import AgentActiveDirectoryProvider


@pytest.fixture()
def provider() -> AgentActiveDirectoryProvider:
    inv = {
        "domain": {"name": "kg.local", "base_dn": "DC=kg,DC=local"},
        "users": [
            {
                "sam_account_name": "admin",
                "display_name": "Admin User",
                "enabled": True,
            }
        ],
        "groups": [{"name": "Domain Admins", "description": "Admins"}],
        "devices": [
            {"name": "CORHQDC01", "dns_name": "CORHQDC01.kg.local"}
        ],
        "health": {
            "status": "healthy",
            "replication": {
                "status": "healthy",
                "pending_replications": 0,
                "failed_replications": 0,
            },
        },
    }
    return AgentActiveDirectoryProvider(inventory=inv, hostname="CORHQROBERTB")


@pytest.mark.anyio()
async def test_agent_ad_provider_shapes(
    provider: AgentActiveDirectoryProvider,
) -> None:
    summary = await provider.get_summary()
    assert summary["connected"] is True
    assert summary["domain"]["name"] == "kg.local"
    assert summary["user_count"] == 1

    users = await provider.get_users()
    assert users["connected"] is True
    assert len(users["users"]) == 1
    assert users["total_count"] == 1
    assert users["users"][0]["sam_account_name"] == "admin"

    groups = await provider.get_groups()
    assert groups["connected"] is True
    assert len(groups["groups"]) == 1
    assert groups["groups"][0]["name"] == "Domain Admins"

    devices = await provider.get_devices()
    assert devices["connected"] is True
    assert len(devices["devices"]) == 1
    assert devices["devices"][0]["name"] == "CORHQDC01"

    health = await provider.get_health()
    assert health["connected"] is True
    assert health["status"] == "healthy"
    assert health["replication"]["status"] == "healthy"


@pytest.mark.anyio()
async def test_agent_ad_provider_write_ops_require_db():
    provider = AgentActiveDirectoryProvider(inventory={}, hostname="agent")
    result = await provider.reset_password("admin", "NewPass123!")
    assert result["success"] is False
    assert "No DB or agent_id" in result["error"]


@pytest.mark.anyio()
async def test_agent_ad_provider_get_user_groups_shape():
    provider = AgentActiveDirectoryProvider(inventory={}, hostname="agent")
    result = await provider.get_user_groups("admin")
    assert result["connected"] is False
    assert result["groups"] == []
    assert result["error"] is not None