"""
RC1 Validation Tests

Tests the validation framework itself:
- Validator runs all phases
- Each audit module produces valid results
- Certification report generation
- Check results have required fields

Sprint 3.12.0 — RC1 Stabilization.
"""




class TestValidator:
    def test_validator_instantiation(self):
        from app.rc1.validator import RC1Validator

        v = RC1Validator()
        assert v.results == {}

    def test_run_api_audit(self):
        from app.rc1.validator import RC1Validator

        v = RC1Validator()
        result = v.run_api_audit()
        assert result.phase == "api_audit"
        assert len(result.checks) > 0
        assert "api_audit" in v.results

    def test_run_plugin_audit(self):
        from app.rc1.validator import RC1Validator

        v = RC1Validator()
        result = v.run_plugin_audit()
        assert result.phase == "plugin_audit"
        assert len(result.checks) > 0

    def test_run_security_audit(self):
        from app.rc1.validator import RC1Validator

        v = RC1Validator()
        result = v.run_security_audit()
        assert result.phase == "security_audit"
        assert len(result.checks) > 0

    def test_run_performance_audit(self):
        from app.rc1.validator import RC1Validator

        v = RC1Validator()
        result = v.run_performance_audit()
        assert result.phase == "performance_audit"
        assert len(result.checks) > 0

    def test_to_dict(self):
        from app.rc1.validator import RC1Validator

        v = RC1Validator()
        v.run_api_audit()
        d = v.to_dict()
        assert "api_audit" in d
        assert "checks" in d["api_audit"]


class TestAuditResult:
    def test_pass_count(self):
        from app.rc1.validator import AuditResult, CheckResult, CheckStatus

        r = AuditResult(phase="test")
        r.checks.append(CheckResult("c1", CheckStatus.PASS))
        r.checks.append(CheckResult("c2", CheckStatus.FAIL))
        assert r.pass_count == 1
        assert r.fail_count == 1
        assert r.passed is False

    def test_all_pass(self):
        from app.rc1.validator import AuditResult, CheckResult, CheckStatus

        r = AuditResult(phase="test")
        r.checks.append(CheckResult("c1", CheckStatus.PASS))
        r.checks.append(CheckResult("c2", CheckStatus.PASS))
        assert r.passed is True

    def test_to_dict(self):
        from app.rc1.validator import AuditResult, CheckResult, CheckStatus

        r = AuditResult(phase="test")
        r.checks.append(CheckResult("c1", CheckStatus.PASS, "ok", 1.5))
        d = r.to_dict()
        assert d["phase"] == "test"
        assert d["pass_count"] == 1
        assert len(d["checks"]) == 1


class TestCheckResult:
    def test_fields(self):
        from app.rc1.validator import CheckResult, CheckStatus

        c = CheckResult(name="test", status=CheckStatus.PASS, message="all good", duration_ms=42.5)
        assert c.name == "test"
        assert c.status == CheckStatus.PASS
        assert c.message == "all good"
        assert c.duration_ms == 42.5

    def test_default_details(self):
        from app.rc1.validator import CheckResult, CheckStatus

        c = CheckResult(name="x", status=CheckStatus.WARN)
        assert c.details == {}


class TestCertification:
    def test_generate_report(self, tmp_path):
        from app.rc1.certification import generate_rc1_report

        result = generate_rc1_report(str(tmp_path))
        assert "certified" in result
        assert "reports" in result
        assert len(result["reports"]) == 3

        # Verify files exist
        for path in result["reports"]:
            from pathlib import Path
            assert Path(path).exists()

    def test_generate_markdown_content(self, tmp_path):
        from app.rc1.certification import generate_rc1_report

        result = generate_rc1_report(str(tmp_path))
        md_path = next(p for p in result["reports"] if p.endswith(".md"))
        with open(md_path, encoding="utf-8") as f:
            content = f.read()
        assert "RC1 Certification Report" in content
        assert "Summary" in content

    def test_generate_summary_content(self, tmp_path):
        from app.rc1.certification import generate_rc1_report

        result = generate_rc1_report(str(tmp_path))
        txt_path = next(p for p in result["reports"] if p.endswith(".txt"))
        with open(txt_path, encoding="utf-8") as f:
            content = f.read()
        assert "CERTIFICATION SUMMARY" in content


class TestApiAudit:
    def test_check_endpoint_naming(self):
        from app.rc1.api_audit import _check_endpoint_naming

        result = _check_endpoint_naming()
        assert result.name == "endpoint_naming"
        assert result.status.value in ("pass", "warn", "fail")

    def test_check_http_methods(self):
        from app.rc1.api_audit import _check_http_methods

        result = _check_http_methods()
        assert result.name == "http_methods"

    def test_check_error_responses(self):
        from app.rc1.api_audit import _check_error_responses

        result = _check_error_responses()
        assert result.name == "error_responses"

    def test_check_authentication(self):
        from app.rc1.api_audit import _check_authentication

        result = _check_authentication()
        assert result.name == "authentication"

    def test_run_api_audit(self):
        from app.rc1.api_audit import run_api_audit

        result = run_api_audit()
        assert result.phase == "api_audit"
        assert len(result.checks) >= 5


class TestPluginAudit:
    def test_check_plugin_files(self):
        from app.rc1.plugin_audit import _check_plugin_files

        result = _check_plugin_files()
        assert result.name == "plugin_files"

    def test_check_plugin_json(self):
        from app.rc1.plugin_audit import _check_plugin_json

        result = _check_plugin_json()
        assert result.name == "plugin_json"

    def test_run_plugin_audit(self):
        from app.rc1.plugin_audit import run_plugin_audit

        result = run_plugin_audit()
        assert result.phase == "plugin_audit"
        assert len(result.checks) >= 4


class TestSecurityAudit:
    def test_check_jwt(self):
        from app.rc1.security_audit import _check_jwt

        result = _check_jwt()
        assert result.name == "jwt"

    def test_check_secrets(self):
        from app.rc1.security_audit import _check_secrets

        result = _check_secrets()
        assert result.name == "secrets"

    def test_run_security_audit(self):
        from app.rc1.security_audit import run_security_audit

        result = run_security_audit()
        assert result.phase == "security_audit"
        assert len(result.checks) >= 6


class TestPerformanceAudit:
    def test_run_performance_audit(self):
        from app.rc1.performance import run_performance_audit

        result = run_performance_audit()
        assert result.phase == "performance_audit"
        assert len(result.checks) >= 5
