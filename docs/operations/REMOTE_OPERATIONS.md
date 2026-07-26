# Remote Operations Guide

**Purpose:** Managing hosts, executing commands, and file operations remotely  
**Related:** [AGENTS.md](./AGENTS.md), [PLAYBOOKS.md](./PLAYBOOKS.md), [ALERTS.md](./ALERTS.md)

---

## Remote Operations Overview

Mission Control provides remote operations capabilities for managing hosts across your infrastructure. Remote operations use an agent-first approach, with SSH/WinRM fallback when the agent is unavailable.

### Connection Priority

| Priority | Method | When Used | Requirements |
|----------|--------|-----------|--------------|
| 1 (Primary) | Agent command | Agent is online and responsive | Agent process running on host |
| 2 (Fallback) | SSH | Agent is offline or unavailable | SSH daemon running, credentials configured |
| 3 (Fallback) | WinRM | Agent is offline on Windows host | WinRM configured, credentials configured |

---

## Managing Hosts

### Viewing Hosts

**API Endpoint:** `GET /api/v1/remote/hosts`

**Via Dashboard:**
1. Navigate to the Remote Operations section.
2. The host list shows all managed hosts with their connection status.

### Host Record

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique host identifier |
| `hostname` | string | Hostname |
| `ipAddress` | string | IP address |
| `osType` | string | `windows`, `linux`, or `other` |
| `connectionStatus` | string | `connected`, `disconnected`, `degraded` |
| `primaryMethod` | string | `agent`, `ssh`, or `winrm` |
| `availableMethods` | array | All available connection methods |
| `agentId` | string | Associated agent ID (if agent installed) |
| `lastConnected` | ISO 8601 | Last successful connection time |
| `credentials` | object | Credential reference (not the actual credentials) |

### Adding a Host

**Via Dashboard:**
1. Navigate to Remote Operations > Hosts.
2. Click "Add Host".
3. Enter the host details:
   - Hostname or IP address
   - Operating system type
   - Connection method(s) to configure
4. Configure credentials (see Credential Management below).
5. Test the connection.
6. Save the host.

### Removing a Host

1. Navigate to the host detail view.
2. Click "Remove Host".
3. Confirm the removal.
4. The host is removed from remote operations (agent, if installed, is unaffected).

---

## Credential Management

Credentials are stored securely and referenced by ID — they are never exposed in full through the API.

### Credential Types

| Type | Use Case | Fields |
|------|----------|--------|
| `ssh_key` | SSH key-based authentication | Private key, passphrase (optional) |
| `ssh_password` | SSH password authentication | Username, password |
| `winrm_password` | WinRM password authentication | Username, password, domain (optional) |
| `agent_token` | Agent-based authentication | Agent registration token |

### Adding Credentials

**API Endpoint:** `POST /api/v1/remote/credentials`

**Via Dashboard:**
1. Navigate to Remote Operations > Credentials.
2. Click "Add Credential".
3. Select the credential type.
4. Enter the required fields.
5. Name the credential for easy reference.
6. Save the credential.

### Credential Security

- All credentials are encrypted at rest.
- Credentials are never returned in full through API responses.
- Credential access is logged in the audit trail.
- Credentials can be scoped to specific hosts.
- Rotate credentials regularly per [MAINTENANCE.md](./MAINTENANCE.md).

---

## Executing Commands

### Remote Command Execution

**API Endpoint:** `POST /api/v1/remote/execute`

**Via Dashboard:**
1. Navigate to Remote Operations > Console.
2. Select the target host from the host list.
3. Choose the connection method (agent, SSH, or WinRM).
4. Enter the command.
5. Click "Execute".
6. View the output in real-time.

### Command Request

