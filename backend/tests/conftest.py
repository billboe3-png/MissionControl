"""
Shared pytest fixtures for backend tests.
"""

import os

from cryptography.fernet import Fernet

# Set secret key BEFORE any app imports trigger Settings()
os.environ.setdefault(
    "MISSIONCONTROL_SECRET_KEY",
    Fernet.generate_key().decode(),
)
os.environ.setdefault("TESTING", "1")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import plugin models so their tables are included in Base.metadata.create_all()
# These models are normally imported during app startup (plugin loading), but tests
# need them registered before create_all() is called.
from app.plugins.installed.git.models import GitRepository  # noqa: F401
from app.plugins.installed.official_docker.models import DockerHost  # noqa: F401

from app.core.auth_dependency import get_current_user
from app.core.config import get_settings
from app.db.database import Base, get_db
from app.main import app
from app.models.db.credential_profile import CredentialProfile
from app.models.db.project import Project
from app.models.db.remote_host import RemoteHost


class _FakeUser:
    """Minimal user object for test auth bypass."""
    id = 1
    email = "test@test.local"
    display_name = "Test User"
    role = "global_admin"
    company_id = None
    site_id = None
    enabled = True


@pytest.fixture(autouse=True)
def mock_secret_key(monkeypatch):
    """Automatically set MISSIONCONTROL_SECRET_KEY for all tests."""
    test_key = Fernet.generate_key().decode()
    monkeypatch.setenv("MISSIONCONTROL_SECRET_KEY", test_key)
    get_settings.cache_clear()
    return test_key


@pytest.fixture(autouse=True)
def _override_auth():
    """Override get_current_user globally for all tests.

    When no Authorization header is present, return a mock admin user
    so non-auth tests don't need to set up users/tokens.
    When a real token is provided, let the real auth handle it (including
    rejection for invalid tokens).
    """
    from fastapi import Depends, Header, HTTPException, status
    from sqlalchemy.orm import Session

    from app.db import get_db
    from app.services.auth_service import AuthService

    async def _smart_auth(
        authorization: str | None = Header(None),
        db: Session = Depends(get_db),
    ):
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]
            try:
                return AuthService.get_current_user(db, token)
            except (ValueError, Exception) as exc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                ) from exc
        return _FakeUser()

    app.dependency_overrides[get_current_user] = _smart_auth
    yield
    app.dependency_overrides.pop(get_current_user, None)


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
    """Provide a FastAPI test client with database override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


def _fake_health_data(_db):
    return {
        "backend": {"status": "healthy", "message": "API responding normally"},
        "database": {"status": "healthy", "message": "Connected", "project_count": 0},
        "redis": {"status": "unhealthy", "message": "Connection failed"},
    }


@pytest.fixture
def mock_docker(monkeypatch):
    """Mock Health provider for dashboard tests."""

    async def fake_health_data(_db):
        return _fake_health_data(_db)

    monkeypatch.setattr(
        "app.providers.health_provider.health_provider.get_health",
        fake_health_data,
    )

    async def fake_remote_data(self, _db):
        return {
            "totalHosts": 0,
            "enabledHosts": 0,
            "recentCommands": [],
        }

    monkeypatch.setattr(
        "app.providers.remote_provider.RemoteProvider.get_remote_data",
        fake_remote_data,
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


@pytest.fixture
def sample_credential(db_session, mock_secret_key):
    """Create a single credential profile for tests with encrypted fields."""
    from app.core.security import CredentialCipher

    cipher = CredentialCipher(mock_secret_key)

    credential = CredentialProfile(
        name="Test SSH Key",
        authentication_type="ssh_key",
        username="testuser",
        private_key_encrypted=cipher.encrypt("fake-key-content"),
    )
    db_session.add(credential)
    db_session.commit()
    db_session.refresh(credential)
    return credential


@pytest.fixture
def sample_host(db_session, sample_credential):
    """Create a single remote host for tests."""
    host = RemoteHost(
        name="Test Server",
        hostname="test.server.local",
        ip_address="10.0.0.1",
        operating_system="Ubuntu 22.04",
        connection_type="ssh",
        port=22,
        enabled=True,
        credential_profile_id=sample_credential.id,
    )
    db_session.add(host)
    db_session.commit()
    db_session.refresh(host)
    return host


@pytest.fixture
def sample_disabled_host(db_session, sample_credential):
    """Create a disabled remote host for tests."""
    host = RemoteHost(
        name="Disabled Server",
        hostname="disabled.server.local",
        connection_type="winrm",
        port=5985,
        enabled=False,
        credential_profile_id=sample_credential.id,
    )
    db_session.add(host)
    db_session.commit()
    db_session.refresh(host)
    return host
