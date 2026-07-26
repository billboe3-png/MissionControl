# Mission Control — Heartbeat

**Version:** 3.0.0

---

## Overview

The heartbeat is the primary communication channel between agents and the server. Every 30 seconds, each agent sends a heartbeat containing health and metrics. The server responds with pending commands and remote targets.

---

## 1. Protocol

```
Agent                                          Server
  |                                              |
  |  POST /api/v1/agents/{id}/heartbeat          |
  |  Content-Type: application/json              |
  |  X-Agent-API-Key: mc_agent_...               |
  |                                              |
  |  {                                            |
  |    health: "healthy",                         |
  |    cpu_percent: 45.2,                         |
  |    memory_percent: 62.1,                      |
  |    disk_percent: 38.0,                        |
  |    agent_version: "3.0.0",                    |
  |    active_plugins: "windows,docker"           |
  |  }                                            |
  |──────────────────────────────────────────────>|
  |                                               |
  |  Response: 200 OK                             |
  |  {                                            |
  |    commands: [...],                           |
  |    heartbeat_interval: 30,                    |
  |    remote_targets: [...]                      |
  |  }                                            |
  |<──────────────────────────────────────────────|
  |                                               |
```

---

## 2. Heartbeat Interval

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `heartbeat_interval` | 30s | 10-300s | Seconds between heartbeats |

The server can adjust the interval via the heartbeat response.

---

## 3. Authentication

Every heartbeat is authenticated via API key.

**Header:**

```
X-Agent-API-Key: mc_agent_<64_hex_chars>
```

**Server validation:**

1. Extract API key from header
2. Hash with SHA-256
3. Compare against stored hash in `agents` table
4. If match → process heartbeat
5. If no match → return 401 Unauthorized

---

## 4. Heartbeat Payload

### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `health` | string | Yes | Agent health status |
| `cpu_percent` | float | No | CPU usage percentage |
| `memory_percent` | float | No | Memory usage percentage |
| `disk_percent` | float | No | Disk usage percentage |
| `agent_version` | string | No | Current agent version |
| `active_plugins` | string | No | Comma-separated plugin names |

### Health Values

| Value | Meaning |
|-------|---------|
| `healthy` | All checks passing |
| `warning` | Non-critical issues |
| `critical` | Critical issues require attention |

---

## 5. Heartbeat Response

### Commands

Pending commands for the agent to execute.

```json
{
  "commands": [
    {
      "id": 1,
      "command_type": "powershell",
      "command": "Get-Service",
      "timeout": 300,
      "file_path": null,
      "file_name": null,
      "file_content_b64": null
    }
  ]
}
```

### Remote Targets

Machines the agent should relay data from.

```json
{
  "remote_targets": [
    {
      "id": 1,
      "name": "DC01",
      "hostname": "dc01.corp.local",
      "protocol": "psremoting",
      "port": 5985,
      "username": "admin",
      "password": "decrypted-password"
    }
  ]
}
```

### Heartbeat Interval

Server can adjust the agent's heartbeat frequency.

```json
{
  "heartbeat_interval": 30
}
```

---

## 6. Processing Pipeline

The heartbeat service processes each heartbeat through a pipeline:

```
1. Authenticate agent (API key)
2. Fetch agent from database
3. Update agent status → "online"
4. Update agent metrics (CPU, memory, disk)
5. Update agent health
6. Update agent version
7. Update agent active plugins
8. Update state engine
9. Publish HEARTBEAT_RECEIVED event
10. Publish AGENT_ONLINE event (if transition)
11. Fetch pending commands
12. Mark commands as "dispatched"
13. Publish COMMAND_DISPATCHED events
14. Fetch remote targets
15. Return response
```

---

## 7. Offline Detection

Agents are considered offline if no heartbeat is received within the threshold.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `OFFLINE_THRESHOLD_SECONDS` | 120s | Seconds before marking agent offline |

### Detection Process

```
Every heartbeat:
  1. Update agent.last_heartbeat = now
  2. Update state engine

State engine refresh:
  1. For each agent:
     a. Check agent.enabled
     b. Check agent.last_heartbeat
     c. If (now - last_heartbeat) > OFFLINE_THRESHOLD → mark offline
  2. Publish AGENT_OFFLINE event
```

---

## 8. State Transitions

```
                    ┌──────────┐
         ┌────────>│  Online   │<────────┐
         │         └────┬─────┘         │
         │              │               │
         │   Heartbeat  │  No heartbeat │
         │   received   │  for 120s     │
         │              │               │
    ┌────┴─────┐        │        ┌──────┴────┐
    │ Disabled │        v        │  Offline   │
    └──────────┘   ┌────────┐   └───────────┘
                   │Warning │
                   │/Unhealthy│
                   └────────┘
```

---

## 9. Retry Behavior

### Agent Side

If the heartbeat request fails:

1. Wait for next interval (default: 30s)
2. Retry on next interval
3. Continue operating normally
4. Queue results locally if offline

### Server Side

If heartbeat processing fails:

1. Log the error
2. Return 500 Internal Server Error
3. Agent retries on next interval
4. No data loss (agent queues locally)

---

## 10. Version Checks

The heartbeat includes the agent version. The server can:

1. Compare against `MIN_AGENT_VERSION`
2. Return update command if outdated
3. Log version mismatch

```json
// Server response with update command
{
  "commands": [
    {
      "command_type": "update",
      "command": "https://mc.example.com/api/v1/agents/update?version=3.1.0"
    }
  ]
}
```
