"""
Plugin Marketplace API Tests

Tests for the /api/v1/plugins/marketplace endpoints.
"""

from fastapi.testclient import TestClient


class TestMarketplaceCatalog:
    """Tests for marketplace catalog endpoint."""

    def test_catalog_returns_entries(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/marketplace/catalog")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        assert len(data["items"]) > 0

    def test_catalog_has_required_fields(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/marketplace/catalog")
        items = response.json()["items"]
        for item in items:
            assert "slug" in item
            assert "name" in item
            assert "version" in item
            assert "execution_target" in item
            assert "installed" in item
            assert isinstance(item["installed"], bool)

    def test_catalog_filter_by_target(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/plugins/marketplace/catalog?execution_target=server"
        )
        assert response.status_code == 200
        items = response.json()["items"]
        for item in items:
            assert item["execution_target"] == "server"

    def test_catalog_filter_by_category(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/plugins/marketplace/catalog?category=monitoring"
        )
        assert response.status_code == 200
        items = response.json()["items"]
        for item in items:
            assert item["category"] == "monitoring"

    def test_catalog_shows_installed_status(self, client: TestClient) -> None:
        client.post(
            "/api/v1/plugins",
            json={
                "slug": "zabbix",
                "name": "Zabbix Monitoring",
                "version": "1.0.0",
                "execution_target": "server",
            },
        )

        response = client.get("/api/v1/plugins/marketplace/catalog")
        items = response.json()["items"]
        zabbix = next((i for i in items if i["slug"] == "zabbix"), None)
        assert zabbix is not None
        assert zabbix["installed"] is True


class TestMarketplaceCategories:
    """Tests for marketplace categories endpoint."""

    def test_categories_returns_list(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) > 0

    def test_categories_are_strings(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/marketplace/categories")
        cats = response.json()["categories"]
        for cat in cats:
            assert isinstance(cat, str)


class TestMarketplacePluginInfo:
    """Tests for individual marketplace plugin info."""

    def test_get_known_plugin(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/marketplace/zabbix")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "zabbix"
        assert data["execution_target"] == "server"

    def test_get_unknown_plugin(self, client: TestClient) -> None:
        response = client.get("/api/v1/plugins/marketplace/nonexistent")
        assert response.status_code == 404
