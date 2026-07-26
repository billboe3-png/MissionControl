"""Dashboard endpoint validator."""

import json
import os
import urllib.request
import urllib.error

from validators import BaseValidator, CheckResult, Status, ValidatorResult


def _get(url, headers=None, timeout=5):
    req = urllib.request.Request(url, headers=headers or {})
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp.status, json.loads(resp.read()), dict(resp.headers)


class DashboardValidator(BaseValidator):
    name = "dashboard"
    description = "Dashboard endpoint availability and schema checks"

    def run(self, config: dict) -> ValidatorResult:
        base = config["api_url"].rstrip("/")
        result = ValidatorResult(module=self.name)

        result.add(self._check("dashboard_endpoint", lambda: self._check_dashboard_endpoint(base), critical=True))
        result.add(self._check("dashboard_with_token", lambda: self._check_dashboard_with_token(base), critical=False))
        result.add(self._check("dashboard_response_schema", lambda: self._check_dashboard_response_schema(base), critical=False))
        result.add(self._check("no_500_errors", lambda: self._check_no_500_errors(base), critical=True))

        return result

    def _check_dashboard_endpoint(self, base):
        try:
            status, _, _ = _get(f"{base}/dashboard")
        except urllib.error.HTTPError as e:
            status = e.code
        except urllib.error.URLError:
            return CheckResult(name="dashboard_endpoint", status=Status.FAIL, message="Connection failed")
        if status == 401:
            return CheckResult(name="dashboard_endpoint", status=Status.PASS, message="Correctly requires auth (401)")
        if status == 500:
            return CheckResult(name="dashboard_endpoint", status=Status.FAIL, message="Server error on dashboard")
        return CheckResult(name="dashboard_endpoint", status=Status.WARN, message=f"Expected 401, got {status}")

    def _check_dashboard_with_token(self, base):
        token = os.environ.get("MC_TEST_TOKEN")
        if not token:
            return self._skip("dashboard_with_token", "MC_TEST_TOKEN not set in environment")
        try:
            status, body, _ = _get(f"{base}/dashboard", headers={"Authorization": f"Bearer {token}"})
        except urllib.error.HTTPError as e:
            return CheckResult(name="dashboard_with_token", status=Status.WARN, message=f"HTTPError {e.code}")
        except urllib.error.URLError:
            return CheckResult(name="dashboard_with_token", status=Status.WARN, message="Connection failed")
        if status == 200:
            return CheckResult(name="dashboard_with_token", status=Status.PASS, message="Dashboard accessible with token")
        return CheckResult(name="dashboard_with_token", status=Status.WARN, message=f"Expected 200, got {status}")

    def _check_dashboard_response_schema(self, base):
        token = os.environ.get("MC_TEST_TOKEN")
        if not token:
            return self._skip("dashboard_response_schema", "MC_TEST_TOKEN not set in environment")
        try:
            status, body, _ = _get(f"{base}/dashboard", headers={"Authorization": f"Bearer {token}"})
        except urllib.error.URLError:
            return self._skip("dashboard_response_schema", "Connection failed")
        if status != 200:
            return self._skip("dashboard_response_schema", f"Dashboard returned {status}, cannot check schema")
        expected_keys = ("agents", "automation", "health")
        missing = [k for k in expected_keys if k not in body]
        if missing:
            return CheckResult(name="dashboard_response_schema", status=Status.WARN, message=f"Missing keys: {', '.join(missing)}")
        return CheckResult(name="dashboard_response_schema", status=Status.PASS, message="All expected keys present")

    def _check_no_500_errors(self, base):
        try:
            status, _, _ = _get(f"{base}/dashboard")
        except urllib.error.HTTPError as e:
            status = e.code
        except urllib.error.URLError:
            return CheckResult(name="no_500_errors", status=Status.FAIL, message="Connection failed")
        if status == 500:
            return CheckResult(name="no_500_errors", status=Status.FAIL, message="Dashboard returned 500")
        return CheckResult(name="no_500_errors", status=Status.PASS, message=f"Status {status} (not 500)")
