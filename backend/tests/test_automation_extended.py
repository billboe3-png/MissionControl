"""
Extended tests for Automation & Playbooks (Sprint 2.8 Phase 9)

Covers: providers (bash, powershell, http), clone, export, import,
retry logic, variable substitution, fire_event, provider factory,
dashboard automation, execution logs, and all new features.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.db.playbook import Playbook
from app.models.db.playbook_step import PlaybookStep
from app.models.db.playbook_variable import PlaybookVariable
from app.models.db.playbook_execution import PlaybookExecution
from app.models.db.execution_log import ExecutionLog
from app.models.db.event_trigger import EventTrigger
from app.models.db.audit_trail import AuditTrail
from app.providers.automation.base_provider import ExecutionContext, StepResult


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


def _make_context(**overrides):
    defaults = {
        "playbook_id": 1,
        "execution_id": 1,
        "step_id": 1,
        "step_name": "Test Step",
        "command": "echo hello",
        "provider": "bash",
    }
    defaults.update(overrides)
    return ExecutionContext(**defaults)


# ------------------------------------------------------------------ #
# Provider Factory Tests — New Providers                               #
# ------------------------------------------------------------------ #

class TestProviderFactoryNew:
    """Test factory returns correct new providers."""

    def test_get_bash_provider(self):
        from app.providers.automation.provider_factory import get_automation_provider
        p = get_automation_provider("bash")
        assert p.provider_name == "bash"
        assert "shell" in p.supported_step_types

    def test_get_powershell_provider(self):
        from app.providers.automation.provider_factory import get_automation_provider
        p = get_automation_provider("powershell")
        assert p.provider_name == "powershell"
        assert "powershell" in p.supported_step_types

    def test_get_http_provider(self):
        from app.providers.automation.provider_factory import get_automation_provider
        p = get_automation_provider("http")
        assert p.provider_name == "http"
        assert "webhook" in p.supported_step_types

    def test_get_all_providers(self):
        from app.providers.automation.provider_factory import get_all_providers
        providers = get_all_providers()
        assert len(providers) >= 8
        for name in ["bash", "powershell", "http", "ssh", "winrm", "agent", "hyperv", "proxmox"]:
            assert name in providers

    def test_provider_singleton(self):
        from app.providers.automation.provider_factory import get_automation_provider
        p1 = get_automation_provider("bash")
        p2 = get_automation_provider("bash")
        assert p1 is p2


# ------------------------------------------------------------------ #
# Bash Provider Tests                                                  #
# ------------------------------------------------------------------ #

class TestBashProvider:
    """Test BashAutomationProvider execution and validation."""

    @pytest.mark.asyncio
    async def test_execute_echo(self):
        from app.providers.automation.bash_provider import BashAutomationProvider
        provider = BashAutomationProvider()
        ctx = _make_context(command="echo hello world")
        result = await provider.execute_step(ctx)
        assert result.success is True
        assert "hello world" in result.stdout
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_execute_failing_command(self):
        from app.providers.automation.bash_provider import BashAutomationProvider
        provider = BashAutomationProvider()
        ctx = _make_context(command="exit 1")
        result = await provider.execute_step(ctx)
        assert result.success is False
        assert result.exit_code == 1

    @pytest.mark.asyncio
    async def test_execute_variable_substitution(self):
        from app.providers.automation.bash_provider import BashAutomationProvider
        provider = BashAutomationProvider()
        ctx = _make_context(
            command="echo {{target}}",
            variables={"target": "production"},
        )
        result = await provider.execute_step(ctx)
        assert result.success is True
        assert "production" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_with_working_directory(self):
        from app.providers.automation.bash_provider import BashAutomationProvider
        provider = BashAutomationProvider()
        ctx = _make_context(command="pwd", working_directory="/tmp")
        result = await provider.execute_step(ctx)
        assert result.success is True
        assert "/tmp" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_with_env_vars(self):
        from app.providers.automation.bash_provider import BashAutomationProvider
        provider = BashAutomationProvider()
        ctx = _make_context(
            command="echo $MY_VAR",
            environment_variables={"MY_VAR": "test_value"},
        )
        result = await provider.execute_step(ctx)
        assert result.success is True
        assert "test_value" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        from app.providers.automation.bash_provider import BashAutomationProvider
        provider = BashAutomationProvider()
        ctx = _make_context(command="sleep 10", timeout_seconds=1)
        result = await provider.execute_step(ctx)
        assert result.success is False
        assert "timed out" in (result.error or "")

    @pytest.mark.asyncio
    async def test_validate_valid(self):
        from app.providers.automation.bash_provider import BashAutomationProvider
        provider = BashAutomationProvider()
        ctx = _make_context(command="echo test")
        result = await provider.validate_step(ctx)
        assert result["valid"] is True
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_validate_no_command(self):
        from app.providers.automation.bash_provider import BashAutomationProvider
        provider = BashAutomationProvider()
        ctx = _make_context(command="")
        result = await provider.validate_step(ctx)
        assert result["valid"] is False
        assert "Command is required" in result["errors"]

    @pytest.mark.asyncio
    async def test_rollback(self):
        from app.providers.automation.bash_provider import BashAutomationProvider
        provider = BashAutomationProvider()
        ctx = _make_context(command="echo step")
        result = await provider.rollback_step(ctx, "echo rollback_done")
        assert result.success is True
        assert "rollback_done" in result.stdout

    def test_provider_name(self):
        from app.providers.automation.bash_provider import BashAutomationProvider
        provider = BashAutomationProvider()
        assert provider.provider_name == "bash"

    def test_supported_step_types(self):
        from app.providers.automation.bash_provider import BashAutomationProvider
        provider = BashAutomationProvider()
        assert set(provider.supported_step_types) == {"bash", "shell", "remote_command"}


# ------------------------------------------------------------------ #
# PowerShell Provider Tests                                            #
# ------------------------------------------------------------------ #

class TestPowerShellProvider:
    """Test PowerShellAutomationProvider execution and validation."""

    @pytest.mark.asyncio
    async def test_execute_echo(self):
        from app.providers.automation.powershell_provider import PowerShellAutomationProvider
        provider = PowerShellAutomationProvider()
        ctx = _make_context(command="Write-Output 'hello ps'", provider="powershell")
        result = await provider.execute_step(ctx)
        if result.success is False and "not found" in (result.error or "").lower():
            pytest.skip("PowerShell not available in test env")
        assert result.success is True
        assert "hello ps" in result.stdout

    @pytest.mark.asyncio
    async def test_validate_valid(self):
        from app.providers.automation.powershell_provider import PowerShellAutomationProvider
        provider = PowerShellAutomationProvider()
        ctx = _make_context(command="Get-Process", provider="powershell")
        result = await provider.validate_step(ctx)
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_no_command(self):
        from app.providers.automation.powershell_provider import PowerShellAutomationProvider
        provider = PowerShellAutomationProvider()
        ctx = _make_context(command="", provider="powershell")
        result = await provider.validate_step(ctx)
        assert result["valid"] is False
        assert "Command is required" in result["errors"]

    def test_provider_name(self):
        from app.providers.automation.powershell_provider import PowerShellAutomationProvider
        provider = PowerShellAutomationProvider()
        assert provider.provider_name == "powershell"

    def test_supported_step_types(self):
        from app.providers.automation.powershell_provider import PowerShellAutomationProvider
        provider = PowerShellAutomationProvider()
        assert set(provider.supported_step_types) == {"powershell", "shell"}


# ------------------------------------------------------------------ #
# HTTP Provider Tests                                                  #
# ------------------------------------------------------------------ #

class TestHTTPProvider:
    """Test HTTPAutomationProvider validation and JSON parsing."""

    @pytest.mark.asyncio
    async def test_validate_json_request(self):
        from app.providers.automation.http_provider import HTTPAutomationProvider
        provider = HTTPAutomationProvider()
        ctx = _make_context(
            command=json.dumps({"method": "GET", "url": "http://example.com"}),
            provider="http",
        )
        result = await provider.validate_step(ctx)
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_no_url_in_json(self):
        from app.providers.automation.http_provider import HTTPAutomationProvider
        provider = HTTPAutomationProvider()
        ctx = _make_context(
            command=json.dumps({"method": "GET"}),
            provider="http",
        )
        result = await provider.validate_step(ctx)
        assert result["valid"] is False
        assert any("url" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_raw_url(self):
        from app.providers.automation.http_provider import HTTPAutomationProvider
        provider = HTTPAutomationProvider()
        ctx = _make_context(
            command="http://example.com/api",
            provider="http",
        )
        result = await provider.validate_step(ctx)
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_no_command(self):
        from app.providers.automation.http_provider import HTTPAutomationProvider
        provider = HTTPAutomationProvider()
        ctx = _make_context(command="", provider="http")
        result = await provider.validate_step(ctx)
        assert result["valid"] is False
        assert "Command/request is required" in result["errors"]

    @pytest.mark.asyncio
    async def test_validate_non_url_warning(self):
        from app.providers.automation.http_provider import HTTPAutomationProvider
        provider = HTTPAutomationProvider()
        ctx = _make_context(
            command="not_a_url_at_all",
            provider="http",
        )
        result = await provider.validate_step(ctx)
        assert result["valid"] is True
        assert len(result["warnings"]) > 0

    @pytest.mark.asyncio
    async def test_execute_no_url(self):
        from app.providers.automation.http_provider import HTTPAutomationProvider
        provider = HTTPAutomationProvider()
        ctx = _make_context(
            command=json.dumps({"method": "GET"}),
            provider="http",
        )
        result = await provider.execute_step(ctx)
        assert result.success is False
        assert "No URL" in result.error

    def test_provider_name(self):
        from app.providers.automation.http_provider import HTTPAutomationProvider
        provider = HTTPAutomationProvider()
        assert provider.provider_name == "http"

    def test_supported_step_types(self):
        from app.providers.automation.http_provider import HTTPAutomationProvider
        provider = HTTPAutomationProvider()
        assert set(provider.supported_step_types) == {"http", "webhook", "api_call"}


# ------------------------------------------------------------------ #
# Variable Substitution Tests                                          #
# ------------------------------------------------------------------ #

class TestVariableSubstitution:
    """Test AutomationService.substitute_variables static method."""

    def test_simple_substitution(self):
        from app.services.automation_service import AutomationService
        result = AutomationService.substitute_variables(
            "Hello {{name}}", {"name": "World"}
        )
        assert result == "Hello World"

    def test_multiple_vars(self):
        from app.services.automation_service import AutomationService
        result = AutomationService.substitute_variables(
            "{{greet}} {{name}}, env={{env}}",
            {"greet": "Hello", "name": "Bob", "env": "prod"},
        )
        assert result == "Hello Bob, env=prod"

    def test_no_vars(self):
        from app.services.automation_service import AutomationService
        result = AutomationService.substitute_variables(
            "No placeholders here", {}
        )
        assert result == "No placeholders here"

    def test_recursive_substitution(self):
        from app.services.automation_service import AutomationService
        result = AutomationService.substitute_variables(
            "{{a}}",
            {"a": "{{b}}", "b": "final"},
        )
        assert result == "final"

    def test_max_depth_limit(self):
        from app.services.automation_service import AutomationService
        result = AutomationService.substitute_variables(
            "{{a}}", {"a": "{{a}}"}, max_depth=1
        )
        assert result == "{{a}}"

    def test_empty_text(self):
        from app.services.automation_service import AutomationService
        result = AutomationService.substitute_variables("", {"key": "val"})
        assert result == ""

    def test_unresolved_var_stays(self):
        from app.services.automation_service import AutomationService
        result = AutomationService.substitute_variables(
            "Hello {{missing}}", {}
        )
        assert result == "Hello {{missing}}"

    def test_same_var_replaced(self):
        from app.services.automation_service import AutomationService
        result = AutomationService.substitute_variables(
            "{{x}} and {{x}}", {"x": "Y"}
        )
        assert result == "Y and Y"

    def test_nested_curly_braces_ignored(self):
        from app.services.automation_service import AutomationService
        result = AutomationService.substitute_variables(
            "{{{a}}}", {"a": "X"}
        )
        assert result == "{X}"

    def test_max_depth_3(self):
        from app.services.automation_service import AutomationService
        result = AutomationService.substitute_variables(
            "{{a}}", {"a": "{{b}}", "b": "{{c}}", "c": "deep"}
        )
        assert result == "deep"


# ------------------------------------------------------------------ #
# Clone Playbook Tests                                                 #
# ------------------------------------------------------------------ #

class TestClonePlaybook:
    """Test clone endpoint and service logic."""

    def test_clone_creates_new_playbook(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="Original")
        _create_step(db_session, pb.id, name="Step 1")
        _create_variable(db_session, pb.id, name="var1", value="val1")

        response = client.post(f"/api/v1/automation/playbooks/{pb.id}/clone")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Original (Copy)"
        assert data["enabled"] is False
        assert data["id"] != pb.id

    def test_clone_copies_steps(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="With Steps")
        _create_step(db_session, pb.id, name="S1", command="echo 1")
        _create_step(db_session, pb.id, name="S2", command="echo 2", step_order=2)

        response = client.post(f"/api/v1/automation/playbooks/{pb.id}/clone")
        clone_id = response.json()["id"]

        steps = client.get(f"/api/v1/automation/playbooks/{clone_id}/steps")
        assert steps.status_code == 200
        assert steps.json()["count"] == 2

    def test_clone_copies_variables(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="With Vars")
        _create_variable(db_session, pb.id, name="env", value="prod")

        response = client.post(f"/api/v1/automation/playbooks/{pb.id}/clone")
        clone_id = response.json()["id"]

        vars_resp = client.get(f"/api/v1/automation/playbooks/{clone_id}/variables")
        assert vars_resp.status_code == 200
        assert vars_resp.json()["count"] == 1
        assert vars_resp.json()["items"][0]["name"] == "env"

    def test_clone_with_custom_name(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="Source")
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/clone?name=My+Clone"
        )
        assert response.status_code == 200
        assert response.json()["name"] == "My Clone"

    def test_clone_not_found(self, client: TestClient):
        response = client.post("/api/v1/automation/playbooks/9999/clone")
        assert response.status_code == 404

    def test_clone_disabled(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="Active")
        response = client.post(f"/api/v1/automation/playbooks/{pb.id}/clone")
        assert response.json()["enabled"] is False

    def test_clone_preserves_settings(self, client: TestClient, db_session):
        pb = _create_playbook(
            db_session, name="Configured",
            requires_approval=True, auto_rollback=True,
            timeout_seconds=7200, max_retries=3,
        )
        response = client.post(f"/api/v1/automation/playbooks/{pb.id}/clone")
        data = response.json()
        assert data["requires_approval"] is True
        assert data["auto_rollback"] is True
        assert data["timeout_seconds"] == 7200
        assert data["max_retries"] == 3


# ------------------------------------------------------------------ #
# Export Playbook Tests                                                #
# ------------------------------------------------------------------ #

class TestExportPlaybook:
    """Test export endpoint and format."""

    def test_export_basic(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="Export Me")
        response = client.get(f"/api/v1/automation/playbooks/{pb.id}/export")
        assert response.status_code == 200
        data = response.json()
        assert "playbook" in data
        assert "steps" in data
        assert "variables" in data
        assert data["playbook"]["name"] == "Export Me"

    def test_export_includes_steps(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        _create_step(db_session, pb.id, command="echo test")
        response = client.get(f"/api/v1/automation/playbooks/{pb.id}/export")
        data = response.json()
        assert len(data["steps"]) == 1
        assert data["steps"][0]["command"] == "echo test"

    def test_export_includes_variables(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        _create_variable(db_session, pb.id, name="env", value="prod")
        response = client.get(f"/api/v1/automation/playbooks/{pb.id}/export")
        data = response.json()
        assert len(data["variables"]) == 1
        assert data["variables"][0]["name"] == "env"

    def test_export_hides_sensitive(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        _create_variable(
            db_session, pb.id, name="secret",
            value="s3cret", sensitive=True,
        )
        response = client.get(f"/api/v1/automation/playbooks/{pb.id}/export")
        var = response.json()["variables"][0]
        assert var["sensitive"] is True
        assert var["value"] is None

    def test_export_not_found(self, client: TestClient):
        response = client.get("/api/v1/automation/playbooks/9999/export")
        assert response.status_code == 404

    def test_export_playbook_fields(self, client: TestClient, db_session):
        pb = _create_playbook(
            db_session, name="Full Export",
            category="deployment", requires_approval=True,
            auto_rollback=True, timeout_seconds=600, max_retries=2,
        )
        response = client.get(f"/api/v1/automation/playbooks/{pb.id}/export")
        data = response.json()["playbook"]
        assert data["name"] == "Full Export"
        assert data["category"] == "deployment"
        assert data["requires_approval"] is True
        assert data["auto_rollback"] is True
        assert data["timeout_seconds"] == 600
        assert data["max_retries"] == 2


# ------------------------------------------------------------------ #
# Import Playbook Tests                                                #
# ------------------------------------------------------------------ #

class TestImportPlaybook:
    """Test import endpoint."""

    def test_import_basic(self, client: TestClient):
        payload = {
            "playbook": {
                "name": "Imported PB",
                "description": "From import",
                "category": "testing",
            },
            "steps": [],
            "variables": [],
        }
        response = client.post(
            "/api/v1/automation/playbooks/import",
            json=payload,
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["name"] == "Imported PB"
        assert data["enabled"] is False
        assert data["created_by"] == "import"

    def test_import_with_steps(self, client: TestClient):
        payload = {
            "playbook": {"name": "PB With Steps"},
            "steps": [
                {"name": "Step 1", "command": "echo 1", "step_order": 1},
                {"name": "Step 2", "command": "echo 2", "step_order": 2},
            ],
            "variables": [],
        }
        response = client.post(
            "/api/v1/automation/playbooks/import",
            json=payload,
        )
        assert response.status_code == 201
        pb_id = response.json()["id"]
        steps = client.get(f"/api/v1/automation/playbooks/{pb_id}/steps")
        assert steps.json()["count"] == 2

    def test_import_with_variables(self, client: TestClient):
        payload = {
            "playbook": {"name": "PB With Vars"},
            "steps": [],
            "variables": [
                {"name": "env", "value": "prod", "variable_type": "string"},
            ],
        }
        response = client.post(
            "/api/v1/automation/playbooks/import",
            json=payload,
        )
        assert response.status_code == 201
        pb_id = response.json()["id"]
        vars_resp = client.get(f"/api/v1/automation/playbooks/{pb_id}/variables")
        assert vars_resp.json()["count"] == 1
        assert vars_resp.json()["items"][0]["name"] == "env"

    def test_import_duplicate_name(self, client: TestClient):
        payload1 = {
            "playbook": {"name": "Same Name"},
            "steps": [],
            "variables": [],
        }
        client.post("/api/v1/automation/playbooks/import", json=payload1)

        payload2 = {
            "playbook": {"name": "Same Name"},
            "steps": [],
            "variables": [],
        }
        response = client.post(
            "/api/v1/automation/playbooks/import",
            json=payload2,
        )
        assert response.status_code == 201
        assert "(Imported)" in response.json()["name"]

    def test_import_preserves_settings(self, client: TestClient):
        payload = {
            "playbook": {
                "name": "Full Import",
                "requires_approval": True,
                "auto_rollback": True,
                "timeout_seconds": 1800,
                "max_retries": 5,
            },
            "steps": [],
            "variables": [],
        }
        response = client.post(
            "/api/v1/automation/playbooks/import",
            json=payload,
        )
        data = response.json()
        assert data["requires_approval"] is True
        assert data["auto_rollback"] is True
        assert data["timeout_seconds"] == 1800
        assert data["max_retries"] == 5

    def test_import_empty_playbook_name(self, client: TestClient):
        payload = {
            "playbook": {},
            "steps": [],
            "variables": [],
        }
        response = client.post(
            "/api/v1/automation/playbooks/import",
            json=payload,
        )
        assert response.status_code == 201
        assert "Imported Playbook" in response.json()["name"]

    def test_import_steps_retain_order(self, client: TestClient):
        payload = {
            "playbook": {"name": "Ordered Import"},
            "steps": [
                {"name": "Z", "step_order": 2},
                {"name": "A", "step_order": 1},
            ],
            "variables": [],
        }
        response = client.post(
            "/api/v1/automation/playbooks/import",
            json=payload,
        )
        pb_id = response.json()["id"]
        steps = client.get(f"/api/v1/automation/playbooks/{pb_id}/steps")
        orders = [s["step_order"] for s in steps.json()["items"]]
        assert sorted(orders) == [1, 2]

    def test_import_roundtrip(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="Roundtrip", category="test")
        _create_step(db_session, pb.id, command="echo rt", provider="bash")
        _create_variable(db_session, pb.id, name="v1", value="val1")

        export_resp = client.get(f"/api/v1/automation/playbooks/{pb.id}/export")
        export_data = export_resp.json()

        import_resp = client.post(
            "/api/v1/automation/playbooks/import",
            json=export_data,
        )
        assert import_resp.status_code == 201
        new_id = import_resp.json()["id"]
        assert new_id != pb.id

        new_steps = client.get(f"/api/v1/automation/playbooks/{new_id}/steps")
        assert new_steps.json()["count"] == 1
        assert new_steps.json()["items"][0]["command"] == "echo rt"


# ------------------------------------------------------------------ #
# Fire Event Tests                                                     #
# ------------------------------------------------------------------ #

class TestFireEvent:
    """Test event trigger firing."""

    def test_fire_event_triggers_playbook(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="Event PB")
        _create_step(db_session, pb.id, command="echo fired")

        trigger = EventTrigger(
            playbook_id=pb.id,
            name="On Deploy",
            event_type="deploy.completed",
            enabled=True,
            trigger_count=0,
        )
        db_session.add(trigger)
        db_session.commit()
        db_session.refresh(trigger)

        response = client.post(
            "/api/v1/automation/triggers/fire/deploy.completed"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["playbooks_triggered"] >= 1

    def test_fire_event_increments_count(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        trigger = EventTrigger(
            playbook_id=pb.id,
            name="Test Trigger",
            event_type="test.event",
            enabled=True,
            trigger_count=0,
        )
        db_session.add(trigger)
        db_session.commit()
        db_session.refresh(trigger)

        client.post("/api/v1/automation/triggers/fire/test.event")

        db_session.refresh(trigger)
        assert trigger.trigger_count == 1
        assert trigger.last_triggered is not None

    def test_fire_event_multiple_triggers(self, client: TestClient, db_session):
        pb1 = _create_playbook(db_session, name="PB1")
        pb2 = _create_playbook(db_session, name="PB2")
        for pb in [pb1, pb2]:
            _create_step(db_session, pb.id)
            t = EventTrigger(
                playbook_id=pb.id,
                name=f"Trigger for {pb.name}",
                event_type="multi.event",
                enabled=True,
                trigger_count=0,
            )
            db_session.add(t)
        db_session.commit()

        response = client.post(
            "/api/v1/automation/triggers/fire/multi.event"
        )
        assert response.json()["playbooks_triggered"] >= 2

    def test_fire_disabled_trigger_not_triggered(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        trigger = EventTrigger(
            playbook_id=pb.id,
            name="Disabled",
            event_type="disabled.event",
            enabled=False,
            trigger_count=0,
        )
        db_session.add(trigger)
        db_session.commit()

        response = client.post(
            "/api/v1/automation/triggers/fire/disabled.event"
        )
        assert response.status_code == 200
        assert response.json()["playbooks_triggered"] == 0


# ------------------------------------------------------------------ #
# Execution with Retry Tests                                           #
# ------------------------------------------------------------------ #

class TestExecutionRetry:
    """Test retry logic in playbook execution."""

    def test_execution_record_created(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        _create_step(db_session, pb.id, command="echo test")
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/execute",
            json={"mode": "dry_run"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] > 0
        assert data["steps_total"] == 1

    def test_execution_status_values(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, requires_approval=True)
        _create_step(db_session, pb.id)
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/execute",
            json={"mode": "live"},
        )
        assert response.json()["status"] == "pending"

    def test_execute_multiple_steps_order(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        _create_step(db_session, pb.id, name="First", step_order=1, command="echo 1")
        _create_step(db_session, pb.id, name="Second", step_order=2, command="echo 2")
        _create_step(db_session, pb.id, name="Third", step_order=3, command="echo 3")
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/dry-run",
            json={"variables": {}},
        )
        assert response.status_code == 200
        assert response.json()["steps_total"] == 3


# ------------------------------------------------------------------ #
# Dashboard Automation Data Tests                                      #
# ------------------------------------------------------------------ #

class TestDashboardAutomation:
    """Test dashboard summary with various data states."""

    def test_dashboard_counts_by_status(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        for status in ["completed", "completed", "failed", "running"]:
            exec_entity = PlaybookExecution(
                playbook_id=pb.id, status=status,
            )
            db_session.add(exec_entity)
        db_session.commit()

        response = client.get("/api/v1/automation/dashboard")
        data = response.json()
        assert data["total_executions"] == 4
        assert data["completed"] == 2
        assert data["failed"] == 1
        assert data["running"] == 1

    def test_dashboard_pending_approvals(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        exec_entity = PlaybookExecution(
            playbook_id=pb.id, status="pending", approval_required=True,
        )
        db_session.add(exec_entity)
        db_session.commit()

        response = client.get("/api/v1/automation/dashboard")
        assert response.json()["pending_approvals"] == 1


# ------------------------------------------------------------------ #
# Execution Log Tests Extended                                         #
# ------------------------------------------------------------------ #

class TestExecutionLogsExtended:
    """Test execution log creation and retrieval."""

    def test_log_creation(self, db_session):
        pb = _create_playbook(db_session)
        exec_entity = PlaybookExecution(
            playbook_id=pb.id, status="completed",
        )
        db_session.add(exec_entity)
        db_session.commit()
        db_session.refresh(exec_entity)

        log = ExecutionLog(
            execution_id=exec_entity.id,
            level="info",
            message="Step completed",
            stdout="output data",
            stderr="",
            exit_code=0,
            duration_ms=150,
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.message == "Step completed"
        assert log.exit_code == 0
        assert log.duration_ms == 150

    def test_log_levels(self, db_session):
        pb = _create_playbook(db_session)
        exec_entity = PlaybookExecution(
            playbook_id=pb.id, status="completed",
        )
        db_session.add(exec_entity)
        db_session.commit()
        db_session.refresh(exec_entity)

        for level in ["info", "warning", "error", "debug"]:
            log = ExecutionLog(
                execution_id=exec_entity.id,
                level=level,
                message=f"Log {level}",
            )
            db_session.add(log)
        db_session.commit()

        from app.repositories.execution_log_repository import ExecutionLogRepository
        logs = ExecutionLogRepository.get_by_execution(db_session, exec_entity.id)
        assert len(logs) == 4

    def test_api_list_logs(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        exec_entity = PlaybookExecution(
            playbook_id=pb.id, status="completed",
        )
        db_session.add(exec_entity)
        db_session.commit()
        db_session.refresh(exec_entity)

        log = ExecutionLog(
            execution_id=exec_entity.id,
            level="info",
            message="Test log entry",
        )
        db_session.add(log)
        db_session.commit()

        response = client.get(
            f"/api/v1/automation/executions/{exec_entity.id}/logs"
        )
        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert response.json()["items"][0]["message"] == "Test log entry"


# ------------------------------------------------------------------ #
# Provider All (Get All) Tests                                         #
# ------------------------------------------------------------------ #

class TestGetAllProviders:
    """Test get_all_providers returns all expected providers."""

    def test_returns_all_eight(self):
        from app.providers.automation.provider_factory import get_all_providers
        providers = get_all_providers()
        expected = ["bash", "powershell", "http", "ssh", "winrm", "agent", "hyperv", "proxmox"]
        for name in expected:
            assert name in providers
        assert len(providers) >= 8


# ------------------------------------------------------------------ #
# Schedule and Trigger Integration Tests                               #
# ------------------------------------------------------------------ #

class TestScheduleIntegration:
    """Test schedule creation and listing via API."""

    def test_list_schedules_for_playbook(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        client.post(
            f"/api/v1/automation/playbooks/{pb.id}/schedules",
            json={"name": "S1", "cron_expression": "0 * * * *"},
        )
        client.post(
            f"/api/v1/automation/playbooks/{pb.id}/schedules",
            json={"name": "S2", "cron_expression": "0 0 * * *"},
        )
        response = client.get(f"/api/v1/automation/schedules?playbook_id={pb.id}")
        assert response.status_code == 200
        assert response.json()["count"] == 2

    def test_disable_schedule(self, client: TestClient, db_session):
        from app.models.db.playbook_schedule import PlaybookSchedule
        pb = _create_playbook(db_session)
        sched = PlaybookSchedule(
            playbook_id=pb.id,
            name="Toggle Me",
            cron_expression="0 * * * *",
            enabled=True,
        )
        db_session.add(sched)
        db_session.commit()
        db_session.refresh(sched)

        response = client.put(
            f"/api/v1/automation/schedules/{sched.id}",
            json={"enabled": False},
        )
        assert response.status_code == 200
        assert response.json()["enabled"] is False


class TestTriggerIntegration:
    """Test trigger creation and listing via API."""

    def test_list_triggers_for_playbook(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        client.post(
            f"/api/v1/automation/playbooks/{pb.id}/triggers",
            json={"name": "T1", "event_type": "event.a"},
        )
        client.post(
            f"/api/v1/automation/playbooks/{pb.id}/triggers",
            json={"name": "T2", "event_type": "event.b"},
        )
        response = client.get(f"/api/v1/automation/triggers?playbook_id={pb.id}")
        assert response.status_code == 200
        assert response.json()["count"] == 2

    def test_delete_trigger(self, client: TestClient, db_session):
        from app.models.db.event_trigger import EventTrigger
        pb = _create_playbook(db_session)
        trigger = EventTrigger(
            playbook_id=pb.id,
            name="Delete Me",
            event_type="del.event",
        )
        db_session.add(trigger)
        db_session.commit()
        db_session.refresh(trigger)

        response = client.delete(
            f"/api/v1/automation/triggers/{trigger.id}"
        )
        assert response.status_code == 204


# ------------------------------------------------------------------ #
# Audit Trail Extended Tests                                           #
# ------------------------------------------------------------------ #

class TestAuditTrailExtended:
    """Test audit trail entries for various operations."""

    def test_audit_on_update(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="Audit Update")
        client.put(
            f"/api/v1/automation/playbooks/{pb.id}",
            json={"name": "Updated Name"},
        )
        response = client.get("/api/v1/automation/audit?entity_type=playbook")
        actions = [e["action"] for e in response.json()["items"]]
        assert "updated" in actions

    def test_audit_on_delete(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, name="Audit Delete")
        client.delete(f"/api/v1/automation/playbooks/{pb.id}")
        response = client.get("/api/v1/automation/audit?entity_type=playbook")
        actions = [e["action"] for e in response.json()["items"]]
        assert "deleted" in actions

    def test_audit_count(self, client: TestClient):
        response = client.get("/api/v1/automation/audit")
        assert response.status_code == 200
        assert "count" in response.json()


# ------------------------------------------------------------------ #
# Step CRUD Extended Tests                                             #
# ------------------------------------------------------------------ #

class TestStepCRUDExtended:
    """Test step CRUD beyond basics."""

    def test_create_multiple_steps(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        for i in range(5):
            client.post(
                f"/api/v1/automation/playbooks/{pb.id}/steps",
                json={
                    "name": f"Step {i}",
                    "step_type": "remote_command",
                    "provider": "ssh",
                    "command": f"echo {i}",
                    "step_order": i + 1,
                },
            )
        response = client.get(f"/api/v1/automation/playbooks/{pb.id}/steps")
        assert response.json()["count"] == 5

    def test_step_fields(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        step = _create_step(
            db_session, pb.id,
            name="Full Step",
            provider="bash",
            command="echo full",
            timeout_seconds=600,
            retry_count=3,
            continue_on_failure=True,
            rollback_command="echo undo",
        )
        response = client.get(
            f"/api/v1/automation/playbooks/{pb.id}/steps"
        )
        step_data = response.json()["items"][0]
        assert step_data["provider"] == "bash"
        assert step_data["retry_count"] == 3
        assert step_data["continue_on_failure"] is True
        assert step_data["rollback_command"] == "echo undo"


# ------------------------------------------------------------------ #
# Variable CRUD Extended Tests                                         #
# ------------------------------------------------------------------ #

class TestVariableCRUDExtended:
    """Test variable CRUD beyond basics."""

    def test_create_sensitive_variable(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/variables",
            json={
                "name": "API_KEY",
                "value": "secret123",
                "variable_type": "secret",
                "sensitive": True,
            },
        )
        assert response.status_code == 201
        assert response.json()["sensitive"] is True

    def test_create_required_variable(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/variables",
            json={
                "name": "TARGET",
                "variable_type": "string",
                "required": True,
            },
        )
        assert response.status_code == 201
        assert response.json()["required"] is True

    def test_create_variable_types(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        for vtype in ["string", "integer", "boolean", "secret"]:
            response = client.post(
                f"/api/v1/automation/playbooks/{pb.id}/variables",
                json={
                    "name": f"var_{vtype}",
                    "variable_type": vtype,
                },
            )
            assert response.status_code == 201
            assert response.json()["variable_type"] == vtype


# ------------------------------------------------------------------ #
# Workflow Extended Tests                                              #
# ------------------------------------------------------------------ #

class TestWorkflowExtended:
    """Test approval workflow extended scenarios."""

    def test_create_multiple_workflows(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, requires_approval=True)
        client.post(
            f"/api/v1/automation/playbooks/{pb.id}/workflows",
            json={"name": "WF1", "required_approvers": 1},
        )
        client.post(
            f"/api/v1/automation/playbooks/{pb.id}/workflows",
            json={"name": "WF2", "required_approvers": 2},
        )
        response = client.get(
            f"/api/v1/automation/playbooks/{pb.id}/workflows"
        )
        assert response.json()["count"] == 2

    def test_workflow_update(self, client: TestClient, db_session):
        from app.models.db.approval_workflow import ApprovalWorkflow
        pb = _create_playbook(db_session)
        wf = ApprovalWorkflow(
            playbook_id=pb.id,
            name="Original WF",
            required_approvers=1,
        )
        db_session.add(wf)
        db_session.commit()
        db_session.refresh(wf)

        response = client.put(
            f"/api/v1/automation/workflows/{wf.id}",
            json={"name": "Updated WF", "required_approvers": 3},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated WF"
        assert response.json()["required_approvers"] == 3


# ------------------------------------------------------------------ #
# Edge Case Tests                                                      #
# ------------------------------------------------------------------ #

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_execute_nonexistent_playbook(self, client: TestClient):
        response = client.post(
            "/api/v1/automation/playbooks/9999/execute",
            json={"mode": "live"},
        )
        assert response.status_code == 404

    def test_update_nonexistent_playbook(self, client: TestClient):
        response = client.put(
            "/api/v1/automation/playbooks/9999",
            json={"name": "Nope"},
        )
        assert response.status_code == 404

    def test_delete_nonexistent_step(self, client: TestClient):
        response = client.delete("/api/v1/automation/steps/9999")
        assert response.status_code == 404

    def test_delete_nonexistent_variable(self, client: TestClient):
        response = client.delete("/api/v1/automation/variables/9999")
        assert response.status_code == 404

    def test_delete_nonexistent_schedule(self, client: TestClient):
        response = client.delete("/api/v1/automation/schedules/9999")
        assert response.status_code == 404

    def test_delete_nonexistent_trigger(self, client: TestClient):
        response = client.delete("/api/v1/automation/triggers/9999")
        assert response.status_code == 404

    def test_approve_nonexistent_request(self, client: TestClient):
        response = client.put(
            "/api/v1/automation/approvals/9999/approve",
            json={"approved_by": "admin"},
        )
        assert response.status_code == 404

    def test_reject_nonexistent_request(self, client: TestClient):
        response = client.put(
            "/api/v1/automation/approvals/9999/reject",
            json={"approved_by": "admin"},
        )
        assert response.status_code == 404

    def test_empty_playbook_search(self, client: TestClient, db_session):
        _create_playbook(db_session, name="FindMe")
        response = client.get("/api/v1/automation/playbooks?search=ZZZZNOTFOUND")
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_invalid_cron_schedule(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/schedules",
            json={"name": "Bad Cron", "cron_expression": "invalid"},
        )
        assert response.status_code == 201


# ------------------------------------------------------------------ #
# StepResult and ExecutionContext Dataclass Tests                      #
# ------------------------------------------------------------------ #

class TestDataclasses:
    """Test base dataclass defaults."""

    def test_step_result_defaults(self):
        sr = StepResult(success=True)
        assert sr.stdout == ""
        assert sr.stderr == ""
        assert sr.exit_code == 0
        assert sr.duration_ms == 0
        assert sr.error is None

    def test_step_result_full(self):
        sr = StepResult(
            success=False, stdout="out", stderr="err",
            exit_code=1, duration_ms=500, error="boom",
        )
        assert sr.success is False
        assert sr.error == "boom"

    def test_execution_context_defaults(self):
        ctx = ExecutionContext(
            playbook_id=1, execution_id=1, step_id=1,
            step_name="S", command="echo", provider="bash",
        )
        assert ctx.target_host is None
        assert ctx.shell is None
        assert ctx.working_directory is None
        assert ctx.timeout_seconds == 300
        assert ctx.variables is None
        assert ctx.environment_variables is None

    def test_execution_context_full(self):
        ctx = ExecutionContext(
            playbook_id=10, execution_id=20, step_id=30,
            step_name="Full", command="run", provider="ssh",
            target_host="host.local", shell="/bin/bash",
            working_directory="/opt",
            environment_variables={"K": "V"},
            timeout_seconds=600,
            variables={"a": "b"},
        )
        assert ctx.target_host == "host.local"
        assert ctx.timeout_seconds == 600


# ------------------------------------------------------------------ #
# Dry Run Tests                                                        #
# ------------------------------------------------------------------ #

class TestDryRun:
    """Test dry run mode."""

    def test_dry_run_with_variables(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        _create_step(db_session, pb.id, command="echo {{env}}")
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/dry-run",
            json={"variables": {"env": "staging"}},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "dry_run_completed"

    def test_dry_run_multiple_steps(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        _create_step(db_session, pb.id, name="S1", command="echo 1", step_order=1)
        _create_step(db_session, pb.id, name="S2", command="echo 2", step_order=2)
        response = client.post(
            f"/api/v1/automation/playbooks/{pb.id}/dry-run",
            json={"variables": {}},
        )
        assert response.json()["steps_total"] == 2


# ------------------------------------------------------------------ #
# Rollback Tests                                                       #
# ------------------------------------------------------------------ #

class TestRollback:
    """Test rollback endpoint."""

    def test_rollback_completed_execution(self, client: TestClient, db_session):
        pb = _create_playbook(db_session, auto_rollback=True)
        exec_entity = PlaybookExecution(
            playbook_id=pb.id,
            status="completed",
        )
        db_session.add(exec_entity)
        db_session.commit()
        db_session.refresh(exec_entity)

        response = client.post(
            f"/api/v1/automation/executions/{exec_entity.id}/rollback",
            json={"reason": "Testing rollback"},
        )
        assert response.status_code == 200

    def test_rollback_failed_execution(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        exec_entity = PlaybookExecution(
            playbook_id=pb.id,
            status="failed",
        )
        db_session.add(exec_entity)
        db_session.commit()
        db_session.refresh(exec_entity)

        response = client.post(
            f"/api/v1/automation/executions/{exec_entity.id}/rollback",
            json={"reason": "Manual rollback"},
        )
        assert response.status_code == 200


# ------------------------------------------------------------------ #
# Execution Filter Tests                                               #
# ------------------------------------------------------------------ #

class TestExecutionFilter:
    """Test execution listing with filters."""

    def test_filter_by_status(self, client: TestClient, db_session):
        pb = _create_playbook(db_session)
        for s in ["completed", "failed", "running", "completed"]:
            db_session.add(PlaybookExecution(playbook_id=pb.id, status=s))
        db_session.commit()

        response = client.get(
            "/api/v1/automation/executions?status=completed"
        )
        assert response.status_code == 200
        for item in response.json()["items"]:
            assert item["status"] == "completed"

    def test_filter_by_playbook(self, client: TestClient, db_session):
        pb1 = _create_playbook(db_session, name="PB1")
        pb2 = _create_playbook(db_session, name="PB2")
        db_session.add(PlaybookExecution(playbook_id=pb1.id, status="completed"))
        db_session.add(PlaybookExecution(playbook_id=pb2.id, status="completed"))
        db_session.commit()

        response = client.get(
            f"/api/v1/automation/executions?playbook_id={pb1.id}"
        )
        assert response.status_code == 200
        for item in response.json()["items"]:
            assert item["playbook_id"] == pb1.id
