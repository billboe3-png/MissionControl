"""
Shared pytest fixtures for backend tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.database import get_db
from app.main import app
from app.models.db import Note
from app.models.db import Project
from app.models.db import Resume
from app.models.db import Task


@pytest.fixture
def db_session():
    """Provide an isolated in-memory database session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Provide a FastAPI test client with database dependency override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _fake_docker_data():
    return {
        "available": True,
        "engine": "running",
        "docker_version": "test",
        "compose_version": "sdk",
        "container_count": 0,
        "running": 0,
        "stopped": 0,
        "image_count": 0,
        "containers": [],
    }


def _fake_health_data(_db):
    return {
        "backend": {"status": "healthy", "message": "API responding normally"},
        "database": {"status": "healthy", "message": "Connected", "project_count": 0},
        "redis": {"status": "unhealthy", "message": "Connection failed"},
    }


def _fake_git_data():
    return {
        "available": False,
        "repository_name": None,
        "current_branch": None,
        "latest_commit": None,
        "commit_author": None,
        "commit_date": None,
        "working_tree_clean": True,
        "ahead_of_origin": 0,
        "behind_origin": 0,
        "last_pull": None,
        "remote_url": None,
    }


@pytest.fixture
def mock_docker(monkeypatch):
    """Mock Docker, Health, Git, and System providers for dashboard tests."""
    import asyncio

    async def fake_docker_data():
        return _fake_docker_data()

    async def fake_health_data(_db):
        return _fake_health_data(_db)

    monkeypatch.setattr(
        "app.providers.docker_provider.docker_provider.get_docker_data",
        fake_docker_data,
    )
    monkeypatch.setattr(
        "app.providers.health_provider.health_provider.get_health",
        fake_health_data,
    )
    monkeypatch.setattr(
        "app.providers.git_provider.git_provider.get_git_info",
        _fake_git_data,
    )
    monkeypatch.setattr(
        "app.providers.system_provider.system_provider.get_system_info",
        lambda: {
            "hostname": "test",
            "os": "Test",
            "platform": "test",
            "cpu_count": 1,
            "cpu_percent": 0.0,
            "memory_total": 1024,
            "memory_used": 512,
            "memory_percent": 50.0,
            "disk_total": 1024,
            "disk_used": 512,
            "disk_percent": 50.0,
            "uptime_seconds": 0,
            "boot_time": 0,
        },
    )


@pytest.fixture
def sample_project(db_session):
    """Create a single project for relationship tests."""
    project = Project(
        name="Test Project",
        description="Test project description",
        active=True,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project
