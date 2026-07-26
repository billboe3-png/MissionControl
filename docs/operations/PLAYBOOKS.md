# Playbook Management Guide

**Purpose:** Creating, managing, and operating playbooks  
**Related:** [AUTOMATION.md](./AUTOMATION.md), [AGENTS.md](./AGENTS.md), [REMOTE_OPERATIONS.md](./REMOTE_OPERATIONS.md)

---

## Playbook Overview

Playbooks are the foundation of Mission Control automation. A playbook defines a sequence of steps to accomplish a specific operational task. Playbooks can be executed manually, on a schedule, in response to alerts, or via API calls.

---

## Playbook Structure

Every playbook consists of the following components:

### Top-Level Definition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Auto | Unique playbook identifier |
| `name` | string | Yes | Human-readable playbook name |
| `description` | string | Yes | What the playbook does |
| `version` | string | Yes | Semantic version (e.g., `1.2.0`) |
| `type` | string | Yes | `manual`, `scheduled`, `alert_triggered`, `api_triggered`, `event_triggered` |
| `steps` | array | Yes | Ordered list of steps to execute |
| `variables` | object | No | User-defined variables for the playbook |
| `schedule` | object | No | Schedule configuration (for scheduled type) |
| `requiresApproval` | boolean | No | Whether operator approval is needed |
| `approvalTimeout` | integer | No | Seconds before approval request expires (default: 86400) |
| `targets` | array | No | Default target hosts or groups |
| `tags` | array | No | Tags for organization and filtering |
| `timeout` | integer | No | Maximum execution time in seconds (default: 3600) |
| `retryPolicy` | object | No | Retry configuration for failed steps |
| `rollbackSteps` | array | No | Steps to run if execution fails (compensation) |

### Example Playbook Definition

```json
{
  "name": "Restart Web Service",
  "description": "Gracefully restarts the web service on target hosts",
  "version": "1.0.0",
  "type": "manual",
  "requiresApproval": true,
  "tags": ["web", "service-management"],
  "variables": {
    "serviceName": { "type": "string", "default": "nginx", "description": "Service to restart" },
    "gracefulTimeout": { "type": "integer", "default": 30, "description": "Seconds to wait for graceful shutdown" }
  },
  "steps": [
    {
      "name": "Check service status",
      "type": "agent_command",
      "command": "systemctl status {{serviceName}}",
      "expectedExitCode": 0,
      "onFailure": "abort"
    },
    {
      "name": "Stop service gracefully",
      "type": "agent_command",
      "command": "systemctl stop {{serviceName}} --timeout={{gracefulTimeout}}",
      "timeout": 60
    },
    {
      "name": "Verify service stopped",
      "type": "agent_command",
      "command": "systemctl is-active {{serviceName}}",
      "expectedExitCode": 3,
      "retry": { "maxAttempts": 5, "delaySeconds": 5 }
    },
    {
      "name": "Start service",
      "type": "agent_command",
      "command": "systemctl start {{serviceName}}"
    },
    {
      "name": "Verify service is running",
      "type": "agent_command",
      "command": "systemctl is-active {{serviceName}}",
      "expectedExitCode": 0,
      "onFailure": "rollback"
    }
  ],
  "rollbackSteps": [
    {
      "name": "Rollback: start service",
      "type": "agent_command",
      "command": "systemctl start {{serviceName}}"
    }
  ]
}
```

---

## Step Types

### Script Step

Executes a script on the target host.

