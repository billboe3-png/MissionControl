"""
Note CRUD API integration tests.
"""

from datetime import UTC
from datetime import datetime
from datetime import timedelta

import pytest

from app.models.db.project import Project
from app.models.db.note import Note
from app.repositories.note_repository import NoteRepository
from app.repositories.project_repository import ProjectRepository

NOTES_URL = "/api/v1/notes"


@pytest.fixture
def note_repository() -> NoteRepository:
    """Shared repository instance for database assertions."""
    return NoteRepository()


@pytest.fixture
def project_repository() -> ProjectRepository:
    """Shared repository instance for database assertions."""
    return ProjectRepository()


def _persist_project(
    db_session,
    *,
    name: str,
    description: str | None = None,
    active: bool = True,
) -> Project:
    """Insert a project directly for test setup."""
    project = Project(
        name=name,
        description=description,
        active=active,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def _persist_note(
    db_session,
    *,
    project_id: int,
    title: str,
    content: str,
    created_at: datetime | None = None,
) -> Note:
    """Insert a note directly for test setup."""
    timestamp = created_at or datetime.now(UTC)
    note = Note(
        project_id=project_id,
        title=title,
        content=content,
        created_at=timestamp,
        updated_at=timestamp,
    )
    db_session.add(note)
    db_session.commit()
    db_session.refresh(note)
    return note


@pytest.fixture
def seed_project(db_session) -> Project:
    """Seed a project used for note creation tests."""
    return _persist_project(
        db_session,
        name="Test Project",
        description="Project for note tests",
    )


# ---------------------------------------------------------------------------
# GET /api/v1/notes
# ---------------------------------------------------------------------------


def test_get_all_notes_returns_ordered_list(
    client,
    db_session,
    note_repository,
    seed_project,
):
    """GET /api/v1/notes returns count, items, and created_at descending order."""
    oldest = _persist_note(
        db_session,
        project_id=seed_project.id,
        title="Oldest Note",
        content="Oldest content",
        created_at=datetime.now(UTC) - timedelta(hours=2),
    )
    middle = _persist_note(
        db_session,
        project_id=seed_project.id,
        title="Middle Note",
        content="Middle content",
        created_at=datetime.now(UTC) - timedelta(hours=1),
    )
    newest = _persist_note(
        db_session,
        project_id=seed_project.id,
        title="Newest Note",
        content="Newest content",
        created_at=datetime.now(UTC),
    )

    response = client.get(NOTES_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 3
    assert len(payload["items"]) == 3
    assert [item["id"] for item in payload["items"]] == [
        newest.id,
        middle.id,
        oldest.id,
    ]
    assert note_repository.get_count(db_session) == 3


# ---------------------------------------------------------------------------
# GET /api/v1/notes/{id}
# ---------------------------------------------------------------------------


def test_get_note_by_id_returns_existing_note(
    client,
    db_session,
    note_repository,
    seed_project,
):
    """GET /api/v1/notes/{id} returns 200 for an existing note."""
    note = _persist_note(
        db_session,
        project_id=seed_project.id,
        title="Lookup Note",
        content="Fetch by identifier",
    )

    response = client.get(f"{NOTES_URL}/{note.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == note.id
    assert payload["title"] == "Lookup Note"
    assert payload["content"] == "Fetch by identifier"
    assert "created_at" in payload
    assert "updated_at" in payload
    assert note_repository.get_by_id(db_session, note.id) is not None


def test_get_note_by_id_returns_404_when_missing(
    client,
    db_session,
    note_repository,
):
    """GET /api/v1/notes/{id} returns 404 when the note does not exist."""
    response = client.get(f"{NOTES_URL}/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Note not found"}
    assert note_repository.get_by_id(db_session, 99999) is None


# ---------------------------------------------------------------------------
# POST /api/v1/notes
# ---------------------------------------------------------------------------


def test_create_note_returns_201_and_persists(
    client,
    db_session,
    note_repository,
    seed_project,
):
    """POST /api/v1/notes returns 201 and stores the note in the database."""
    payload = {
        "project_id": seed_project.id,
        "title": "New Integration Note",
        "content": "Created for API integration tests",
    }
    response = client.post(NOTES_URL, json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "New Integration Note"
    assert body["content"] == "Created for API integration tests"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body

    stored = note_repository.get_by_id(db_session, body["id"])
    assert stored is not None
    assert stored.title == "New Integration Note"
    assert stored.content == "Created for API integration tests"


def test_create_duplicate_note_returns_409(
    client,
    db_session,
    note_repository,
    seed_project,
):
    """POST /api/v1/notes returns 409 when the note title already exists in the project."""
    first = client.post(
        NOTES_URL,
        json={
            "project_id": seed_project.id,
            "title": "Duplicate Note",
            "content": "First version",
        },
    )
    assert first.status_code == 201

    response = client.post(
        NOTES_URL,
        json={
            "project_id": seed_project.id,
            "title": "duplicate note",
            "content": "Second version",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Note already exists"}
    assert note_repository.get_count(db_session) == 1


def test_create_note_with_missing_project_returns_404(
    client,
    db_session,
    note_repository,
):
    """POST /api/v1/notes returns 404 when the project does not exist."""
    response = client.post(
        NOTES_URL,
        json={
            "project_id": 99999,
            "title": "Orphan Note",
            "content": "No parent project",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
    assert note_repository.get_count(db_session) == 0


# ---------------------------------------------------------------------------
# PUT /api/v1/notes/{id}
# ---------------------------------------------------------------------------


def test_update_note_returns_200_and_persists_changes(
    client,
    db_session,
    note_repository,
    seed_project,
):
    """PUT /api/v1/notes/{id} returns 200 and updates the database record."""
    note = _persist_note(
        db_session,
        project_id=seed_project.id,
        title="Original Title",
        content="Original content",
    )
    update_payload = {
        "title": "Updated Title",
        "content": "Updated content",
    }

    response = client.put(
        f"{NOTES_URL}/{note.id}",
        json=update_payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == note.id
    assert body["title"] == "Updated Title"
    assert body["content"] == "Updated content"

    stored = note_repository.get_by_id(db_session, note.id)
    assert stored is not None
    assert stored.title == "Updated Title"
    assert stored.content == "Updated content"


def test_update_missing_note_returns_404(
    client,
    db_session,
    note_repository,
):
    """PUT /api/v1/notes/{id} returns 404 when the note does not exist."""
    response = client.put(
        f"{NOTES_URL}/99999",
        json={"title": "Missing Note", "content": "Does not matter"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Note not found"}
    assert note_repository.get_by_id(db_session, 99999) is None


def test_update_note_duplicate_title_returns_409(
    client,
    db_session,
    note_repository,
    seed_project,
):
    """PUT /api/v1/notes/{id} returns 409 when renaming to an existing title in the same project."""
    first = _persist_note(
        db_session,
        project_id=seed_project.id,
        title="First Note",
        content="First content",
    )
    second = _persist_note(
        db_session,
        project_id=seed_project.id,
        title="Second Note",
        content="Second content",
    )

    response = client.put(
        f"{NOTES_URL}/{first.id}",
        json={"title": second.title},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Note already exists"}

    stored = note_repository.get_by_id(db_session, first.id)
    assert stored is not None
    assert stored.title == "First Note"


def test_update_note_invalid_project_returns_404(
    client,
    db_session,
    note_repository,
    seed_project,
):
    """PUT /api/v1/notes/{id} returns 404 when the project does not exist."""
    note = _persist_note(
        db_session,
        project_id=seed_project.id,
        title="Existing Note",
        content="Existing content",
    )

    response = client.put(
        f"{NOTES_URL}/{note.id}",
        json={"project_id": 99999},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}


# ---------------------------------------------------------------------------
# DELETE /api/v1/notes/{id}
# ---------------------------------------------------------------------------


def test_delete_note_returns_204_and_removes_record(
    client,
    db_session,
    note_repository,
    seed_project,
):
    """DELETE /api/v1/notes/{id} returns 204 and removes the note."""
    note = _persist_note(
        db_session,
        project_id=seed_project.id,
        title="Note To Delete",
        content="Will be deleted",
    )

    response = client.delete(f"{NOTES_URL}/{note.id}")

    assert response.status_code == 204
    assert response.content == b""
    assert note_repository.get_by_id(db_session, note.id) is None
    assert note_repository.get_count(db_session) == 0


def test_delete_missing_note_returns_404(
    client,
    db_session,
    note_repository,
):
    """DELETE /api/v1/notes/{id} returns 404 when the note does not exist."""
    response = client.delete(f"{NOTES_URL}/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Note not found"}
    assert note_repository.get_by_id(db_session, 99999) is None
