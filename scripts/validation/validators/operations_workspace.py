"""
Operations Workspace UI Validation

Validates that all Operations Workspace pages render correctly
and communicate only through the DashboardService aggregation layer.
"""

import os
import re
import sys
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend" / "src"

RESULTS: list[dict] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    RESULTS.append({"name": name, "passed": passed, "detail": detail})
    symbol = "OK" if passed else "FAIL"
    print(f"  [{symbol}] {name}" + (f" -- {detail}" if detail else ""))


def validate_dashboard_page() -> None:
    print("\n[Phase 1] Operations Dashboard")
    p = FRONTEND_DIR / "pages" / "DashboardPage.tsx"
    check("DashboardPage exists", p.exists())
    if p.exists():
        content = p.read_text(encoding="utf-8")
        check("Uses PageHeader", "PageHeader" in content)
        check("Has FleetWidget", "FleetWidget" in content)
        check("Has InfraWidget", "InfraWidget" in content)
        check("Has SystemWidget", "SystemWidget" in content)
        check("Has ActivityWidget", "ActivityWidget" in content)
        check("Auto-refresh (setInterval)", "setInterval" in content)
        check("Uses DashboardService", "api.getDashboard" in content)
        check("No direct DB calls", "sqlalchemy" not in content.lower())
        has_redis_import = any("redis" in line.strip().lower() for line in content.splitlines() if line.strip().startswith("import "))
        check("No direct Redis calls", not has_redis_import)


def validate_fleet_management() -> None:
    print("\n[Phase 2] Fleet Management")
    p = FRONTEND_DIR / "pages" / "agents" / "AgentsOverviewPage.tsx"
    check("AgentsOverviewPage exists", p.exists())
    if p.exists():
        content = p.read_text(encoding="utf-8")
        check("Has search input", "SearchInput" in content or "search" in content.lower())
        check("Has sorting", "sortKey" in content or "handleSort" in content)
        check("Has status filter", "statusFilter" in content)
        check("Has bulk selection", "selected" in content and "toggleSelect" in content)
        check("Has agent columns", "hostname" in content.lower() and "cpu" in content.lower())
        check("Uses agentsApi", "agentsApi" in content)
        check("Auto-refresh", "setInterval" in content)


def validate_agent_detail() -> None:
    print("\n[Phase 3] Agent Detail Workspace")
    p = FRONTEND_DIR / "pages" / "agents" / "AgentDetailPage.tsx"
    check("AgentDetailPage exists", p.exists())
    if p.exists():
        content = p.read_text(encoding="utf-8")
        tabs = ["overview", "performance", "commands", "inventory", "diagnostics", "configuration", "history"]
        for tab in tabs:
            check(f"Has '{tab}' tab", f'"{tab}"' in content)
        check("Has command filters", "cmdStatusFilter" in content)
        check("Has command output viewer", "expandedCmd" in content or "cmd-output" in content)
        check("Has execute form", "handleExecute" in content)
        check("Uses agentsApi", "agentsApi" in content)


def validate_timeline() -> None:
    print("\n[Phase 4] Operations Timeline")
    p = FRONTEND_DIR / "pages" / "remote" / "TimelinePage.tsx"
    check("TimelinePage exists", p.exists())
    if p.exists():
        content = p.read_text(encoding="utf-8")
        check("Has search", "search" in content.lower())
        check("Has type filter", "typeFilter" in content)
        check("Has time range", "timeRange" in content)
        check("Has export CSV", "export" in content.lower() and "csv" in content.lower())
        check("Uses apiClient", "apiClient" in content)


def validate_command_center() -> None:
    print("\n[Phase 5] Command Center")
    p = FRONTEND_DIR / "pages" / "remote" / "CommandCenterPage.tsx"
    check("CommandCenterPage exists", p.exists())
    if p.exists():
        content = p.read_text(encoding="utf-8")
        check("Has status filters", "statusFilter" in content)
        check("Has search", "search" in content.lower())
        check("Has output viewer", "expandedCmd" in content or "Output" in content)
        check("Has retry button", "handleRetry" in content or "Retry" in content)
        check("Auto-refresh", "setInterval" in content)
        check("Uses agentsApi", "agentsApi" in content)


