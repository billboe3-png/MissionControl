import json
import os
import urllib.request
import urllib.error

from validators import BaseValidator, CheckResult, Status, ValidatorResult


def _post_raw(url, data, timeout=5):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status, resp.read().decode(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), dict(e.headers)


def _get(url, timeout=5):
    req = urllib.request.Request(url)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status, resp.read().decode(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), dict(e.headers)


class SecurityValidator(BaseValidator):
    name = "security"
    description = "Security configuration and hardening checks"

    def run(self, config: dict) -> ValidatorResult:
        base = config["api_url"].rstrip("/")
        result = ValidatorResult(module=self.name)

        result.add(self._check(
            "secret_key_set",
            lambda: self._check_secret_key_set(),
            critical=True,
        ))
        result.add(self._check(
            "secret_key_valid",
            lambda: self._check_secret_key_valid(),
            critical=True,
        ))
        result.add(self._check(
            "jwt_configured",
            lambda: self._check_jwt_configured(),
            critical=False,
        ))
        result.add(self._check(
            "rate_limiting_active",
            lambda: self._check_rate_limiting_active(base),
            critical=True,
        ))
        result.add(self._check(
            "no_stack_traces",
            lambda: self._check_no_stack_traces(base),
            critical=True,
        ))
        result.add(self._check(
            "error_format_consistent",
            lambda: self._check_error_format_consistent(base),
            critical=False,
        ))
        result.add(self._check(
            "rbac_enforced",
            lambda: self._check_rbac_enforced(base),
            critical=False,
        ))
        return result

    def _check_secret_key_set(self):
        key = os.environ.get("MISSIONCONTROL_SECRET_KEY", "")
        if not key:
            raise RuntimeError("MISSIONCONTROL_SECRET_KEY is not set or empty")
        return CheckResult(
            name="secret_key_set",
            status=Status.PASS,
            message=f"Key is set ({len(key)} chars)",
        )

    def _check_secret_key_valid(self):
        key = os.environ.get("MISSIONCONTROL_SECRET_KEY", "")
        if not key:
            raise RuntimeError("MISSIONCONTROL_SECRET_KEY is not set")
        try:
            from cryptography.fernet import Fernet
            Fernet(key.encode() if isinstance(key, str) else key)
        except ImportError:
            return CheckResult(
                name="secret_key_valid",
                status=Status.WARN,
                message="cryptography package not installed - cannot validate key format",
            )
        except Exception as e:
            raise RuntimeError(f"Invalid Fernet key: {e}")
        return "Valid Fernet key"

    def _check_jwt_configured(self):
        try:
            from app.services.auth_service import AuthService  # noqa: F401
            return CheckResult(
                name="jwt_configured",
                status=Status.PASS,
                message="AuthService imported successfully",
            )
        except ImportError as e:
            return CheckResult(
                name="jwt_configured",
                status=Status.WARN,
                message=f"Cannot import AuthService: {e}",
            )

    def _check_rate_limiting_active(self, base):
        got_429 = False
        for i in range(65):
            try:
                req = urllib.request.Request(f"{base}/api/v1/dashboard")
                resp = urllib.request.urlopen(req, timeout=3)
                resp.read()
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    got_429 = True
                    return CheckResult(
                        name="rate_limiting_active",
                        status=Status.PASS,
                        message=f"429 received after {i + 1} requests",
                        metrics={"requests_before_429": i + 1},
                    )
                e.read()
            except urllib.error.URLError:
                pass
        if not got_429:
            return CheckResult(
                name="rate_limiting_active",
                status=Status.WARN,
                message="No 429 response in 65 rapid requests",
            )

    def _check_no_stack_traces(self, base):
        url = f"{base}/api/v1/auth/login"
        status, body, _ = _post_raw(url, {"invalid": True})
        if "Traceback" in body:
            raise RuntimeError("Response contains Python traceback")
        if 'File "' in body:
            raise RuntimeError("Response contains file path from stack trace")
        return True

    def _check_error_format_consistent(self, base):
        url = f"{base}/api/v1/auth/login"
        status, body, _ = _post_raw(url, {"invalid": True})
        if not body:
            return CheckResult(
                name="error_format_consistent",
                status=Status.WARN,
                message="Empty response body",
            )
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise RuntimeError(f"Response is not valid JSON: {body[:200]}")
        if "error" not in data:
            return CheckResult(
                name="error_format_consistent",
                status=Status.WARN,
                message=f"Response missing 'error' key. Keys: {list(data.keys())}",
            )
        error = data["error"]
        missing = [k for k in ("status_code", "message") if k not in error]
        if missing:
            raise RuntimeError(f"error object missing keys: {missing}")
        return CheckResult(
            name="error_format_consistent",
            status=Status.PASS,
            message=f"error.status_code={error['status_code']}, error.message present",
        )

    def _check_rbac_enforced(self, base):
        status, body, _ = _get(f"{base}/auth/users")
        if status == 200:
            raise RuntimeError("GET /auth/users returned 200 without auth token - RBAC not enforced")
        if status != 401:
            return CheckResult(
                name="rbac_enforced",
                status=Status.WARN,
                message=f"Expected 401, got HTTP {status}",
            )
        return True
