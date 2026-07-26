# Automation Operations Guide

**Purpose:** Overseeing automated operations, executions, and approvals  
**Related:** [PLAYBOOKS.md](./PLAYBOOKS.md), [ALERTS.md](./ALERTS.md), [AGENTS.md](./AGENTS.md), [DASHBOARD.md](./DASHBOARD.md)

---

## Automation Overview

Mission Control automation is built around playbooks — predefined sequences of steps that can be executed manually, on a schedule, or in response to alerts. Playbooks support approval workflows and maintain a full audit trail of every execution.

---

## Playbook Types

| Type | Description | Use Case |
|------|-------------|----------|
| `manual` | Triggered explicitly by an operator | On-demand remediation, ad-hoc tasks |
| `scheduled` | Runs on a defined schedule (cron or interval) | Routine maintenance, compliance checks |
| `alert_triggered` | Runs automatically when a specific alert fires | Automated incident response |
| `api_triggered` | Runs via API call from external systems | Integration with CI/CD, ticketing systems |
| `event_triggered` | Runs in response to specific event bus events | Reactive automation |

---

## Execution Status

Every playbook execution progresses through a defined status lifecycle.

### Status Values

| Status | Description | Next Possible Statuses |
|--------|-------------|----------------------|
| `pending` | Execution queued but not yet started | `executing`, `cancelled` |
| `awaiting_approval` | Execution paused, waiting for operator approval | `executing`, `rejected` |
| `executing` | Steps are being processed | `completed`, `failed`, `paused` |
| `paused` | Execution paused (manual or conditional) | `executing`, `cancelled` |
| `completed` | All steps finished successfully | Terminal state |
| `failed` | Execution failed due to error | Terminal state (can be retried) |
| `cancelled` | Execution was cancelled by operator or policy | Terminal state |
| `rejected` | Approval was denied | Terminal state |

### Status Transitions

```
pending ──→ awaiting_approval ──→ executing ──→ completed
   │               │                │
   │               │                ├──→ failed
   │               │                ├──→ paused ──→ executing
   │               │                │           └──→ cancelled
   │               │                │
   │               ├──→ rejected   │
   │               │               │
   └──→ cancelled  └──→ cancelled  └──→ cancelled
```

---

## Approval Workflows

Some playbooks require operator approval before execution. This ensures that high-impact or irreversible actions are reviewed.

### When Approval Is Required

| Condition | Reason |
|-----------|--------|
| Playbook has `requiresApproval: true` | Explicit approval gate in playbook definition |
| Execution involves critical systems | Policy-based approval for production systems |
| Execution modifies security configuration | Security review required |
| Execution exceeds resource thresholds | Resource impact review |

### Approving an Execution

**API Endpoint:** `POST /api/v1/automations/executions/{executionId}/approve`

**Via Dashboard:**
1. Navigate to the Automation section.
2. Open the "Pending Approvals" tab.
3. Review the execution details:
   - Playbook name and description
   - Target hosts
   - Steps to be executed
   - Expected impact
4. Click "Approve" or "Reject" with a reason.

### Approval Details

When reviewing an approval request, the following information is available:

| Field | Description |
|-------|-------------|
| `executionId` | Unique execution identifier |
| `playbookName` | Name of the playbook |
| `triggerType` | What triggered the execution |
| `targetHosts` | Hosts that will be affected |
| `steps` | Ordered list of steps to execute |
| `estimatedDuration` | Expected execution time |
| `riskAssessment` | AI-generated risk assessment |
| `requestedBy` | Who or what triggered the execution |
| `requestedAt` | When the execution was requested |
| `expiresAt` | When the approval request expires |

### Approval Timeout

Approval requests expire after a configurable period (default: 24 hours). If the approval expires without action, the execution is cancelled and an alert is generated.

---

## Viewing Execution History

**API Endpoint:** `GET /api/v1/automations/executions`

### Execution Record

Each execution record contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Execution identifier |
| `playbookId` | string | Source playbook identifier |
| `playbookName` | string | Source playbook name |
| `status` | string | Current execution status |
| `triggerType` | string | What triggered the execution |
| `triggeredBy` | string | Operator or system that triggered |
| `targetHosts` | array | Hosts involved |
| `startedAt` | ISO 8601 | When execution started |
| `completedAt` | ISO 8601 | When execution finished |
| `duration` | integer | Total execution time in seconds |
| `steps` | array | Step-by-step execution details |
| `approval` | object | Approval details (if applicable) |
| `result` | object | Overall execution result |
| `auditTrail` | array | Complete audit trail |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `playbookId` | string | Filter by playbook |
| `status` | string | Filter by execution status |
| `triggerType` | string | Filter by trigger type |
| `startDate` | ISO 8601 | Start of date range |
| `endDate` | ISO 8601 | End of date range |
| `page` | integer | Pagination page number |
| `pageSize` | integer | Results per page (default: 50) |

### Via Dashboard

1. Navigate to the Automation section.
2. The "Execution History" tab shows all past executions.
3. Use the filter panel to narrow results by status, playbook, date range, or trigger type.
4. Click an execution to view its detailed step-by-step progress.

---

## Audit Trail

Every action in the automation system is recorded in a comprehensive audit trail.

### What Is Audited

