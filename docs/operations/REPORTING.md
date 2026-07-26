# Reporting Guide

**Purpose:** Available reports, data export, and operational reporting  
**Related:** [DASHBOARD.md](./DASHBOARD.md), [AUTOMATION.md](./AUTOMATION.md), [AGENTS.md](./AGENTS.md), [INVENTORY.md](./INVENTORY.md)

---

## Reporting Overview

Mission Control provides built-in reports for operational visibility and compliance. Reports can be generated on-demand or scheduled for automatic delivery.

---

## Available Reports

### Dashboard Summary Report

Provides a snapshot of the current operational state.

**API Endpoint:** `GET /api/v1/reports/dashboard-summary`

**Contents:**

| Section | Data Included |
|---------|--------------|
| Application Health | Total, healthy, degraded, critical counts |
| Health Score | Current score, trend, component breakdown |
| Agent Status | Total agents, state distribution, stale heartbeats |
| Automation Status | Active playbooks, recent executions, success rate |
| AI Insights | Active recommendations, anomalies, correlated incidents |
| Infrastructure Status | Hyper-V, Proxmox, Zabbix, Veeam summaries |
| Alert Summary | Active alerts by severity, resolution rates |

**Use Cases:**
- Daily operational briefing
- Shift handover documentation
- Executive status summary

### Automation Report

Detailed report on automation activity over a specified period.

**API Endpoint:** `GET /api/v1/reports/automation`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `startDate` | ISO 8601 | Report period start |
| `endDate` | ISO 8601 | Report period end |
| `playbookId` | string | Filter by specific playbook |
| `format` | string | `json`, `csv`, `pdf` |

**Contents:**

| Section | Data Included |
|---------|--------------|
| Execution Summary | Total executions, success rate, average duration |
| Execution Details | Per-execution breakdown with step results |
| Approval Summary | Approvals granted, denied, expired, average wait time |
| Failure Analysis | Failed executions grouped by playbook, step, and error type |
| Audit Trail | Complete audit log for the period |
| Trends | Execution volume and success rate over time |

**Use Cases:**
- Weekly automation review
- Compliance audit documentation
- Performance trending

### Agent Health Report

Comprehensive report on agent health and availability.

**API Endpoint:** `GET /api/v1/reports/agent-health`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `startDate` | ISO 8601 | Report period start |
| `endDate` | ISO 8601 | Report period end |
| `agentId` | string | Filter by specific agent |
| `format` | string | `json`, `csv`, `pdf` |

**Contents:**

| Section | Data Included |
|---------|--------------|
| Availability Summary | Uptime percentage per agent, aggregate availability |
| State Transitions | History of state changes per agent |
| Heartbeat Analysis | Missed heartbeats, latency trends |
| Health Score Trends | Health score changes over time |
| Resource Usage | CPU, memory, disk trends per agent |
| Issue Log | All warnings, errors, and failures per agent |

**Use Cases:**
- Monthly agent reliability review
- Capacity planning
- Agent deployment validation

### Inventory Report

Snapshot or historical report of infrastructure inventory.

**API Endpoint:** `GET /api/v1/reports/inventory`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | `system`, `software`, `services`, `network`, or `all` |
| `agentId` | string | Filter by specific agent |
| `format` | string | `json`, `csv`, `pdf` |

**Contents:**

| Section | Data Included |
|---------|--------------|
| System Overview | Hardware and OS inventory across all hosts |
| Software Inventory | Installed software with versions |
| Service Inventory | Running services with status |
| Network Inventory | Network interfaces and configuration |
| Changes | Inventory changes since last report |

**Use Cases:**
- Software license auditing
- Hardware asset tracking
- Configuration compliance verification
- Change management documentation

### Audit Trail Report

Complete record of all system and operator actions.

**API Endpoint:** `GET /api/v1/reports/audit-trail`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `startDate` | ISO 8601 | Report period start |
| `endDate` | ISO 8601 | Report period end |
| `actor` | string | Filter by operator or system |
| `eventType` | string | Filter by event type |
| `resourceType` | string | Filter by resource type |
| `format` | string | `json`, `csv`, `pdf` |

