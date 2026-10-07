# backend/tests/test_veeam_target_bridge.py
from datetime import UTC, datetime

from app.plugins.installed.official_veeam.bridge import (
    remove_target_server,
    sync_target_to_server,
)
from app.plugins.installed.official_veeam.models import VeeamBackupServer
from app.repositories.agent_remote_target_repository import AgentRemoteTargetRepository
from app.repositories.agent_repository import AgentRepository


def _make_target(
    db, name="Veeam Host", plugins="veeam,hyperv", enabled=True,
    api_key="mc_agent_vbridge1234567890", **overrides,
):
    agent = AgentRepository.create(
        db, name=f"{name} agent", hostname=f"{name.lower().replace(' ', '.')}.local",
        api_key=api_key, status="online",
    )
    kwargs = {
        "name": name,
        "hostname": "192.168.10.49",
        "protocol": "ssh",
        "port": 22,
        "username": "kg\\administrator",
        "password_encrypted": "enc",
        "enabled": enabled,
        "target_plugins": plugins,
    }
    kwargs.update(overrides)
    target = AgentRemoteTargetRepository.create(db, agent_id=agent.id, **kwargs)
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
    assert row.db_type == "postgresql"
    assert row.column_case == "auto"


def test_sync_propagates_db_type_and_column_case(db_session):
    _, target = _make_target(
        db_session, db_type="mssql", column_case="snake"
    )
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.db_type == "mssql"
    assert row.column_case == "snake"


def test_sync_does_not_overwrite_db_type_on_existing_row(db_session):
    """Re-sync must not rewrite db_type/column_case of an existing row.

    Propagation happens once, when the row is created. Afterwards the registry
    row is authoritative: it holds the lazily detected value, and copying a
    stale target value has already corrupted a working MSSQL registration.
    Host/credential refresh must still happen on re-sync.
    """
    _, target = _make_target(db_session, db_type="postgresql", column_case="auto")
    sync_target_to_server(db_session, target)

    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.db_type == "postgresql"

    # Detection (or an operator override) resolves the real type.
    row.db_type = "mssql"
    row.column_case = "snake"
    db_session.commit()

    target.db_type = "postgresql"
    target.column_case = "auto"
    target.hostname = "10.9.9.10"
    db_session.commit()
    sync_target_to_server(db_session, target)

    db_session.refresh(row)
    assert row.db_type == "mssql"
    assert row.column_case == "snake"
    assert row.legacy_ssh_host == "10.9.9.10"
    assert row.enabled is True


def test_sync_disables_row_when_veeam_unchecked(db_session):
    _, target = _make_target(db_session)
    sync_target_to_server(db_session, target)
    target.target_plugins = "hyperv"
    db_session.commit()
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.enabled is False


def test_remove_target_server_purges_row_and_data(db_session):
    from app.plugins.installed.official_veeam.collector import _upsert_snapshot
    from app.plugins.installed.official_veeam.models import (
        VeeamBackupServer,
        VeeamJob,
        VeeamSnapshot,
    )

    _, target = _make_target(db_session)
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    server_id = row.id
    db_session.add(VeeamJob(
        server_id=server_id, veeam_id="job-1", name="Copy Job",
        job_type="backup", status="Success", is_enabled=True,
    ))
    _upsert_snapshot(db_session, server_id, "job_stats_daily:8:jobs", {"success": True})
    db_session.commit()

    remove_target_server(db_session, target.id)

    assert db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).first() is None
    assert db_session.get(VeeamBackupServer, server_id) is None
    assert db_session.query(VeeamJob).filter(
        VeeamJob.server_id == server_id
    ).first() is None
    assert db_session.query(VeeamSnapshot).filter(
        VeeamSnapshot.server_id == server_id
    ).first() is None


