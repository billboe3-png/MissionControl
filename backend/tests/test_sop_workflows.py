"""
SOP workflow tests using in-memory SQLite schema.
"""

from fastapi.testclient import TestClient

from app.main import app


def _make_client() -> TestClient:
    client = TestClient(app)
    return client


def test_submit_changes_status():
    client = _make_client()
    created = client.post("/api/v1/sops", json={"title": "Submit", "status": "draft"}).json()
    response = client.post(f"/api/v1/sops/{created['id']}/submit")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "pending_approval"


def test_approve_sop():
    client = _make_client()
    created = client.post("/api/v1/sops", json={"title": "Approve", "status": "pending_approval"}).json()
    response = client.post(f"/api/v1/sops/{created['id']}/approve", json={"comments": "Looks good"})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "approved"


def test_reject_sop():
    client = _make_client()
    created = client.post("/api/v1/sops", json={"title": "Reject", "status": "pending_approval"}).json()
    response = client.post(f"/api/v1/sops/{created['id']}/reject", json={"comments": "Needs revision"})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "rejected"


def test_publish_sop():
    client = _make_client()
    created = client.post("/api/v1/sops", json={"title": "Publish", "status": "approved"}).json()
    response = client.post(f"/api/v1/sops/{created['id']}/publish")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "published"


def test_version_history_after_update():
    client = _make_client()
    created = client.post("/api/v1/sops", json={"title": "History", "status": "draft"}).json()
    client.put(f"/api/v1/sops/{created['id']}", json={"title": "History v2", "status": "draft"})
    response = client.get(f"/api/v1/sops/{created['id']}/versions")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_search_sops():
    client = _make_client()
    client.post("/api/v1/sops", json={"title": "UniqueWorkflowSearch", "status": "draft"})
    response = client.get("/api/v1/sops/search", params={"q": "UniqueWorkflowSearch"})
    assert response.status_code == 200
    assert response.json()["count"] >= 1


def test_ai_review_endpoint():
    client = _make_client()
    created = client.post("/api/v1/sops", json={"title": "AI Review", "status": "draft"}).json()
    response = client.post(f"/api/v1/sops/{created['id']}/ai/review")
    assert response.status_code == 200, response.text
    assert "assessment" in response.json()


def test_ai_query_endpoint():
    client = _make_client()
    response = client.post("/api/v1/sops/query", params={"query": "test"})
    assert response.status_code == 200, response.text
    assert "answer" in response.json()


def test_document_import_creates_sop(tmp_path):
    client = _make_client()
    sample = tmp_path / "sample.txt"
    sample.write_text("Extracted operational knowledge for testing.")
    response = client.post(
        "/api/v1/sops/import",
        json={"file_path": str(sample), "source_name": "sample.txt", "title": "Ingested", "company_id": None, "site_id": None},
    )
    assert response.status_code == 200, response.text
    assert response.json()["sop"]["title"] == "Ingested"
