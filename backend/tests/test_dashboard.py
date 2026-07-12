"""
Dashboard endpoint tests.

Sprint 2.0 - Updated for provider-based architecture.
"""

from app.models.db.note import Note
from app.models.db.parking_lot import ParkingLot
from app.models.db.project import Project
from app.models.db.resume import Resume
from app.models.db.task import Task
from app.repositories.note_repository import NoteRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.task_repository import TaskRepository


def test_dashboard_returns_live_postgresql_sections(
    client,
    db_session,
    sample_project,
    mock_docker,
):
    ProjectRepository().create_many(
        db_session,
        [Project(name="Dashboard Project", description="Visible in API", active=True)],
    )
    TaskRepository().create_many(
        db_session,
        [
            Task(
                project_id=sample_project.id,
                title="Dashboard task",
                description="Task visible in API",
                status="pending",
                priority="low",
            )
        ],
    )
    NoteRepository().create_many(
        db_session,
        [Note(title="Dashboard note", content="Note visible in API")],
    )
    ResumeRepository().create_many(
        db_session,
        [
            Resume(
                title="Dashboard resume",
                description="Resume visible in API",
                available=True,
            )
        ],
    )
    db_session.add(
        ParkingLot(
            title="Dashboard parking item",
            description="Parking lot visible in API",
            priority="medium",
            status="parked",
        )
    )
    db_session.commit()

    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200

    payload = response.json()
    assert payload["projects"]["count"] >= 1
    assert payload["tasks"]["count"] == 1
    assert payload["notes"]["count"] == 1
    assert payload["resume"]["available"] is True
    assert payload["resume"]["title"] == "Dashboard resume"
    assert payload["summary"]["projects"] >= 1
    assert payload["summary"]["tasks"] == 1
    assert payload["summary"]["notes"] == 1
    assert payload["summary"]["resume_available"] is True
    assert "parking_lot" in payload
    assert payload["parking_lot"]["count"] >= 1
    assert "health" in payload
    assert "system" in payload
    assert "docker" in payload
    assert "git" in payload
