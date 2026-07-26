# Dashboard Operations Guide

**Purpose:** How to read and interpret the Mission Control dashboard  
**API Endpoint:** `GET /api/v1/dashboard`  
**Related:** [OPERATIONS_MANUAL.md](./OPERATIONS_MANUAL.md), [ALERTS.md](./ALERTS.md), [AGENTS.md](./AGENTS.md)

---

## Dashboard Overview

The Mission Control dashboard is the primary operational view. It aggregates data from all domain services into a single response, providing a real-time snapshot of your entire infrastructure.

**Endpoint:** `GET /api/v1/dashboard`  
**Method:** `GET`  
**Authentication:** JWT Bearer token required  
**Response:** JSON object containing all dashboard sections

The dashboard returns the following major sections:

1. Application Summary
2. Health Status
3. Agent Status
4. Automation Summary
5. AI Overview
6. Infrastructure Overview (Hyper-V, Proxmox, Zabbix, Veeam)

---

## Application Summary

The application summary provides a high-level count of all managed resources.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `totalApplications` | integer | Total number of monitored applications |
| `healthyCount` | integer | Applications in healthy state |
| `degradedCount` | integer | Applications experiencing degradation |
| `criticalCount` | integer | Applications in critical state |
| `unknownCount` | integer | Applications with unknown status |

### Interpreting the Data

- **All healthy:** Normal operations. No action required.
- **Degraded > 0:** Investigate affected applications. Cross-reference with [ALERTS.md](./ALERTS.md) for active alerts.
- **Critical > 0:** Immediate investigation required. Follow [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) procedures.
- **Unknown > 0:** Check agent connectivity. Unknown status typically indicates the monitoring agent is offline or unable to reach the application endpoint.

---

## Health Status

The health status section provides an aggregate health score across the entire infrastructure.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `overallScore` | integer (0-100) | Aggregate health score |
| `trend` | string | `improving`, `stable`, or `degrading` |
| `lastCalculated` | ISO 8601 timestamp | When the score was last computed |
| `components` | array | Per-component health breakdown |

### Components Array

Each entry in the `components` array contains:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Component name (e.g., `hyper-v`, `proxmox`, `zabbix`, `veeam`) |
| `score` | integer (0-100) | Component health score |
| `status` | string | `healthy`, `degraded`, `critical`, or `unknown` |
| `issues` | array | List of active issues affecting this component |

### Interpreting Health Scores

| Score Range | Status | Action |
|-------------|--------|--------|
| 80-100 | Healthy | Monitor, no immediate action |
| 60-79 | Degraded | Investigate, review alerts, check AI recommendations |
| 0-59 | Critical | Immediate action, follow [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) |
| N/A | Unknown | Check agent connectivity and data collection |

### Trend Analysis

- **`improving`:** Health score is increasing. Continue monitoring.
- **`stable`:** No significant change. Normal operations.
- **`degrading`:** Health score is declining. Investigate root cause before it becomes critical.

---

## Agent Status

The agent status section provides a summary of all monitoring agents across the infrastructure.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `totalAgents` | integer | Total registered agents |
| `byState` | object | Count of agents in each state |
| `lastHeartbeat` | ISO 8601 timestamp | Most recent heartbeat received |
| `staleHeartbeats` | integer | Number of agents with stale heartbeats |

### Agent States

Agents transition through 9 distinct states:

| State | Description | Typical Action |
|-------|-------------|----------------|
| `online` | Agent is active and reporting normally | None required |
| `offline` | Agent is not communicating | Check agent process, network connectivity |
| `warning` | Agent is reporting but with warnings | Review agent logs, check resource utilization |
| `healthy` | Agent is active and all checks passing | None required |
| `unhealthy` | Agent is active but checks are failing | Investigate failing checks, review agent logs |
| `updating` | Agent is currently being updated | Wait for update to complete, verify post-update |
| `pending` | Agent is registered but not yet activated | Activate agent or investigate registration issue |
| `executing` | Agent is running a command or task | Wait for completion, monitor for errors |
| `disabled` | Agent has been manually disabled | Verify intentional disable, re-enable if needed |

