"""
Mission Control Veeam B&R Provider Tests

Tests for mocked Veeam provider.
Validates all standardized provider methods return correct shapes.
"""

import pytest

from app.providers.veeam.mock_provider import MockVeeamProvider
from app.providers.veeam.provider_factory import (
    get_veeam_provider,
    reset_veeam_provider,
)

# ------------------------------------------------------------------ #
# Mock Provider Tests                                                 #
# ------------------------------------------------------------------ #


class TestMockVeeamTestConnection:
    """Tests for Veeam mock provider test_connection."""

    @pytest.fixture()
    def provider(self) -> MockVeeamProvider:
        return MockVeeamProvider()

    @pytest.mark.anyio()
    async def test_returns_connected_true(self, provider: MockVeeamProvider) -> None:
        result = await provider.test_connection()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_has_version(self, provider: MockVeeamProvider) -> None:
        result = await provider.test_connection()
        assert "version" in result
        assert result["version"] != ""

    @pytest.mark.anyio()
    async def test_has_name(self, provider: MockVeeamProvider) -> None:
        result = await provider.test_connection()
        assert "name" in result
        assert result["name"] != ""

    @pytest.mark.anyio()
    async def test_has_mock_flag(self, provider: MockVeeamProvider) -> None:
        result = await provider.test_connection()
        assert result.get("_mock") is True


