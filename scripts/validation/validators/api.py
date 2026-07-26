"""API health and behaviour validator."""

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


def _options(url, headers=None, timeout=5):
    req = urllib.request.Request(url, headers=headers or {}, method="OPTIONS")
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp.status, dict(resp.headers)


class APIValidator(BaseValidator):
    name = "api"
    description = "API health endpoints and behaviour checks"

    def run(self, config: dict) -> ValidatorResult:
        base = config["api_url"].rstrip("/")
        result = ValidatorResult(module=self.name)

        result.add(self._check("health_live", lambda: self._check_health_live(base), critical=True))
        result.add(self._check("health_ready", lambda: self._check_health_ready(base), critical=True))
        result.add(self._check("health_subsystems", lambda: self._check_health_subsystems(base), critical=True))
        result.add(self._check("version", lambda: self._check_version(base), critical=True))
        result.add(self._check("api_root", lambda: self._check_api_root(base), critical=True))
        result.add(self._check("rate_limiting", lambda: self._check_rate_limiting(base), critical=False))
        result.add(self._check("request_id", lambda: self._check_request_id(base), critical=False))
        result.add(self._check("cors_headers", lambda: self._check_cors(base), critical=False))

        return result

    def _check_health_live(self, base):
        status, body, _ = _get(f"{base}/health/live")
        if status != 200:
            return CheckResult(name="health_live", status=Status.FAIL, message=f"Expected 200, got {status}")
        if body.get("status") != "ok":
            return CheckResult(name="health_live", status=Status.FAIL, message=f"Missing or wrong status: {body.get('status')}")
        return CheckResult(name="health_live", status=Status.PASS, message="ok")

    def _check_health_ready(self, base):
        status, body, _ = _get(f"{base}/health/ready")
        if status not in (200, 503):
            return CheckResult(name="health_ready", status=Status.FAIL, message=f"Expected 200 or 503, got {status}")
        if "status" not in body:
            return CheckResult(name="health_ready", status=Status.FAIL, message="Body missing 'status' key")
        return CheckResult(name="health_ready", status=Status.PASS, message=f"status={body['status']}")

    def _check_health_subsystems(self, base):
        status, body, _ = _get(f"{base}/health/subsystems")
        if status not in (200, 503):
            return CheckResult(name="health_subsystems", status=Status.FAIL, message=f"Expected 200 or 503, got {status}")
        if "status" not in body:
            return CheckResult(name="health_subsystems", status=Status.FAIL, message="Body missing 'status' key")
        if "subsystems" not in body:
            return CheckResult(name="health_subsystems", status=Status.FAIL, message="Body missing 'subsystems' key")
        return CheckResult(name="health_subsystems", status=Status.PASS, message=f"status={body['status']}, subsystems={len(body['subsystems'])}")

    def _check_version(self, base):
        status, body, _ = _get(f"{base}/version")
        if status != 200:
            return CheckResult(name="version", status=Status.FAIL, message=f"Expected 200, got {status}")
        for key in ("version", "edition", "uptime_seconds"):
            if key not in body:
                return CheckResult(name="version", status=Status.FAIL, message=f"Body missing '{key}'")
        return CheckResult(name="version", status=Status.PASS, message=f"version={body.get('version')}")

    def _check_api_root(self, base):
        status, body, _ = _get(f"{base}/")
        if status != 200:
            return CheckResult(name="api_root", status=Status.FAIL, message=f"Expected 200, got {status}")
        for key in ("name", "status", "version"):
            if key not in body:
                return CheckResult(name="api_root", status=Status.FAIL, message=f"Body missing '{key}'")
        return CheckResult(name="api_root", status=Status.PASS, message=f"name={body.get('name')}")

    def _check_rate_limiting(self, base):
        for i in range(70):
            req = urllib.request.Request(f"{base}/health/live", headers={})
            try:
                resp = urllib.request.urlopen(req, timeout=2)
                headers = dict(resp.headers)
                resp.read()
                if "X-RateLimit-Limit" in headers:
                    return CheckResult(
                        name="rate_limiting",
                        status=Status.PASS,
                        message="X-RateLimit-Limit header observed",
                        metrics={"request_index": i},
                    )
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    return CheckResult(name="rate_limiting", status=Status.PASS, message="429 Too Many Requests received")
                headers = dict(e.headers)
                if "X-RateLimit-Limit" in headers:
                    return CheckResult(
                        name="rate_limiting",
                        status=Status.PASS,
                        message="X-RateLimit-Limit header observed",
                        metrics={"request_index": i},
                    )
            except urllib.error.URLError:
                pass
        return CheckResult(name="rate_limiting", status=Status.WARN, message="No rate-limit headers observed in 70 requests")

    def _check_request_id(self, base):
        test_id = "test-request-id-00000001"
        headers = {"X-Request-ID": test_id}
        status, body, resp_headers = _get(f"{base}/health/live", headers=headers)
        if status != 200:
            return CheckResult(name="request_id", status=Status.WARN, message=f"Unexpected status {status}")
        if resp_headers.get("X-Request-ID") == test_id:
            return CheckResult(name="request_id", status=Status.PASS, message="X-Request-ID echoed back")
        return CheckResult(name="request_id", status=Status.WARN, message="X-Request-ID not echoed in response headers")

    def _check_cors(self, base):
        try:
            status, headers = _options(f"{base}/")
            origin = headers.get("Access-Control-Allow-Origin")
            if origin:
                return CheckResult(name="cors_headers", status=Status.PASS, message=f"Access-Control-Allow-Origin={origin}")
            return CheckResult(name="cors_headers", status=Status.WARN, message="Access-Control-Allow-Origin header missing")
        except Exception as e:
            return CheckResult(name="cors_headers", status=Status.WARN, message=f"OPTIONS request failed: {e}")