### Interpreting Agent Status

- **All agents `online` or `healthy`:** Normal operations.
- **Any agents `offline`:** Those hosts are not being monitored. Check [AGENTS.md](./AGENTS.md) for reconnection procedures.
- **`staleHeartbeats` > 0:** Agents are not reporting within the expected 30-second heartbeat interval. This may indicate network issues or agent performance problems.
- **Agents in `updating` state:** Expected during scheduled updates. Verify update completes successfully.

---

## Automation Summary

The automation summary provides an overview of all playbook executions.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `totalPlaybooks` | integer | Total number of defined playbooks |
| `activePlaybooks` | integer | Playbooks currently enabled |
| `scheduledPlaybooks` | integer | Playbooks with active schedules |
| `recentExecutions` | integer | Executions in the last 24 hours |
| `successRate` | float | Percentage of successful executions |
| `pendingApprovals` | integer | Executions awaiting approval |
| `failedExecutions` | integer | Failed executions in the last 24 hours |

### Interpreting Automation Data

- **`failedExecutions` > 0:** Review failed executions immediately. See [AUTOMATION.md](./AUTOMATION.md) for investigation procedures.
- **`pendingApprovals` > 0:** Operator action required to approve pending playbook runs.
- **`successRate` < 95%:** Investigate automation failures. May indicate infrastructure issues or playbook errors.
- **`activePlaybooks` significantly lower than `totalPlaybooks`:** Review whether disabled playbooks should be re-enabled.

---

## AI Overview

The AI overview section summarizes AI-generated insights and recommendations.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `activeRecommendations` | integer | Number of actionable AI recommendations |
| `correlatedIncidents` | integer | Incidents currently being correlated |
| `healthScore` | integer (0-100) | AI-computed infrastructure health score |
| `anomaliesDetected` | integer | Number of detected anomalies |
| `topRecommendations` | array | Top 5 prioritized recommendations |

### Top Recommendations Array

Each recommendation contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique recommendation identifier |
| `priority` | string | `critical`, `high`, `medium`, `low` |
| `category` | string | Category of the recommendation |
| `summary` | string | Brief description |
| `affectedComponents` | array | Components impacted |
| `estimatedImpact` | string | Expected impact if addressed |
| `suggestedAction` | string | Recommended action to take |

### Interpreting AI Data

- **`anomaliesDetected` > 0:** Review anomalies. The AI engine compares current patterns against historical baselines.
- **`correlatedIncidents` > 0:** Multiple alerts may be related to a single root cause. The AI is analyzing these relationships.
- **`activeRecommendations` with `critical` or `high` priority:** Address these first. Follow the `suggestedAction` field.
- **AI health score diverging from dashboard health score:** Investigate why the AI model disagrees with rule-based health checks. This may indicate emerging issues not yet captured by static rules.

---

## Infrastructure Overview

The infrastructure overview provides detailed status for each integrated platform.

### Hyper-V

| Field | Type | Description |
|-------|------|-------------|
| `hosts` | integer | Total Hyper-V hosts |
| `vms` | integer | Total virtual machines |
| `runningVms` | integer | VMs currently running |
| `stoppedVms` | integer | VMs in stopped state |
| `resourceUtilization` | object | CPU, memory, storage utilization |
| `clusterStatus` | string | Cluster health status |

### Proxmox

| Field | Type | Description |
|-------|------|-------------|
| `nodes` | integer | Total Proxmox nodes |
| `vms` | integer | Total virtual machines |
| `containers` | integer | Total containers (LXC) |
| `runningCount` | integer | Running VMs and containers |
| `storagePools` | array | Storage pool status |
| `clusterStatus` | string | Cluster health status |

### Zabbix

