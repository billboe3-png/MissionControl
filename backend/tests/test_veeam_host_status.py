"""Tests for the Veeam per-host backup health endpoint and its classifier.

``_classify_host`` is exercised directly against a real ``VeeamBackupServer``
row, and ``hosts_status`` is awaited directly with the ``db_session`` fixture.
Neither path enters the FastAPI lifespan, matching the ``test_veeam_bridge``
style and keeping the suite safe to run inside the production container.
"""

import asyncio

from app.plugins.installed.official_veeam import routes as routes_module
from app.plugins.installed.official_veeam.models import VeeamBackupServer
from app.plugins.installed.official_veeam.routes import _classify_host


def make_server(server_id: int = 1, name: str = "host", enabled: bool = True) -> VeeamBackupServer:
    return VeeamBackupServer(id=server_id, name=name, enabled=enabled)


def make_payload(dates, jobs):
    return {
        "success": True,
        "jobs": jobs,
        "dates": dates,
        "count": len(jobs),
        "ssh_available": True,
        "error": None,
    }


def cell(result="Success", failed=0, warning=0, runs=None, **extra):
    data = {
        "success_count": 1 if result == "Success" else 0,
        "failed_count": failed,
        "warning_count": warning,
        "result": result,
        "runs": runs if runs is not None else [{"result": result}],
    }
    data.update(extra)
    return data


DATES = ["2026-08-01", "2026-08-02", "2026-08-03"]


def test_classify_passed_when_all_jobs_succeed():
    jobs = [
        {"job_name": "A", "daily": {"2026-08-03": cell()}},
        {"job_name": "B", "daily": {"2026-08-02": cell()}},
    ]
    result = _classify_host(make_server(), make_payload(DATES, jobs), 3)
    assert result["status"] == "passed"
    assert result["jobs_total"] == 2
    assert result["jobs_failed"] == 0
    assert result["failures"] == []


def test_classify_failed_collects_reason_and_last_run():
    jobs = [
        {
            "job_name": "A",
            "daily": {
                "2026-08-03": cell(
                    "Failed",
                    failed=1,
                    runs=[
                        {
                            "result": "Failed",
                            "reason": "VSS timeout",
                            "end_time": "2026-08-03T01:00:00Z",
                        }
                    ],
                )
            },
        },
        {"job_name": "B", "daily": {"2026-08-02": cell()}},
    ]
    result = _classify_host(make_server(), make_payload(DATES, jobs), 3)
    assert result["status"] == "failed"
    assert result["jobs_failed"] == 1
    assert result["failures"] == [
        {"job_name": "A", "date": "2026-08-03", "reason": "VSS timeout"}
    ]
    assert result["last_run"] == "2026-08-03T01:00:00Z"


def test_classify_warning_when_no_failures():
    jobs = [{"job_name": "A", "daily": {"2026-08-03": cell("Warning", warning=2)}}]
    result = _classify_host(make_server(), make_payload(DATES, jobs), 3)
    assert result["status"] == "warning"
    assert result["jobs_warning"] == 1
    assert result["jobs_failed"] == 0


def test_classify_no_data_when_no_activity():
    result = _classify_host(make_server(), make_payload([], []), 3)
    assert result["status"] == "no_data"
    assert result["jobs_total"] == 0
    assert result["error"] is None


def test_classify_error_payload():
    result = _classify_host(make_server(), {"success": False, "error": "relay down"}, 3)
    assert result["status"] == "error"
    assert result["error"] == "relay down"


def test_classify_tolerates_non_dict_payload():
    result = _classify_host(make_server(), None, 3)
    assert result["status"] == "no_data"
    assert result["error"] is None


def test_classify_ignores_activity_outside_window():
    jobs = [
        {
            "job_name": "A",
            "daily": {
                "2026-08-01": cell(
                    "Failed",
                    failed=1,
                    runs=[{"result": "Failed", "reason": "old"}],
                ),
                "2026-08-03": cell(),
            },
        }
    ]
    result = _classify_host(make_server(), make_payload(DATES, jobs), 1)
    assert result["status"] == "passed"
    assert result["failures"] == []


