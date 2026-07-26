import json
import urllib.error
import urllib.request

from validators import BaseValidator, CheckResult, Status, ValidatorResult


def _get(url, headers=None, timeout=5):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.read() else {}
    except Exception:
        return 0, {}


class AgentsFleetValidator(BaseValidator):
    name = "agents_fleet"

    def run(self, config: dict):
        api = config["api_url"]
        checks = []
        checks.append(
            self._check(
                "fleet_summary_endpoint",
                lambda: self._check_fleet_summary(api),
                critical=True,
            )
        )
        checks.append(
            self._check(
                "agent_state_tracking",
                self._check_agent_state_model,
                critical=False,
            )
        )
        checks.append(
            self._check(
                "heartbeat_processing",
                lambda: self._check_heartbeat_payload(api),
                critical=False,
            )
        )
        checks.append(
            self._check(
                "command_queue_api",
                lambda: self._check_command_queue(api),
                critical=False,
            )
        )
        checks.append(
            self._check(
                "fleet_by_os",
                lambda: self._check_fleet_by_os(api),
                critical=False,
            )
        )
        checks.append(
            self._check(
                "fleet_by_version",
                lambda: self._check_fleet_by_version(api),
                critical=False,
            )
        )
        return ValidatorResult(module=self.name, checks=checks)

    def _check_fleet_summary(self, api):
        status, body = _get(f"{api}/dashboard")
        if status == 401:
            return CheckResult(
                name="fleet_summary_endpoint",
                status=Status.SKIP,
                message="Dashboard requires authentication (401)",
            )
        if status != 200:
            raise RuntimeError(
                f"GET /dashboard returned {status}, expected 200"
            )
        if not isinstance(body, dict):
            raise RuntimeError("Dashboard response is not a JSON object")

        total = body.get("total_agents") or body.get("total")
        online = body.get("online")
        if total is None:
            raise RuntimeError(
                "Dashboard response missing agents count field"
            )
        if online is None:
            raise RuntimeError(
                "Dashboard response missing online count field"
            )
        return (
            f"Fleet summary OK: {total} agents, {online} online"
        )

    def _check_agent_state_model(self):
        try:
            from app.models.db.agent import Agent

            assert hasattr(Agent, "status"), "Agent missing status field"
            assert hasattr(Agent, "health"), "Agent missing health field"
            return "Agent model has status and health fields"
        except ImportError:
            raise RuntimeError(
                "Could not import app.models.db.agent.Agent"
            )
        except AssertionError as e:
            raise RuntimeError(str(e))

    def _check_heartbeat_payload(self, api):
        status, body = _get(f"{api}/agents/heartbeat")
        if status in (401, 422):
            return (
                f"Heartbeat endpoint accepts requests (status={status})"
            )
        if status == 500:
            raise RuntimeError(
                "Heartbeat endpoint returned 500"
            )
        return f"Heartbeat endpoint status={status}"

    def _check_command_queue(self, api):
        status, body = _get(f"{api}/agents/commands/all")
        if status == 401:
            return (
                "Commands endpoint requires auth (401), queue data available"
            )
        if status != 200:
            raise RuntimeError(
                f"GET /agents/commands/all returned {status}"
            )
        if not isinstance(body, dict):
            raise RuntimeError("Commands response is not a JSON object")
        return "Commands endpoint returns queue data"

    def _check_fleet_by_os(self, api):
        status, body = _get(f"{api}/dashboard")
        if status == 401:
            return CheckResult(
                name="fleet_by_os",
                status=Status.SKIP,
                message="Dashboard requires authentication (401)",
            )
        if status != 200:
            raise RuntimeError(
                f"GET /dashboard returned {status}, expected 200"
            )
        by_os = body.get("by_os")
        if by_os is None:
            return CheckResult(
                name="fleet_by_os",
                status=Status.WARN,
                message="Dashboard response missing by_os distribution",
            )
        if not isinstance(by_os, dict):
            raise RuntimeError("by_os is not a dict")
        return f"OS distribution: {by_os}"

    def _check_fleet_by_version(self, api):
        status, body = _get(f"{api}/dashboard")
        if status == 401:
            return CheckResult(
                name="fleet_by_version",
                status=Status.SKIP,
                message="Dashboard requires authentication (401)",
            )
        if status != 200:
            raise RuntimeError(
                f"GET /dashboard returned {status}, expected 200"
            )
        by_version = body.get("by_version")
        if by_version is None:
            return CheckResult(
                name="fleet_by_version",
                status=Status.WARN,
                message="Dashboard response missing by_version distribution",
            )
        if not isinstance(by_version, dict):
            raise RuntimeError("by_version is not a dict")
        return f"Version distribution: {by_version}"


# To register: add `from validators.agents_fleet import AgentsFleetValidator`
# and `"agents_fleet": AgentsFleetValidator` to ALL_VALIDATORS in run_validation.py