| Field | Type | Description |
|-------|------|-------------|
| `monitoredHosts` | integer | Total monitored hosts |
| `activeTriggers` | integer | Currently active triggers |
| `problems` | integer | Open problems |
| `dataCollectionRate` | float | Metrics collected per second |
| `proxyStatus` | string | Zabbix proxy connectivity status |

### Veeam

| Field | Type | Description |
|-------|------|-------------|
| `backupJobs` | integer | Total backup jobs |
| `successfulBackups` | integer | Successful backups in last 24 hours |
| `failedBackups` | integer | Failed backups in last 24 hours |
| `lastBackupTime` | ISO 8601 timestamp | Most recent backup completion |
| `storageUsed` | string | Total backup storage consumed |
| `retentionPolicy` | string | Current retention policy summary |

---

## Dashboard Widgets

The dashboard UI presents data in the following widget layout:

### Top Row (Summary Cards)

| Widget | Description |
|--------|-------------|
| Application Count | Total applications with health breakdown |
| Health Score | Overall infrastructure health (0-100) with trend indicator |
| Active Alerts | Count of unresolved alerts by severity |
| Automation Status | Active playbooks and recent execution success rate |

### Middle Row (Detailed Views)

| Widget | Description |
|--------|-------------|
| Agent Grid | Visual grid of all agents with color-coded state indicators |
| AI Insights | Top recommendations with priority badges |
| Infrastructure Map | Visual representation of Hyper-V, Proxmox, Zabbix, Veeam status |
| Event Timeline | Recent events from the 34-type event bus |

### Bottom Row (Operational)

| Widget | Description |
|--------|-------------|
| Recent Activity | Last 50 operational actions with timestamps |
| Pending Approvals | Queue of playbook executions awaiting operator approval |
| System Health | API response times, rate limit status, database health |

---

## Refresh Behavior

The dashboard supports both automatic and manual refresh:

### Automatic Refresh

| Trigger | Behavior |
|---------|----------|
| WebSocket connection | Real-time updates pushed to the UI when data changes |
| Polling fallback | If WebSocket is unavailable, the UI polls `GET /api/v1/dashboard` every 30 seconds |
| Agent heartbeat cycle | Agent data is refreshed every 30 seconds as heartbeats arrive |
| Event bus | Dashboard updates are triggered by events on the 34-type event bus |

### Manual Refresh

- **UI Refresh Button:** Click the refresh icon in the dashboard header to force an immediate data fetch.
- **API Call:** Make a direct `GET /api/v1/dashboard` request to retrieve the current snapshot.

### Caching Behavior

- Dashboard responses are cached for up to 5 seconds to prevent thundering herd from concurrent clients.
- Cache is invalidated immediately when a significant event occurs (e.g., agent state change, alert triggered).
- Infrastructure data (Hyper-V, Proxmox, Zabbix, Veeam) may have slightly different refresh intervals depending on the domain service polling frequency.

---

## Common Dashboard Scenarios

### Scenario: All Green

**Indicator:** All summary cards show normal values, health score > 80, no active alerts.  
**Action:** Routine monitoring. Proceed with daily checklist.

### Scenario: Agent Offline

**Indicator:** Agent status shows one or more agents in `offline` state.  
**Action:** See [AGENTS.md](./AGENTS.md) for agent reconnection procedures. Check network connectivity to the affected host.

### Scenario: Health Score Dropping

**Indicator:** Health score is below 80 and trend shows `degrading`.  
**Action:** Review component breakdown for the lowest-scoring component. Check AI recommendations for correlated issues. Follow [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) if score drops below 60.

### Scenario: Failed Automation

**Indicator:** `failedExecutions` > 0 in automation summary.  
**Action:** See [AUTOMATION.md](./AUTOMATION.md) for investigating failed playbook executions. Check agent status for agents involved in the failed execution.

### Scenario: Backup Failures

**Indicator:** Veeam `failedBackups` > 0 or `lastBackupTime` is stale.  
**Action:** Review Veeam backup job details in the infrastructure overview. Follow [MAINTENANCE.md](./MAINTENANCE.md) backup verification procedures.