def test_sync_recreates_row_with_new_id_after_delete(db_session):
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    _, target_a = _make_target(db_session, name="Moved Host", plugins="veeam")
    sync_target_to_server(db_session, target_a)
    db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target_a.id
    ).one()

    remove_target_server(db_session, target_a.id)
    assert db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target_a.id
    ).first() is None

    _, target_b = _make_target(
        db_session, name="Moved Host", plugins="veeam",
        api_key="mc_agent_vbridgeMovedBBBBBBBBBB",
        # SQLite reuses a deleted row's rowid, so pin a provably different id
        # (Postgres sequences never reuse); without this the "recreated host"
        # would look indistinguishable from the deleted one in the test.
        id=7002,
    )
    sync_target_to_server(db_session, target_b)

    # The old row is gone and exactly one clean row remains, re-pointed at the
    # new target id. On Postgres the fresh insert takes a brand new sequence id;
    # on SQLite the freed server rowid happens to be reused, so the guarantee
    # asserted here is "a fresh row", not "a numerically different server id".
    rows = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.name == "[Moved Host]"
    ).all()
    assert len(rows) == 1
    new = rows[0]
    assert new.target_id == target_b.id
    assert new.agent_id == target_b.agent_id


def test_sync_reuses_clean_name_when_old_target_row_is_orphaned(db_session):
    from app.plugins.installed.official_veeam.collector import _upsert_snapshot
    from app.plugins.installed.official_veeam.models import VeeamSnapshot
    from app.repositories.agent_remote_target_repository import (
        AgentRemoteTargetRepository,
    )

    _, target_a = _make_target(db_session, name="Orphaned Host", plugins="veeam")
    sync_target_to_server(db_session, target_a)
    old = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target_a.id
    ).one()
    _upsert_snapshot(db_session, old.id, "jobs", {"success": True, "jobs": []})
    db_session.commit()

    # Target vanishes without remove_target_server (e.g. its agent was deleted
    # and the target cascaded away) - the veeam row is orphaned.
    AgentRemoteTargetRepository.delete(db_session, target_a.id)

    _, target_b = _make_target(
        db_session, name="Orphaned Host", plugins="veeam",
        api_key="mc_agent_vbridgeOrphanBBBBBBBBBB",
        # Distinct id so the stale name clash is detected even on SQLite, where
        # the deleted target's rowid would otherwise be reused by the new row.
        id=7003,
    )
    sync_target_to_server(db_session, target_b)

    rows = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.name == "[Orphaned Host]"
    ).all()
    assert len(rows) == 1
    assert rows[0].target_id == target_b.id
    assert db_session.query(VeeamBackupServer).count() == 1
    assert db_session.query(VeeamSnapshot).filter(
        VeeamSnapshot.server_id == old.id
    ).first() is None


def test_sync_keeps_suffix_for_live_target_with_same_name(db_session):
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    _, target_a = _make_target(db_session, name="Twin Host", plugins="veeam")
    sync_target_to_server(db_session, target_a)

    _, target_b = _make_target(db_session, name="Twin Host", plugins="veeam",
                               api_key="mc_agent_vbridgeTwinBBBBBBBBBBBB")
    sync_target_to_server(db_session, target_b)

    names = sorted(
        r.name for r in db_session.query(VeeamBackupServer).all()
    )
    assert names == ["[Twin Host]", f"[Twin Host] #{target_b.id}"]
    assert len(names) == 2


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


def test_sync_skips_non_ssh_veeam_target(db_session):
    _, target = _make_target(db_session, plugins="veeam", protocol="psremoting")
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).first()
    assert row is None


def test_sync_disables_row_when_protocol_changed_to_non_ssh(db_session):
    _, target = _make_target(db_session, plugins="veeam", protocol="ssh")
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.enabled is True
    target.protocol = "winrm"
    db_session.commit()
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.enabled is False


def test_first_server_prefers_enterprise(db_session):
    from app.plugins.installed.official_veeam.models import VeeamBackupServer
    from app.plugins.installed.official_veeam.routes import _first_server

    db_session.add(VeeamBackupServer(
        name="[Community]", edition="community", data_source="both",
        agent_id=1, target_id=1, enabled=True, status="unknown",
    ))
    db_session.add(VeeamBackupServer(
        name="Enterprise", edition="enterprise", data_source="api",
        url="https://v:9419/api/v1", enabled=True, status="unknown",
    ))
    db_session.commit()
    server = _first_server(db_session)
    assert server is not None
    assert server.name == "Enterprise"


