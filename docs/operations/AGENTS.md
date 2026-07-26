# Agent Management Guide

**Purpose:** Monitoring agent lifecycle, states, and management  
**Related:** [DASHBOARD.md](./DASHBOARD.md), [INVENTORY.md](./INVENTORY.md), [REMOTE_OPERATIONS.md](./REMOTE_OPERATIONS.md)

---

## Agent Overview

Agents are lightweight components installed on each managed host. They communicate with Mission Control via a heartbeat cycle every 30 seconds, reporting host status, collecting inventory, and receiving commands. Each heartbeat response from the server includes any pending commands and remote target information.

---

## Viewing the Agent List

The agent list is accessible from the dashboard's Agent Grid widget and via the API.

**API Endpoint:** `GET /api/v1/agents`  
**Response:** Array of agent objects

Each agent object contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique agent identifier |
| `hostname` | string | Hostname of the managed machine |
| `state` | string | Current agent state (one of 9 states) |
| `lastHeartbeat` | ISO 8601 timestamp | Time of last received heartbeat |
| `ipAddress` | string | Agent IP address |
| `operatingSystem` | string | OS detected by the agent |
| `agentVersion` | string | Installed agent version |
| `uptime` | integer | Seconds since agent process started |
| `inventory` | object | Latest inventory snapshot |
| `remoteTargets` | array | Remote access targets configured |

### Example Response

```json
{
  "id": "agent-7f3a2b",
  "hostname": "web-server-01",
  "state": "online",
  "lastHeartbeat": "2026-07-26T10:30:00Z",
  "ipAddress": "192.168.1.50",
  "operatingSystem": "Ubuntu 22.04 LTS",
  "agentVersion": "2.4.1",
  "uptime": 864000,
  "inventory": { "...": "..." },
  "remoteTargets": [
    { "type": "ssh", "host": "192.168.1.50", "port": 22 },
    { "type": "agent", "host": "192.168.1.50" }
  ]
}
```

---

## Agent Detail View

Selecting a specific agent provides detailed information.

**API Endpoint:** `GET /api/v1/agents/{agentId}`

### Detail Sections

| Section | Description |
|---------|-------------|
| **General Info** | Hostname, IP, OS, agent version, uptime |
| **State History** | Timeline of state transitions |
| **Health History** | Health check results over time |
| **Inventory** | Full inventory data collected by this agent (see [INVENTORY.md](./INVENTORY.md)) |
| **Remote Targets** | Configured remote access methods |
| **Command History** | Recent commands executed via this agent |
| **Resource Usage** | CPU, memory, disk usage on the host |

---

## Agent States

Agents transition through 9 distinct states. Understanding these states is critical for monitoring operations.

### State Definitions

#### `online`
The agent is active, communicating normally, and all health checks are passing. This is the expected steady-state for a properly functioning agent.

**Action:** No action required.

#### `offline`
The agent has not sent a heartbeat within the expected interval (30 seconds × defined tolerance). The agent process may be stopped, the host may be unreachable, or network connectivity may be lost.

**Immediate Actions:**
1. Check if the host is reachable via ping or other network tools.
2. Verify the agent process is running on the host (see [REMOTE_OPERATIONS.md](./REMOTE_OPERATIONS.md)).
3. Review agent logs for error messages.
4. If the host is a VM, verify it is powered on via Hyper-V or Proxmox management.

#### `warning`
The agent is communicating but reporting one or more warning conditions. The agent is functional but degraded.

**Actions:**
1. Review the specific warnings in the agent detail view.
2. Common warnings include: high resource utilization, approaching disk space thresholds, certificate expiry approaching.
3. Determine if the warning requires immediate action or can be scheduled.

#### `healthy`
The agent is active and all health checks are passing. Similar to `online` but explicitly indicates all configured health checks returned positive results.

**Action:** No action required.

#### `unhealthy`
The agent is communicating but one or more health checks are failing. The agent itself is functional but the host it monitors has issues.

**Actions:**
1. Review which health checks are failing in the agent detail view.
2. Check the relevant infrastructure component (e.g., if a service health check fails, verify the service).
3. Follow [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) if the unhealthy state persists.

#### `updating`
The agent is currently being updated to a new version. This state is expected during scheduled or manual agent updates.

**Actions:**
1. Wait for the update to complete.
2. Monitor the agent state for transition back to `online` or `healthy`.
3. If the agent remains in `updating` for longer than the expected update duration, investigate the update process.
4. After update completes, verify the agent version and health.

#### `pending`
The agent has been registered in Mission Control but has not yet completed its initial activation handshake. This is expected for newly deployed agents.

**Actions:**
1. Verify the agent is installed and configured on the target host.
2. Check that the agent can reach the Mission Control server.
3. Complete the activation process or remove the registration if no longer needed.

#### `executing`
The agent is currently running a command or task received from Mission Control. This is expected during automation execution or manual command dispatch.

**Actions:**
1. Monitor execution progress via the agent detail view.
2. Wait for the execution to complete.
3. If execution is stuck or taking longer than expected, review the command and agent logs.

#### `disabled`
The agent has been manually disabled by an operator. A disabled agent does not process commands and may or may not continue heartbeating.

**Actions:**
1. Verify the disable was intentional.
2. If re-enabling, use the agent management controls to set the agent back to an active state.
3. Document the reason for disabling in the operational log.

---

## Enabling and Disabling Agents

### Disabling an Agent

