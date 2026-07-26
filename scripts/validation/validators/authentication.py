"""Authentication and authorisation validator."""

import json
import urllib.request
import urllib.error

from validators import BaseValidator, CheckResult, Status, ValidatorResult


def _get(url, headers=None, timeout=5):
    req = urllib.request.Request(url, headers=headers or {})
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp.status, json.loads(resp.read()), dict(resp.headers)


def _post(url, data=None, headers=None, timeout=5):
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers=headers or {"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp.status, json.loads(resp.read()), dict(resp.headers)


class AuthenticationValidator(BaseValidator):
    name = "authentication"
    description = "Auth endpoints and authorization checks"

    def run(self, config: dict) -> ValidatorResult:
        base = config["api_url"].rstrip("/")
        result = ValidatorResult(module=self.name)

        result.add(self._check("login_endpoint", lambda: self._check_login_endpoint(base), critical=True))
        result.add(self._check("unauthorized_access", lambda: self._check_unauthorized_access(base), critical=True))
        result.add(self._check("invalid_token", lambda: self._check_invalid_token(base), critical=True))
        result.add(self._check("user_list_requires_auth", lambda: self._check_user_list_requires_auth(base), critical=False))
        result.add(self._check("password_change_requires_auth", lambda: self._check_password_change_requires_auth(base), critical=False))

        return result

    def _check_login_endpoint(self, base):
        status, body, _ = _post(
            f"{base}/auth/login",
            data={"email": "nonexistent@test.com", "password": "wrong"},
        )
        if status in (401, 400):
            return CheckResult(name="login_endpoint", status=Status.PASS, message=f"Invalid credentials correctly rejected with {status}")
        if status == 500:
            return CheckResult(name="login_endpoint", status=Status.FAIL, message="Server error on invalid login")
        return CheckResult(name="login_endpoint", status=Status.WARN, message=f"Unexpected status {status}")

    def _check_unauthorized_access(self, base):
        status, _, _ = _get(f"{base}/auth/me")
        if status == 401:
            return CheckResult(name="unauthorized_access", status=Status.PASS, message="Correctly returns 401")
        if status == 500:
            return CheckResult(name="unauthorized_access", status=Status.FAIL, message="Server error instead of 401")
        return CheckResult(name="unauthorized_access", status=Status.WARN, message=f"Expected 401, got {status}")

    def _check_invalid_token(self, base):
        status, _, _ = _get(f"{base}/auth/me", headers={"Authorization": "Bearer invalid_token"})
        if status == 401:
            return CheckResult(name="invalid_token", status=Status.PASS, message="Invalid token correctly rejected with 401")
        if status == 500:
            return CheckResult(name="invalid_token", status=Status.FAIL, message="Server error on invalid token")
        return CheckResult(name="invalid_token", status=Status.WARN, message=f"Expected 401, got {status}")

    def _check_user_list_requires_auth(self, base):
        try:
            status, _, _ = _get(f"{base}/auth/users")
        except urllib.error.HTTPError as e:
            status = e.code
        except urllib.error.URLError:
            return CheckResult(name="user_list_requires_auth", status=Status.WARN, message="Connection failed")
        if status == 401:
            return CheckResult(name="user_list_requires_auth", status=Status.PASS, message="Correctly requires auth")
        if status == 500:
            return CheckResult(name="user_list_requires_auth", status=Status.FAIL, message="Server error instead of 401")
        return CheckResult(name="user_list_requires_auth", status=Status.WARN, message=f"Expected 401, got {status}")

    def _check_password_change_requires_auth(self, base):
        try:
            status, _, _ = _post(f"{base}/auth/change-password", data={})
        except urllib.error.HTTPError as e:
            status = e.code
        except urllib.error.URLError:
            return CheckResult(name="password_change_requires_auth", status=Status.WARN, message="Connection failed")
        if status == 401:
            return CheckResult(name="password_change_requires_auth", status=Status.PASS, message="Correctly requires auth")
        if status == 500:
            return CheckResult(name="password_change_requires_auth", status=Status.FAIL, message="Server error instead of 401")
        return CheckResult(name="password_change_requires_auth", status=Status.WARN, message=f"Expected 401, got {status}")
