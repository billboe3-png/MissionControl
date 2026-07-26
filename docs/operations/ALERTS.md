# Alert Management Guide

**Purpose:** Managing, responding to, and resolving alerts  
**Related:** [DASHBOARD.md](./DASHBOARD.md), [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md), [AGENTS.md](./AGENTS.md), [AUTOMATION.md](./AUTOMATION.md)

---

## Alert Overview

Alerts are generated when Mission Control detects conditions that require operator attention. The AI engine correlates related alerts to reduce noise and identify root causes.

---

## Alert Types

| Type | Source | Description |
|------|--------|-------------|
| `agent_offline` | Agent system | Agent heartbeat timeout detected |
| `agent_unhealthy` | Agent system | Agent health check failures |
| `agent_warning` | Agent system | Agent reporting warning conditions |
| `service_down` | Agent / Zabbix | Monitored service is not running or unreachable |
| `resource_critical` | Agent / Zabbix | Resource utilization exceeds critical threshold |
| `resource_warning` | Agent / Zabbix | Resource utilization exceeds warning threshold |
| `backup_failed` | Veeam | Backup job failed or did not complete |
| `backup_warning` | Veeam | Backup job completed with warnings |
| `certificate_expiring` | Agent / Plugin | TLS certificate approaching expiry |
| `certificate_expired` | Agent / Plugin | TLS certificate has expired |
| `disk_critical` | Agent / Zabbix | Disk space below critical threshold |
| `disk_warning` | Agent / Zabbix | Disk space below warning threshold |
| `security` | Agent / Plugin | Security-related event detected |
| `automation_failed` | Automation | Playbook execution failed |
| `automation_requires_approval` | Automation | Playbook requires operator approval |
| `plugin_error` | Plugin system | Plugin experiencing errors |
| `plugin_health_degraded` | Plugin system | Plugin health below threshold |
| `hyper_v_alert` | Hyper-V | Hyper-V platform alert |
| `proxmox_alert` | Proxmox | Proxmox platform alert |
| `zabbix_problem` | Zabbix | Zabbix trigger activated |
| `network_issue` | Agent / Zabbix | Network connectivity problem detected |
| `dns_issue` | Agent | DNS resolution failure |
| `authentication_failure` | API / Agent | Authentication failure detected |
| `rate_limit_exceeded` | API | Rate limit threshold breached |
| `database_health` | Platform | Database health check failure |
| `api_health` | Platform | API health check failure |
| `event_bus_lag` | Platform | Event bus processing delay |
| `ai_anomaly` | AI Engine | AI-detected anomaly |
| `ai_recommendation_critical` | AI Engine | Critical AI recommendation generated |
| `ai_recommendation_high` | AI Engine | High-priority AI recommendation |
| `maintenance_reminder` | Platform | Scheduled maintenance approaching |
| `disaster_recovery` | Platform | DR-related alert |
| `host_hardware` | Agent / Hyper-V / Proxmox | Hardware issue detected |
| `license_expiring` | Platform | License approaching expiry |

---

## Alert Severity

Every alert is assigned a severity level that determines response priority.

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| `critical` | Immediate action required. System or service at risk. | 15 minutes | Service down, disk full, security breach |
| `high` | Urgent attention needed. Degraded operations. | 1 hour | Agent offline, backup failed, resource critical |
| `medium` | Should be addressed soon. May become high severity. | 4 hours | Resource warning, certificate expiring in 7 days |
| `low` | Informational or minor. Address during normal operations. | 24 hours | Maintenance reminder, low-priority recommendation |
| `info` | Informational only. No action typically required. | Best effort | Agent updated, automation completed successfully |

---

## Responding to Alerts

### Step 1: Acknowledge the Alert

When you begin working on an alert, acknowledge it to inform other operators.

**API Endpoint:** `POST /api/v1/alerts/{alertId}/acknowledge`

**Via Dashboard:**
1. Navigate to the active alerts panel.
2. Click on the alert to open the detail view.
3. Click "Acknowledge" to claim the alert.

### Step 2: Assess the Alert

Review the alert details:

