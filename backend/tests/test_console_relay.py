"""Tests for the agent-relayed interactive console.

Covers the in-memory session manager contract and the edge console I/O
endpoint used by agents to stream PTY bytes. The WebSocket bridge itself
is exercised lightly (auth rejection) since full duplex PTY behavior is
verified against a live agent.
"""

import json

import pytest

from app.services.console_session_manager import ConsoleSessionManager
from app.services.console_session_manager import manager as global_manager


@pytest.fixture
def registered_agent(client):
    resp = client.post(
        "/api/v1/agents/register",
        json={"name": "Console Agent", "hostname": "console.agent.local"},
    )
    assert resp.status_code == 201
    return resp.json()["agent_id"], resp.json()["api_key"]


# ------------------------------------------------------------------ #
# Session manager unit behaviour
# ------------------------------------------------------------------ #


def test_create_session_enqueues_start_op_for_agent():
    mgr = ConsoleSessionManager()
    session = mgr.create_session(agent_id=7, host_id=1, hostname="veeam.lan")

    assert session.status == "pending"
    ops = mgr.drain_pending_ops(7)
    assert len(ops) == 1
    op = ops[0]
    assert op["session_id"] == session.session_id
    assert op["hostname"] == "veeam.lan"
    # Draining twice returns nothing.
    assert mgr.drain_pending_ops(7) == []


def test_apply_agent_update_ownership_check():
    mgr = ConsoleSessionManager()
    session = mgr.create_session(agent_id=7, host_id=1, hostname="veeam.lan")

    # Wrong agent id must not touch the session and must close the relay.
    reply = mgr.apply_agent_update(
        agent_id=99, session_id=session.session_id, output="nope"
    )
    assert reply["closed"] is True
    assert reply["input"] == []

    # Correct agent id works.
    reply = mgr.apply_agent_update(
        agent_id=7,
        session_id=session.session_id,
        output="hello",
        status="connected",
    )
    assert reply["closed"] is False
    stored = mgr.get_session(session.session_id)
    assert stored.status == "connected"
    assert stored.buffer == "hello"


def test_input_resize_close_round_trip():
    mgr = ConsoleSessionManager()
    session = mgr.create_session(agent_id=7, host_id=1, hostname="veeam.lan")
    sid = session.session_id

    mgr.send_input(sid, "ls\r")
    mgr.request_resize(sid, 200, 50)

    reply = mgr.apply_agent_update(agent_id=7, session_id=sid, status="connected")
    assert reply["input"] == ["ls\r"]
    assert reply["resize"] == {"width": 200, "height": 50}
    assert reply["closed"] is False

    # Queues are drained after each post.
    reply = mgr.apply_agent_update(agent_id=7, session_id=sid)
    assert reply["input"] == []
    assert reply["resize"] is None

    mgr.request_close(sid)
    reply = mgr.apply_agent_update(agent_id=7, session_id=sid)
    assert reply["closed"] is True


def test_read_output_cursor_semantics():
    mgr = ConsoleSessionManager()
    session = mgr.create_session(agent_id=7, host_id=1, hostname="veeam.lan")
    sid = session.session_id

    chunk, cursor = mgr.read_output(sid, 0)
    assert chunk == "" and cursor == 0

    mgr.apply_agent_update(agent_id=7, session_id=sid, output="abc")
    chunk, cursor = mgr.read_output(sid, 0)
    assert chunk == "abc" and cursor == 3

    mgr.apply_agent_update(agent_id=7, session_id=sid, output="def")
    chunk, cursor = mgr.read_output(sid, cursor)
    assert chunk == "def" and cursor == 6
    chunk, _ = mgr.read_output(sid, cursor)
    assert chunk == ""


def test_exited_status_closes_session():
    mgr = ConsoleSessionManager()
    session = mgr.create_session(agent_id=7, host_id=1, hostname="veeam.lan")
    sid = session.session_id

    mgr.apply_agent_update(
        agent_id=7, session_id=sid, status="exited", exit_code=0
    )
    stored = mgr.get_session(sid)
    assert stored.status == "closed"
    assert stored.exit_code == 0
    reply = mgr.apply_agent_update(agent_id=7, session_id=sid)
    assert reply["closed"] is True


def test_stale_sessions_are_swept():
    mgr = ConsoleSessionManager()
    session = mgr.create_session(agent_id=7, host_id=1, hostname="veeam.lan")
    session.last_activity -= mgr.STALE_AFTER + 1

    # Any new create triggers the sweep.
    mgr.create_session(agent_id=8, host_id=2, hostname="other.lan")
    swept = mgr.get_session(session.session_id)
    assert swept.status == "closed"


# ------------------------------------------------------------------ #
# Edge HTTP surface
# ------------------------------------------------------------------ #


def test_edge_commands_inject_console_start(client, registered_agent):
    agent_id, api_key = registered_agent
    session = global_manager.create_session(
        agent_id=agent_id, host_id=999, hostname="veeam.lan", width=150, height=45
    )

    resp = client.get(
        f"/api/v1/edge/{agent_id}/commands",
        headers={"X-Agent-API-Key": api_key},
    )
    assert resp.status_code == 200
    commands = resp.json()["commands"]
    starts = [c for c in commands if c["command_type"] == "console_start"]
    assert len(starts) == 1
    payload = json.loads(starts[0]["command"])
    assert payload["session_id"] == session.session_id
    assert payload["hostname"] == "veeam.lan"
    assert payload["width"] == 150
    assert payload["height"] == 45


def test_edge_console_io_round_trip(client, registered_agent):
    agent_id, api_key = registered_agent
    session = global_manager.create_session(
        agent_id=agent_id, host_id=999, hostname="veeam.lan"
    )
    global_manager.send_input(session.session_id, "whoami\r")

    resp = client.post(
        f"/api/v1/edge/{agent_id}/console/io",
        headers={"X-Agent-API-Key": api_key},
        json={
            "session_id": session.session_id,
            "output": "$ ",
            "status": "connected",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["input"] == ["whoami\r"]
    assert body["closed"] is False

    stored = global_manager.get_session(session.session_id)
    assert stored.buffer == "$ "
    assert stored.status == "connected"


def test_edge_console_io_rejects_wrong_agent(client, registered_agent):
    agent_id, api_key = registered_agent
    other = client.post(
        "/api/v1/agents/register",
        json={"name": "Other Agent", "hostname": "other.agent.local"},
    )
    other_id = other.json()["agent_id"]

    session = global_manager.create_session(
        agent_id=agent_id, host_id=999, hostname="veeam.lan"
    )
    resp = client.post(
        f"/api/v1/edge/{other_id}/console/io",
        headers={"X-Agent-API-Key": api_key},
        json={"session_id": session.session_id, "output": "hijack"},
    )
    assert resp.status_code == 403


def test_edge_console_io_unknown_session_returns_closed(client, registered_agent):
    agent_id, api_key = registered_agent
    resp = client.post(
        f"/api/v1/edge/{agent_id}/console/io",
        headers={"X-Agent-API-Key": api_key},
        json={"session_id": "does-not-exist", "output": "x"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"closed": True, "input": [], "resize": None}


def test_console_agent_ws_requires_token(client):
    with client.websocket_connect(
        "/api/v1/remote/console-agent?host_id=1&agent_id=1"
    ) as ws:
        msg = ws.receive_json()
    assert msg["type"] == "error"
    assert msg["message"] == "Unauthorized"
