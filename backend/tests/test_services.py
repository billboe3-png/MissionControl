"""
Service layer tests.
"""

import pytest
from fastapi import HTTPException

from app.models.db.note import Note
from app.models.db.project import Project
from app.models.db.resume import Resume
from app.models.db.task import Task
from app.repositories.note_repository import NoteRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.project import ProjectCreate
from app.services.note_service import NoteService
from app.services.project_service import ProjectService
from app.services.resume_service import ResumeService
from app.services.task_service import TaskService


@pytest.mark.asyncio
async def test_project_service_returns_live_data(db_session):
    ProjectRepository().create_many(
        db_session,
        [Project(name="UnitSphere", description="Infra platform", active=True)],
    )

    data = await ProjectService().get_data(db_session)

    assert data["count"] == 1
    assert data["items"][0]["name"] == "UnitSphere"
    assert data["items"][0]["status"] == "active"


@pytest.mark.asyncio
async def test_project_service_get_all_returns_api_models(db_session):
    ProjectRepository().create_many(
        db_session,
        [Project(name="API Project", description="Readable via API", active=True)],
    )

    data = await ProjectService().get_all(db_session)

    assert data.count == 1
    assert data.items[0].name == "API Project"
    assert data.items[0].active is True


@pytest.mark.asyncio
async def test_project_service_get_by_id_returns_404_when_missing(db_session):
    with pytest.raises(HTTPException) as exc_info:
        await ProjectService().get_by_id(db_session, 999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Project not found"


@pytest.mark.asyncio
async def test_project_service_create_persists_project(db_session):
    data = await ProjectService().create(
        db_session,
        ProjectCreate(name="New API Project", description="Created via API"),
    )

    assert data.name == "New API Project"
    assert ProjectRepository().get_by_id(db_session, data.id) is not None


@pytest.mark.asyncio
async def test_project_service_create_returns_409_for_duplicate_name(db_session):
    ProjectRepository().create_many(
        db_session,
        [Project(name="Duplicate Project", description="Existing", active=True)],
    )

    with pytest.raises(HTTPException) as exc_info:
        await ProjectService().create(
            db_session,
            ProjectCreate(name="duplicate project", description="Conflict"),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Project already exists"


@pytest.mark.asyncio
async def test_task_service_returns_live_data(db_session, sample_project):
    TaskRepository().create_many(
        db_session,
        [
            Task(
                project_id=sample_project.id,
                title="Write tests",
                description="Add service coverage",
                status="in_progress",
                priority="medium",
            )
        ],
    )

    data = await TaskService().get_data(db_session)

    assert data["count"] == 1
    assert data["items"][0]["title"] == "Write tests"
    assert data["items"][0]["project_name"] == "Test Project"


@pytest.mark.asyncio
async def test_note_service_returns_live_data(db_session):
    NoteRepository().create_many(
        db_session,
        [Note(title="Runbook", content="Restart nginx after config changes.")],
    )

    data = await NoteService().get_data(db_session)

    assert data["count"] == 1
    assert data["items"][0]["title"] == "Runbook"


@pytest.mark.asyncio
async def test_resume_service_returns_unavailable_when_empty(db_session):
    data = await ResumeService().get_data(db_session)

    assert data["available"] is False
    assert data["title"] is None
    assert data["description"] is None


@pytest.mark.asyncio
async def test_resume_service_returns_active_resume(db_session):
    ResumeRepository().create_many(
        db_session,
        [
            Resume(
                title="Continue Sprint 1.1.0E",
                description="Finish architecture cleanup",
                available=True,
            )
        ],
    )

    data = await ResumeService().get_data(db_session)

    assert data["available"] is True
    assert data["title"] == "Continue Sprint 1.1.0E"
    assert data["description"] == "Finish architecture cleanup"