| Field | What to Look For |
|-------|-----------------|
| `severity` | Determines response urgency |
| `type` | Determines the investigation approach |
| `source` | Which system generated the alert |
| `affectedComponents` | What infrastructure is impacted |
| `timestamp` | When the condition was first detected |
| `correlatedAlerts` | Related alerts grouped by AI correlation |
| `aiRecommendations` | AI-generated suggestions for resolution |

### Step 3: Investigate

Follow the investigation path based on alert type:

| Alert Type | Investigation Path |
|------------|-------------------|
| Agent alerts | [AGENTS.md](./AGENTS.md) — Check agent state, logs, connectivity |
| Resource alerts | Check agent resource usage, investigate workload spikes |
| Backup alerts | Review Veeam job details, check storage, verify backup targets |
| Security alerts | Follow security incident procedures in [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) |
| Automation alerts | [AUTOMATION.md](./AUTOMATION.md) — Review execution logs |
| Plugin alerts | [PLUGINS.md](./PLUGINS.md) — Check plugin health and logs |
| Infrastructure alerts | Check Hyper-V/Proxmox/Zabbix dashboards for details |

### Step 4: Take Action

Based on your investigation, take the appropriate remediation action. This may involve:
- Restarting a service
- Freeing disk space
- Reconnecting an agent
- Running a remediation playbook
- Escalating to another team

### Step 5: Resolve the Alert

Once the underlying condition is addressed:

**API Endpoint:** `POST /api/v1/alerts/{alertId}/resolve`

**Via Dashboard:**
1. Click "Resolve" on the alert detail view.
2. Add a resolution note describing what was done.
3. The alert moves to the resolved state.

---

## Alert Severity Response Procedures

### Critical Alert Response

**Response Time:** 15 minutes

1. **Immediate acknowledgment** — Acknowledge the alert within 15 minutes.
2. **Assess impact** — Determine which systems and users are affected.
3. **Begin remediation** — Take immediate action to restore service.
4. **Escalate if needed** — If unable to resolve within 30 minutes, escalate per [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md).
5. **Document actions** — Record all actions taken in the alert notes.
6. **Verify resolution** — Confirm the alert condition is cleared.
7. **Post-incident** — Complete post-incident review per [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md).

### High Alert Response

**Response Time:** 1 hour

1. **Acknowledge** — Acknowledge the alert within 1 hour.
2. **Investigate** — Review alert details and affected components.
3. **Remediate** — Take corrective action.
4. **Verify** — Confirm the condition is resolved.
5. **Document** — Record the issue and resolution.

### Medium Alert Response

**Response Time:** 4 hours

1. **Acknowledge** — Acknowledge during working hours.
2. **Schedule** — If immediate resolution is not possible, schedule the work.
3. **Monitor** — Ensure the condition does not escalate.
4. **Resolve** — Complete the remediation.

### Low Alert Response

**Response Time:** 24 hours

1. **Review** — Review during daily operations check.
2. **Plan** — Include in upcoming work planning.
3. **Resolve** — Address when appropriate.

---

## Resolving Alerts

An alert can be resolved only when the underlying condition has been corrected.

### Resolution Requirements

| Field | Required | Description |
|-------|----------|-------------|
| `alertId` | Yes | The alert to resolve |
| `resolutionNote` | Yes | Description of what was done to resolve the issue |
| `rootCause` | Recommended | Root cause of the alert condition |
| `preventiveAction` | Optional | Actions taken to prevent recurrence |

### Auto-Resolution

Some alerts are automatically resolved when the condition clears:
- Agent returns to `online` or `healthy` state
- Resource utilization drops below threshold
- Certificate is renewed
- Service comes back online

Auto-resolved alerts retain their full history and can be reviewed in the alert history.

---

## Alert History

All alerts, including resolved ones, are retained for historical analysis.

**API Endpoint:** `GET /api/v1/alerts/history`

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by alert type |
| `severity` | string | Filter by severity level |
| `source` | string | Filter by alert source |
| `startDate` | ISO 8601 | Start of date range |
| `endDate` | ISO 8601 | End of date range |
| `status` | string | `active`, `acknowledged`, `resolved` |
| `page` | integer | Pagination page number |
| `pageSize` | integer | Results per page |

