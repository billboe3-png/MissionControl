"""
Tests for Automation & Playbooks (Sprint 2.8)

Covers: playbooks CRUD, steps, variables, executions,
dry run, rollback, approvals, audit trail, schedules,
event triggers, and automation dashboard.
"""


import pytest
from fastapi.testclient import TestClient

from app.models.db.approval_request import ApprovalRequest
from app.models.db.approval_workflow import ApprovalWorkflow
from app.models.db.playbook import Playbook
from app.models.db.playbook_execution import PlaybookExecution
from app.models.db.playbook_schedule import PlaybookSchedule
from app.models.db.playbook_step import PlaybookStep
from app.models.db.playbook_variable import PlaybookVariable

# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _create_playbook(db, **overrides):
    defaults = {
        "name": "Test Playbook",
        "description": "A test playbook",
        "category": "testing",
        "enabled": True,
        "requires_approval": False,
        "auto_rollback": False,
        "timeout_seconds": 3600,
        "max_retries": 0,
    }
    defaults.update(overrides)
    entity = Playbook(**defaults)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def _create_step(db, playbook_id, **overrides):
    defaults = {
        "playbook_id": playbook_id,
        "name": "Test Step",
        "step_type": "remote_command",
        "provider": "ssh",
        "command": "echo hello",
        "step_order": 1,
        "timeout_seconds": 300,
        "retry_count": 0,
        "continue_on_failure": False,
    }
    defaults.update(overrides)
    entity = PlaybookStep(**defaults)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def _create_variable(db, playbook_id, **overrides):
    defaults = {
        "playbook_id": playbook_id,
        "name": "env",
        "value": "production",
        "variable_type": "string",
        "required": False,
        "sensitive": False,
    }
    defaults.update(overrides)
    entity = PlaybookVariable(**defaults)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


# ------------------------------------------------------------------ #
# Playbook CRUD Tests                                                  #
# ------------------------------------------------------------------ #

