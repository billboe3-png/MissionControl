"""
Veeam integration-profile bridge tests.

A "veeam" IntegrationProfile (Settings -> Integrations) is the user-facing way
to register a Veeam B&R server. The bridge mirrors it into the plugin's live
``veeam_backup_servers`` registry so servers added/edited/deleted after the
initial alembic backfill take effect without a migration.

Covers:
- create (enterprise with base_url, community without)
- update in place (same profile name -> same server row)
- delete removes the row
- non-veeam profiles are no-ops
"""

from app.models.db.integration_profile import IntegrationProfile
from app.plugins.installed.official_veeam.bridge import (
    delete_profile_server,
    sync_profile_to_server,
)
from app.plugins.installed.official_veeam.models import VeeamBackupServer


def _make_profile(
    db,
    name: str = "VBR01",
    *,
    integration_type: str = "veeam",
    base_url: str | None = "https://veeam.example.com",
    username: str = "admin",
    data_source: str = "both",
) -> IntegrationProfile:
    profile = IntegrationProfile(
        name=name,
        integration_type=integration_type,
        base_url=base_url,
        username=username,
        encrypted_secret="gAAAAABcrypted",
        data_source=data_source,
        verify_ssl=True,
        timeout=30,
        enabled=True,
        ssh_host="10.0.0.5",
        ssh_port=22,
        ssh_username="root",
        ssh_password_encrypted="gAAAAABssh",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _get_server(db, name: str) -> VeeamBackupServer | None:
    return db.query(VeeamBackupServer).filter(
        VeeamBackupServer.name == name
    ).one_or_none()


class TestSyncProfileToServer:
    def test_creates_enterprise_row_from_profile(self, db_session):
        profile = _make_profile(db_session, name="VBR01", base_url="https://veeam.example.com")

        sync_profile_to_server(db_session, profile)

        server = _get_server(db_session, "VBR01")
        assert server is not None
        assert server.edition == "enterprise"
        assert server.rest_url == "https://veeam.example.com"
        assert server.rest_username == "admin"
        assert server.rest_password_encrypted == "gAAAAABcrypted"
        assert server.data_source == "both"
        assert server.verify_ssl is True
        assert server.timeout == 30
        assert server.enabled is True
        assert server.status == "unknown"
        assert server.legacy_ssh_host == "10.0.0.5"
        assert server.legacy_ssh_port == 22
        assert server.legacy_ssh_username == "root"
        assert server.legacy_ssh_password_encrypted == "gAAAAABssh"

    def test_creates_community_row_when_no_base_url(self, db_session):
        _make_profile(db_session, name="VBR02", base_url=None)

        sync_profile_to_server(db_session, _make_profile(
            db_session, name="VBR02", base_url=None,
        ))

        server = _get_server(db_session, "VBR02")
        assert server is not None
        assert server.edition == "community"
        assert server.rest_url is None

    def test_updates_existing_row_in_place(self, db_session):
        profile = _make_profile(db_session, name="VBR03", base_url="https://old.example.com")
        sync_profile_to_server(db_session, profile)
        first = _get_server(db_session, "VBR03")
        assert first is not None and first.rest_url == "https://old.example.com"

        profile.base_url = "https://new.example.com"
        db_session.commit()
        sync_profile_to_server(db_session, profile)

        servers = db_session.query(VeeamBackupServer).all()
        assert len(servers) == 1
        assert servers[0].rest_url == "https://new.example.com"
        assert servers[0].edition == "enterprise"

    def test_update_flips_edition_to_community(self, db_session):
        profile = _make_profile(db_session, name="VBR04", base_url="https://old.example.com")
        sync_profile_to_server(db_session, profile)

        profile.base_url = None
        db_session.commit()
        sync_profile_to_server(db_session, profile)

        server = _get_server(db_session, "VBR04")
        assert server is not None
        assert server.edition == "community"
        assert server.rest_url is None

    def test_non_veeam_profile_is_noop(self, db_session):
        profile = _make_profile(db_session, name="zabbix-prod", integration_type="zabbix")

        sync_profile_to_server(db_session, profile)

        assert db_session.query(VeeamBackupServer).count() == 0


class TestDeleteProfileServer:
    def test_deletes_server_row(self, db_session):
        profile = _make_profile(db_session, name="VBR05")
        sync_profile_to_server(db_session, profile)
        assert _get_server(db_session, "VBR05") is not None

        delete_profile_server(db_session, "VBR05")

        assert _get_server(db_session, "VBR05") is None

    def test_delete_missing_row_is_safe(self, db_session):
        delete_profile_server(db_session, "missing")
        assert db_session.query(VeeamBackupServer).count() == 0


class TestIntegrationServiceWiring:
    """End-to-end: creating/updating/deleting a veeam profile syncs the registry.

    This is the regression test for the onboarding gap: before the bridge, a
    ``veeam`` profile created after the initial alembic backfill never produced
    a ``veeam_backup_servers`` row, so every live route returned
    "No Veeam server configured".
    """

    async def test_create_veeam_profile_syncs_server_row(self, db_session):
        from app.schemas.integration import IntegrationProfileCreate
        from app.services.integration_service import IntegrationService

        data = IntegrationProfileCreate(
            name="UI Onboarded VBR",
            integration_type="veeam",
            base_url="https://veeam.corp.local",
            username="admin",
            password="s3cret",
            ssh_host="10.0.0.5",
            ssh_username="root",
            ssh_password="rootpw",
            data_source="both",
            enabled=True,
        )
        service = IntegrationService()
        await service.create_profile(db_session, data)

        server = _get_server(db_session, "UI Onboarded VBR")
        assert server is not None
        assert server.edition == "enterprise"
        assert server.rest_url == "https://veeam.corp.local"
        assert server.enabled is True
        assert server.legacy_ssh_host == "10.0.0.5"
        assert server.rest_password_encrypted is not None

    async def test_update_veeam_profile_updates_server_row(self, db_session):
        from app.schemas.integration import (
            IntegrationProfileCreate,
            IntegrationProfileUpdate,
        )
        from app.services.integration_service import IntegrationService

        service = IntegrationService()
        created = await service.create_profile(
            db_session,
            IntegrationProfileCreate(
                name="VBR Update",
                integration_type="veeam",
                base_url="https://old.example.com",
                username="admin",
                password="s3cret",
            ),
        )
        await service.update_profile(
            db_session,
            created.id,
            IntegrationProfileUpdate(base_url="https://new.example.com"),
        )

        servers = db_session.query(VeeamBackupServer).all()
        assert len(servers) == 1
        assert servers[0].rest_url == "https://new.example.com"
        assert servers[0].edition == "enterprise"

    async def test_delete_veeam_profile_removes_server_row(self, db_session):
        from app.schemas.integration import IntegrationProfileCreate
        from app.services.integration_service import IntegrationService

        service = IntegrationService()
        created = await service.create_profile(
            db_session,
            IntegrationProfileCreate(
                name="VBR Delete",
                integration_type="veeam",
                base_url="https://veeam.example.com",
                username="admin",
                password="s3cret",
            ),
        )
        assert _get_server(db_session, "VBR Delete") is not None

        await service.delete_profile(db_session, created.id)

        assert _get_server(db_session, "VBR Delete") is None
        assert db_session.query(VeeamBackupServer).count() == 0