def test_classify_dedupes_and_caps_failures():
    runs = [{"result": "Failed", "reason": f"r{i}"} for i in range(15)]
    jobs = [
        {
            "job_name": "A",
            "daily": {"2026-08-03": cell("Failed", failed=15, runs=runs)},
        }
    ]
    result = _classify_host(make_server(), make_payload(DATES, jobs), 3)
    assert len(result["failures"]) == 10


class StubProvider:
    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    async def get_job_stats_daily(self, days=7, include_system=False):
        self.calls.append((days, include_system))
        return self._payload


def _patch_provider(monkeypatch, payload):
    provider = StubProvider(payload)

    def _build(_db, _server):
        return provider

    monkeypatch.setattr(routes_module, "build_server_provider", _build)
    return provider


def test_hosts_status_aggregates_enabled_servers(db_session, monkeypatch):
    enabled = VeeamBackupServer(name="enabled-host", enabled=True)
    disabled = VeeamBackupServer(name="disabled-host", enabled=False)
    db_session.add_all([enabled, disabled])
    db_session.commit()

    jobs = [
        {
            "job_name": "Nightly",
            "daily": {
                "2026-08-03": cell(
                    "Failed",
                    failed=1,
                    runs=[{"result": "Failed", "reason": "disk full"}],
                )
            },
        }
    ]
    provider = _patch_provider(monkeypatch, make_payload(DATES, jobs))

    data = asyncio.run(routes_module.hosts_status(days=3, refresh=False, db=db_session))

    assert data["success"] is True
    assert data["days"] == 3
    assert data["count"] == 1
    host = data["hosts"][0]
    assert host["name"] == "enabled-host"
    assert host["server_id"] == enabled.id
    assert host["status"] == "failed"
    assert host["failures"][0]["reason"] == "disk full"
    assert provider.calls == [(3, False)]


def test_hosts_status_empty_when_no_enabled_servers(db_session, monkeypatch):
    db_session.add(VeeamBackupServer(name="disabled-host", enabled=False))
    db_session.commit()
    _patch_provider(monkeypatch, make_payload(DATES, []))

    data = asyncio.run(routes_module.hosts_status(days=3, refresh=False, db=db_session))

    assert data == {"success": True, "days": 3, "count": 0, "hosts": []}


def test_hosts_status_isolates_provider_errors(db_session, monkeypatch):
    server = VeeamBackupServer(name="broken-host", enabled=True)
    db_session.add(server)
    db_session.commit()

    def _build(_db, _server):
        raise RuntimeError("no provider")

    monkeypatch.setattr(routes_module, "build_server_provider", _build)

    data = asyncio.run(routes_module.hosts_status(days=3, refresh=False, db=db_session))

    assert data["count"] == 1
    host = data["hosts"][0]
    assert host["status"] == "error"
    assert "no provider" in host["error"]


def test_hosts_status_served_from_fresh_snapshot(db_session, monkeypatch):
    server = VeeamBackupServer(name="cached-host", enabled=True)
    db_session.add(server)
    db_session.commit()

    jobs = [{"job_name": "A", "daily": {"2026-08-03": cell()}}]
    snapshot = make_payload(DATES, jobs)
    routes_module._upsert_snapshot(db_session, server.id, "job_stats_daily:3:jobs", snapshot)
    db_session.commit()

    provider = _patch_provider(monkeypatch, make_payload(DATES, []))

    async def boom(days=7, include_system=False):
        raise AssertionError("provider must not be called for a fresh snapshot")

    monkeypatch.setattr(provider, "get_job_stats_daily", boom)

    data = asyncio.run(routes_module.hosts_status(days=3, refresh=False, db=db_session))

    assert data["count"] == 1
    assert data["hosts"][0]["status"] == "passed"


def test_classify_ignores_unparseable_counts():
    jobs = [
        {
            "job_name": "A",
            "daily": {
                "2026-08-03": {
                    "failed_count": None,
                    "warning_count": None,
                    "runs": [{"result": "Success"}],
                }
            },
        }
    ]
    result = _classify_host(make_server(), make_payload(DATES, jobs), 3)
    assert result["status"] == "passed"
    assert result["jobs_failed"] == 0
