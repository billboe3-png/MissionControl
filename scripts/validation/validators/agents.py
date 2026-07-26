import urllib.request
import urllib.error
import json
import uuid

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


def _post(url, data=None, headers=None, timeout=5):
    body = json.dumps(data).encode() if data else b""
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.read() else {}
    except Exception:
        return 0, {}


class AgentsValidator(BaseValidator):
    name = "agents"

    def run(self, config: dict):
        api = config["api_url"]
        checks = []
        checks.append(self._check("agent_list_endpoint", lambda: self._check_list_endpoint(api), critical=True))
        checks.append(self._check("agent_register_endpoint", lambda: self._check_register_endpoint(api), critical=False))
        checks.append(self._check("agent_heartbeat_endpoint", lambda: self._check_heartbeat_endpoint(api), critical=False))
        checks.append(self._check("agent_version_endpoint", lambda: self._check_version_endpoint(api), critical=False))
        checks.append(self._check("agent_commands_endpoint", lambda: self._check_commands_endpoint(api), critical=False))
        checks.append(self._check("simulated_agent_test", lambda: self._check_simulated_agent(api, config), critical=False))
        return ValidatorResult(module=self.name, checks=checks)

    def _check_list_endpoint(self, api):
        status, body = _get(f"{api}/agents")
        if status != 401:
            raise RuntimeError(f"GET /agents returned {status}, expected 401 without auth")
        return "GET /agents correctly returns 401"

    def _check_register_endpoint(self, api):
        status, body = _post(f"{api}/agents/register", data={})
        if status == 500:
            raise RuntimeError("POST /agents/register returned 500 on empty body")
        if status not in (401, 422):
            raise RuntimeError(f"POST /agents/register returned {status}, expected 401 or 422")
        return f"POST /agents/register returns {status} (not 500)"

    def _check_heartbeat_endpoint(self, api):
        status, body = _post(f"{api}/agents/heartbeat", data={}, headers={})
        if status == 500:
            raise RuntimeError("POST /agents/heartbeat returned 500 without X-Agent-API-Key")
        if status not in (401, 422):
            raise RuntimeError(f"POST /agents/heartbeat returned {status}, expected 401 or 422")
        return f"POST /agents/heartbeat returns {status} without API key"

    def _check_version_endpoint(self, api):
        status, body = _get(f"{api}/agents/version")
        if status != 200:
            raise RuntimeError(f"GET /agents/version returned {status}, expected 200")
        if not isinstance(body, dict) or "version" not in body:
            raise RuntimeError("GET /agents/version response missing 'version' field")
        return f"GET /agents/version returns version={body['version']}"

    def _check_commands_endpoint(self, api):
        status, body = _get(f"{api}/agents/commands/all")
        if status != 401:
            raise RuntimeError(f"GET /agents/commands/all returned {status}, expected 401 without auth")
        return "GET /agents/commands/all correctly returns 401"

    def _check_simulated_agent(self, api, config):
        if not config.get("simulate_agent"):
            return CheckResult(
                name="simulated_agent_test",
                status=Status.SKIP,
                message="simulate_agent not configured",
            )
        api_key = str(uuid.uuid4())
        payload = {
            "name": "validation-test-agent",
            "api_key": api_key,
            "capabilities": ["test"],
        }
        status, body = _post(f"{api}/agents/register", data=payload)
        if status == 500:
            raise RuntimeError("Agent registration returned 500")
        if status not in (200, 201, 401, 422):
            raise RuntimeError(f"Agent registration returned unexpected status {status}")

        hb_payload = {"agent_id": "validation-test-agent"}
        hb_status, hb_body = _post(
            f"{api}/agents/heartbeat",
            data=hb_payload,
            headers={"X-Agent-API-Key": api_key},
        )
        if hb_status == 500:
            raise RuntimeError("Heartbeat returned 500 for simulated agent")
        return f"Simulated agent: register={status}, heartbeat={hb_status}"