```json
{
  "name": "Run cleanup script",
  "type": "script",
  "interpreter": "/bin/bash",
  "script": "#!/bin/bash\nfind /tmp -mtime +7 -delete\necho 'Cleanup complete'",
  "timeout": 120,
  "onFailure": "continue"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `interpreter` | string | Script interpreter path |
| `script` | string | Script content to execute |
| `timeout` | integer | Maximum execution time in seconds |
| `onFailure` | string | `abort`, `continue`, `retry`, or `rollback` |
| `environment` | object | Environment variables for the script |

### HTTP Step

Makes an HTTP request to an external endpoint.

```json
{
  "name": "Notify external system",
  "type": "http",
  "method": "POST",
  "url": "https://hooks.example.com/deploy",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "event": "deployment",
    "host": "{{targetHost}}",
    "status": "complete"
  },
  "expectedStatusCodes": [200, 201],
  "onFailure": "continue"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `method` | string | HTTP method (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`) |
| `url` | string | Target URL (supports variable interpolation) |
| `headers` | object | HTTP headers |
| `body` | object | Request body |
| `expectedStatusCodes` | array | Acceptable HTTP response codes |
| `timeout` | integer | Request timeout in seconds |
| `onFailure` | string | Failure handling strategy |

### Agent Command Step

Sends a command to be executed through an agent.

```json
{
  "name": "Check disk space",
  "type": "agent_command",
  "command": "df -h /",
  "expectedExitCode": 0,
  "captureOutput": true,
  "outputVariable": "diskInfo",
  "onFailure": "abort"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `command` | string | Command to execute |
| `expectedExitCode` | integer | Expected exit code for success |
| `captureOutput` | boolean | Whether to capture stdout/stderr |
| `outputVariable` | string | Variable name to store output for subsequent steps |
| `timeout` | integer | Command timeout in seconds |
| `onFailure` | string | Failure handling strategy |

### Conditional Step

Evaluates a condition and branches execution.

```json
{
  "name": "Check if service needs restart",
  "type": "conditional",
  "condition": {
    "type": "expression",
    "expression": "{{serviceStatus}} != 'active'"
  },
  "thenSteps": [
    {
      "name": "Restart service",
      "type": "agent_command",
      "command": "systemctl restart nginx"
    }
  ],
  "elseSteps": [
    {
      "name": "Log no action needed",
      "type": "script",
      "script": "echo 'Service is already active, no restart needed'"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `condition` | object | Condition to evaluate |
| `condition.type` | string | `expression`, `variable_check`, or `exit_code` |
| `condition.expression` | string | Boolean expression to evaluate |
| `thenSteps` | array | Steps to execute if condition is true |
| `elseSteps` | array | Steps to execute if condition is false |

### Approval Step

Pauses execution and waits for operator approval.

```json
{
  "name": "Approve production deployment",
  "type": "approval",
  "message": "Ready to deploy to production. Approve to continue?",
  "requiredApprovers": 1,
  "timeout": 3600,
  "onTimeout": "cancel"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Message shown to the approver |
| `requiredApprovers` | integer | Number of approvals needed |
| `timeout` | integer | Seconds to wait for approval |
| `onTimeout` | string | Action if approval times out (`cancel` or `continue`) |

### Parallel Step

Executes multiple steps concurrently.

```json
{
  "name": "Update all web servers",
  "type": "parallel",
  "steps": [
    {
      "name": "Update server 1",
      "type": "agent_command",
      "command": "apt update && apt upgrade -y",
      "target": "web-server-01"
    },
    {
      "name": "Update server 2",
      "type": "agent_command",
      "command": "apt update && apt upgrade -y",
      "target": "web-server-02"
    }
  ],
  "waitForAll": true,
  "onFailure": "abort"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `steps` | array | Steps to execute in parallel |
| `waitForAll` | boolean | Wait for all steps to complete before proceeding |
| `onFailure` | string | Failure handling if any parallel step fails |

---

## Variables

Variables allow playbooks to be parameterized and reused.

### Variable Definition

Variables are defined at the playbook level and can be overridden at execution time.

```json
{
  "variables": {
    "targetService": {
      "type": "string",
      "default": "nginx",
      "description": "Service to manage",
      "required": true
    },
    "maxRetries": {
      "type": "integer",
      "default": 3,
      "description": "Maximum retry attempts",
      "min": 0,
      "max": 10
    },
    "enableDryRun": {
      "type": "boolean",
      "default": false,
      "description": "Run in dry-run mode"
    }
  }
}
```

### Variable Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | Text value | `"nginx"` |
| `integer` | Whole number | `3` |
| `float` | Decimal number | `3.14` |
| `boolean` | True/false | `true` |
| `array` | List of values | `["web-01", "web-02"]` |
| `object` | Key-value map | `{"host": "web-01", "port": 80}` |
| `secret` | Sensitive value (masked in logs) | `"***"` |

### Variable Interpolation

Use `{{variableName}}` syntax in step definitions:

```json
{
  "command": "systemctl restart {{targetService}}"
}
```

### Built-in Variables

| Variable | Description |
|----------|-------------|
| `{{executionId}}` | Current execution identifier |
| `{{targetHost}}` | Current target host |
| `{{targetAgentId}}` | Current target agent ID |
| `{{timestamp}}` | Current ISO 8601 timestamp |
| `{{previousStepOutput}}` | Output from the immediately preceding step |

---

## Scheduling

Scheduled playbooks run automatically at defined times.

### Schedule Configuration

```json
{
  "schedule": {
    "type": "cron",
    "expression": "0 2 * * 0",
    "timezone": "UTC",
    "enabled": true
  }
}
```

### Schedule Types

| Type | Description | Example |
|------|-------------|---------|
| `cron` | Standard cron expression | `"0 2 * * 0"` (every Sunday at 2 AM) |
| `interval` | Fixed interval in seconds | `3600` (every hour) |
| `daily` | Once per day at specified time | `"02:00"` |
| `weekly` | Once per week on specified day | `"Sunday 02:00"` |
| `monthly` | Once per month | `"1st 02:00"` |

### Common Schedule Examples

| Purpose | Schedule |
|---------|----------|
| Daily backup verification | `daily: 06:00` |
| Weekly security scan | `cron: 0 3 * * 0` |
| Monthly certificate check | `monthly: 1st 09:00` |
| Hourly health check | `interval: 3600` |

---

## Testing Playbooks

Always test playbooks before deploying to production.

### Dry-Run Mode

Dry-run mode simulates execution without making actual changes.

**API Endpoint:** `POST /api/v1/automations/playbooks/{playbookId}/execute`

```json
{
  "dryRun": true,
  "targets": ["web-server-01"]
}
```

During dry-run:
- Steps are evaluated but not executed on hosts.
- Commands are logged but not sent to agents.
- Conditional steps evaluate their conditions.
- Output shows what would happen without making changes.

### Testing Best Practices

1. **Use a non-production target first:** Execute against a test or development host.
2. **Review dry-run output:** Verify each step would execute as expected.
3. **Test failure scenarios:** Intentionally cause failures to verify error handling.
4. **Validate variable interpolation:** Ensure all variables resolve correctly.
5. **Check timeout behavior:** Verify steps complete within expected timeframes.
6. **Test rollback steps:** Verify rollback procedures execute correctly.

---

## Best Practices

### Playbook Design

- **Single responsibility:** Each playbook should accomplish one specific task.
- **Descriptive naming:** Use clear, descriptive names (e.g., "Rotate TLS Certificates" not "Playbook 12").
- **Version control:** Use semantic versioning and track changes.
- **Documentation:** Include a thorough description of what the playbook does and when to use it.

### Step Design

- **Idempotency:** Design steps that can be safely re-run without side effects.
- **Error handling:** Always define `onFailure` behavior for each step.
- **Timeouts:** Set appropriate timeouts for every step to prevent hung executions.
- **Validation:** Use expected exit codes and output validation where possible.

### Security

- **Use secret variables** for credentials and sensitive data.
- **Require approval** for playbooks that modify production systems.
- **Limit targets:** Restrict which hosts a playbook can target.
- **Audit trail:** Ensure all actions are traceable through the audit system.

### Maintenance

- **Review regularly:** Audit playbooks quarterly for relevance and correctness.
- **Update for changes:** Update playbooks when infrastructure or procedures change.
- **Remove obsolete playbooks:** Delete playbooks that are no longer needed.
- **Test after changes:** Always retest after modifying a playbook.