class TestPlaybookCRUD:
    """Test playbook create, read, update, delete endpoints."""

    def test_list_playbooks_empty(self, client: TestClient):
        response = client.get("/api/v1/automation/playbooks")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["items"] == []

    def test_create_playbook(self, client: TestClient):
        response = client.post(
            "/api/v1/automation/playbooks",
            json={
                "name": "Deploy App",
                "description": "Deploy to production",
                "category": "deployment",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Deploy App"
        assert data["version"] == 1
        assert data["enabled"] is True
        assert data["requires_approval"] is False
        assert data["auto_rollback"] is False

    def test_get_playbook(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="Get Me")
        response = client.get(f"/api/v1/automation/playbooks/{pb.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Me"

    def test_get_playbook_not_found(self, client: TestClient):
        response = client.get("/api/v1/automation/playbooks/9999")
        assert response.status_code == 404

    def test_update_playbook(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="Original")
        response = client.put(
            f"/api/v1/automation/playbooks/{pb.id}",
            json={"name": "Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["version"] == 2

    def test_delete_playbook(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="Delete Me")
        response = client.delete(
            f"/api/v1/automation/playbooks/{pb.id}"
        )
        assert response.status_code == 204

    def test_list_playbooks_with_search(self, client: TestClient, db_session):
        _create_playbook(db_session, name="Alpha Deploy")
        _create_playbook(db_session, name="Beta Test")
        response = client.get(
            "/api/v1/automation/playbooks?search=alpha"
        )
        assert response.status_code == 200
        assert response.json()["count"] == 1


# ------------------------------------------------------------------ #
# Playbook Step Tests                                                  #
# ------------------------------------------------------------------ #

class TestPlaybookSteps:
    """Test playbook step CRUD endpoints."""

    def test_list_steps_empty(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        response = client.get(
            f"/api/v1/automation/playbooks/{pb.id}/steps"
        )
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_create_step(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/steps",
            json={
                "name": "Run Tests",
                "step_type": "remote_command",
                "provider": "ssh",
                "command": "pytest tests/",
                "step_order": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Run Tests"
        assert data["provider"] == "ssh"
        assert data["command"] == "pytest tests/"

    def test_update_step(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        step = _create_step(db_session, pb.id)
        response = client.put(
            f"/api/v1/automation/steps/{step.id}",
            json={"command": "echo updated"},
        )
        assert response.status_code == 200
        assert response.json()["command"] == "echo updated"

    def test_delete_step(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        step = _create_step(db_session, pb.id)
        response = client.delete(
            f"/api/v1/automation/steps/{step.id}"
        )
        assert response.status_code == 204


# ------------------------------------------------------------------ #
# Playbook Variable Tests                                             #
# ------------------------------------------------------------------ #

class TestPlaybookVariables:
    """Test playbook variable CRUD endpoints."""

    def test_list_variables_empty(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        response = client.get(
            f"/api/v1/automation/playbooks/{pb.id}/variables"
        )
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_create_variable(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/variables",
            json={
                "name": "TARGET_ENV",
                "value": "staging",
                "variable_type": "string",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "TARGET_ENV"
        assert data["value"] == "staging"

    def test_delete_variable(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        var = _create_variable(db_session, pb.id)
        response = client.delete(
            f"/api/v1/automation/variables/{var.id}"
        )
        assert response.status_code == 204


# ------------------------------------------------------------------ #
# Execution Tests                                                      #
# ------------------------------------------------------------------ #

class TestPlaybookExecution:
    """Test playbook execution endpoints."""

    def test_list_executions_empty(self, client: TestClient):
        response = client.get("/api/v1/automation/executions")
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_execute_disabled_playbook(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, enabled=False)
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/execute",
            json={"mode": "live"},
        )
        assert response.status_code == 400

    def test_dry_run(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        _create_step(db_session, pb.id, command="echo test")
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/dry-run",
            json={"variables": {}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "dry_run_completed"
        assert data["steps_total"] == 1

    def test_execute_playbook_with_approval(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, requires_approval=True)
        _create_step(db_session, pb.id)
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/execute",
            json={"mode": "live"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["approval_required"] is True

    def test_rollback_nonexistent(self, client: TestClient):
        response = client.post(
            "/api/v1/automation/executions/9999/rollback",
            json={"reason": "test"},
        )
        assert response.status_code == 404


# ------------------------------------------------------------------ #
# Approval Workflow Tests                                              #
# ------------------------------------------------------------------ #

class TestApprovalWorkflows:
    """Test approval workflow and request endpoints."""

    def test_create_workflow(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/workflows",
            json={
                "name": "Manager Approval",
                "required_approvers": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Manager Approval"
        assert data["required_approvers"] == 1

    def test_list_workflows(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        response = client.get(
            f"/api/v1/automation/playbooks/{pb.id}/workflows"
        )
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_pending_approvals_empty(self, client: TestClient):
        response = client.get("/api/v1/automation/approvals/pending")
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_approve_request(self, client: TestClient, db_session):
        pb = _create_playbook(
            db_session, requires_approval=True
        )
        wf = ApprovalWorkflow(
            playbook_id=pb.id,
            name="Test WF",
            required_approvers=1,
        )
        db_session.add(wf)
        db_session.commit()
        db_session.refresh(wf)

        exec_entity = PlaybookExecution(
            playbook_id=pb.id,
            status="pending",
            approval_required=True,
        )
        db_session.add(exec_entity)
        db_session.commit()
        db_session.refresh(exec_entity)

        ar = ApprovalRequest(
            execution_id=exec_entity.id,
            workflow_id=wf.id,
        )
        db_session.add(ar)
        db_session.commit()
        db_session.refresh(ar)

        response = client.put(
            f"/api/v1/automation/approvals/{ar.id}/approve",
            json={
                "approved_by": "admin",
                "comments": "LGTM",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    def test_reject_request(self, client: TestClient, db_session):
        pb = _create_playbook(
            db_session, requires_approval=True
        )
        wf = ApprovalWorkflow(
            playbook_id=pb.id,
            name="Test WF",
            required_approvers=1,
        )
        db_session.add(wf)
        db_session.commit()
        db_session.refresh(wf)

        exec_entity = PlaybookExecution(
            playbook_id=pb.id,
            status="pending",
            approval_required=True,
        )
        db_session.add(exec_entity)
        db_session.commit()
        db_session.refresh(exec_entity)

        ar = ApprovalRequest(
            execution_id=exec_entity.id,
            workflow_id=wf.id,
        )
        db_session.add(ar)
        db_session.commit()
        db_session.refresh(ar)

        response = client.put(
            f"/api/v1/automation/approvals/{ar.id}/reject",
            json={
                "approved_by": "admin",
                "comments": "Not now",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"


# ------------------------------------------------------------------ #
# Audit Trail Tests                                                    #
# ------------------------------------------------------------------ #

class TestAuditTrail:
    """Test audit trail endpoints."""

    def test_list_audit_empty(self, client: TestClient):
        response = client.get("/api/v1/automation/audit")
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_audit_created_on_playbook_create(
        self, client: TestClient
    ):
        response = client.post(
            "/api/v1/automation/playbooks",
            json={"name": "Audit Test"},
        )
        assert response.status_code == 201

        audit = client.get("/api/v1/automation/audit")
        assert audit.status_code == 200
        data = audit.json()
        assert data["count"] >= 1
        assert any(
            e["action"] == "created" and e["entity_type"] == "playbook"
            for e in data["items"]
        )

    def test_audit_filter(self, client: TestClient):
        client.post(
            "/api/v1/automation/playbooks",
            json={"name": "Filter Test"},
        )
        response = client.get(
            "/api/v1/automation/audit?entity_type=playbook"
        )
        assert response.status_code == 200
        for item in response.json()["items"]:
            assert item["entity_type"] == "playbook"


# ------------------------------------------------------------------ #
# Schedule Tests                                                       #
# ------------------------------------------------------------------ #

class TestSchedules:
    """Test playbook schedule endpoints."""

    def test_list_schedules_empty(self, client: TestClient):
        response = client.get("/api/v1/automation/schedules")
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_create_schedule(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/schedules",
            json={
                "name": "Nightly Run",
                "cron_expression": "0 2 * * *",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Nightly Run"
        assert data["cron_expression"] == "0 2 * * *"
        assert data["enabled"] is True

    def test_delete_schedule(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        sched = PlaybookSchedule(
            playbook_id=pb.id,
            name="To Delete",
            cron_expression="0 * * * *",
        )
        db_session.add(sched)
        db_session.commit()
        db_session.refresh(sched)

        response = client.delete(
            f"/api/v1/automation/schedules/{sched.id}"
        )
        assert response.status_code == 204


# ------------------------------------------------------------------ #
# Event Trigger Tests                                                  #
# ------------------------------------------------------------------ #

class TestEventTriggers:
    """Test event trigger endpoints."""

    def test_list_triggers_empty(self, client: TestClient):
        response = client.get("/api/v1/automation/triggers")
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_create_trigger(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/triggers",
            json={
                "name": "On Deploy",
                "event_type": "deployment.completed",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["event_type"] == "deployment.completed"
        assert data["enabled"] is True
        assert data["trigger_count"] == 0

    def test_fire_event_no_triggers(self, client: TestClient):
        response = client.post(
            "/api/v1/automation/triggers/fire/no.such.event"
        )
        assert response.status_code == 200
        assert response.json()["playbooks_triggered"] == 0


# ------------------------------------------------------------------ #
# Execution Log Tests                                                  #
# ------------------------------------------------------------------ #

class TestExecutionLogs:
    """Test execution log endpoints."""

    def test_list_logs_empty(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        exec_entity = PlaybookExecution(
            playbook_id=pb.id,
            status="completed",
        )
        db_session.add(exec_entity)
        db_session.commit()
        db_session.refresh(exec_entity)

        response = client.get(
            f"/api/v1/automation/executions/{exec_entity.id}/logs"
        )
        assert response.status_code == 200
        assert response.json()["count"] == 0


# ------------------------------------------------------------------ #
# Dashboard Summary Tests                                              #
# ------------------------------------------------------------------ #

class TestAutomationDashboard:
    """Test automation dashboard summary endpoint."""

    def test_dashboard_empty(self, client: TestClient):
        response = client.get("/api/v1/automation/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["total_playbooks"] == 0
        assert data["total_executions"] == 0
        assert data["running"] == 0
        assert data["completed"] == 0
        assert data["failed"] == 0
        assert data["pending_approvals"] == 0

    def test_dashboard_with_data(self, client: TestClient, db_session):
        _create_playbook(db_session, name="PB1")
        _create_playbook(db_session, name="PB2")

        response = client.get("/api/v1/automation/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["total_playbooks"] == 2


# ------------------------------------------------------------------ #
# Provider Factory Tests                                               #
# ------------------------------------------------------------------ #

class TestProviderFactory:
    """Test automation provider factory."""

    def test_get_ssh_provider(self):
        from app.providers.automation.provider_factory import (
            get_automation_provider,
        )

        provider = get_automation_provider("ssh")
        assert provider.provider_name == "ssh"

    def test_get_winrm_provider(self):
        from app.providers.automation.provider_factory import (
            get_automation_provider,
        )

        provider = get_automation_provider("winrm")
        assert provider.provider_name == "winrm"

    def test_get_agent_provider(self):
        from app.providers.automation.provider_factory import (
            get_automation_provider,
        )

        provider = get_automation_provider("agent")
        assert provider.provider_name == "agent"

    def test_get_hyperv_provider(self):
        from app.providers.automation.provider_factory import (
            get_automation_provider,
        )

        provider = get_automation_provider("hyperv")
        assert provider.provider_name == "hyperv"

    def test_get_proxmox_provider(self):
        from app.providers.automation.provider_factory import (
            get_automation_provider,
        )

        provider = get_automation_provider("proxmox")
        assert provider.provider_name == "proxmox"

    def test_unsupported_provider(self):
        from app.providers.automation.provider_factory import (
            get_automation_provider,
        )

        with pytest.raises(ValueError, match="Unsupported"):
            get_automation_provider("docker")
