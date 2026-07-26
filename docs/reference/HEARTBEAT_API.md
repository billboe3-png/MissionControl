# Mission Control Heartbeat Protocol

Reference for the agent heartbeat system — communication, command dispatch, and health monitoring.

---

## Overview

Agents communicate with Mission Control via a heartbeat mechanism:

```
Agent ──(POST /agents/{id}/heartbeat)──► Server
Agent ◄──(Response: commands + config)── Server
```

The heartbeat serves as the primary communication channel for:
- **Health monitoring** — server knows agent is alive
- **Command dispatch** — server queues commands in heartbeat responses
- **Configuration push** — server sends config updates to agents
- **Remote target delivery** — server provides connection details for remote access

---

## Heartbeat Request

### Timing

| Parameter | Default | Description |
|-----------|---------|-------------|
| Interval | 30 seconds | Time between heartbeats |
| Timeout | 10 seconds | HTTP request timeout |
| Missed threshold | 3 consecutive | Missed heartbeats before marked offline |

### Request Format

```http
POST /api/v1/agents/agt_x1y2z3/heartbeat HTTP/1.1
Host: localhost:8000
X-API-Key: mc_agent_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
Content-Type: application/json
```

```json
{
  "status": "online",
  "timestamp": "2026-07-26T10:30:00Z",
  "system": {
    "hostname": "web-server-01",
    "platform": "linux",
    "platform_version": "22.04 LTS",
    "architecture": "x86_64",
    "python_version": "3.12.4",
    "agent_version": "1.0.0",
    "uptime_seconds": 345600
  },
  "resources": {
    "cpu_percent": 23.5,
    "memory_percent": 67.2,
    "memory_used_mb": 5376,
    "memory_total_mb": 8192,
    "disk_percent": 45.8,
    "disk_used_gb": 183.2,
    "disk_total_gb": 400.0,
    "network_sent_bytes": 1073741824,
    "network_recv_bytes": 2147483648,
    "load_average": [1.2, 0.8, 0.5]
  },
  "services": [
    {
      "name": "nginx",
      "status": "running",
      "pid": 1234,
      "memory_mb": 128
    },
    {
      "name": "postgresql",
      "status": "running",
      "pid": 2345,
      "memory_mb": 1024
    },
    {
      "name": "redis",
      "status": "stopped",
      "pid": null,
      "memory_mb": 0
    }
  ],
  "pending_commands": 0
}
```

### System Information Fields

| Field | Type | Description |
|-------|------|-------------|
| `hostname` | string | Machine hostname |
| `platform` | string | OS platform (`linux`, `windows`, `darwin`) |
| `platform_version` | string | OS version string |
| `architecture` | string | CPU architecture |
| `python_version` | string | Python runtime version |
| `agent_version` | string | Agent software version |
| `uptime_seconds` | integer | System uptime in seconds |

### Resource Metrics Fields

| Field | Type | Description |
|-------|------|-------------|
| `cpu_percent` | float | CPU usage percentage (0-100) |
| `memory_percent` | float | Memory usage percentage (0-100) |
| `memory_used_mb` | integer | Used memory in megabytes |
| `memory_total_mb` | integer | Total memory in megabytes |
| `disk_percent` | float | Disk usage percentage (0-100) |
| `disk_used_gb` | float | Used disk space in gigabytes |
| `disk_total_gb` | float | Total disk space in gigabytes |
| `network_sent_bytes` | integer | Total bytes sent |
| `network_recv_bytes` | integer | Total bytes received |
| `load_average` | array | 1min, 5min, 15min load averages (Linux/macOS) |

---

## Heartbeat Response

The server responds with commands to execute and configuration updates:

