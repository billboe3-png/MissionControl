"""
Repository layer tests.
"""

from datetime import datetime

from app.models.db.note import Note
from app.models.db.project import Project
from app.models.db.resume import Resume
from app.models.db.task import Task
from app.repositories.note_repository import NoteRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.task_repository import TaskRepository


def test_project_repository_create_and_count(db_session):
    repository = ProjectRepository()
    assert repository.get_count(db_session) == 0

    projects = repository.create_many(
        db_session,
        [
            Project(
                name="Mission Control",
                description="Platform project",
                active=True,
            )
        ],
    )

    assert len(projects) == 1
    assert repository.get_count(db_session) == 1
    assert repository.get_all(db_session)[0].name == "Mission Control"


def test_project_repository_get_by_id(db_session):
    repository = ProjectRepository()
    created = repository.create_many(
        db_session,
        [
            Project(
                name="Lookup Project",
                description="Find me by id",
                active=True,
            )
        ],
    )[0]

    found = repository.get_by_id(db_session, created.id)
    missing = repository.get_by_id(db_session, 999)

    assert found is not None
    assert found.name == "Lookup Project"
    assert missing is None


def test_task_repository_links_to_project(db_session, sample_project):
    repository = TaskRepository()
    repository.create_many(
        db_session,
        [
            Task(
                project_id=sample_project.id,
                title="Implement repository tests",
                description="Cover task persistence",
                status="pending",
                priority="high",
            )
        ],
    )

    tasks = repository.get_all(db_session)
    assert repository.get_count(db_session) == 1
    assert tasks[0].project.name == "Test Project"


def test_note_repository_create_and_count(db_session):
    repository = NoteRepository()
    repository.create_many(
        db_session,
        [
            Note(
                title="Operations note",
                content="Document the backup schedule.",
            )
        ],
    )

    notes = repository.get_all(db_session)
    assert repository.get_count(db_session) == 1
    assert notes[0].title == "Operations note"


def test_resume_repository_get_active(db_session):
    repository = ResumeRepository()
    now = datetime.utcnow()
    repository.create_many(
        db_session,
        [
            Resume(
                title="Older resume",
                description="Completed work",
                available=False,
                created_at=now,
                updated_at=now,
            ),
            Resume(
                title="Current resume",
                description="Continue dashboard work",
                available=True,
                created_at=now,
                updated_at=now,
            ),
        ],
    )

    active = repository.get_active(db_session)
    assert active is not None
    assert active.title == "Current resume"
    assert repository.get_count(db_session) == 2
