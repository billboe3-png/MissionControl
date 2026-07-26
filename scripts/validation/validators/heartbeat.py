import urllib.request
import urllib.error
import json

from validators import BaseValidator, ValidatorResult


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


class HeartbeatValidator(BaseValidator):
    name = "heartbeat"

    def run(self, config: dict):
        api = config["api_url"]
        checks = []
        checks.append(self._check("heartbeat_endpoint_exists", lambda: self._check_endpoint_exists(api), critical=True))
        checks.append(self._check("heartbeat_requires_api_key", lambda: self._check_requires_api_key(api), critical=False))
        checks.append(self._check("heartbeat_payload_validation", lambda: self._check_payload_validation(api), critical=False))
        checks.append(self._check("command_dispatch_endpoint", lambda: self._check_command_dispatch(api), critical=False))
        return ValidatorResult(module=self.name, checks=checks)

    def _check_endpoint_exists(self, api):
        status, body = _post(f"{api}/agents/heartbeat", data={})
        if status == 500:
            raise RuntimeError("POST /agents/heartbeat returned 500")
        if status == 404:
            raise RuntimeError("POST /agents/heartbeat returned 404 (endpoint not found)")
        if status != 422:
            raise RuntimeError(f"POST /agents/heartbeat returned {status}, expected 422")
        return "POST /agents/heartbeat exists and returns 422 without headers"

    def _check_requires_api_key(self, api):
        status, body = _post(
            f"{api}/agents/heartbeat",
            data={},
            headers={"X-Agent-API-Key": ""},
        )
        if status == 500:
            raise RuntimeError("Heartbeat with empty API key returned 500")
        if status not in (401, 422):
            raise RuntimeError(f"Heartbeat with empty API key returned {status}, expected 401 or 422")
        return f"Heartbeat with empty API key returns {status}"

    def _check_payload_validation(self, api):
        status, body = _post(
            f"{api}/agents/heartbeat",
            data={},
            headers={"X-Agent-API-Key": "test"},
        )
        if status == 500:
            raise RuntimeError("Heartbeat with test key and empty body returned 500")
        if status != 422:
            raise RuntimeError(f"Heartbeat with test key and empty body returned {status}, expected 422")
        return "Heartbeat with test key and empty body returns 422 (not 500)"

    def _check_command_dispatch(self, api):
        status, body = _post(f"{api}/agents/1/execute", data={})
        if status == 500:
            raise RuntimeError("POST /agents/1/execute returned 500")
        if status != 401:
            raise RuntimeError(f"POST /agents/1/execute returned {status}, expected 401 without auth")
        return "POST /agents/1/execute correctly returns 401"
