"""
Mission Control remote target move tests.

Covers POST /api/v1/agents/{agent_id}/remote-targets/{target_id}/move:
- Ownership / argument validation (404 / 400).
- enabled_plugins merged add-only into the destination agent.
- Veeam server registry row follows the target.
- MikroTik relay pairing cascades to the new agent.
- Integration profiles with matching ssh_host move when move_profiles is set.
"""

from app.models.db.agent import Agent


def _register_agent(client, name: str) -> dict:
    resp = client.post(
        "/api/v1/agents/register",
        json={"name": name, "hostname": name.lower().replace(" ", ".") + ".local"},
    )
    assert resp.status_code == 201
    return resp.json()


def _create_target(client, agent_id: int, **overrides) -> dict:
    payload = {
        "name": "Move Target",
        "hostname": "192.168.10.49",
        "protocol": "ssh",
        "port": 22,
        "username": "kg\\administrator",
        "password": "secret",
        "target_plugins": "veeam,hyperv",
    }
    payload.update(overrides)
    resp = client.post(f"/api/v1/agents/{agent_id}/remote-targets", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _move(client, source_id: int, target_id: int, new_agent_id: int, **extra):
    payload = {"new_agent_id": new_agent_id}
    payload.update(extra)
    return client.post(
        f"/api/v1/agents/{source_id}/remote-targets/{target_id}/move",
        json=payload,
    )


class TestRemoteTargetMoveValidation:
    def test_move_reassigns_agent_id(self, client):
        src = _register_agent(client, "Move Source")
        dst = _register_agent(client, "Move Destination")
        target = _create_target(client, src["agent_id"])

        resp = _move(client, src["agent_id"], target["id"], dst["agent_id"])
        assert resp.status_code == 200, resp.text
        assert resp.json()["agent_id"] == dst["agent_id"]

        src_list = client.get(f"/api/v1/agents/{src['agent_id']}/remote-targets")
        assert src_list.json()["targets"] == []
        dst_list = client.get(f"/api/v1/agents/{dst['agent_id']}/remote-targets")
        assert len(dst_list.json()["targets"]) == 1

    def test_move_wrong_source_agent_404(self, client):
        src = _register_agent(client, "Move Wrong Owner")
        other = _register_agent(client, "Move Bystander")
        dst = _register_agent(client, "Move Wrong Dest")
        target = _create_target(client, src["agent_id"])

        resp = _move(client, other["agent_id"], target["id"], dst["agent_id"])
        assert resp.status_code == 404

    def test_move_missing_target_404(self, client):
        src = _register_agent(client, "Move No Target")
        dst = _register_agent(client, "Move No Target Dest")
        resp = _move(client, src["agent_id"], 999999, dst["agent_id"])
        assert resp.status_code == 404

    def test_move_missing_destination_agent_404(self, client):
        src = _register_agent(client, "Move Bad Dest")
        target = _create_target(client, src["agent_id"])
        resp = _move(client, src["agent_id"], target["id"], 999999)
        assert resp.status_code == 404

    def test_move_same_agent_400(self, client):
        src = _register_agent(client, "Move Same Agent")
        target = _create_target(client, src["agent_id"])
        resp = _move(client, src["agent_id"], target["id"], src["agent_id"])
        assert resp.status_code == 400


class TestRemoteTargetMovePluginCascade:
    def test_plugins_merged_into_destination_add_only(self, client, db_session):
        src = _register_agent(client, "Move Plugins Source")
        dst = _register_agent(client, "Move Plugins Dest")
        dst_agent = db_session.get(Agent, dst["agent_id"])
        dst_agent.enabled_plugins = "linux"
        db_session.commit()

        target = _create_target(client, src["agent_id"])
        resp = _move(client, src["agent_id"], target["id"], dst["agent_id"])
        assert resp.status_code == 200

        db_session.refresh(dst_agent)
        assert dst_agent.enabled_plugins == "linux,veeam,hyperv"

        src_agent = db_session.get(Agent, src["agent_id"])
        assert "veeam" not in (src_agent.enabled_plugins or "")

    def test_existing_destination_plugins_not_duplicated(self, client, db_session):
        src = _register_agent(client, "Move Dup Source")
        dst = _register_agent(client, "Move Dup Dest")
        dst_agent = db_session.get(Agent, dst["agent_id"])
        dst_agent.enabled_plugins = "veeam,linux"
        db_session.commit()

        target = _create_target(client, src["agent_id"])
        resp = _move(client, src["agent_id"], target["id"], dst["agent_id"])
        assert resp.status_code == 200

        db_session.refresh(dst_agent)
        assert dst_agent.enabled_plugins == "veeam,linux,hyperv"

    def test_move_without_plugins_leaves_destination_untouched(
        self, client, db_session
    ):
        src = _register_agent(client, "Move Null Plugins Source")
        dst = _register_agent(client, "Move Null Plugins Dest")
        target = _create_target(client, src["agent_id"], target_plugins=None)

        resp = _move(client, src["agent_id"], target["id"], dst["agent_id"])
        assert resp.status_code == 200

        db_session.refresh(db_session.get(Agent, dst["agent_id"]))
        assert db_session.get(Agent, dst["agent_id"]).enabled_plugins in (
            None,
            "",
        )


class TestRemoteTargetMoveRegistries:
    def test_veeam_server_row_follows_target(self, client, db_session):
        from app.plugins.installed.official_veeam.models import VeeamBackupServer

        src = _register_agent(client, "Move Veeam Source")
        dst = _register_agent(client, "Move Veeam Dest")
        target = _create_target(client, src["agent_id"], target_plugins="veeam")

        row = (
            db_session.query(VeeamBackupServer)
            .filter(VeeamBackupServer.target_id == target["id"])
            .one()
        )
        assert row.agent_id == src["agent_id"]

        resp = _move(client, src["agent_id"], target["id"], dst["agent_id"])
        assert resp.status_code == 200
        db_session.refresh(row)
        assert row.agent_id == dst["agent_id"]

    def test_mikrotik_relay_cascades(self, client, db_session):
        from app.plugins.installed.official_mikrotik.models import MikroTikServer

        src = _register_agent(client, "Move MT Source")
        dst = _register_agent(client, "Move MT Dest")
        target = _create_target(client, src["agent_id"])

        row = MikroTikServer(
            name="Move Relay",
            host="192.168.88.1",
            username="admin",
            relay_agent_id=src["agent_id"],
            remote_target_id=target["id"],
        )
        db_session.add(row)
        db_session.commit()

        resp = _move(client, src["agent_id"], target["id"], dst["agent_id"])
        assert resp.status_code == 200
        db_session.refresh(row)
        assert row.relay_agent_id == dst["agent_id"]
        assert row.remote_target_id == target["id"]


class TestRemoteTargetMoveProfiles:
    def _create_profile(self, client, agent_id: int, ssh_host: str) -> dict:
        resp = client.post(
            "/api/v1/integrations",
            json={
                "name": f"AD Profile {agent_id}-{ssh_host}",
                "integration_type": "active_directory",
                "agent_id": agent_id,
                "ssh_host": ssh_host,
                "enabled": True,
            },
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    def _profile_agent_id(self, db_session, profile_id: int) -> int | None:
        # The API response omits agent_id (integration_service._to_response
        # never passes it), so assert against the database.
        from app.models.db.integration_profile import IntegrationProfile

        db_session.expire_all()
        row = (
            db_session.query(IntegrationProfile)
            .filter(IntegrationProfile.id == profile_id)
            .one()
        )
        return row.agent_id

    def test_matching_profile_moves_case_insensitive(self, client, db_session):
        src = _register_agent(client, "Move Profile Source")
        dst = _register_agent(client, "Move Profile Dest")
        target = _create_target(client, src["agent_id"], hostname="DC01.corp.local")
        profile = self._create_profile(
            client, src["agent_id"], ssh_host="dc01.CORP.LOCAL"
        )

        resp = _move(client, src["agent_id"], target["id"], dst["agent_id"])
        assert resp.status_code == 200

        assert self._profile_agent_id(db_session, profile["id"]) == dst["agent_id"]

    def test_non_matching_profile_stays(self, client, db_session):
        src = _register_agent(client, "Move Profile Stay Source")
        dst = _register_agent(client, "Move Profile Stay Dest")
        target = _create_target(client, src["agent_id"], hostname="192.168.10.49")
        profile = self._create_profile(
            client, src["agent_id"], ssh_host="other-host.corp.local"
        )

        resp = _move(client, src["agent_id"], target["id"], dst["agent_id"])
        assert resp.status_code == 200

        assert self._profile_agent_id(db_session, profile["id"]) == src["agent_id"]

    def test_move_profiles_false_skips_cascade(self, client, db_session):
        src = _register_agent(client, "Move Profile Skip Source")
        dst = _register_agent(client, "Move Profile Skip Dest")
        target = _create_target(client, src["agent_id"], hostname="DC02.corp.local")
        profile = self._create_profile(
            client, src["agent_id"], ssh_host="DC02.corp.local"
        )

        resp = _move(
            client,
            src["agent_id"],
            target["id"],
            dst["agent_id"],
            move_profiles=False,
        )
        assert resp.status_code == 200

        assert self._profile_agent_id(db_session, profile["id"]) == src["agent_id"]