class TestMockVeeamGetSummary:
    """Tests for Veeam mock provider get_summary."""

    @pytest.fixture()
    def provider(self) -> MockVeeamProvider:
        return MockVeeamProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_summary()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_job_counts(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_summary()
        assert "total_jobs" in result
        assert isinstance(result["total_jobs"], int)
        assert result["total_jobs"] > 0

    @pytest.mark.anyio()
    async def test_has_repository_counts(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_summary()
        assert "total_repositories" in result
        assert result["total_repositories"] > 0

    @pytest.mark.anyio()
    async def test_has_space_info(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_summary()
        assert "total_space_bytes" in result
        assert "used_space_bytes" in result
        assert result["total_space_bytes"] > 0

    @pytest.mark.anyio()
    async def test_has_session_stats(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_summary()
        assert "sessions_success" in result
        assert "sessions_warning" in result
        assert "sessions_failed" in result


class TestMockVeeamGetJobs:
    """Tests for Veeam mock provider get_jobs."""

    @pytest.fixture()
    def provider(self) -> MockVeeamProvider:
        return MockVeeamProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_jobs()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_jobs_list(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_jobs()
        assert "jobs" in result
        assert isinstance(result["jobs"], list)
        assert len(result["jobs"]) > 0

    @pytest.mark.anyio()
    async def test_has_count(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_jobs()
        assert "count" in result
        assert result["count"] == len(result["jobs"])

    @pytest.mark.anyio()
    async def test_job_has_required_fields(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_jobs()
        job = result["jobs"][0]
        assert "id" in job
        assert "name" in job
        assert "status" in job
        assert "type" in job


class TestMockVeeamGetRepositories:
    """Tests for Veeam mock provider get_repositories."""

    @pytest.fixture()
    def provider(self) -> MockVeeamProvider:
        return MockVeeamProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_repositories()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_repositories(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_repositories()
        assert "repositories" in result
        assert len(result["repositories"]) > 0

    @pytest.mark.anyio()
    async def test_repo_has_capacity(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_repositories()
        repo = result["repositories"][0]
        assert "capacityBytes" in repo or "capacity_bytes" in repo


class TestMockVeeamGetSessions:
    """Tests for Veeam mock provider get_sessions."""

    @pytest.fixture()
    def provider(self) -> MockVeeamProvider:
        return MockVeeamProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_sessions()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_sessions(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_sessions()
        assert "sessions" in result
        assert len(result["sessions"]) > 0


class TestMockVeeamGetLicense:
    """Tests for Veeam mock provider get_license."""

    @pytest.fixture()
    def provider(self) -> MockVeeamProvider:
        return MockVeeamProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_license()
        assert result["success"] is True
        assert "license" in result


class TestMockVeeamGetRestorePoints:
    """Tests for Veeam mock provider get_restore_points."""

    @pytest.fixture()
    def provider(self) -> MockVeeamProvider:
        return MockVeeamProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_restore_points()
        assert result["success"] is True
        assert len(result["restore_points"]) > 0

    @pytest.mark.anyio()
    async def test_filter_by_vm_id(self, provider: MockVeeamProvider) -> None:
        result_all = await provider.get_restore_points()
        vm_id = result_all["restore_points"][0]["vmId"]
        result_filtered = await provider.get_restore_points(vm_id=vm_id)
        assert all(rp["vmId"] == vm_id for rp in result_filtered["restore_points"])


class TestMockVeeamGetCapacityTier:
    """Tests for Veeam mock provider get_capacity_tier."""

    @pytest.fixture()
    def provider(self) -> MockVeeamProvider:
        return MockVeeamProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_capacity_tier()
        assert result["success"] is True
        assert "object_storages" in result


class TestMockVeeamJobControl:
    """Tests for Veeam mock provider job start/stop."""

    @pytest.fixture()
    def provider(self) -> MockVeeamProvider:
        return MockVeeamProvider()

    @pytest.mark.anyio()
    async def test_start_job(self, provider: MockVeeamProvider) -> None:
        result = await provider.start_job("job-001")
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_stop_job(self, provider: MockVeeamProvider) -> None:
        result = await provider.stop_job("job-001")
        assert result["success"] is True


class TestMockVeeamHealth:
    """Tests for Veeam mock provider get_health."""

    @pytest.fixture()
    def provider(self) -> MockVeeamProvider:
        return MockVeeamProvider()

    @pytest.mark.anyio()
    async def test_returns_healthy(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_health()
        assert result["healthy"] is True


class TestMockVeeamGetManagedServers:
    """Tests for Veeam mock provider get_managed_servers."""

    @pytest.fixture()
    def provider(self) -> MockVeeamProvider:
        return MockVeeamProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_managed_servers()
        assert result["success"] is True
        assert len(result["servers"]) > 0


class TestMockVeeamGetJobDetail:
    """Tests for Veeam mock provider get_job_detail."""

    @pytest.fixture()
    def provider(self) -> MockVeeamProvider:
        return MockVeeamProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockVeeamProvider) -> None:
        result = await provider.get_job_detail("job-001")
        assert result["success"] is True
        assert "job" in result


# ------------------------------------------------------------------ #
# Provider Factory Tests                                              #
# ------------------------------------------------------------------ #


class TestVeeamProviderFactory:
    """Tests for Veeam provider factory."""

    def setup_method(self) -> None:
        reset_veeam_provider()

    def teardown_method(self) -> None:
        reset_veeam_provider()

    def test_factory_returns_mock_without_db(self) -> None:
        provider = get_veeam_provider(db=None)
        assert isinstance(provider, MockVeeamProvider)

    def test_factory_returns_singleton(self) -> None:
        p1 = get_veeam_provider(db=None)
        p2 = get_veeam_provider(db=None)
        assert p1 is p2

    def test_reset_clears_singleton(self) -> None:
        p1 = get_veeam_provider(db=None)
        reset_veeam_provider()
        p2 = get_veeam_provider(db=None)
        assert p1 is not p2


# ------------------------------------------------------------------ #
# SSH Bridge Stats Tests                                              #
# ------------------------------------------------------------------ #


def _make_provider(**kwargs):
    from app.providers.veeam.veeam_provider import VeeamRESTProvider
    defaults = {
        "base_url": "https://veeam.local:9419",
        "username": "admin",
        "password": "pass",
        "ssh_host": "10.0.0.1",
        "ssh_username": "root",
        "ssh_password": "pw",
        "data_source": "ssh",
    }
    defaults.update(kwargs)
    return VeeamRESTProvider(**defaults)


class TestSessionStatsParsing:
    """Tests for Veeam SSH bridge session stats output parsing."""

    @pytest.mark.anyio()
    async def test_no_ssh_returns_empty(self) -> None:
        provider = _make_provider(ssh_host="", ssh_username="")
        result = await provider.get_session_stats()
        assert result["success"] is True
        assert result["stats"] == []
        assert result["ssh_available"] is False

    @pytest.mark.anyio()
    async def test_parse_single_session(self) -> None:
        provider = _make_provider()
        mock_output = (
            "sess-001|job-abc|Daily Backup|Stopped|2025-01-15 02:00:00|"
            "2025-01-15 03:30:00|0|107374182400|53687091200|"
            "85899345920|42949672960|104857600|"
        )
        provider._run_pg_query = lambda sql: _async_pg_result(mock_output)
        result = await provider.get_session_stats()
        assert result["success"] is True
        assert result["ssh_available"] is True
        assert len(result["stats"]) == 1
        s = result["stats"][0]
        assert s["session_id"] == "sess-001"
        assert s["job_id"] == "job-abc"
        assert s["job_name"] == "Daily Backup"
        assert s["processed_bytes"] == 53687091200
        assert s["read_bytes"] == 85899345920
        assert s["transferred_bytes"] == 42949672960

    @pytest.mark.anyio()
    async def test_parse_multiple_sessions(self) -> None:
        provider = _make_provider()
        mock_output = (
            "sess-001|job-01|Job A|Stopped|2025-01-15 02:00:00|"
            "2025-01-15 03:00:00|0|100|50|60|40|10\n"
            "sess-002|job-02|Job B|Stopped|2025-01-15 03:00:00|"
            "2025-01-15 04:00:00|1|200|100|120|80|20\n"
            "sess-003|job-01|Job A|Stopped|2025-01-15 04:00:00|"
            "2025-01-15 05:00:00|0|300|150|180|120|30\n"
        )
        provider._run_pg_query = lambda sql: _async_pg_result(mock_output)
        result = await provider.get_session_stats()
        assert len(result["stats"]) == 3
        assert result["count"] == 3
        assert result["stats"][0]["job_id"] == "job-01"
        assert result["stats"][1]["job_id"] == "job-02"

    @pytest.mark.anyio()
    async def test_skips_warning_and_empty_lines(self) -> None:
        provider = _make_provider()
        mock_output = (
            "\nWARNING: something\n"
            "sess-001|job-01|Job A|Stopped|2025-01-15 02:00:00|"
            "2025-01-15 03:00:00|0|100|50|60|40|10\n"
            "(3 rows)\n"
        )
        provider._run_pg_query = lambda sql: _async_pg_result(mock_output)
        result = await provider.get_session_stats()
        assert len(result["stats"]) == 1

    @pytest.mark.anyio()
    async def test_ssh_failure_returns_error(self) -> None:
        provider = _make_provider()
        provider._run_pg_query = lambda sql: _async_pg_error("Connection refused", "Permission denied")
        result = await provider.get_session_stats()
        assert result["success"] is False
        assert result["ssh_available"] is False
        assert "Permission denied" in result["error"]

    @pytest.mark.anyio()
    async def test_zero_bytes_handled(self) -> None:
        provider = _make_provider()
        mock_output = (
            "sess-001|job-01|Job A|Stopped|2025-01-15 02:00:00|"
            "2025-01-15 03:00:00|0|||0|||"
        )
        provider._run_pg_query = lambda sql: _async_pg_result(mock_output)
        result = await provider.get_session_stats()
        assert len(result["stats"]) == 1
        assert result["stats"][0]["processed_bytes"] == 0
        assert result["stats"][0]["read_bytes"] == 0


class TestJobStatsParsing:
    """Tests for Veeam SSH bridge job stats output parsing."""

    @pytest.mark.anyio()
    async def test_no_ssh_returns_empty(self) -> None:
        provider = _make_provider(ssh_host="", ssh_username="")
        result = await provider.get_job_stats()
        assert result["success"] is True
        assert result["jobs"] == []
        assert result["ssh_available"] is False

    @pytest.mark.anyio()
    async def test_parse_single_job(self) -> None:
        provider = _make_provider()
        mock_output = (
            "Daily Backup|30|5000000000000|3000000000000|"
            "2000000000000|2500000000000|104857600|"
            "2025-01-15 03:30:00|25|3|2|"
        )
        provider._run_pg_query = lambda sql: _async_pg_result(mock_output)
        result = await provider.get_job_stats()
        assert result["success"] is True
        assert result["ssh_available"] is True
        assert len(result["jobs"]) == 1
        j = result["jobs"][0]
        assert j["job_name"] == "Daily Backup"
        assert j["session_count"] == 30
        assert j["processed_bytes"] == 3000000000000
        assert j["success_count"] == 25
        assert j["warning_count"] == 3
        assert j["failed_count"] == 2

    @pytest.mark.anyio()
    async def test_parse_multiple_jobs(self) -> None:
        provider = _make_provider()
        mock_output = (
            "Job A|10|1000|500|400|300|50|2025-01-15 03:00:00|9|1|0|\n"
            "Job B|5|500|250|200|150|25|2025-01-15 04:00:00|4|0|1|\n"
        )
        provider._run_pg_query = lambda sql: _async_pg_result(mock_output)
        result = await provider.get_job_stats()
        assert len(result["jobs"]) == 2
        assert result["count"] == 2

    @pytest.mark.anyio()
    async def test_ssh_failure_returns_error(self) -> None:
        provider = _make_provider()
        provider._run_pg_query = lambda sql: _async_pg_error("timeout")
        result = await provider.get_job_stats()
        assert result["success"] is False
        assert result["ssh_available"] is False


class TestJobsFromPg:
    """Tests for Veeam SSH-only job list construction from PG stats."""

    @pytest.mark.anyio()
    async def test_ssh_only_builds_job_list_from_stats(self) -> None:
        provider = _make_provider()
        mock_output = (
            "Daily Backup|30|5000000000000|3000000000000|"
            "2000000000000|2500000000000|104857600|"
            "2025-01-15 03:30:00|25|3|2|"
        )
        provider._run_pg_query = lambda sql: _async_pg_result(mock_output)
        result = await provider.get_jobs()
        assert result["success"] is True
        assert len(result["jobs"]) == 1
        job = result["jobs"][0]
        assert job["name"] == "Daily Backup"
        assert job["id"] == "Daily Backup"
        assert job["state"] == "Failed"
        assert "_pg_stats" in job
        assert job["_pg_stats"]["processed_bytes"] == 3000000000000

    @pytest.mark.anyio()
    async def test_ssh_only_failed_job_state(self) -> None:
        provider = _make_provider()
        mock_output = (
            "Failed Job|1|100|50|40|30|10|"
            "2025-01-15 03:30:00|0|0|1|"
        )
        provider._run_pg_query = lambda sql: _async_pg_result(mock_output)
        result = await provider.get_jobs()
        job = result["jobs"][0]
        assert job["state"] == "Failed"


class TestSessionsFromPg:
    """Tests for Veeam SSH-only session list construction from PG stats."""

    @pytest.mark.anyio()
    async def test_ssh_only_builds_session_list(self) -> None:
        provider = _make_provider()
        mock_output = (
            "sess-001|job-01|Daily Backup|Stopped|"
            "2025-01-15 02:00:00|2025-01-15 03:00:00|0|"
            "100|50|60|40|10\n"
        )
        provider._run_pg_query = lambda sql: _async_pg_result(mock_output)
        result = await provider.get_sessions()
        assert result["success"] is True
        assert len(result["sessions"]) == 1
        s = result["sessions"][0]
        assert s["id"] == "sess-001"
        assert s["jobId"] == "job-01"
        assert s["name"] == "Daily Backup"
        assert s["result"] == {"result": "Success"}

    @pytest.mark.anyio()
    async def test_ssh_only_failed_result(self) -> None:
        provider = _make_provider()
        mock_output = (
            "sess-002|job-02|Backup Job|Stopped|"
            "2025-01-15 04:00:00|2025-01-15 05:00:00|2|"
            "200|100|120|80|20\n"
        )
        provider._run_pg_query = lambda sql: _async_pg_result(mock_output)
        result = await provider.get_sessions()
        s = result["sessions"][0]
        assert s["result"] == {"result": "Failed"}


async def _async_pg_result(output: str) -> dict:
    return {
        "success": True,
        "output": output,
        "stderr": "",
        "exit_code": 0,
    }


async def _async_pg_error(error: str, stderr: str = "") -> dict:
    return {
        "success": False,
        "error": error,
        "output": "",
        "stderr": stderr,
    }
