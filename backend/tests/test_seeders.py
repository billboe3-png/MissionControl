"""
Production seed framework tests.
"""

from app.repositories.note_repository import NoteRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.task_repository import TaskRepository
from app.seed.notes import seed as seed_notes
from app.seed.parking_lot import seed as seed_parking_lot
from app.seed.projects import seed as seed_projects
from app.seed.resumes import seed as seed_resumes
from app.seed.runner import run_seed
from app.seed.tasks import seed as seed_tasks


def test_project_seed_is_idempotent(db_session):
    assert seed_projects(db_session) is True
    assert ProjectRepository().get_count(db_session) == 4
    assert seed_projects(db_session) is False
    assert ProjectRepository().get_count(db_session) == 4


def test_task_seed_is_idempotent(db_session):
    seed_projects(db_session)
    assert seed_tasks(db_session) is True
    assert TaskRepository().get_count(db_session) == 8
    assert seed_tasks(db_session) is False
    assert TaskRepository().get_count(db_session) == 8


def test_note_seed_leaves_empty_baseline(db_session):
    assert seed_notes(db_session) is False
    assert NoteRepository().get_count(db_session) == 0


def test_resume_seed_leaves_empty_baseline(db_session):
    assert seed_resumes(db_session) is False
    assert ResumeRepository().get_count(db_session) == 0


def test_parking_lot_seed_is_noop(db_session):
    assert seed_parking_lot(db_session) is False


def test_runner_seeds_production_baseline(db_session, monkeypatch):
    class NonClosingSession:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self) -> None:
            return None

    monkeypatch.setattr(
        "app.seed.runner.SessionLocal",
        lambda: NonClosingSession(db_session),
    )

    exit_code = run_seed()
    assert exit_code == 0
    assert ProjectRepository().get_count(db_session) == 4
    assert TaskRepository().get_count(db_session) == 8
    assert NoteRepository().get_count(db_session) == 0
    assert ResumeRepository().get_count(db_session) == 0

    exit_code = run_seed()
    assert exit_code == 0
    assert ProjectRepository().get_count(db_session) == 4
    assert TaskRepository().get_count(db_session) == 8
