#!/usr/bin/env python3
"""
Mission Control Validation Framework — Runner

Executes all validation modules and produces reports.

Usage:
    python scripts/validation/run_validation.py
    python scripts/validation/run_validation.py --base-url http://localhost:8000
    python scripts/validation/run_validation.py --modules api,agents,plugins
    python scripts/validation/run_validation.py --output reports/validation/
"""

import argparse
import json
import platform
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from validators import BaseValidator, Status, ValidatorResult
from validators.installation import InstallationValidator
from validators.database import DatabaseValidator
from validators.redis import RedisValidator
from validators.api import APIValidator
from validators.dashboard import DashboardValidator
from validators.authentication import AuthenticationValidator
from validators.agents import AgentsValidator
from validators.plugins import PluginsValidator
from validators.automation import AutomationValidator
from validators.heartbeat import HeartbeatValidator
from validators.backup import BackupValidator
from validators.restore import RestoreValidator
from validators.performance import PerformanceValidator
from validators.security import SecurityValidator

# All available validators
ALL_VALIDATORS: dict[str, type[BaseValidator]] = {
    "installation": InstallationValidator,
    "database": DatabaseValidator,
    "redis": RedisValidator,
    "api": APIValidator,
    "dashboard": DashboardValidator,
    "authentication": AuthenticationValidator,
    "agents": AgentsValidator,
    "plugins": PluginsValidator,
    "automation": AutomationValidator,
    "heartbeat": HeartbeatValidator,
    "backup": BackupValidator,
    "restore": RestoreValidator,
    "performance": PerformanceValidator,
    "security": SecurityValidator,
}

# Default execution order
DEFAULT_ORDER = [
    "installation",
    "database",
    "redis",
    "api",
    "authentication",
    "dashboard",
    "agents",
    "plugins",
    "automation",
    "heartbeat",
    "backup",
    "restore",
    "performance",
    "security",
]


def get_system_info() -> dict:
    """Collect system information for the report."""
    info: dict = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Git info
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
            timeout=5,
        )
        if result.returncode == 0:
            info["git_commit"] = result.stdout.strip()
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
            timeout=5,
        )
        if result.returncode == 0:
            info["git_branch"] = result.stdout.strip()
    except Exception:
        pass

    # Docker info
    try:
        result = subprocess.run(
            ["docker", "compose", "version", "--short"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
            timeout=5,
        )
        if result.returncode == 0:
            info["docker_compose"] = result.stdout.strip()
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            info["docker"] = result.stdout.strip()
    except Exception:
        pass

    return info


def print_summary(results: list[ValidatorResult]) -> None:
    """Print a summary table to the console."""
    print("")
    print("=" * 70)
    print("  Mission Control — Validation Summary")
    print("=" * 70)
    print("")
    print(f"  {'Module':<20} {'Pass':>5} {'Fail':>5} {'Warn':>5} {'Skip':>5} {'Time':>8}")
    print("  " + "-" * 55)

    total_pass = 0
    total_fail = 0
    total_warn = 0
    total_skip = 0

    for r in results:
        marker = " " if r.ok else "!"
        print(
            f"  {marker} {r.module:<18} {r.passed:>5} {r.failed:>5} "
            f"{r.warnings:>5} {r.skipped:>5} {r.duration_ms:>7.0f}ms"
        )
        total_pass += r.passed
        total_fail += r.failed
        total_warn += r.warnings
        total_skip += r.skipped

    print("  " + "-" * 55)
    print(
        f"  {'TOTAL':<20} {total_pass:>5} {total_fail:>5} "
        f"{total_warn:>5} {total_skip:>5}"
    )
    print("")

    if total_fail == 0:
        print("  RESULT: ALL VALIDATIONS PASSED")
        print("  Mission Control Community Edition v1.0 is certified.")
    else:
        print(f"  RESULT: {total_fail} VALIDATION(S) FAILED")
        print("  Review the failed checks before releasing.")

    print("")
    print("=" * 70)
    print("")


def generate_markdown_report(
    results: list[ValidatorResult],
    system_info: dict,
    output_dir: Path,
) -> Path:
    """Generate a Markdown validation report."""
    lines = [
        "# Mission Control — Validation Report",
        "",
        f"**Date:** {system_info.get('timestamp', 'unknown')}",
        f"**Platform:** {system_info.get('platform', 'unknown')}",
        f"**Python:** {system_info.get('python', 'unknown')}",
        f"**Docker Compose:** {system_info.get('docker_compose', 'unknown')}",
        f"**Git Commit:** {system_info.get('git_commit', 'unknown')}",
        f"**Git Branch:** {system_info.get('git_branch', 'unknown')}",
        "",
        "---",
        "",
        "## Summary",
        "",
    ]

    total_pass = sum(r.passed for r in results)
    total_fail = sum(r.failed for r in results)
    total_warn = sum(r.warnings for r in results)
    total_skip = sum(r.skipped for r in results)
    all_ok = total_fail == 0

    if all_ok:
        lines.append("**Status: CERTIFIED**")
    else:
        lines.append(f"**Status: {total_fail} FAILURE(S)**")

    lines.extend([
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Passed | {total_pass} |",
        f"| Failed | {total_fail} |",
        f"| Warnings | {total_warn} |",
        f"| Skipped | {total_skip} |",
        f"| Total | {total_pass + total_fail + total_warn + total_skip} |",
        "",
        "---",
        "",
        "## Detailed Results",
        "",
    ])

    for r in results:
        status_icon = "PASS" if r.ok else "FAIL"
        lines.append(f"### {r.module.title()} [{status_icon}]")
        lines.append("")
        lines.append(
            "| Check | Status | Message | Duration |"
        )
        lines.append(
            "|-------|--------|---------|----------|"
        )
        for c in r.checks:
            lines.append(
                f"| {c.name} | {c.status.value} | {c.message} | {c.duration_ms:.0f}ms |"
            )
        lines.append("")

        # Show failed details
        failed = [c for c in r.checks if c.status == Status.FAIL]
        if failed:
            lines.append("<details>")
            lines.append(f"<summary>Failed Checks ({len(failed)})</summary>")
            lines.append("")
            for c in failed:
                lines.append(f"**{c.name}**: {c.message}")
                if c.details:
                    lines.append("```")
                    lines.append(c.details[:500])
                    lines.append("```")
                lines.append("")
            lines.append("</details>")
            lines.append("")

    lines.extend([
        "---",
        "",
        "*Generated by Mission Control Validation Framework*",
    ])

    report_path = output_dir / "validation-report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def generate_json_report(
    results: list[ValidatorResult],
    system_info: dict,
    output_dir: Path,
) -> Path:
    """Generate a JSON validation report."""
    total_pass = sum(r.passed for r in results)
    total_fail = sum(r.failed for r in results)
    total_warn = sum(r.warnings for r in results)

    report = {
        "version": "1.0",
        "timestamp": system_info.get("timestamp", ""),
        "system": system_info,
        "summary": {
            "passed": total_pass,
            "failed": total_fail,
            "warnings": total_warn,
            "total": total_pass + total_fail + total_warn,
            "certified": total_fail == 0,
        },
        "modules": [r.to_dict() for r in results],
    }

    report_path = output_dir / "validation-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    return report_path


