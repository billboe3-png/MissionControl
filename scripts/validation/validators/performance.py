import time
import urllib.request
import urllib.error

from validators import BaseValidator, CheckResult, Status, ValidatorResult


def _get(url, timeout=5):
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp.status, resp.read()


class PerformanceValidator(BaseValidator):
    name = "performance"
    description = "API response time and performance checks"

    def run(self, config: dict) -> ValidatorResult:
        base = config["api_url"].rstrip("/")
        result = ValidatorResult(module=self.name)

        result.add(self._check(
            "health_latency",
            lambda: self._check_health_latency(base),
            critical=True,
        ))
        result.add(self._check(
            "version_latency",
            lambda: self._check_version_latency(base),
            critical=True,
        ))
        result.add(self._check(
            "subsystems_latency",
            lambda: self._check_subsystems_latency(base),
            critical=False,
        ))
        result.add(self._check(
            "dashboard_latency",
            lambda: self._check_dashboard_latency(base),
            critical=False,
        ))
        result.add(self._check(
            "concurrent_requests",
            lambda: self._check_concurrent_requests(base),
            critical=False,
        ))
        result.add(self._check(
            "response_size",
            lambda: self._check_response_size(base),
            critical=False,
        ))
        return result

    def _measure(self, url, expected_status=None, timeout=5):
        start = time.time()
        try:
            status, body = _get(url, timeout=timeout)
        except urllib.error.HTTPError as e:
            status = e.code
            body = e.read()
        elapsed_ms = (time.time() - start) * 1000
        if expected_status is not None and status != expected_status:
            raise RuntimeError(f"Expected HTTP {expected_status}, got {status}")
        return status, body, elapsed_ms

    def _check_health_latency(self, base):
        status, body, elapsed_ms = self._measure(
            f"{base}/health/live", expected_status=200, timeout=5
        )
        if elapsed_ms >= 1000:
            raise RuntimeError(f"Response too slow: {elapsed_ms:.0f}ms (limit 1000ms)")
        return CheckResult(
            name="health_latency",
            status=Status.PASS,
            message=f"{elapsed_ms:.0f}ms",
            metrics={"latency_ms": round(elapsed_ms, 2)},
        )

    def _check_version_latency(self, base):
        status, body, elapsed_ms = self._measure(
            f"{base}/version", expected_status=200, timeout=5
        )
        if elapsed_ms >= 1000:
            raise RuntimeError(f"Response too slow: {elapsed_ms:.0f}ms (limit 1000ms)")
        return CheckResult(
            name="version_latency",
            status=Status.PASS,
            message=f"{elapsed_ms:.0f}ms",
            metrics={"latency_ms": round(elapsed_ms, 2)},
        )

    def _check_subsystems_latency(self, base):
        status, body, elapsed_ms = self._measure(
            f"{base}/health/subsystems", expected_status=200, timeout=10
        )
        if elapsed_ms >= 5000:
            raise RuntimeError(f"Response too slow: {elapsed_ms:.0f}ms (limit 5000ms)")
        return CheckResult(
            name="subsystems_latency",
            status=Status.PASS,
            message=f"{elapsed_ms:.0f}ms",
            metrics={"latency_ms": round(elapsed_ms, 2)},
        )

    def _check_dashboard_latency(self, base):
        status, body, elapsed_ms = self._measure(
            f"{base}/api/v1/dashboard", expected_status=401, timeout=10
        )
        if elapsed_ms >= 2000:
            raise RuntimeError(f"Response too slow: {elapsed_ms:.0f}ms (limit 2000ms)")
        return CheckResult(
            name="dashboard_latency",
            status=Status.PASS,
            message=f"{elapsed_ms:.0f}ms (HTTP {status})",
            metrics={"latency_ms": round(elapsed_ms, 2), "http_status": status},
        )

    def _check_concurrent_requests(self, base):
        url = f"{base}/health/live"
        latencies = []
        for _ in range(10):
            _, _, elapsed_ms = self._measure(url, expected_status=200, timeout=5)
            latencies.append(elapsed_ms)
        avg_ms = sum(latencies) / len(latencies)
        if avg_ms >= 500:
            raise RuntimeError(f"Average latency too high: {avg_ms:.0f}ms (limit 500ms)")
        return CheckResult(
            name="concurrent_requests",
            status=Status.PASS,
            message=f"Avg {avg_ms:.0f}ms over 10 requests",
            metrics={
                "avg_ms": round(avg_ms, 2),
                "min_ms": round(min(latencies), 2),
                "max_ms": round(max(latencies), 2),
                "request_count": len(latencies),
            },
        )

    def _check_response_size(self, base):
        _, body, _ = self._measure(f"{base}/health/subsystems", timeout=10)
        size_bytes = len(body)
        if size_bytes >= 10240:
            raise RuntimeError(f"Response too large: {size_bytes} bytes (limit 10240)")
        return CheckResult(
            name="response_size",
            status=Status.PASS,
            message=f"{size_bytes} bytes",
            metrics={"response_size_bytes": size_bytes},
        )