**Contents:**

| Section | Data Included |
|---------|--------------|
| Action Log | Chronological list of all actions |
| Operator Activity | Actions grouped by operator |
| System Activity | Automated actions and system events |
| Change Summary | Summary of all configuration changes |
| Security Events | Authentication, authorization, and security-related events |

**Use Cases:**
- Compliance auditing
- Security investigations
- Change tracking
- Accountability documentation

---

## Exporting Data

### Export Formats

| Format | Use Case | Features |
|--------|----------|----------|
| `json` | API integration, data processing | Full data fidelity, machine-readable |
| `csv` | Spreadsheet analysis, data import | Tabular data, human-readable |
| `pdf` | Documentation, presentations, archival | Formatted, printable, includes charts |

### Exporting via API

All reports support format selection via the `format` query parameter:

```bash
# JSON export
curl -H "Authorization: Bearer <token>" \
  "https://missioncontrol.example.com/api/v1/reports/automation?startDate=2026-07-01&endDate=2026-07-26&format=json"

# CSV export
curl -H "Authorization: Bearer <token>" \
  "https://missioncontrol.example.com/api/v1/reports/automation?startDate=2026-07-01&endDate=2026-07-26&format=csv"

# PDF export
curl -H "Authorization: Bearer <token>" \
  "https://missioncontrol.example.com/api/v1/reports/automation?startDate=2026-07-01&endDate=2026-07-26&format=pdf"
```

### Exporting via Dashboard

1. Navigate to the Reports section.
2. Select the desired report type.
3. Configure the report parameters (date range, filters).
4. Click "Generate Report".
5. Wait for the report to be generated.
6. Click "Export" and select the desired format.
7. The file will be downloaded to your local machine.

### Bulk Export

Export multiple reports in a single operation:

**API Endpoint:** `POST /api/v1/reports/export`

```json
{
  "reports": [
    { "type": "dashboard-summary", "format": "pdf" },
    { "type": "automation", "format": "csv", "startDate": "2026-07-01", "endDate": "2026-07-26" },
    { "type": "agent-health", "format": "pdf", "startDate": "2026-07-01", "endDate": "2026-07-26" }
  ]
}
```

---

## Scheduled Reports

Reports can be scheduled for automatic generation and delivery.

**API Endpoint:** `POST /api/v1/reports/schedules`

### Schedule Configuration

```json
{
  "name": "Weekly Automation Report",
  "reportType": "automation",
  "schedule": {
    "type": "cron",
    "expression": "0 8 * * 1"
  },
  "parameters": {
    "format": "pdf"
  },
  "recipients": ["ops-team@example.com"],
  "enabled": true
}
```

### Default Scheduled Reports

| Report | Schedule | Recipients | Format |
|--------|----------|-----------|--------|
| Daily Dashboard Summary | Daily 07:00 | On-call operator | PDF |
| Weekly Automation Report | Monday 08:00 | Operations team | PDF |
| Weekly Agent Health | Monday 08:00 | Operations team | PDF |
| Monthly Inventory Report | 1st of month 09:00 | Infrastructure team | PDF |
| Monthly Audit Trail | 1st of month 09:00 | Compliance team | PDF |

---

## Report Retention

| Report Type | Retention Period | Notes |
|-------------|-----------------|-------|
| Generated reports | 90 days | Auto-cleanup of old generated files |
| Scheduled report outputs | 30 days per instance | Latest always available |
| Raw data for reports | Indefinite | Source data retained indefinitely |
| Export history | 30 days | Records of what was exported and when |

---

## Custom Report Queries

For advanced reporting needs, use the raw data APIs with custom filtering.

### Agent Data Query

```
GET /api/v1/agents?state=offline&lastHeartbeat=before:2026-07-26T00:00:00Z
```

### Alert Data Query

```
GET /api/v1/alerts/history?severity=critical&startDate=2026-07-01&endDate=2026-07-26
```

### Automation Data Query

```
GET /api/v1/automations/executions?status=failed&startDate=2026-07-01&endDate=2026-07-26
```

### Inventory Data Query

```
GET /api/v1/inventory/search?q=nginx&type=software
```
