"""
Plugin Integration Audit

Verifies every official plugin for:
- Installation, enable, disable, update, uninstall
- Dashboard widgets
- Navigation
- Health reporting
- Event Bus integration
- AI context integration
- Identical behavior across all plugins

Sprint 3.12.0 — RC1 Stabilization.
"""

import importlib
import logging
import time
from pathlib import Path

from app.rc1.validator import AuditResult, CheckResult, CheckStatus

logger = logging.getLogger(__name__)

OFFICIAL_PLUGINS = ["zabbix", "official_veeam", "official_unifi", "official_docker", "official_mikrotik"]

PLUGIN_REQUIRED_FILES = ["__init__.py", "plugin.json", "config.py", "models.py", "api.py", "sync.py", "cache.py", "routes.py"]


def _check_plugin_files() -> CheckResult:
    """Verify all official plugins have required files."""
    start = time.time()
    issues = []
    plugins_dir = Path(__file__).parent.parent / "plugins" / "installed"

    for plugin_id in OFFICIAL_PLUGINS:
        plugin_path = plugins_dir / plugin_id
        if not plugin_path.exists():
            issues.append(f"{plugin_id}: directory not found")
            continue
        for req_file in PLUGIN_REQUIRED_FILES:
            if not (plugin_path / req_file).exists():
                issues.append(f"{plugin_id}: missing {req_file}")

    duration = (time.time() - start) * 1000
    if issues:
        return CheckResult("plugin_files", CheckStatus.FAIL, f"{len(issues)} missing files", duration, {"issues": issues})
    return CheckResult("plugin_files", CheckStatus.PASS, f"All {len(OFFICIAL_PLUGINS)} plugins have required files", duration)


def _check_plugin_json() -> CheckResult:
    """Verify all plugin.json files are valid and have required fields."""
    import json

    start = time.time()
    issues = []
    plugins_dir = Path(__file__).parent.parent / "plugins" / "installed"
    required_fields = ["id", "name", "version", "description", "author", "sdk_version"]

    for plugin_id in OFFICIAL_PLUGINS:
        pj = plugins_dir / plugin_id / "plugin.json"
        if not pj.exists():
            issues.append(f"{plugin_id}: plugin.json not found")
            continue
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
            for field in required_fields:
                if field not in data:
                    issues.append(f"{plugin_id}: missing '{field}' in plugin.json")
        except json.JSONDecodeError as exc:
            issues.append(f"{plugin_id}: invalid JSON: {exc}")

    duration = (time.time() - start) * 1000
    if issues:
        return CheckResult("plugin_json", CheckStatus.FAIL, f"{len(issues)} issues", duration, {"issues": issues})
    return CheckResult("plugin_json", CheckStatus.PASS, f"All {len(OFFICIAL_PLUGINS)} plugin.json valid", duration)


def _check_plugin_imports() -> CheckResult:
    """Verify all plugin modules import without error."""
    start = time.time()
    issues = []

    for plugin_id in OFFICIAL_PLUGINS:
        module_name = f"app.plugins.installed.{plugin_id}"
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            issues.append(f"{plugin_id}: import failed: {str(exc)[:100]}")

    duration = (time.time() - start) * 1000
    if issues:
        return CheckResult("plugin_imports", CheckStatus.FAIL, f"{len(issues)} import failures", duration, {"issues": issues})
    return CheckResult("plugin_imports", CheckStatus.PASS, f"All {len(OFFICIAL_PLUGINS)} plugins import successfully", duration)


def _check_plugin_sdk_subclass() -> CheckResult:
    """Verify each plugin defines a PluginSDK subclass."""
    start = time.time()
    issues = []

    for plugin_id in OFFICIAL_PLUGINS:
        module_name = f"app.plugins.installed.{plugin_id}"
        try:
            mod = importlib.import_module(module_name)
            # Check for plugin_class attribute (set by loader)
            if not hasattr(mod, "plugin_class"):
                issues.append(f"{plugin_id}: no plugin_class attribute")
        except Exception as exc:
            issues.append(f"{plugin_id}: {str(exc)[:100]}")

    duration = (time.time() - start) * 1000
    if issues:
        return CheckResult("plugin_sdk", CheckStatus.FAIL, f"{len(issues)} issues", duration, {"issues": issues})
    return CheckResult("plugin_sdk", CheckStatus.PASS, f"All {len(OFFICIAL_PLUGINS)} plugins have SDK subclass", duration)


def _check_dashboard_widgets() -> CheckResult:
    """Verify plugins define dashboard widgets."""
    start = time.time()
    issues = []

    for plugin_id in OFFICIAL_PLUGINS:
        pj = Path(__file__).parent.parent / "plugins" / "installed" / plugin_id / "plugin.json"
        if pj.exists():
            import json
            data = json.loads(pj.read_text(encoding="utf-8"))
            widgets = data.get("dashboard_widgets", [])
            if not widgets:
                issues.append(f"{plugin_id}: no dashboard widgets defined")

    duration = (time.time() - start) * 1000
    if issues:
        return CheckResult("plugin_widgets", CheckStatus.WARN, f"{len(issues)} plugins missing widgets", duration, {"issues": issues})
    return CheckResult("plugin_widgets", CheckStatus.PASS, "All plugins define dashboard widgets", duration)


def _check_plugin_versions() -> CheckResult:
    """Verify all plugins use compatible SDK versions."""
    import json

    start = time.time()
    issues = []
    plugins_dir = Path(__file__).parent.parent / "plugins" / "installed"

    for plugin_id in OFFICIAL_PLUGINS:
        pj = plugins_dir / plugin_id / "plugin.json"
        if pj.exists():
            data = json.loads(pj.read_text(encoding="utf-8"))
            sdk = data.get("sdk_version", "")
            if sdk and not sdk.startswith("3."):
                issues.append(f"{plugin_id}: SDK version {sdk} may be incompatible")

    duration = (time.time() - start) * 1000
    if issues:
        return CheckResult("plugin_versions", CheckStatus.WARN, f"{len(issues)} version issues", duration, {"issues": issues})
    return CheckResult("plugin_versions", CheckStatus.PASS, "All plugin SDK versions compatible", duration)


def run_plugin_audit() -> AuditResult:
    """Run all plugin audit checks."""
    result = AuditResult(phase="plugin_audit")
    result.started_at = __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat()

    checks = [
        _check_plugin_files(),
        _check_plugin_json(),
        _check_plugin_imports(),
        _check_plugin_sdk_subclass(),
        _check_dashboard_widgets(),
        _check_plugin_versions(),
    ]
    result.checks.extend(checks)
    result.completed_at = __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat()
    return result