def test_profile_linked_to_matching_target(db_session):
    from app.models.db.integration_profile import IntegrationProfile
    from app.plugins.installed.official_veeam.bridge import sync_profile_to_server
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    _, target = _make_target(db_session, name="Veeam Host", plugins="veeam")
    profile = IntegrationProfile(
        name="Veeam Profile",
        integration_type="veeam",
        enabled=True,
        data_source="both",
        ssh_host=target.hostname,
        ssh_username="kg\\administrator",
    )
    db_session.add(profile)
    db_session.commit()

    sync_profile_to_server(db_session, profile)

    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.name == "Veeam Profile"
    ).one()
    assert row.agent_id == target.agent_id
    assert row.target_id == target.id


def test_profile_with_non_matching_ssh_host_does_not_link(db_session):
    from app.models.db.integration_profile import IntegrationProfile
    from app.plugins.installed.official_veeam.bridge import sync_profile_to_server
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    _make_target(db_session, name="Veeam Host", plugins="veeam")
    profile = IntegrationProfile(
        name="Veeam Profile",
        integration_type="veeam",
        enabled=True,
        data_source="both",
        ssh_host="10.99.99.99",
        ssh_username="kg\\administrator",
    )
    db_session.add(profile)
    db_session.commit()

    sync_profile_to_server(db_session, profile)

    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.name == "Veeam Profile"
    ).one()
    assert row.agent_id is None
    assert row.target_id is None
    assert row.legacy_ssh_host == "10.99.99.99"
    assert row.url is None


def _make_profile(db, name, ssh_host, **overrides):
    from app.models.db.integration_profile import IntegrationProfile

    fields = {
        "integration_type": "veeam",
        "enabled": True,
        "data_source": "both",
        "ssh_host": ssh_host,
        "ssh_port": 22,
        "ssh_username": "kg\\administrator",
    }
    fields.update(overrides)
    profile = IntegrationProfile(name=name, **fields)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def test_profile_relinks_target_when_ssh_host_changes(db_session):
    """Editing a profile's SSH host must re-point the relay at the new host.

    Regression: the bridge only resolved a target while both agent_id and
    target_id were unset, so a profile that later got the right SSH host kept
    relaying to whatever unrelated target it was first linked to.
    """
    from app.plugins.installed.official_veeam.bridge import sync_profile_to_server

    _, first = _make_target(
        db_session, name="Host A", plugins="veeam",
        hostname="192.168.8.2", api_key="mc_agent_vbridgeAAAAAAAAAA",
    )
    _, second = _make_target(
        db_session, name="Host B", plugins="veeam",
        hostname="192.168.2.3", api_key="mc_agent_vbridgeBBBBBBBBBB",
    )
    profile = _make_profile(db_session, "Relink", ssh_host=first.hostname)
    sync_profile_to_server(db_session, profile)

    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.name == "Relink"
    ).one()
    assert row.target_id == first.id

    profile.ssh_host = second.hostname
    db_session.commit()
    sync_profile_to_server(db_session, profile)

    assert row.target_id == second.id
    assert row.agent_id == second.agent_id
    assert row.legacy_ssh_host == second.hostname


def test_profile_unlinks_target_when_no_target_matches(db_session):
    """A profile SSH host with no matching target must not relay anywhere.

    Regression: leaving the stale link in place ran one server's SQL against
    another machine and reported that machine's repositories underneath it.
    """
    from app.plugins.installed.official_veeam.bridge import sync_profile_to_server

    _, other = _make_target(
        db_session, name="Host A", plugins="veeam",
        hostname="192.168.10.49", api_key="mc_agent_vbridgeAAAAAAAAAA",
    )
    profile = _make_profile(db_session, "Unlink", ssh_host=other.hostname)
    sync_profile_to_server(db_session, profile)

    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.name == "Unlink"
    ).one()
    assert row.target_id == other.id

    profile.ssh_host = "192.168.8.2"
    db_session.commit()
    sync_profile_to_server(db_session, profile)

    assert row.target_id is None
    assert row.agent_id is None
    assert row.legacy_ssh_host == "192.168.8.2"


