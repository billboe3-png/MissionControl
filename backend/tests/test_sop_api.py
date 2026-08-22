from fastapi.testclient import TestClient
from app.main import app

class _FakeUser:
    id=1
    email="test@test.local"
    display_name="Test User"
    role="global_admin"
    company_id=None
    site_id=None
    enabled=True

def _make_client():
    from app.core.auth_dependency import get_current_user
    from app.db.database import Base, SessionLocal, engine
    from app.db import get_db
    client = TestClient(app)
    client.app.dependency_overrides[get_current_user] = lambda: _FakeUser()
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    client.app.dependency_overrides[get_db] = override_get_db
    return client

def test_create_sop_returns_draft():
    client = _make_client()
    payload = {"title":"Test SOP","description":"Automated test SOP","status":"draft"}
    response = client.post("/api/v1/sops", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["status"] == "draft"

def test_list_sops_returns_items():
    client = _make_client()
    client.post("/api/v1/sops", json={"title":"List Test","status":"draft"})
    response = client.get("/api/v1/sops")
    assert response.status_code == 200
    assert response.json()["count"] >= 1

def test_update_sop_fields():
    client = _make_client()
    created = client.post("/api/v1/sops", json={"title":"Before","status":"draft"}).json()
    response = client.put(f"/api/v1/sops/{created['id']}", json={"title":"After","status":"draft"})
    assert response.status_code == 200, response.text
    assert response.json()["title"] == "After"

def test_delete_sop():
    client = _make_client()
    created = client.post("/api/v1/sops", json={"title":"Delete Me","status":"draft"}).json()
    response = client.delete(f"/api/v1/sops/{created['id']}")
    assert response.status_code == 204

def test_search_sops():
    client = _make_client()
    client.post("/api/v1/sops", json={"title":"UniqueSearchable","status":"draft"})
    response = client.get("/api/v1/sops/search", params={"q":"UniqueSearchable"})
    assert response.status_code == 200
    assert response.json()["count"] >= 1

def test_version_history():
    client = _make_client()
    created = client.post("/api/v1/sops", json={"title":"Versioned","status":"draft"}).json()
    client.put(f"/api/v1/sops/{created['id']}", json={"title":"Versioned v2","status":"draft"})
    response = client.get(f"/api/v1/sops/{created['id']}/versions")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_approval_workflow():
    client = _make_client()
    created = client.post("/api/v1/sops", json={"title":"Approval","status":"pending_approval"}).json()
    approve = client.post(f"/api/v1/sops/{created['id']}/approve", json={"comments":"LGTM"}).json()
    assert approve["status"] == "approved"
