"""
Plugin API Tests

Tests for the /api/v1/plugins endpoints.
"""

from fastapi.testclient import TestClient


class TestPluginCRUD:
    """Tests for plugin CRUD endpoints."""

    def test_list_plugins_empty(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["items"] == []

    def test_register_plugin(self, client: TestClient) -> None:
        payload = {
            "slug": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "execution_target": "server",
            "category": "monitoring",
            "capabilities": ["dashboard_widget", "rest_api"],
            "permissions": ["read:dashboard"],
            "dependencies": [],
        }
        response = client.post("/api/v1/plugins", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["slug"] == "test-plugin"
        assert data["name"] == "Test Plugin"
        assert data["version"] == "1.0.0"
        assert data["execution_target"] == "server"
        assert data["category"] == "monitoring"
        assert data["enabled"] is True
        assert data["status"] == "registered"
        assert data["capabilities"] == ["dashboard_widget", "rest_api"]
        assert data["permissions"] == ["read:dashboard"]

    def test_register_plugin_minimal(self, client: TestClient) -> None:
        payload = {
            "slug": "minimal-plugin",
            "name": "Minimal",
            "version": "0.1.0",
            "execution_target": "agent",
        }
        response = client.post("/api/v1/plugins", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["slug"] == "minimal-plugin"
        assert data["execution_target"] == "agent"
        assert data["capabilities"] == []
        assert data["permissions"] == []

    def test_register_plugin_duplicate_slug(self, client: TestClient) -> None:
        payload = {
            "slug": "dup-plugin",
            "name": "Dup",
            "version": "1.0.0",
            "execution_target": "server",
        }
        response = client.post("/api/v1/plugins", json=payload)
        assert response.status_code == 201

        response = client.post("/api/v1/plugins", json=payload)
        assert response.status_code == 409

    def test_register_plugin_invalid_slug(self, client: TestClient) -> None:
        payload = {
            "slug": "INVALID_SLUG!",
            "name": "Bad",
            "version": "1.0.0",
            "execution_target": "server",
        }
        response = client.post("/api/v1/plugins", json=payload)
        assert response.status_code == 422

    def test_register_plugin_invalid_target(self, client: TestClient) -> None:
        payload = {
            "slug": "bad-target",
            "name": "Bad",
            "version": "1.0.0",
            "execution_target": "invalid",
        }
        response = client.post("/api/v1/plugins", json=payload)
        assert response.status_code == 422

    def test_list_plugins_with_data(self, client: TestClient) -> None:
        for slug, target in [("server-plug", "server"), ("agent-plug", "agent")]:
            client.post(
                "/api/v1/plugins",
                json={
                    "slug": slug,
                    "name": slug.replace("-", " ").title(),
                    "version": "1.0.0",
                    "execution_target": target,
                },
            )

        response = client.get("/api/v1/plugins")
        assert response.status_code == 200
        assert response.json()["count"] == 2

    def test_list_plugins_filter_by_target(self, client: TestClient) -> None:
        for slug, target in [("sv", "server"), ("ag", "agent"), ("sv2", "server")]:
            client.post(
                "/api/v1/plugins",
                json={
                    "slug": slug,
                    "name": slug,
                    "version": "1.0.0",
                    "execution_target": target,
                },
            )

        response = client.get("/api/v1/plugins?execution_target=server")
        assert response.status_code == 200
        assert response.json()["count"] == 2

        response = client.get("/api/v1/plugins?execution_target=agent")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_get_plugin(self, client: TestClient) -> None:
        reg = client.post(
            "/api/v1/plugins",
            json={
                "slug": "get-me",
                "name": "Get Me",
                "version": "1.0.0",
                "execution_target": "hybrid",
            },
        )
        plugin_id = reg.json()["id"]

        response = client.get(f"/api/v1/plugins/{plugin_id}")
        assert response.status_code == 200
        assert response.json()["slug"] == "get-me"

    def test_get_plugin_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/9999")
        assert response.status_code == 404

    def test_get_plugin_by_slug(self, client: TestClient) -> None:
        client.post(
            "/api/v1/plugins",
            json={
                "slug": "find-me",
                "name": "Find Me",
                "version": "1.0.0",
                "execution_target": "server",
            },
        )
        response = client.get("/api/v1/plugins/by-slug/find-me")
        assert response.status_code == 200
        assert response.json()["id"] > 0

    def test_get_plugin_by_slug_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/by-slug/nonexistent")
        assert response.status_code == 404

    def test_update_plugin(self, client: TestClient) -> None:
        reg = client.post(
            "/api/v1/plugins",
            json={
                "slug": "update-me",
                "name": "Original",
                "version": "1.0.0",
                "execution_target": "server",
            },
        )
        plugin_id = reg.json()["id"]

        response = client.put(
            f"/api/v1/plugins/{plugin_id}",
            json={"name": "Updated", "version": "2.0.0", "category": "backup"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["version"] == "2.0.0"
        assert data["category"] == "backup"

    def test_update_plugin_not_found(self, client: TestClient) -> None:
        response = client.put(
            "/api/v1/plugins/9999", json={"name": "X"}
        )
        assert response.status_code == 404

    def test_delete_plugin(self, client: TestClient) -> None:
        reg = client.post(
            "/api/v1/plugins",
            json={
                "slug": "delete-me",
                "name": "Delete",
                "version": "1.0.0",
                "execution_target": "server",
            },
        )
        plugin_id = reg.json()["id"]

        response = client.delete(f"/api/v1/plugins/{plugin_id}")
        assert response.status_code == 204

        response = client.get(f"/api/v1/plugins/{plugin_id}")
        assert response.status_code == 404

    def test_delete_plugin_not_found(self, client: TestClient) -> None:
        response = client.delete("/api/v1/plugins/9999")
        assert response.status_code == 404


class TestPluginLifecycle:
    """Tests for plugin lifecycle endpoints."""

    def test_enable_plugin(self, client: TestClient) -> None:
        reg = client.post(
            "/api/v1/plugins",
            json={
                "slug": "enable-me",
                "name": "Enable",
                "version": "1.0.0",
                "execution_target": "server",
            },
        )
        plugin_id = reg.json()["id"]

        client.post(f"/api/v1/plugins/{plugin_id}/disable")
        response = client.get(f"/api/v1/plugins/{plugin_id}")
        assert response.json()["enabled"] is False

        response = client.post(f"/api/v1/plugins/{plugin_id}/enable")
        assert response.status_code == 200
        assert response.json()["enabled"] is True

    def test_disable_plugin(self, client: TestClient) -> None:
        reg = client.post(
            "/api/v1/plugins",
            json={
                "slug": "disable-me",
                "name": "Disable",
                "version": "1.0.0",
                "execution_target": "server",
            },
        )
        plugin_id = reg.json()["id"]

        response = client.post(f"/api/v1/plugins/{plugin_id}/disable")
        assert response.status_code == 200
        assert response.json()["enabled"] is False

    def test_start_plugin(self, client: TestClient) -> None:
        reg = client.post(
            "/api/v1/plugins",
            json={
                "slug": "start-me",
                "name": "Start",
                "version": "1.0.0",
                "execution_target": "server",
            },
        )
        plugin_id = reg.json()["id"]

        response = client.post(f"/api/v1/plugins/{plugin_id}/start")
        assert response.status_code == 200
        assert response.json()["status"] == "running"

    def test_stop_plugin(self, client: TestClient) -> None:
        reg = client.post(
            "/api/v1/plugins",
            json={
                "slug": "stop-me",
                "name": "Stop",
                "version": "1.0.0",
                "execution_target": "server",
            },
        )
        plugin_id = reg.json()["id"]

        client.post(f"/api/v1/plugins/{plugin_id}/start")
        response = client.post(f"/api/v1/plugins/{plugin_id}/stop")
        assert response.status_code == 200
        assert response.json()["status"] == "stopped"

    def test_start_nonexistent_plugin(self, client: TestClient) -> None:
        response = client.post("/api/v1/plugins/9999/start")
        assert response.status_code == 200
        assert response.json()["status"] == "error"

    def test_stop_nonexistent_plugin(self, client: TestClient) -> None:
        response = client.post("/api/v1/plugins/9999/stop")
        assert response.status_code == 200
        assert response.json()["status"] == "error"


class TestPluginStats:
    """Tests for plugin statistics endpoint."""

    def test_stats_empty(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["enabled"] == 0
        assert data["running"] == 0

    def test_stats_with_plugins(self, client: TestClient) -> None:
        for slug, target in [("s1", "server"), ("s2", "server"), ("a1", "agent")]:
            client.post(
                "/api/v1/plugins",
                json={
                    "slug": slug,
                    "name": slug,
                    "version": "1.0.0",
                    "execution_target": target,
                },
            )

        response = client.get("/api/v1/plugins/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["by_target"]["server"] == 2
        assert data["by_target"]["agent"] == 1


class TestPluginHeartbeat:
    """Tests for plugin heartbeat endpoint."""

    def test_heartbeat(self, client: TestClient) -> None:
        reg = client.post(
            "/api/v1/plugins",
            json={
                "slug": "hb-plugin",
                "name": "HB",
                "version": "1.0.0",
                "execution_target": "agent",
            },
        )
        plugin_id = reg.json()["id"]

        response = client.post(f"/api/v1/plugins/{plugin_id}/heartbeat")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_heartbeat_not_found(self, client: TestClient) -> None:
        response = client.post("/api/v1/plugins/9999/heartbeat")
        assert response.status_code == 404


class TestPluginExecutionTargets:
    """Tests for all three execution target types."""

    def test_register_all_targets(self, client: TestClient) -> None:
        for target in ["server", "agent", "hybrid"]:
            response = client.post(
                "/api/v1/plugins",
                json={
                    "slug": f"target-{target}",
                    "name": f"{target.title()} Plugin",
                    "version": "1.0.0",
                    "execution_target": target,
                },
            )
            assert response.status_code == 201
            assert response.json()["execution_target"] == target

        response = client.get("/api/v1/plugins")
        assert response.json()["count"] == 3


class TestPluginMarketplaceAPI:
    """Tests for marketplace endpoints via the plugin router."""

    def test_marketplace_catalog(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/marketplace/catalog")
        assert response.status_code == 200
        assert response.json()["count"] > 0

    def test_marketplace_categories(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/marketplace/categories")
        assert response.status_code == 200
        assert len(response.json()["categories"]) > 0

    def test_marketplace_plugin_info(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/marketplace/zabbix")
        assert response.status_code == 200
        assert response.json()["slug"] == "zabbix"

    def test_marketplace_plugin_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/marketplace/does-not-exist")
        assert response.status_code == 404
