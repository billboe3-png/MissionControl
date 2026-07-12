"""
Dashboard statistics integration tests.
"""

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
    """Verify project_statistics contains correct total, active, and inactive counts."""
    _persist_project(db_session, name="Active One", active=True)
    _persist_project(db_session, name="Active Two", active=True)
    _persist_project(db_session, name="Inactive One", active=False)

    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    stats = response.json()["summary"]["project_statistics"]
    assert stats["total"] == 3
    assert stats["active"] == 2
    assert stats["inactive"] == 1


def test_dashboard_returns_task_statistics(client, db_session, mock_docker):
    """Verify task_statistics contains correct counts for every status."""
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
    stats = response.json()["summary"]["task_statistics"]
    assert stats["total"] == 7
    assert stats["pending"] == 2
    assert stats["in_progress"] == 1
    assert stats["completed"] == 3
    assert stats["blocked"] == 1


def test_dashboard_backward_compatibility(client, db_session, mock_docker):
    """Verify legacy summary fields still exist and match statistics."""
    project = _persist_project(db_session, name="Compat Project", active=True)
    _persist_task(db_session, project_id=project.id, title="Compat Pending", status="pending")
    _persist_task(db_session, project_id=project.id, title="Compat Done", status="completed")

    response = client.get(DASHBOARD_URL)
    summary = response.json()["summary"]

    assert summary["projects"] == summary["project_statistics"]["total"]
    assert summary["active_projects"] == summary["project_statistics"]["active"]
    assert summary["tasks"] == summary["task_statistics"]["total"]
    assert summary["completed_tasks"] == summary["task_statistics"]["completed"]
    assert summary["pending_tasks"] == summary["task_statistics"]["pending"]


def test_dashboard_statistics_are_consistent(client, db_session, mock_docker):
    """Verify totals equal the sum of their parts for both project and task statistics."""
    project = _persist_project(db_session, name="Consistency Project", active=True)
    _persist_project(db_session, name="Consistency Inactive", active=False)

    _persist_task(db_session, project_id=project.id, title="C Pending", status="pending")
    _persist_task(db_session, project_id=project.id, title="C In Progress", status="in_progress")
    _persist_task(db_session, project_id=project.id, title="C Completed", status="completed")
    _persist_task(db_session, project_id=project.id, title="C Blocked", status="blocked")

    response = client.get(DASHBOARD_URL)
    summary = response.json()["summary"]

    ps = summary["project_statistics"]
    assert ps["total"] == ps["active"] + ps["inactive"]

    ts = summary["task_statistics"]
    assert ts["total"] == ts["pending"] + ts["in_progress"] + ts["completed"] + ts["blocked"]


def test_dashboard_empty_database(client, db_session, mock_docker):
    """Verify all statistics return zero with an empty database and endpoint returns 200."""
    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    summary = response.json()["summary"]

    assert summary["project_statistics"] == {"total": 0, "active": 0, "inactive": 0}
    assert summary["task_statistics"] == {
        "total": 0,
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
        "blocked": 0,
    }
    assert summary["projects"] == 0
    assert summary["active_projects"] == 0
    assert summary["tasks"] == 0
    assert summary["completed_tasks"] == 0
    assert summary["pending_tasks"] == 0
