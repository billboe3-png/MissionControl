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


class AutomationValidator(BaseValidator):
    name = "automation"

    def run(self, config: dict):
        api = config["api_url"]
        checks = []
        checks.append(self._check("automation_api_endpoint", lambda: self._check_automation_endpoint(api), critical=True))
        checks.append(self._check("playbook_api_endpoint", lambda: self._check_playbook_endpoint(api), critical=False))
        checks.append(self._check("no_500_on_empty_body", lambda: self._check_empty_body(api), critical=False))
        return ValidatorResult(module=self.name, checks=checks)

    def _check_automation_endpoint(self, api):
        status, body = _get(f"{api}/automation")
        if status == 500:
            raise RuntimeError("GET /automation returned 500")
        if status != 401:
            raise RuntimeError(f"GET /automation returned {status}, expected 401 without auth")
        return "GET /automation correctly returns 401"

    def _check_playbook_endpoint(self, api):
        status, body = _get(f"{api}/automation/playbooks")
        if status == 500:
            raise RuntimeError("GET /automation/playbooks returned 500")
        if status != 401:
            raise RuntimeError(f"GET /automation/playbooks returned {status}, expected 401 without auth")
        return "GET /automation/playbooks correctly returns 401"

    def _check_empty_body(self, api):
        status, body = _post(f"{api}/automation/playbooks", data={})
        if status == 500:
            raise RuntimeError("POST /automation/playbooks with empty body returned 500")
        if status not in (401, 422):
            raise RuntimeError(f"POST /automation/playbooks returned {status}, expected 401 or 422")
        return f"POST /automation/playbooks with empty body returns {status} (not 500)"