```json
{
  "status": "success",
  "data": {
    "acknowledged": true,
    "server_timestamp": "2026-07-26T10:30:01Z",
    "commands": [
      {
        "id": "cmd_x1y2z3",
        "type": "script",
        "priority": "normal",
        "payload": {
          "script": "df -h",
          "timeout": 30
        },
        "queued_at": "2026-07-26T10:29:50Z"
      },
      {
        "id": "cmd_a1b2c3d4",
        "type": "config_update",
        "priority": "high",
        "payload": {
          "config": {
            "heartbeat_interval": 30,
            "log_level": "info"
          }
        },
        "queued_at": "2026-07-26T10:28:00Z"
      }
    ],
    "remote_targets": [
      {
        "id": "rmt_x1y2z3",
        "type": "ssh",
        "host": "10.0.0.50",
        "port": 22,
        "username": "admin",
        "fingerprint": "SHA256:abc123...",
        "expires_at": "2026-07-26T11:00:00Z"
      }
    ],
    "config_update": {
      "version": 5,
      "settings": {
        "heartbeat_interval": 30,
        "log_level": "info",
        "monitor_services": ["nginx", "postgresql", "redis"]
      }
    }
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `acknowledged` | boolean | Server received and processed the heartbeat |
| `server_timestamp` | string | Server's current timestamp (ISO 8601) |
| `commands` | array | Commands queued for the agent to execute |
| `remote_targets` | array | Remote connection targets available to this agent |
| `config_update` | object | Latest configuration (only sent when version changed) |

---

## Command Dispatch

Commands are delivered to agents via heartbeat responses. The agent executes each command and reports results in the next heartbeat or via a dedicated result endpoint.

### Command Priority

| Priority | Description |
|----------|-------------|
| `critical` | Execute immediately, interrupt current operations |
| `high` | Execute before normal tasks |
| `normal` | Execute in order received |
| `low` | Execute when idle |

### Command Types

| Type | Description |
|------|-------------|
| `script` | Execute a shell command or script |
| `config_update` | Update agent configuration |
| `restart` | Restart agent service |
| `upgrade` | Update agent software |
| `remote_connect` | Establish remote connection |
| `snapshot` | Take system snapshot |
| `diagnostic` | Run diagnostic checks |

### Command Execution Flow

```
1. Server queues command for agent
2. Agent receives command in heartbeat response
3. Agent executes command (respecting priority and timeout)
4. Agent reports result via POST /agents/{id}/commands/{cmd_id}/result
5. Server records result and triggers webhooks if configured
```

### Reporting Command Results

```bash
curl -X POST -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/agents/agt_x1y2z3/commands/cmd_x1y2z3/result \
  -d '{
    "status": "success",
    "exit_code": 0,
    "stdout": "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       400G  183G  217G  46% /",
    "stderr": "",
    "duration_ms": 1250,
    "completed_at": "2026-07-26T10:30:02Z"
  }'
```

---

## Remote Target Delivery

When a user initiates a remote connection through the Mission Control UI, the server delivers connection details to the target agent via the heartbeat response.

### SSH Target

```json
{
  "remote_targets": [
    {
      "id": "rmt_x1y2z3",
      "type": "ssh",
      "host": "10.0.0.50",
      "port": 22,
      "username": "admin",
      "fingerprint": "SHA256:abc123...",
      "private_key_ref": "vault:ssh-keys/web-server-01",
      "expires_at": "2026-07-26T11:00:00Z",
      "session_id": "rs_x1y2z3"
    }
  ]
}
```

### RDP Target

```json
{
  "remote_targets": [
    {
      "id": "rmt_a1b2c3d4",
      "type": "rdp",
      "host": "10.0.0.60",
      "port": 3389,
      "username": "administrator",
      "password_ref": "vault:rdp/windows-server-01",
      "expires_at": "2026-07-26T11:00:00Z",
      "session_id": "rs_a1b2c3d4"
    }
  ]
}
```

### Web Terminal Target

```json
{
  "remote_targets": [
    {
      "id": "rmt_e5f6g7h8",
      "type": "terminal",
      "host": "localhost",
      "port": 8765,
      "session_token": "ws_x1y2z3...",
      "expires_at": "2026-07-26T11:00:00Z",
      "session_id": "rs_e5f6g7h8"
    }
  ]
}
```

### Remote Target Lifecycle

```
1. User clicks "Connect" in Mission Control UI
2. Server creates remote target with expiry time
3. Server stores credentials in secure vault
4. Agent receives target in heartbeat response
5. Agent initiates connection to target host
6. Agent establishes tunnel/proxy to Mission Control
7. User interacts through Mission Control UI
8. Session expires or user disconnects
9. Agent tears down tunnel
10. Server removes remote target
```

---

## Offline Detection

### State Machine

```
                 ┌──────────────┐
        ┌───────│    ONLINE    │◄────────┐
        │       └──────┬───────┘         │
        │              │                  │
        │     Missed 3 heartbeats        │
        │              │                  │
        │              ▼                  │
        │       ┌──────────────┐    Heartbeat
        │       │   DEGRADED   │    received
        │       └──────┬───────┘         │
        │              │                  │
        │     Missed 3 more heartbeats   │
        │     (6 total)                  │
        │              │                  │
        │              ▼                  │
        │       ┌──────────────┐    Heartbeat
        │       │   OFFLINE    │─────────┘
        │       └──────┬───────┘
        │              │
        │     24 hours with
        │     no heartbeat
        │              │
        │              ▼
        │       ┌──────────────┐
        └──────►│   STALE      │
                └──────────────┘