def generate_text_summary(
    results: list[ValidatorResult],
    system_info: dict,
    output_dir: Path,
) -> Path:
    """Generate a plain text summary."""
    lines = [
        "Mission Control — Validation Summary",
        "=" * 50,
        f"Date: {system_info.get('timestamp', '')}",
        f"Platform: {system_info.get('platform', '')}",
        f"Python: {system_info.get('python', '')}",
        "",
    ]

    total_pass = sum(r.passed for r in results)
    total_fail = sum(r.failed for r in results)
    total_warn = sum(r.warnings for r in results)

    for r in results:
        status = "PASS" if r.ok else "FAIL"
        lines.append(f"[{status}] {r.module}: {r.passed} pass, {r.failed} fail, {r.warnings} warn")

    lines.extend([
        "",
        f"Total: {total_pass} passed, {total_fail} failed, {total_warn} warnings",
        "",
        "CERTIFIED" if total_fail == 0 else "NOT CERTIFIED",
    ])

    summary_path = output_dir / "validation-summary.txt"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mission Control Validation Framework"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--modules",
        default=None,
        help="Comma-separated list of modules to run (default: all)",
    )
    parser.add_argument(
        "--output",
        default="reports/validation",
        help="Output directory for reports (default: reports/validation/)",
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip backup and restore validators (destructive tests)",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only output JSON report",
    )
    args = parser.parse_args()

    print("")
    print("  Mission Control — Release Validation Framework")
    print("  ================================================")
    print("")
    print(f"  Base URL: {args.base_url}")
    print(f"  Output:   {args.output}")
    print("")

    # Determine which modules to run
    if args.modules:
        module_names = [m.strip() for m in args.modules.split(",")]
    else:
        module_names = list(DEFAULT_ORDER)

    if args.skip_backup:
        module_names = [m for m in module_names if m not in ("backup", "restore")]

    # Validate module names
    for name in module_names:
        if name not in ALL_VALIDATORS:
            print(f"  ERROR: Unknown module '{name}'")
            print(f"  Available: {', '.join(sorted(ALL_VALIDATORS.keys()))}")
            return 1

    # Config
    config = {
        "base_url": args.base_url,
        "api_url": f"{args.base_url}/api/v1",
        "project_root": str(PROJECT_ROOT),
        "backend_dir": str(PROJECT_ROOT / "backend"),
        "scripts_dir": str(SCRIPT_DIR),
    }

    # System info
    system_info = get_system_info()

    # Run validators
    results: list[ValidatorResult] = []
    overall_start = time.perf_counter()

    for name in module_names:
        cls = ALL_VALIDATORS[name]
        validator = cls()
        print(f"  Running: {validator.name}...", end=" ", flush=True)

        start = time.perf_counter()
        try:
            result = validator.run(config)
        except Exception as e:
            result = ValidatorResult(module=name)
            from validators import CheckResult
            result.add(CheckResult(
                name=f"{name}_runner",
                status=Status.FAIL,
                message=f"Validator crashed: {e}",
                details=traceback.format_exc(),
            ))

        result.duration_ms = (time.perf_counter() - start) * 1000
        results.append(result)

        if result.ok:
            print(f"PASS ({result.passed}/{result.total})")
        else:
            print(f"FAIL ({result.failed} failures)")

    overall_duration = (time.perf_counter() - overall_start) * 1000

    # Print summary
    print_summary(results)

    # Generate reports
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    md_path = generate_markdown_report(results, system_info, output_dir)
    json_path = generate_json_report(results, system_info, output_dir)
    txt_path = generate_text_summary(results, system_info, output_dir)

    print("  Reports generated:")
    print(f"    Markdown: {md_path}")
    print(f"    JSON:     {json_path}")
    print(f"    Summary:  {txt_path}")
    print(f"    Duration: {overall_duration:.0f}ms")
    print("")

    total_fail = sum(r.failed for r in results)
    return 1 if total_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
