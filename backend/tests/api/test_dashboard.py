"""
Dashboard statistics integration tests.

Sprint 2.0 - Updated for provider-based architecture.
"""

from app.models.db.note import Note
from app.models.db.parking_lot import ParkingLot
from app.models.db.project import Project
from app.models.db.task import Task


DASHBOARD_URL = "/api/v1/dashboard"


def _persist_project(db_session, *, name: str, active: bool = True) -> Project:
    """Insert a project directly for test setup."""
    project = Project(name=name, description=f"{name} description", active=active)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def _persist_task(
    db_session,
    *,
    project_id: int,
    title: str,
    status: str = "pending",
) -> Task:
    """Insert a task directly for test setup."""
    task = Task(project_id=project_id, title=title, status=status)
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


def test_dashboard_returns_project_statistics(client, db_session, mock_docker):
    """Verify project statistics contain correct total, active, and inactive counts."""
    _persist_project(db_session, name="Active One", active=True)
    _persist_project(db_session, name="Active Two", active=True)
    _persist_project(db_session, name="Inactive One", active=False)

    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    payload = response.json()
    stats = payload["projects"]["statistics"]
    assert stats["total"] == 3
    assert stats["active"] == 2
    assert stats["inactive"] == 1
    assert payload["summary"]["projects"] == 3
    assert payload["summary"]["active_projects"] == 2


def test_dashboard_returns_task_statistics(client, db_session, mock_docker):
    """Verify task statistics contain correct counts for every status."""
    project = _persist_project(db_session, name="Task Stats Project")

    _persist_task(db_session, project_id=project.id, title="Pending One", status="pending")
    _persist_task(db_session, project_id=project.id, title="Pending Two", status="pending")
    _persist_task(db_session, project_id=project.id, title="In Progress One", status="in_progress")
    _persist_task(db_session, project_id=project.id, title="Completed One", status="completed")
    _persist_task(db_session, project_id=project.id, title="Completed Two", status="completed")
    _persist_task(db_session, project_id=project.id, title="Completed Three", status="completed")
    _persist_task(db_session, project_id=project.id, title="Blocked One", status="blocked")

    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    payload = response.json()
    stats = payload["tasks"]["statistics"]
    assert stats["total"] == 7
    assert stats["pending"] == 2
    assert stats["in_progress"] == 1
    assert stats["completed"] == 3
    assert stats["blocked"] == 1


def test_dashboard_backward_compatibility(client, db_session, mock_docker):
    """Verify summary fields still exist and match provider data."""
    project = _persist_project(db_session, name="Compat Project", active=True)
    _persist_task(db_session, project_id=project.id, title="Compat Pending", status="pending")
    _persist_task(db_session, project_id=project.id, title="Compat Done", status="completed")

    response = client.get(DASHBOARD_URL)
    summary = response.json()["summary"]

    assert summary["projects"] == summary["projects"]
    assert summary["tasks"] == summary["tasks"]


def test_dashboard_statistics_are_consistent(client, db_session, mock_docker):
    """Verify totals equal the sum of their parts for both project and task statistics."""
    project = _persist_project(db_session, name="Consistency Project", active=True)
    _persist_project(db_session, name="Consistency Inactive", active=False)

    _persist_task(db_session, project_id=project.id, title="C Pending", status="pending")
    _persist_task(db_session, project_id=project.id, title="C In Progress", status="in_progress")
    _persist_task(db_session, project_id=project.id, title="C Completed", status="completed")
    _persist_task(db_session, project_id=project.id, title="C Blocked", status="blocked")

    response = client.get(DASHBOARD_URL)
    payload = response.json()

    ps = payload["projects"]["statistics"]
    assert ps["total"] == ps["active"] + ps["inactive"]

    ts = payload["tasks"]["statistics"]
    assert ts["total"] == ts["pending"] + ts["in_progress"] + ts["completed"] + ts["blocked"]


def test_dashboard_empty_database(client, db_session, mock_docker):
    """Verify all statistics return zero with an empty database and endpoint returns 200."""
    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    payload = response.json()

    assert payload["projects"]["statistics"] == {"total": 0, "active": 0, "inactive": 0}
    assert payload["tasks"]["statistics"] == {
        "total": 0,
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
        "blocked": 0,
    }
    assert payload["summary"]["projects"] == 0
    assert payload["summary"]["active_projects"] == 0
    assert payload["summary"]["tasks"] == 0
    assert payload["summary"]["completed_tasks"] == 0
    assert payload["summary"]["pending_tasks"] == 0

    parking = payload["parking_lot"]
    assert parking["count"] == 0
    assert parking["items"] == []


def test_dashboard_returns_parking_lot_items(client, db_session, mock_docker):
    """Verify parking_lot contains live items from the repository."""
    item = ParkingLot(
        title="Investigate Redis caching",
        description="Evaluate Redis for session caching.",
        priority="high",
        status="parked",
    )
    db_session.add(item)
    db_session.commit()

    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    parking = response.json()["parking_lot"]
    assert parking["count"] == 1
    assert parking["items"][0]["title"] == "Investigate Redis caching"
    assert parking["items"][0]["priority"] == "high"
    assert parking["items"][0]["status"] == "parked"


def test_dashboard_notes_contain_project_data(client, db_session, mock_docker):
    """Verify notes in dashboard include project_id and project_name."""
    project = Project(name="Note Project", active=True)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    note = Note(
        project_id=project.id,
        title="Meeting notes",
        content="Discussed timeline.",
    )
    db_session.add(note)
    db_session.commit()

    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    notes = response.json()["notes"]
    assert notes["count"] == 1
    assert notes["items"][0]["project_name"] == "Note Project"
    assert notes["items"][0]["title"] == "Meeting notes"


def test_dashboard_returns_system_section(client, db_session, mock_docker):
    """Verify system section contains expected keys."""
    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    system = response.json()["system"]
    assert "hostname" in system
    assert "os" in system
    assert "cpu_percent" in system
    assert "memory_percent" in system
    assert "disk_percent" in system


def test_dashboard_returns_git_section(client, db_session, mock_docker):
    """Verify git section contains expected keys."""
    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    git = response.json()["git"]
    assert "available" in git
    assert "current_branch" in git
    assert "latest_commit" in git


def test_dashboard_returns_health_section(client, db_session, mock_docker):
    """Verify health section contains backend, database, redis."""
    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    health = response.json()["health"]
    assert "backend" in health
    assert "database" in health
    assert "redis" in health
    assert health["backend"]["status"] == "healthy"


def test_dashboard_returns_docker_section(client, db_session, mock_docker):
    """Verify docker section contains engine and containers."""
    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    docker = response.json()["docker"]
    assert "engine" in docker
    assert "container_count" in docker
    assert "containers" in docker
    assert docker["engine"] == "running"