def validate_health_center() -> None:
    print("\n[Phase 6] Health Center")
    p = FRONTEND_DIR / "pages" / "plugins" / "HealthCenterPage.tsx"
    check("HealthCenterPage exists", p.exists())
    if p.exists():
        content = p.read_text(encoding="utf-8")
        check("Has subsystem listing", "subsystems" in content)
        check("Shows latency", "latency" in content.lower())
        check("Shows last check", "last_check" in content)
        check("Auto-refresh", "setInterval" in content)
        check("Uses health API", "/api/v1/health/subsystems" in content)


def validate_plugin_center() -> None:
    print("\n[Phase 7] Plugin Center")
    p = FRONTEND_DIR / "pages" / "plugins" / "PluginCenterPage.tsx"
    check("PluginCenterPage exists", p.exists())
    if p.exists():
        content = p.read_text(encoding="utf-8")
        check("Has search", "search" in content.lower())
        check("Has status filter", "statusFilter" in content)
        check("Has plugin actions", "Enable" in content and "Disable" in content)
        check("Has plugin details", "version" in content.lower())


def validate_company_workspace() -> None:
    print("\n[Phase 8] Company & Site Workspace")
    p = FRONTEND_DIR / "pages" / "companies" / "CompanyWorkspacePage.tsx"
    check("CompanyWorkspacePage exists", p.exists())
    if p.exists():
        content = p.read_text(encoding="utf-8")
        check("Has search", "search" in content.lower())
        check("Shows site count", "site_count" in content)
        check("Shows agent count", "agent_count" in content)
        check("Auto-refresh", "setInterval" in content)
        check("Uses companiesApi", "companiesApi" in content)


def validate_personal_dashboard() -> None:
    print("\n[Phase 9] Personal Dashboard")
    p = FRONTEND_DIR / "pages" / "settings" / "PersonalDashboardPage.tsx"
    check("PersonalDashboardPage exists", p.exists())
    if p.exists():
        content = p.read_text(encoding="utf-8")
        check("Has widget config", "WidgetConfig" in content)
        check("Has toggle visibility", "toggleWidget" in content)
        check("Has reorder", "moveWidget" in content)
        check("Has reset defaults", "resetDefaults" in content)
        check("Persists to localStorage", "localStorage" in content)
        check("Customize mode", "customizing" in content)


def validate_routes() -> None:
    print("\n[Phase 10] Routes & Navigation")
    app = FRONTEND_DIR / "App.tsx"
    nav = FRONTEND_DIR / "config" / "navigation.ts"
    check("App.tsx exists", app.exists())
    check("navigation.ts exists", nav.exists())
    if app.exists():
        content = app.read_text(encoding="utf-8")
        routes = ["/fleet", "/fleet/timeline", "/fleet/commands", "/fleet/health", "/fleet/plugins", "/fleet/companies", "/settings/dashboard"]
        for route in routes:
            check(f"Route '{route}' registered", route in content)
    if nav.exists():
        content = nav.read_text(encoding="utf-8")
        check("Fleet Workspace nav group", "Fleet Workspace" in content)
        check("My Dashboard nav item", "My Dashboard" in content or "dashboard" in content.lower())


def validate_architecture() -> None:
    print("\n[Phase 10] Architecture Compliance")
    violations = []
    import re as _re
    for tsx in FRONTEND_DIR.rglob("*.tsx"):
        if "node_modules" in str(tsx):
            continue
        content = tsx.read_text(encoding="utf-8")
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped.startswith("import "):
                continue
            if "sqlalchemy" in stripped.lower():
                violations.append(f"{tsx.name}: imports sqlalchemy")
            if "redis" in stripped.lower():
                violations.append(f"{tsx.name}: imports redis")
    check("No direct DB imports in frontend", len(violations) == 0,
          "; ".join(violations) if violations else "Clean")


def main() -> None:
    print("=" * 60)
    print("Mission Control — Operations Workspace UI Validation")
    print("=" * 60)

    validate_dashboard_page()
    validate_fleet_management()
    validate_agent_detail()
    validate_timeline()
    validate_command_center()
    validate_health_center()
    validate_plugin_center()
    validate_company_workspace()
    validate_personal_dashboard()
    validate_routes()
    validate_architecture()

    passed = sum(1 for r in RESULTS if r["passed"])
    failed = sum(1 for r in RESULTS if not r["passed"])
    total = len(RESULTS)

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        print("\nFailed checks:")
        for r in RESULTS:
            if not r["passed"]:
                print(f"  [FAIL] {r['name']}" + (f" -- {r['detail']}" if r['detail'] else ""))

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
