"""
Task CRUD API integration tests.
"""

from datetime import UTC
from datetime import datetime
from datetime import timedelta

import pytest

from app.models.db.project import Project
from app.models.db.task import Task
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository

TASKS_URL = "/api/v1/tasks"


@pytest.fixture
def task_repository() -> TaskRepository:
    """Shared repository instance for database assertions."""
    return TaskRepository()


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


def _persist_task(
    db_session,
    *,
    project_id: int,
    title: str,
    description: str | None = None,
    status: str = "pending",
    priority: str = "medium",
    created_at: datetime | None = None,
) -> Task:
    """Insert a task directly for test setup."""
    timestamp = created_at or datetime.now(UTC)
    task = Task(
        project_id=project_id,
        title=title,
        description=description,
        status=status,
        priority=priority,
        created_at=timestamp,
        updated_at=timestamp,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def seed_project(db_session) -> Project:
    """Seed a project used for task creation tests."""
    return _persist_project(
        db_session,
        name="Test Project",
        description="Project for task tests",
    )


def test_get_all_tasks_returns_ordered_list(
    client,
    db_session,
    task_repository,
    seed_project,
):
    """GET /api/v1/tasks returns count, items, and created_at descending order."""
    oldest = _persist_task(
        db_session,
        project_id=seed_project.id,
        title="Oldest Task",
        created_at=datetime.now(UTC) - timedelta(hours=2),
    )
    middle = _persist_task(
        db_session,
        project_id=seed_project.id,
        title="Middle Task",
        created_at=datetime.now(UTC) - timedelta(hours=1),
    )
    newest = _persist_task(
        db_session,
        project_id=seed_project.id,
        title="Newest Task",
        created_at=datetime.now(UTC),
    )

    response = client.get(TASKS_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 3
    assert len(payload["items"]) == 3
    assert [item["id"] for item in payload["items"]] == [
        newest.id,
        middle.id,
        oldest.id,
    ]
    assert task_repository.get_count(db_session) == 3


def test_get_task_by_id_returns_existing_task(
    client,
    db_session,
    task_repository,
    seed_project,
):
    """GET /api/v1/tasks/{id} returns 200 for an existing task."""
    task = _persist_task(
        db_session,
        project_id=seed_project.id,
        title="Lookup Task",
        description="Fetch by identifier",
        status="in_progress",
        priority="high",
    )

    response = client.get(f"{TASKS_URL}/{task.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == task.id
    assert payload["project_id"] == seed_project.id
    assert payload["title"] == "Lookup Task"
    assert payload["description"] == "Fetch by identifier"
    assert payload["status"] == "in_progress"
    assert payload["priority"] == "high"
    assert task_repository.get_by_id(db_session, task.id) is not None


def test_get_task_by_id_returns_404_when_missing(
    client,
    db_session,
    task_repository,
):
    """GET /api/v1/tasks/{id} returns 404 when the task does not exist."""
    response = client.get(f"{TASKS_URL}/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}
    assert task_repository.get_by_id(db_session, 99999) is None


def test_create_task_returns_201_and_persists(
    client,
    db_session,
    task_repository,
    seed_project,
):
    """POST /api/v1/tasks returns 201 and stores the task in the database."""
    payload = {
        "project_id": seed_project.id,
        "title": "New Integration Task",
        "description": "Created for API integration tests",
        "status": "pending",
        "priority": "medium",
    }
    response = client.post(TASKS_URL, json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["project_id"] == seed_project.id
    assert body["title"] == "New Integration Task"
    assert body["description"] == "Created for API integration tests"
    assert body["status"] == "pending"
    assert body["priority"] == "medium"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body

    stored = task_repository.get_by_id(db_session, body["id"])
    assert stored is not None
    assert stored.project_id == seed_project.id
    assert stored.title == "New Integration Task"
    assert stored.description == "Created for API integration tests"
    assert stored.status == "pending"
    assert stored.priority == "medium"


def test_create_duplicate_task_returns_409(
    client,
    db_session,
    task_repository,
    seed_project,
):
    """POST /api/v1/tasks returns 409 when the task title already exists in the project."""
    first = client.post(
        TASKS_URL,
        json={
            "project_id": seed_project.id,
            "title": "Duplicate Task",
        },
    )
    assert first.status_code == 201

    response = client.post(
        TASKS_URL,
        json={
            "project_id": seed_project.id,
            "title": "duplicate task",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Task already exists"}
    assert task_repository.get_count(db_session) == 1


def test_create_task_with_missing_project_returns_404(
    client,
    db_session,
    task_repository,
):
    """POST /api/v1/tasks returns 404 when the project does not exist."""
    response = client.post(
        TASKS_URL,
        json={
            "project_id": 99999,
            "title": "Orphan Task",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
    assert task_repository.get_count(db_session) == 0


def test_update_task_returns_200_and_persists_changes(
    client,
    db_session,
    task_repository,
    seed_project,
):
    """PUT /api/v1/tasks/{id} returns 200 and updates the database record."""
    task = _persist_task(
        db_session,
        project_id=seed_project.id,
        title="Original Title",
        description="Original description",
        status="pending",
        priority="low",
    )
    update_payload = {
        "title": "Updated Title",
        "description": "Updated description",
        "status": "completed",
        "priority": "high",
    }

    response = client.put(f"{TASKS_URL}/{task.id}", json=update_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == task.id
    assert body["title"] == "Updated Title"
    assert body["description"] == "Updated description"
    assert body["status"] == "completed"
    assert body["priority"] == "high"

    stored = task_repository.get_by_id(db_session, task.id)
    assert stored is not None
    assert stored.title == "Updated Title"
    assert stored.description == "Updated description"
    assert stored.status == "completed"
    assert stored.priority == "high"


def test_update_missing_task_returns_404(
    client,
    db_session,
    task_repository,
):
    """PUT /api/v1/tasks/{id} returns 404 when the task does not exist."""
    response = client.put(
        f"{TASKS_URL}/99999",
        json={"title": "Missing Task"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}
    assert task_repository.get_by_id(db_session, 99999) is None


def test_update_task_duplicate_title_returns_409(
    client,
    db_session,
    task_repository,
    seed_project,
):
    """PUT /api/v1/tasks/{id} returns 409 when renaming to an existing title in the same project."""
    first = _persist_task(
        db_session,
        project_id=seed_project.id,
        title="First Task",
    )
    second = _persist_task(
        db_session,
        project_id=seed_project.id,
        title="Second Task",
    )

    response = client.put(
        f"{TASKS_URL}/{first.id}",
        json={"title": second.title},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Task already exists"}

    stored = task_repository.get_by_id(db_session, first.id)
    assert stored is not None
    assert stored.title == "First Task"


def test_delete_task_returns_204_and_removes_record(
    client,
    db_session,
    task_repository,
    seed_project,
):
    """DELETE /api/v1/tasks/{id} returns 204 and removes the task."""
    task = _persist_task(
        db_session,
        project_id=seed_project.id,
        title="Task To Delete",
    )

    response = client.delete(f"{TASKS_URL}/{task.id}")

    assert response.status_code == 204
    assert response.content == b""
    assert task_repository.get_by_id(db_session, task.id) is None
    assert task_repository.get_count(db_session) == 0


def test_delete_missing_task_returns_404(
    client,
    db_session,
    task_repository,
):
    """DELETE /api/v1/tasks/{id} returns 404 when the task does not exist."""
    response = client.delete(f"{TASKS_URL}/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}
    assert task_repository.get_by_id(db_session, 99999) is None