### Alert History Record

Each record contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Alert identifier |
| `type` | string | Alert type |
| `severity` | string | Severity level |
| `status` | string | Current status |
| `title` | string | Alert title |
| `description` | string | Detailed description |
| `source` | string | Source system |
| `affectedComponents` | array | Impacted components |
| `createdAt` | ISO 8601 | When the alert was generated |
| `acknowledgedAt` | ISO 8601 | When acknowledged |
| `acknowledgedBy` | string | Operator who acknowledged |
| `resolvedAt` | ISO 8601 | When resolved |
| `resolvedBy` | string | Operator who resolved |
| `resolutionNote` | string | Resolution description |
| `correlatedAlerts` | array | Related alert IDs |
| `aiCorrelationId` | string | AI correlation group identifier |

---

## AI Alert Correlation

The AI engine analyzes incoming alerts to identify related incidents and reduce alert noise.

### How Correlation Works

1. **Pattern matching:** The AI compares current alerts against historical patterns.
2. **Causal analysis:** The AI identifies which alerts are symptoms of the same root cause.
3. **Grouping:** Related alerts are grouped under a single correlation ID.
4. **Prioritization:** The AI identifies the root-cause alert and assigns it the highest priority.

### Viewing Correlated Alerts

**Via Dashboard:**
1. Navigate to the active alerts panel.
2. Correlated alerts are displayed with a "Correlated" badge and a shared correlation ID.
3. Click the correlation ID to view all related alerts.

**Via API:**
```
GET /api/v1/alerts/correlations/{correlationId}
```

### Using AI Correlation

- **Focus on root cause:** When multiple alerts are correlated, address the root-cause alert first.
- **Resolve together:** Resolving the root cause typically clears all correlated symptoms.
- **Review correlation accuracy:** If the AI incorrectly correlates unrelated alerts, provide feedback to improve the model.

---

## Alert Notifications

Mission Control can send notifications through multiple channels when alerts are generated.

### Notification Channels

| Channel | Configuration | Use Case |
|---------|--------------|----------|
| Email | SMTP settings | General notifications |
| Webhook | URL and payload template | Integration with external systems |
| SMS | SMS gateway configuration | Critical alerts requiring immediate attention |
| Slack/Teams | Bot configuration | Team channel notifications |
| PagerDuty | API key integration | On-call escalation |

### Notification Rules

Configure which alerts trigger which notifications:

| Rule | Alert Types | Severity | Channel |
|------|------------|----------|---------|
| Critical on-call | All types | `critical` | SMS + PagerDuty |
| High priority | All types | `high` | Email + Slack |
| Backup failures | `backup_failed`, `backup_warning` | `high`, `medium` | Email |
| Security | `security`, `authentication_failure` | `critical`, `high` | SMS + Email |
| Info | All types | `info` | None (dashboard only) |

---

## Common Alert Scenarios

### Scenario: Agent Goes Offline

**Alert:** `agent_offline` severity `high`  
**Steps:**
1. Acknowledge the alert.
2. Check if the host is reachable (ping, SSH).
3. Verify the agent process status on the host.
4. If the host is down, escalate per [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md).
5. If the agent process stopped, restart it.
6. Verify the agent returns to `online` state.
7. Resolve the alert.

### Scenario: Disk Space Critical

**Alert:** `disk_critical` severity `critical`  
**Steps:**
1. Acknowledge the alert within 15 minutes.
2. Connect to the affected host via [REMOTE_OPERATIONS.md](./REMOTE_OPERATIONS.md).
3. Identify large files or directories consuming space.
4. Clean up temporary files, old logs, or unused data.
5. If cleanup is insufficient, consider expanding the disk.
6. Verify disk usage drops above the critical threshold.
7. Resolve the alert and document the root cause.

### Scenario: Multiple Correlated Alerts

**Alerts:** Multiple `service_down`, `resource_critical`, and `agent_warning` alerts correlated by AI  
**Steps:**
1. View the correlation group to identify the root cause.
2. Address the root-cause alert first (likely a host-level issue).
3. As the root cause is resolved, verify correlated symptom alerts clear.
4. Resolve all alerts in the correlation group.