```

### State Descriptions

| State | Condition | Behavior |
|-------|-----------|----------|
| `online` | Heartbeat received within expected interval | Normal operation |
| `degraded` | 3 missed heartbeats (~90s) | Alert triggered, commands still queued |
| `offline` | 6 missed heartbeats (~180s) | Critical alert, webhook fired, no commands sent |
| `stale` | 24 hours with no heartbeat | Agent marked for cleanup review |

### Offline Alert Webhook

When an agent goes offline, a webhook is fired:

```json
{
  "event": "agent.offline",
  "data": {
    "agent_id": "agt_x1y2z3",
    "agent_name": "Server Agent 01",
    "site_name": "Cape Town DC",
    "last_heartbeat": "2026-07-26T10:25:00Z",
    "offline_duration_seconds": 180,
    "state_transition": "degraded → offline"
  }
}
```

### Heartbeat Missed Alert

```json
{
  "event": "agent.heartbeat.missed",
  "data": {
    "agent_id": "agt_x1y2z3",
    "agent_name": "Server Agent 01",
    "missed_count": 3,
    "threshold": 3,
    "last_heartbeat": "2026-07-26T10:25:00Z",
    "next_expected": "2026-07-26T10:25:30Z"
  }
}
```

---

## Sequence Diagrams

### Normal Heartbeat

```
Agent                    Server
  │                        │
  │──POST /heartbeat──────►│
  │   { system, resources }│
  │                        │──Update agent status
  │                        │──Check command queue
  │◄──200 OK──────────────│
  │   { commands: [] }     │
  │                        │
  │   (wait 30s)           │
  │                        │
  │──POST /heartbeat──────►│
  │   { system, resources }│
  │◄──200 OK──────────────│
  │   { commands: [cmd1] } │
  │                        │
  │──Execute cmd1          │
  │──POST /result─────────►│
  │   { status: "success" }│
```

### Offline Detection

```
Agent                    Server
  │                        │
  │──POST /heartbeat──────►│
  │   { status: "online" } │
  │◄──200 OK──────────────│
  │                        │
  │   (agent crashes)      │
  │                        │
  │                        │──30s: No heartbeat
  │                        │──60s: No heartbeat
  │                        │──90s: 3 missed
  │                        │──State: ONLINE → DEGRADED
  │                        │──Trigger alert
  │                        │──Fire webhook
  │                        │
  │                        │──120s: No heartbeat
  │                        │──150s: No heartbeat
  │                        │──180s: 6 missed
  │                        │──State: DEGRADED → OFFLINE
  │                        │──Trigger critical alert
```

### Command Dispatch

```
Agent                    Server                User
  │                        │                     │
  │                        │◄──POST /commands────│
  │                        │   { agent_id, type }│
  │                        │──Queue command      │
  │                        │                     │
  │──POST /heartbeat──────►│                     │
  │◄──200 OK──────────────│                     │
  │   { commands: [cmd1] } │                     │
  │                        │                     │
  │──Execute cmd1          │                     │
  │                        │                     │
  │──POST /result─────────►│                     │
  │   { status: "success" }│                     │
  │                        │──Webhook: cmd       │
  │                        │   .completed        │
  │                        │──────notify────────►│
```

### Remote Connection

```
Agent                    Server                User
  │                        │                     │
  │                        │◄──POST /remote/     │
  │                        │   connect───────────│
  │                        │──Create target      │
  │                        │──Store credentials  │
  │                        │                     │
  │──POST /heartbeat──────►│                     │
  │◄──200 OK──────────────│                     │
  │   { remote_targets:    │                     │
  │     [{ id, host, }] }  │                     │
  │                        │                     │
  │──Connect to target     │                     │
  │──Establish tunnel─────►│                     │
  │                        │──Open WS to user    │
  │                        │                     │
  │                        │◄────terminal I/O────│
  │◄────terminal I/O──────│                     │
```

---

## Agent Configuration

### Heartbeat Config (`~/.config/mission-control-agent/config.yaml`)

```yaml
server:
  url: "https://your-domain.com"
  api_key: "mc_agent_..."
  verify_ssl: true

heartbeat:
  interval: 30          # Seconds between heartbeats
  timeout: 10           # HTTP request timeout in seconds
  retry_delay: 5        # Seconds to wait before retry on failure
  max_retries: 3        # Maximum retry attempts per heartbeat
  include_services: true # Include running service status
  services:             # Services to monitor
    - nginx
    - postgresql
    - redis

resources:
  collect_interval: 10  # Seconds between resource metric collection
  cpu_percent: true
  memory: true
  disk: true
  network: true
  load_average: true    # Linux/macOS only

commands:
  max_concurrent: 3     # Maximum concurrent command executions
  default_timeout: 60   # Default command timeout in seconds
  script_timeout: 300   # Maximum script execution time
```

---

## Monitoring Heartbeat Health

### Dashboard View

The Mission Control dashboard shows real-time agent status:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/dashboard/agent-status
```

```json
{
  "status": "success",
  "data": {
    "total": 45,
    "online": 42,
    "degraded": 1,
    "offline": 2,
    "agents": [
      {
        "id": "agt_x1y2z3",
        "name": "Server Agent 01",
        "status": "online",
        "last_heartbeat": "2026-07-26T10:30:00Z",
        "heartbeat_latency_ms": 45,
        "site_name": "Cape Town DC"
      }
    ]
  }
}
```

### Log Analysis

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/logs?source=heartbeat&level=warning&limit=50"
```

---

## Related Documentation

- [REST_API.md](./REST_API.md) — Agent API endpoints
- [AUTHENTICATION.md](./AUTHENTICATION.md) — API key authentication
- [WEBHOOKS.md](./WEBHOOKS.md) — Webhook events for heartbeat failures
- [DEPLOYMENT_DOCKER.md](./DEPLOYMENT_DOCKER.md) — Server deployment