| Event | Recorded Data |
|-------|--------------|
| Playbook created | Who created it, when, full playbook definition |
| Playbook modified | Who modified it, what changed, when |
| Playbook deleted | Who deleted it, when |
| Execution triggered | Who or what triggered it, trigger type, parameters |
| Approval requested | When requested, who needs to approve |
| Approval granted | Who approved it, when, any conditions |
| Approval denied | Who denied it, when, reason |
| Step started | Which step started, on which host, when |
| Step completed | Step result, output, duration |
| Step failed | Error details, when, which host |
| Execution completed | Final status, duration, summary |
| Configuration changed | What changed, who changed it, when |

### Viewing the Audit Trail

**API Endpoint:** `GET /api/v1/automations/audit`

**Via Dashboard:**
1. Navigate to the Automation section.
2. Open the "Audit Trail" tab.
3. Browse the chronological list of all automation events.
4. Use filters to narrow by event type, operator, date range, or playbook.

### Audit Trail Record

Each audit record contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Audit record identifier |
| `timestamp` | ISO 8601 | When the event occurred |
| `eventType` | string | Type of event (see table above) |
| `actor` | string | Who or what performed the action |
| `actorType` | string | `operator`, `system`, `automation` |
| `resource` | string | Affected resource (playbook, execution, etc.) |
| `resourceId` | string | Identifier of the affected resource |
| `details` | object | Event-specific details |
| `previousState` | object | State before the change (if applicable) |
| `newState` | object | State after the change (if applicable) |

---

## Automation Dashboard

The automation section of the dashboard provides a real-time operational view.

### Widgets

| Widget | Description |
|--------|-------------|
| **Active Executions** | Currently running playbook executions with progress |
| **Pending Approvals** | Queue of executions awaiting operator approval |
| **Recent Results** | Last 20 completed executions with pass/fail status |
| **Execution Trends** | Chart showing execution volume and success rate over time |
| **Top Playbooks** | Most frequently executed playbooks |
| **Failure Summary** | Recent failures grouped by playbook and error type |

---

## Manual Execution

Operators can trigger playbook execution manually at any time.

**API Endpoint:** `POST /api/v1/automations/playbooks/{playbookId}/execute`

**Via Dashboard:**
1. Navigate to the Playbooks section.
2. Find the desired playbook.
3. Click "Execute" to start a manual run.
4. Confirm the execution targets and any parameters.
5. If the playbook requires approval, it enters the approval queue.

### Execution Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `targets` | array | Host IDs or groups to execute against |
| `variables` | object | Override playbook variables for this execution |
| `dryRun` | boolean | Simulate execution without making changes |

---

## Monitoring Active Executions

When playbooks are executing, monitor their progress:

**Via Dashboard:**
1. Navigate to the Automation section.
2. Open the "Active Executions" tab.
3. Each execution shows:
   - Current step being executed
   - Overall progress percentage
   - Elapsed time
   - Target hosts and their individual status

**Via API:**
```
GET /api/v1/automations/executions/{executionId}
```

### Execution Detail View

The detail view for an active execution shows:

| Section | Content |
|---------|---------|
| **Progress Bar** | Visual progress indicator |
| **Step List** | All steps with status indicators (pending, running, completed, failed) |
| **Live Output** | Real-time output from the executing step |
| **Target Status** | Per-host execution status |
| **Timeline** | Chronological event log |

---

## Handling Failed Executions

When an execution fails:

### Step 1: Review the Failure

1. Navigate to the execution detail view.
2. Identify which step failed and the error message.
3. Review the output from the failed step.

### Step 2: Determine Root Cause

Common failure causes:

| Cause | Investigation |
|-------|--------------|
| Agent offline | Check agent status in [AGENTS.md](./AGENTS.md) |
| Permission denied | Verify credentials and permissions on target host |
| Network timeout | Check connectivity to target host |
| Invalid command | Review the playbook step definition |
| Resource constraint | Check target host resource availability |

### Step 3: Take Action

| Action | When to Use |
|--------|-------------|
| Retry the execution | Transient failure (network timeout, agent busy) |
| Fix and re-execute | Playbook error or configuration issue |
| Skip and continue | Non-critical step failure |
| Cancel | Execution no longer needed or safe to abort |

### Retry Policy

| Retry Setting | Description |
|---------------|-------------|
| `autoRetry` | Automatically retry failed steps |
| `maxRetries` | Maximum retry attempts (default: 3) |
| `retryDelay` | Seconds between retries (default: 30) |
| `backoffMultiplier` | Delay multiplier for exponential backoff (default: 2.0) |

---

## Automation Best Practices

### Playbook Design

- Keep playbooks focused on a single objective.
- Use conditional steps to handle different scenarios.
- Test playbooks in dry-run mode before live execution.
- Include rollback steps for destructive operations.

### Execution Management

- Always review pending approvals carefully before approving.
- Monitor active executions, especially for critical infrastructure.
- Use dry-run mode to validate execution plans.
- Schedule non-urgent automations during maintenance windows.

### Audit and Compliance

- Document the purpose of each playbook.
- Review the audit trail weekly for unauthorized changes.
- Ensure all automation-triggered actions are traceable.
- Retain execution history per your organization's retention policy.

### Security

- Require approval for playbooks that modify security configurations.
- Use least-privilege credentials for automation targets.
- Review automation access permissions regularly.
- Audit who has permission to create and modify playbooks.