Use case: Temporarily stop monitoring a host during planned maintenance, or deactivate a decommissioned host.

**API Endpoint:** `POST /api/v1/agents/{agentId}/disable`

**Procedure:**
1. Navigate to the agent detail view.
2. Click "Disable Agent" or call the API endpoint.
3. Confirm the action when prompted.
4. The agent state transitions to `disabled`.
5. Document the reason for disabling in your operational notes.

**Considerations:**
- Disabling an agent stops all monitoring for that host.
- Active alerts for the agent will remain open but no new alerts will be generated.
- Automation tasks targeting this agent will fail if attempted.

### Enabling an Agent

Use case: Re-enable monitoring after maintenance, or reactivate a previously disabled agent.

**API Endpoint:** `POST /api/v1/agents/{agentId}/enable`

**Procedure:**
1. Navigate to the agent detail view.
2. Click "Enable Agent" or call the API endpoint.
3. The agent state transitions to `pending` while it re-establishes communication.
4. Once the agent completes its handshake and first heartbeat, it transitions to `online` or `healthy`.
5. Verify the agent is reporting correctly in the agent grid.

---

## Viewing Agent Inventory

Each agent collects and reports inventory data via its heartbeat. This data includes system information, installed software, running services, and network configuration.

**API Endpoint:** `GET /api/v1/agents/{agentId}/inventory`  
**Full Guide:** See [INVENTORY.md](./INVENTORY.md)

### Quick Inventory Check

1. Navigate to the agent detail view.
2. Select the "Inventory" tab.
3. Review the three inventory categories:
   - **System:** OS, hardware, kernel version
   - **Software:** Installed packages and applications
   - **Services:** Running and configured services
   - **Network:** Interfaces, IP addresses, DNS configuration

---

## Remote Targets

Each agent reports its available remote access targets. These targets determine how Mission Control can execute commands on the host.

### Target Types

| Type | Description | Priority |
|------|-------------|----------|
| `agent` | Commands executed through the agent process itself | Highest (agent-first) |
| `ssh` | SSH fallback for when the agent is unavailable | Medium |
| `winrm` | WinRM fallback for Windows hosts | Medium |

### Viewing Remote Targets

In the agent detail view, the "Remote Targets" section lists all configured access methods.

### Remote Target Priority

Mission Control uses an agent-first approach:
1. **Agent command:** Attempt to execute via the agent process.
2. **SSH/WinRM fallback:** If the agent is offline or unavailable, fall back to SSH (Linux) or WinRM (Windows).

See [REMOTE_OPERATIONS.md](./REMOTE_OPERATIONS.md) for detailed remote operations procedures.

---

## Agent Commands

Mission Control can dispatch commands to agents. These commands are delivered via the heartbeat response mechanism.

### Command Flow

1. Operator or automation triggers a command.
2. Command is queued for the target agent.
3. On the agent's next heartbeat (every 30 seconds), the server responds with any pending commands.
4. The agent executes the command and reports the result on its next heartbeat.
5. The operator can view the result in the agent detail view or via the API.

### Viewing Command History

**API Endpoint:** `GET /api/v1/agents/{agentId}/commands`

Each command record contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Command identifier |
| `command` | string | The command string or object |
| `status` | string | `pending`, `executing`, `completed`, `failed` |
| `submittedAt` | ISO 8601 timestamp | When the command was queued |
| `executedAt` | ISO 8601 timestamp | When the agent started execution |
| `completedAt` | ISO 8601 timestamp | When execution finished |
| `result` | object | Execution result including stdout, stderr, exit code |

---

## Agent Health History

The health history provides a timeline of health check results for each agent.

**API Endpoint:** `GET /api/v1/agents/{agentId}/health`

### Health History Data Points

Each data point contains:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | ISO 8601 timestamp | When the health check was recorded |
| `score` | integer (0-100) | Health score at that point in time |
| `checks` | array | Individual check results |
| `state` | string | Agent state at that point in time |

### Using Health History

- **Identify patterns:** Look for recurring health score drops at specific times (may indicate scheduled workloads).
- **Correlate with events:** Cross-reference health score changes with event bus activity.
- **Baseline establishment:** Use historical data to establish what "normal" looks like for each agent.
- **Trending:** Detect gradual degradation before it becomes critical.

---

## Agent Heartbeat Details

The heartbeat is the core communication mechanism between agents and Mission Control.

### Heartbeat Cycle

| Parameter | Value | Description |
|-----------|-------|-------------|
| Interval | 30 seconds | How often the agent sends a heartbeat |
| Timeout | Configurable | How long before a missed heartbeat triggers `offline` state |
| Payload | JSON | Status, inventory delta, health check results |
| Response | JSON | Commands to execute, remote targets, configuration updates |

### Heartbeat Payload

Each heartbeat from the agent includes:

| Field | Description |
|-------|-------------|
| `agentId` | Agent identifier |
| `timestamp` | Current agent time |
| `state` | Current self-reported state |
| `healthChecks` | Results of local health checks |
| `inventoryDelta` | Changes since last heartbeat |
| `resourceUsage` | CPU, memory, disk metrics |
| `commandResults` | Results of previously received commands |

### Heartbeat Response

The server responds to each heartbeat with:

| Field | Description |
|-------|-------------|
| `commands` | Array of pending commands to execute |
| `remoteTargets` | Updated remote access target list |
| `configuration` | Any configuration changes to apply |
| `acknowledgments` | Confirmation of received inventory data |
