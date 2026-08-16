# backend/tests/test_veeam_target_bridge.py
from app.plugins.installed.official_veeam.bridge import (
    remove_target_server,
    sync_target_to_server,
)
from app.plugins.installed.official_veeam.models import VeeamBackupServer
from app.repositories.agent_remote_target_repository import AgentRemoteTargetRepository
from app.repositories.agent_repository import AgentRepository


def _make_target(db, name="Veeam Host", plugins="veeam,hyperv", enabled=True):
    agent = AgentRepository.create(
        db, name=f"{name} agent", hostname=f"{name.lower().replace(' ', '.')}.local",
        api_key="mc_agent_vbridge1234567890", status="online",
    )
    target = AgentRemoteTargetRepository.create(
        db, agent_id=agent.id, name=name, hostname="192.168.10.49",
        protocol="ssh", port=22, username="kg\\administrator",
        password_encrypted="enc", enabled=enabled, target_plugins=plugins,
    )
    return agent, target


def test_sync_creates_server_row(db_session):
    _, target = _make_target(db_session)
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.edition == "community"
    assert row.agent_id == target.agent_id
    assert row.target_id == target.id
    assert row.enabled is True
    assert row.name == "[Veeam Host]"


def test_sync_removes_row_when_veeam_unchecked(db_session):
    _, target = _make_target(db_session)
    sync_target_to_server(db_session, target)
    target.target_plugins = "hyperv"
    db_session.commit()
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.enabled is False


def test_remove_target_server_disables_row(db_session):
    _, target = _make_target(db_session)
    sync_target_to_server(db_session, target)
    remove_target_server(db_session, target.id)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.enabled is False


def test_sync_updates_creds_on_existing_row(db_session):
    _, target = _make_target(db_session)
    sync_target_to_server(db_session, target)
    target.hostname = "10.0.0.9"
    db_session.commit()
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.legacy_ssh_host == "10.0.0.9"


def test_first_server_prefers_enterprise(db_session):
    from app.plugins.installed.official_veeam.models import VeeamBackupServer
    from app.plugins.installed.official_veeam.routes import _first_server

    db_session.add(VeeamBackupServer(
        name="[Community]", edition="community", data_source="both",
        agent_id=1, target_id=1, enabled=True, status="unknown",
    ))
    db_session.add(VeeamBackupServer(
        name="Enterprise", edition="enterprise", data_source="api",
        rest_url="https://v:9419/api/v1", enabled=True, status="unknown",
    ))
    db_session.commit()
    server = _first_server(db_session)
    assert server is not None
    assert server.name == "Enterprise"