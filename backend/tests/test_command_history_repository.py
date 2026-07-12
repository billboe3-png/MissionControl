"""
Command History Repository Tests
"""

from app.models.db.command_history import CommandHistory
from app.repositories.command_history_repository import CommandHistoryRepository


def _create_history(
    db_session,
    host_id: int,
    command: str = "hostname",
    shell: str = "bash",
    success: bool = True,
) -> CommandHistory:
    """Helper to create a command history record."""
    return CommandHistoryRepository.create(
        db=db_session,
        host_id=host_id,
        command=command,
        shell=shell,
        stdout="test-server",
        stderr="",
        exit_code=0,
        success=success,
        duration_ms=150,
        executed_by="testuser",
    )


def test_create_command_history(db_session, sample_host):
    """Test creating a new command history record."""
    record = _create_history(db_session, sample_host.id)

    assert record.id is not None
    assert record.host_id == sample_host.id
    assert record.command == "hostname"
    assert record.shell == "bash"
    assert record.stdout == "test-server"
    assert record.exit_code == 0
    assert record.success is True
    assert record.duration_ms == 150
    assert record.executed_by == "testuser"


def test_get_history_by_id(db_session, sample_host):
    """Test retrieving a history record by ID."""
    created = _create_history(db_session, sample_host.id)
    found = CommandHistoryRepository.get_by_id(db_session, created.id)

    assert found is not None
    assert found.id == created.id
    assert found.command == "hostname"


def test_get_history_by_id_not_found(db_session):
    """Test that None is returned for a nonexistent ID."""
    found = CommandHistoryRepository.get_by_id(db_session, 9999)
    assert found is None


def test_get_recent(db_session, sample_host):
    """Test retrieving recent history records."""
    _create_history(db_session, sample_host.id, command="cmd1")
    _create_history(db_session, sample_host.id, command="cmd2")

    records = CommandHistoryRepository.get_recent(db_session, limit=5)
    assert len(records) >= 2


def test_get_filtered_by_search(db_session, sample_host):
    """Test filtering history records by command text."""
    _create_history(db_session, sample_host.id, command="hostname")
    _create_history(db_session, sample_host.id, command="uptime")

    results = CommandHistoryRepository.get_filtered(db_session, search="host")
    assert len(results) >= 1
    assert all("host" in r.command.lower() for r in results)


def test_get_filtered_by_host_id(db_session, sample_host):
    """Test filtering history records by host ID."""
    _create_history(db_session, sample_host.id, command="cmd1")

    results = CommandHistoryRepository.get_filtered(db_session, host_id=sample_host.id)
    assert len(results) >= 1
    assert all(r.host_id == sample_host.id for r in results)


def test_get_filtered_by_success(db_session, sample_host):
    """Test filtering history records by success status."""
    _create_history(db_session, sample_host.id, command="good", success=True)
    _create_history(db_session, sample_host.id, command="bad", success=False)

    success_results = CommandHistoryRepository.get_filtered(db_session, success=True)
    failure_results = CommandHistoryRepository.get_filtered(db_session, success=False)

    assert len(success_results) >= 1
    assert len(failure_results) >= 1
    assert all(r.success is True for r in success_results)
    assert all(r.success is False for r in failure_results)


def test_attach_host_names(db_session, sample_host):
    """Test enriching history records with host names."""
    record = _create_history(db_session, sample_host.id)
    enriched = CommandHistoryRepository.attach_host_names(db_session, [record])

    assert len(enriched) == 1
    assert enriched[0]["host_name"] == "Test Server"
    assert enriched[0]["command"] == "hostname"
