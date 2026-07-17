"""
Project CRUD API integration tests.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.models.db.project import Project
from app.repositories.project_repository import ProjectRepository

PROJECTS_URL = "/api/v1/projects"


@pytest.fixture
def project_repository() -> ProjectRepository:
    """Shared repository instance for database assertions."""
    return ProjectRepository()


@pytest.fixture
def project_create_payload() -> dict:
    """Default POST payload for project creation."""
    return {
        "name": "Integration Test Project",
        "description": "Created for API integration tests",
        "active": True,
    }


def _persist_project(
    db_session,
    *,
    name: str,
    description: str | None = None,
    active: bool = True,
    created_at: datetime | None = None,
) -> Project:
    """Insert a project directly for test setup."""
    timestamp = created_at or datetime.now(UTC)
    project = Project(
        name=name,
        description=description,
        active=active,
        created_at=timestamp,
        updated_at=timestamp,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def test_get_all_projects_returns_ordered_list(client, db_session, project_repository):
    """GET /api/v1/projects returns count, items, and created_at descending order."""
    oldest = _persist_project(
        db_session,
        name="Oldest Project",
        created_at=datetime.now(UTC) - timedelta(hours=2),
    )
    middle = _persist_project(
        db_session,
        name="Middle Project",
        created_at=datetime.now(UTC) - timedelta(hours=1),
    )
    newest = _persist_project(
        db_session,
        name="Newest Project",
        created_at=datetime.now(UTC),
    )

    response = client.get(PROJECTS_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 3
    assert len(payload["items"]) == 3
    assert [item["id"] for item in payload["items"]] == [
        newest.id,
        middle.id,
        oldest.id,
    ]
    assert project_repository.get_count(db_session) == 3


def test_get_project_by_id_returns_existing_project(
    client,
    db_session,
    project_repository,
):
    """GET /api/v1/projects/{id} returns 200 for an existing project."""
    project = _persist_project(
        db_session,
        name="Lookup Project",
        description="Fetch by identifier",
    )

    response = client.get(f"{PROJECTS_URL}/{project.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == project.id
    assert payload["name"] == "Lookup Project"
    assert payload["description"] == "Fetch by identifier"
    assert payload["active"] is True
    assert project_repository.get_by_id(db_session, project.id) is not None


def test_get_project_by_id_returns_404_when_missing(client, db_session, project_repository):
    """GET /api/v1/projects/{id} returns 404 when the project does not exist."""
    response = client.get(f"{PROJECTS_URL}/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
    assert project_repository.get_by_id(db_session, 99999) is None


def test_create_project_returns_201_and_persists(
    client,
    db_session,
    project_repository,
    project_create_payload,
):
    """POST /api/v1/projects returns 201 and stores the project in the database."""
    response = client.post(PROJECTS_URL, json=project_create_payload)

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == project_create_payload["name"]
    assert payload["description"] == project_create_payload["description"]
    assert payload["active"] is True
    assert "id" in payload
    assert "created_at" in payload
    assert "updated_at" in payload

    stored = project_repository.get_by_id(db_session, payload["id"])
    assert stored is not None
    assert stored.name == project_create_payload["name"]
    assert stored.description == project_create_payload["description"]
    assert stored.active is True


def test_create_duplicate_project_returns_409(
    client,
    db_session,
    project_repository,
    project_create_payload,
):
    """POST /api/v1/projects returns 409 when the project name already exists."""
    first = client.post(PROJECTS_URL, json=project_create_payload)
    assert first.status_code == 201

    duplicate_payload = {
        "name": project_create_payload["name"].upper(),
        "description": "Duplicate attempt",
        "active": False,
    }
    response = client.post(PROJECTS_URL, json=duplicate_payload)

    assert response.status_code == 409
    assert response.json() == {"detail": "Project already exists"}
    assert project_repository.get_count(db_session) == 1


def test_update_project_returns_200_and_persists_changes(
    client,
    db_session,
    project_repository,
):
    """PUT /api/v1/projects/{id} returns 200 and updates the database record."""
    project = _persist_project(
        db_session,
        name="Original Name",
        description="Original description",
        active=True,
    )
    update_payload = {
        "name": "Updated Name",
        "description": "Updated description",
        "active": False,
    }

    response = client.put(f"{PROJECTS_URL}/{project.id}", json=update_payload)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == project.id
    assert payload["name"] == "Updated Name"
    assert payload["description"] == "Updated description"
    assert payload["active"] is False

    stored = project_repository.get_by_id(db_session, project.id)
    assert stored is not None
    assert stored.name == "Updated Name"
    assert stored.description == "Updated description"
    assert stored.active is False


def test_update_missing_project_returns_404(client, db_session, project_repository):
    """PUT /api/v1/projects/{id} returns 404 when the project does not exist."""
    response = client.put(
        f"{PROJECTS_URL}/99999",
        json={"name": "Missing Project"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
    assert project_repository.get_by_id(db_session, 99999) is None


def test_update_project_duplicate_name_returns_409(
    client,
    db_session,
    project_repository,
):
    """PUT /api/v1/projects/{id} returns 409 when renaming to an existing name."""
    first = _persist_project(db_session, name="First Project")
    second = _persist_project(db_session, name="Second Project")

    response = client.put(
        f"{PROJECTS_URL}/{first.id}",
        json={"name": second.name},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Project already exists"}

    stored = project_repository.get_by_id(db_session, first.id)
    assert stored is not None
    assert stored.name == "First Project"


def test_delete_project_returns_204_and_removes_record(
    client,
    db_session,
    project_repository,
):
    """DELETE /api/v1/projects/{id} returns 204 and removes the project."""
    project = _persist_project(db_session, name="Project To Delete")

    response = client.delete(f"{PROJECTS_URL}/{project.id}")

    assert response.status_code == 204
    assert response.content == b""
    assert project_repository.get_by_id(db_session, project.id) is None
    assert project_repository.get_count(db_session) == 0


def test_delete_missing_project_returns_404(client, db_session, project_repository):
    """DELETE /api/v1/projects/{id} returns 404 when the project does not exist."""
    response = client.delete(f"{PROJECTS_URL}/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
    assert project_repository.get_by_id(db_session, 99999) is None


@pytest.fixture
def mission_control_project(db_session) -> Project:
    """Seed a project used for duplicate-name validation tests."""
    return _persist_project(
        db_session,
        name="Mission Control",
        description="Existing project for duplicate checks",
    )


@pytest.mark.parametrize(
    "duplicate_name",
    [
        "Mission Control",
        " mission control ",
        "MISSION CONTROL",
    ],
)
def test_create_duplicate_project_rejects_case_and_whitespace_variants(
    client,
    db_session,
    project_repository,
    mission_control_project,
    duplicate_name,
):
    """POST rejects duplicate names regardless of case or surrounding whitespace."""
    response = client.post(
        PROJECTS_URL,
        json={"name": duplicate_name, "description": "Duplicate attempt"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Project already exists"}
    assert project_repository.get_count(db_session) == 1


def test_update_project_description_only_returns_200(
    client,
    db_session,
    project_repository,
    mission_control_project,
):
    """PUT allows updates that do not change the normalized project name."""
    response = client.put(
        f"{PROJECTS_URL}/{mission_control_project.id}",
        json={"description": "Updated description only"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Mission Control"
    assert payload["description"] == "Updated description only"

    stored = project_repository.get_by_id(db_session, mission_control_project.id)
    assert stored is not None
    assert stored.description == "Updated description only"


def test_update_project_rejects_renaming_to_existing_normalized_name(
    client,
    db_session,
    project_repository,
):
    """PUT returns 409 when renaming to another project's normalized name."""
    first = _persist_project(
        db_session,
        name="Mission Control Updated",
        description="First project",
    )
    _persist_project(
        db_session,
        name="Mission Control",
        description="Second project",
    )

    response = client.put(
        f"{PROJECTS_URL}/{first.id}",
        json={"name": "Mission Control"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Project already exists"}

    stored = project_repository.get_by_id(db_session, first.id)
    assert stored is not None
    assert stored.name == "Mission Control Updated"


def test_update_project_allows_case_only_name_change(
    client,
    db_session,
    project_repository,
    mission_control_project,
):
    """PUT allows a case-only rename for the same project."""
    response = client.put(
        f"{PROJECTS_URL}/{mission_control_project.id}",
        json={"name": "mission control"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "mission control"

    stored = project_repository.get_by_id(db_session, mission_control_project.id)
    assert stored is not None
    assert stored.name == "mission control"
    assert project_repository.get_count(db_session) == 1
