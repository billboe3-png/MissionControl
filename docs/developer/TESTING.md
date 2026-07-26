# Testing Guide

Mission Control uses pytest for backend testing. The frontend does not yet have a test framework configured.

## Running Tests

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_remote_service.py -v

# Run a specific test
python -m pytest tests/test_remote_service.py::test_create_host -v

# Run with short tracebacks
python -m pytest tests/ -v --tb=short

# Run tests matching a keyword
python -m pytest tests/ -k "host" -v
```

## Test Structure

```
backend/tests/
├── conftest.py                 # Shared fixtures
├── test_auth.py                # Authentication tests
├── test_remote_service.py      # Remote operations service tests
├── test_host_repository.py     # Host repository tests
├── test_automation.py          # Playbook execution tests
├── test_agent.py               # Agent management tests
├── test_providers/             # Provider tests (SSH, WinRM, etc.)
│   ├── test_ssh_provider.py
│   ├── test_winrm_provider.py
│   └── test_provider_factory.py
├── test_routers/               # API endpoint tests
│   ├── test_remote_router.py
│   ├── test_auth_router.py
│   └── test_dashboard_router.py
└── test_integration/           # Cross-module integration tests
    ├── test_full_workflow.py
    └── test_migration.py
```

## Shared Fixtures (`conftest.py`)

The `conftest.py` file provides reusable fixtures for the entire test suite:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.database import get_db


# Test database engine (uses SQLite for speed)
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Authenticate and return authorization headers."""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

## Writing Tests

### API Endpoint Tests

Test the full HTTP request/response cycle:

```python
def test_list_hosts(client, auth_headers):
    response = client.get("/api/v1/remote/hosts", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_host(client, auth_headers):
    host_data = {
        "name": "Test Server",
        "hostname": "192.168.1.100",
        "protocol": "ssh",
        "port": 22,
    }
    response = client.post(
        "/api/v1/remote/hosts",
        json=host_data,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Server"
    assert data["hostname"] == "192.168.1.100"
    assert "id" in data


def test_get_host_not_found(client, auth_headers):
    response = client.get("/api/v1/remote/hosts/99999", headers=auth_headers)
    assert response.status_code == 404


def test_create_host_unauthorized(client):
    host_data = {
        "name": "Test Server",
        "hostname": "192.168.1.100",
        "protocol": "ssh",
        "port": 22,
    }
    response = client.post("/api/v1/remote/hosts", json=host_data)
    assert response.status_code in (401, 403)
```

### Repository Tests

Test data access logic directly:

```python
def test_host_repository_create(db_session):
    from app.repositories.host_repository import HostRepository
    from app.schemas.remote import HostCreate

    host_in = HostCreate(
        name="Test Host",
        hostname="10.0.0.1",
        protocol="ssh",
        port=22,
    )
    host = HostRepository.create(db_session, obj_in=host_in, created_by=1)
    assert host.id is not None
    assert host.name == "Test Host"


def test_host_repository_search(db_session):
    from app.repositories.host_repository import HostRepository
    from app.schemas.remote import HostCreate

    HostRepository.create(
        db_session,
        obj_in=HostCreate(name="Web Server", hostname="10.0.0.1", protocol="ssh", port=22),
        created_by=1,
    )
    HostRepository.create(
        db_session,
        obj_in=HostCreate(name="DB Server", hostname="10.0.0.2", protocol="ssh", port=22),
        created_by=1,
    )

    results = HostRepository.search(db_session, "Web")
    assert len(results) == 1
    assert results[0].name == "Web Server"
```

### Service Tests

Test business logic with mocked repositories:

```python
from unittest.mock import patch, MagicMock


def test_remote_service_create_host(db_session):
    from app.services.remote_service import RemoteService
    from app.schemas.remote import HostCreate

    host_in = HostCreate(
        name="New Host",
        hostname="10.0.0.5",
        protocol="ssh",
        port=22,
    )
    host = RemoteService.create_host(db_session, host_in, created_by=1)
    assert host.name == "New Host"
    assert host.is_active is True
```

### Provider Tests

Test provider implementations with mocked external connections:

```python
from unittest.mock import patch, MagicMock


@patch("app.providers.remote.ssh_provider.paramiko.SSHClient")
def test_ssh_provider_execute(mock_ssh_class):
    from app.providers.remote.ssh_provider import SSHProvider

    mock_client = MagicMock()
    mock_ssh_class.return_value = mock_client
    mock_client.exec_command.return_value = (
        None,
        MagicMock(read=b"output\n"),
        MagicMock(read=b""),
    )

    provider = SSHProvider()
    provider.connect("10.0.0.1", 22, {"username": "root", "password": "secret"})
    output = provider.execute("uname -a")
    assert "output" in output
    provider.disconnect()
    mock_client.close.assert_called_once()
```

## Mocking

### Mocking Database Sessions

Use the `db_session` fixture for tests that need database access. The fixture creates a fresh SQLite database per test.

### Mocking External Services

Use `unittest.mock.patch` for external dependencies (SSH, WinRM, API calls):

```python
@patch("app.services.remote_service.paramiko.SSHClient")
def test_execute_command(mock_ssh):
    ...
```

### Mocking the Auth Dependency

Override the auth dependency for tests that don't need real authentication:

```python
from app.core.auth_dependency import get_current_user
from app.models.db.user import User


@pytest.fixture
def mock_admin_user():
    user = User(id=1, username="admin", role="global_admin", company_id=1)
    return user


def test_admin_endpoint(client, mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    response = client.get("/api/v1/admin/endpoint")
    assert response.status_code == 200
    app.dependency_overrides.clear()
```

## Test Naming Conventions

| Pattern | Example |
|---------|---------|
| `test_<function>_<scenario>` | `test_create_host_valid_input` |
| `test_<function>_<scenario>_<expected>` | `test_get_host_not_found_returns_404` |
| `test_<class>_<method>` | `test_HostRepository_search` |

## Test Coverage

The test suite covers:

| Area | Description |
|------|-------------|
| API Integration | CRUD endpoints, auth, remote operations |
| Repositories | Data access, search, encryption |
| Services | Business logic, validation, credential handling |
| Providers | SSH, WinRM, provider factory, platform integrations |
| History & Audit | Command history, templates, schedules, bulk execution |
| Automation | Playbook execution, scheduling, event triggers |
| Auth & Multi-Tenancy | Login, JWT, role-based access, company/site scoping |
| Agent Management | Agent registration, command dispatch, authentication |

## CI Integration

Tests run automatically in CI via GitHub Actions:

```yaml
- name: Run tests
  run: |
    cd backend
    python -m pytest tests/ -v --tb=short
```

See [CI_CD.md](CI_CD.md) for the full pipeline configuration.

## Cross-References

- See [BACKEND.md](BACKEND.md) for the architecture being tested.
- See [CODING_STANDARDS.md](CODING_STANDARDS.md) for code style in tests.
- See [CI_CD.md](CI_CD.md) for how tests run in the pipeline.
