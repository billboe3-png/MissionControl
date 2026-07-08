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


@pytest.fixture
def mock_docker(monkeypatch):
    """Avoid Docker calls during dashboard tests."""

    async def fake_docker_status():
        return {
            "engine": "running",
            "compose": "available",
            "container_count": 0,
            "docker_version": "test",
            "containers": [],
        }

    monkeypatch.setattr(
        "app.services.dashboard_service.get_docker_status",
        fake_docker_status,
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