```json
{
  "hostId": "host-abc123",
  "command": "df -h /",
  "method": "agent",
  "timeout": 30,
  "workingDirectory": "/tmp"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `hostId` | string | Target host identifier |
| `command` | string | Command to execute |
| `method` | string | Connection method (`agent`, `ssh`, `winrm`, or `auto`) |
| `timeout` | integer | Maximum execution time in seconds |
| `workingDirectory` | string | Working directory for the command |
| `environment` | object | Additional environment variables |

### Command Response

```json
{
  "executionId": "exec-xyz789",
  "hostId": "host-abc123",
  "status": "completed",
  "exitCode": 0,
  "stdout": "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       100G   45G   55G  45% /",
  "stderr": "",
  "duration": 1.2,
  "method": "agent"
}
```

### Auto Method Selection

When `method` is set to `auto`, Mission Control automatically selects the best available connection method:
1. Try agent command first (if agent is online).
2. Fall back to SSH (if SSH credentials are available).
3. Fall back to WinRM (if WinRM credentials are available for Windows hosts).

---

## File Browser

Mission Control provides a file browser for navigating host filesystems.

**API Endpoint:** `GET /api/v1/remote/hosts/{hostId}/files?path={path}`

### Listing Directory Contents

**Via Dashboard:**
1. Navigate to Remote Operations > File Browser.
2. Select the target host.
3. Browse the filesystem using the directory tree.
4. Click on directories to navigate into them.

### File Entry

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | File or directory name |
| `type` | string | `file`, `directory`, `link`, `other` |
| `size` | integer | File size in bytes |
| `permissions` | string | Unix permissions or Windows ACL summary |
| `owner` | string | File owner |
| `modifiedAt` | ISO 8601 | Last modification time |

### File Operations

| Operation | API Endpoint | Description |
|-----------|-------------|-------------|
| Download | `GET /api/v1/remote/hosts/{hostId}/files/download?path={path}` | Download a file |
| Upload | `POST /api/v1/remote/hosts/{hostId}/files/upload` | Upload a file |
| Delete | `DELETE /api/v1/remote/hosts/{hostId}/files?path={path}` | Delete a file |
| Create directory | `POST /api/v1/remote/hosts/{hostId}/files/mkdir` | Create a directory |
| Rename | `PUT /api/v1/remote/hosts/{hostId}/files/rename` | Rename or move a file |

---

## Command History

All remotely executed commands are recorded for audit and review purposes.

**API Endpoint:** `GET /api/v1/remote/history`

### History Record

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Execution identifier |
| `hostId` | string | Target host |
| `hostname` | string | Target hostname |
| `command` | string | Command executed |
| `method` | string | Connection method used |
| `executedBy` | string | Operator who executed the command |
| `executedAt` | ISO 8601 | When the command was executed |
| `exitCode` | integer | Command exit code |
| `duration` | integer | Execution time in seconds |
| `status` | string | `completed`, `failed`, `timeout` |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `hostId` | string | Filter by host |
| `executedBy` | string | Filter by operator |
| `startDate` | ISO 8601 | Start of date range |
| `endDate` | ISO 8601 | End of date range |
| `status` | string | Filter by status |

### Via Dashboard

1. Navigate to Remote Operations > Command History.
2. Browse the list of all executed commands.
3. Use filters to narrow by host, operator, date range, or status.
4. Click on a command to view the full output.

---

## Quick Commands

Quick commands provide one-click access to frequently used operations.

### Default Quick Commands

| Command | Description | Target |
|---------|-------------|--------|
| Check disk space | `df -h` | Linux hosts |
| Check memory | `free -m` | Linux hosts |
| Check processes | `top -bn1 \| head -20` | Linux hosts |
| Check disk space | `Get-PSDrive` | Windows hosts |
| Check memory | `Get-CimInstance Win32_OperatingSystem` | Windows hosts |
| Check services | `Get-Service` | Windows hosts |
| Check network | `ip addr show` | Linux hosts |
| Check network | `Get-NetIPAddress` | Windows hosts |
| Restart service | `systemctl restart {serviceName}` | Linux hosts |
| Restart service | `Restart-Service {serviceName}` | Windows hosts |

### Custom Quick Commands

**API Endpoint:** `POST /api/v1/remote/quick-commands`

**Via Dashboard:**
1. Navigate to Remote Operations > Quick Commands.
2. Click "Add Quick Command".
3. Define the command:
   - Name
   - Command template (supports variables)
   - Target OS type
   - Description
4. Save the quick command.

### Using Quick Commands

1. Navigate to Remote Operations.
2. Select the target host.
3. Open the Quick Commands panel.
4. Click on the desired command.
5. If the command has variables, fill in the prompted values.
6. Confirm and execute.

---

## Remote Console

The remote console provides an interactive shell experience.

**Via Dashboard:**
1. Navigate to Remote Operations > Console.
2. Select the target host.
3. Choose the connection method.
4. The console opens with an interactive session.

### Console Features

| Feature | Description |
|---------|-------------|
| **Interactive shell** | Full shell access on the target host |
| **Session history** | Scroll back through previous output |
| **Multi-tab** | Open multiple console sessions simultaneously |
| **Copy/paste** | Copy output and paste commands |
| **Session recording** | All console sessions are recorded for audit |

### Console Limitations

| Limit | Value | Reason |
|-------|-------|--------|
| Session timeout | 30 minutes | Security policy |
| Max concurrent sessions | 10 per operator | Resource management |
| Command history | 1000 lines | Memory management |
| File upload size | 100 MB | Bandwidth management |

---

## Agent-First vs Fallback

### Agent-First Approach

Mission Control always attempts to use the agent as the primary communication channel.

**Advantages of agent-first:**
- No need to store SSH/WinRM credentials
- Agent commands are delivered via the heartbeat mechanism (30-second cycle)
- Agent can execute commands even if the host is behind a firewall
- Full inventory and health data available
- Command results are returned via the next heartbeat

**When agent is unavailable:**
- Agent process is stopped or crashed
- Agent heartbeat has timed out (offline state)
- Agent is updating or restarting
- Network between agent and server is disrupted

### SSH/WinRM Fallback

When the agent is unavailable, Mission Control falls back to direct SSH or WinRM connections.

**SSH fallback (Linux):**
- Requires SSH daemon running on the target host
- Requires SSH credentials configured in Mission Control
- Direct command execution without heartbeat delay
- Full output returned immediately

**WinRM fallback (Windows):**
- Requires WinRM configured and enabled on the target host
- Requires WinRM credentials configured in Mission Control
- Supports both HTTP and HTTPS WinRM connections
- Full output returned immediately

### Fallback Decision Tree

```
Agent available?
  ├── Yes → Use agent command
  └── No → SSH available?
              ├── Yes → Use SSH
              └── No → WinRM available?
                          ├── Yes → Use WinRM
                          └── No → Connection failed
```

### When to Use Fallback

| Scenario | Recommended Approach |
|----------|---------------------|
| Agent is online | Always use agent |
| Agent is offline, urgent command needed | Use SSH/WinRM fallback |
| Agent is updating | Use SSH/WinRM if urgent, otherwise wait |
| Host never had agent installed | Configure SSH/WinRM directly |
| Agent cannot reach Mission Control server | Use SSH/WinRM from Mission Control server directly |