def test_profile_without_ssh_host_keeps_target_derived_link(db_session):
    """Rows mirrored from a remote target survive a profile sync with no SSH host."""
    from app.models.db.integration_profile import IntegrationProfile
    from app.plugins.installed.official_veeam.bridge import sync_profile_to_server

    _, target = _make_target(db_session, name="Host A", plugins="veeam")
    sync_target_to_server(db_session, target)

    profile = IntegrationProfile(
        name=f"[{target.name}]", integration_type="veeam",
        enabled=True, data_source="both",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    sync_profile_to_server(db_session, profile)

    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.name == f"[{target.name}]"
    ).one()
    assert row.target_id == target.id
    assert row.agent_id == target.agent_id


class TestSyncPreservesDbSettings:
    """Re-syncing a target must not overwrite a resolved db_type/column_case.

    A stale target db_type once rewrote a working MSSQL registration to
    postgresql, which broke its SQL queries.
    """

    def _target(self, db_session, api_key="k" * 64, **overrides):
        from app.models.db.agent import Agent
        from app.models.db.agent_remote_target import AgentRemoteTarget

        agent = Agent(
            name="target-sync-agent",
            hostname="target-sync-agent",
            api_key=api_key,
            status="online",
            last_heartbeat=datetime.now(UTC),
        )
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        kwargs = {
            "agent_id": agent.id,
            "name": "SYNCSRV",
            "hostname": "10.9.9.9",
            "port": 22,
            "protocol": "ssh",
            "username": "svc",
            "password_encrypted": "enc",
            "target_plugins": "veeam,windows",
            "enabled": True,
            "db_type": "postgresql",
            "column_case": "pascal",
        }
        kwargs.update(overrides)
        target = AgentRemoteTarget(**kwargs)
        db_session.add(target)
        db_session.commit()
        db_session.refresh(target)
        return target

    def test_resync_keeps_resolved_db_type_and_column_case(self, db_session):
        from app.plugins.installed.official_veeam.bridge import sync_target_to_server
        from app.plugins.installed.official_veeam.models import VeeamBackupServer

        target = self._target(db_session)
        sync_target_to_server(db_session, target)

        row = (
            db_session.query(VeeamBackupServer)
            .filter(VeeamBackupServer.target_id == target.id)
            .one()
        )
        assert row.db_type == "postgresql"
        assert row.column_case == "pascal"

        # The row has since been auto-detected / overridden to MSSQL + snake.
        row.db_type = "mssql"
        row.column_case = "snake"
        db_session.commit()

        # Host/credential refresh still happens...
        target.hostname = "10.9.9.10"
        target.username = "svc2"
        db_session.commit()
        sync_target_to_server(db_session, target)

        db_session.refresh(row)
        assert row.legacy_ssh_host == "10.9.9.10"
        assert row.legacy_ssh_username == "svc2"
        assert row.enabled is True
        # ...but the detected db settings survive the re-sync.
        assert row.db_type == "mssql"
        assert row.column_case == "snake"

    def test_new_target_row_defaults_to_auto_detection(self, db_session):
        from app.plugins.installed.official_veeam.bridge import sync_target_to_server
        from app.plugins.installed.official_veeam.models import VeeamBackupServer

        target = self._target(db_session, api_key="j" * 64, name="AUTOSRV")
        # db_type is NOT NULL with a 'postgresql' python-side default, so use an
        # empty value to exercise the "nothing configured" fallback.
        target.db_type = ""
        target.column_case = ""
        sync_target_to_server(db_session, target)

        row = (
            db_session.query(VeeamBackupServer)
            .filter(VeeamBackupServer.target_id == target.id)
            .one()
        )
        assert row.db_type == "auto"
        assert row.column_case == "auto"
