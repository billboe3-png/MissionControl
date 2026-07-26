# Mission Control — Data Flow

**Version:** 3.0.0

---

## Overview

Data in Mission Control flows through well-defined channels. The server never initiates connections to agents — all data collection is agent-driven.

---

## 1. Heartbeat Flow

The primary communication channel. Every 30 seconds, each agent sends a heartbeat.

```
Agent                                          Server
  |                                              |
  |  POST /api/v1/agents/{id}/heartbeat          |
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
  |                    Heartbeat Service          |
  |                    ├── Authenticate agent     |
  |                    ├── Update agent status    |
  |                    ├── Update state engine    |
  |                    ├── Publish HEARTBEAT_RECEIVED
  |                    ├── Fetch pending commands  |
  |                    └── Fetch remote targets    |
  |                                               |
  |  <─────────────────────────────────────────── |
  |  {                                            |
  |    commands: [                                |
  |      { id: 1, type: "powershell",             |
  |        command: "Get-Service" }               |
  |    ],                                         |
  |    heartbeat_interval: 30,                    |
  |    remote_targets: [                          |
  |      { id: 1, hostname: "dc01",               |
  |        protocol: "psremoting" }               |
  |    ]                                          |
  |  }                                            |
  |                                               |
```

---

## 2. Inventory Flow

Agents collect inventory data and push it to the server.

```
Agent                                          Server
  |                                              |
  |  System change detected                      |
  |  (new service, IP change, etc.)              |
  |                                              |
  |  POST /api/v1/agents/{id}/inventory          |
  |  {                                            |
  |    hostname: "web01",                         |
  |    os: "Windows Server 2022",                 |
  |    services: [...],                           |
  |    software: [...],                           |
  |    network: [...]                             |
  |  }                                            |
  |──────────────────────────────────────────────>|
  |                                               |
  |                    Agent Service              |
  |                    ├── Update agent record    |
  |                    ├── Store inventory        |
  |                    └── Publish INVENTORY_UPDATED
  |                                               |
  |  Dashboard                                    |
  |  ── GET /api/v1/agents/{id}/inventory         |
  |  <─────────────────────────────────────────── |
  |  { inventory data }                           |
  |                                               |
```

---

## 3. Command Execution Flow

Commands are queued by the server and delivered on the next heartbeat.

```
User / Automation / API
  |
  |  POST /api/v1/agents/{id}/commands
  |  { type: "powershell", command: "Get-Process" }
  |
  v
Agent Service
  ├── Create command record (status: queued)
  └── Publish COMMAND_QUEUED
          |
          v
    Next Agent Heartbeat
          |
          v
    Heartbeat Response includes command
          |
          v
Agent receives command
  ├── Execute via PowerShell/Bash
  ├── Collect stdout/stderr/exit_code
  └── POST result to server
          |
          v
    Agent Service
    ├── Update command (status: completed)
    └── Publish COMMAND_COMPLETED
          |
          v
    Dashboard / API shows result
```

---

## 4. Automation Flow

Playbook execution follows a multi-step process.

```
User triggers playbook
  |
  v
Automation Service
  ├── Validate playbook and steps
  ├── Check approval requirements
  ├── Create execution record (status: running)
  └── Publish AUTOMATION_STARTED
          |
          v
    For each step:
    ├── Resolve variables
    ├── Check conditionals
    ├── Execute step (agent command / HTTP / script)
    ├── Record result
    └── Continue or abort
          |
          v
    Execution complete
    ├── Update execution record
    ├── Publish AUTOMATION_COMPLETED
    └── Record in audit trail
```

---

## 5. Dashboard Request Flow

The dashboard aggregates data from all domain services in a single request.

```
Browser
  |
  |  GET /api/v1/dashboard
  |  Authorization: Bearer <jwt>
  |
  v
Dashboard Router
  |
  v
DashboardService.get_dashboard()
  ├── health_provider.get_health(db)
  ├── project_provider.get_project_data(db)
  ├── task_provider.get_task_data(db)
  ├── note_provider.get_note_data(db)
  ├── agent_service.get_dashboard_summary(db)
  ├── automation_service.get_automation_summary(db)
  ├── integration_service.get_dashboard_summary(db)
  ├── ai_service.get_overview(db)
  ├── zabbix.provider_factory.get_summary()
  ├── hyperv.provider_factory.get_summary()
  └── proxmox.provider_factory.get_summary()
          |
          v
    Single aggregated response
    {
      application: {...},
      summary: {...},
      health: {...},
      agents: {...},
      automation: {...},
      ...
    }
```

---

## 6. Plugin Event Flow

Plugins publish and subscribe to events through the event bus.

```
Plugin publishes event
  |
  |  await event_bus.publish(Event(
  |    type=EventType.BACKUP_SUCCEEDED,
  |    data={"job_id": 1, "duration": 120},
  |    source="veeam_plugin"
  |  ))
  |
  v
Event Bus
  ├── Route to all subscribers of BACKUP_SUCCEEDED
  ├── Execute handlers concurrently
  └── Log failures (no crash)
          |
          v
    Handler 1: Update dashboard cache
    Handler 2: Send notification
    Handler 3: Record in audit trail
```

---

## 7. AI Analysis Flow

AI operations analyze infrastructure data for insights.

```
Dashboard / API request
  |
  v
AI Service
  ├── Collect data from agents, Zabbix, Veeam
  ├── Correlate alerts across sources
  ├── Classify incidents by severity
  ├── Generate recommendations
  ├── Calculate confidence scores
  └── Return analysis results
          |
          v
    Dashboard displays:
    ├── Health Score (0-100)
    ├── Critical Incidents
    ├── Recommendations
    ├── Correlated Alerts
    └── Top Risks
```

---

## 8. Authentication Flow

```
Login Request
  |
  |  POST /api/v1/auth/login
  |  { username: "admin", password: "..." }
  |
  v
Auth Service
  ├── Validate credentials (bcrypt)
  ├── Generate JWT access token
  ├── Generate refresh token
  └── Return tokens
          |
          v
    Client stores tokens
          |
          v
    Subsequent requests
    Authorization: Bearer <access_token>
          |
          v
    Auth Dependency
    ├── Validate JWT signature
    ├── Check expiry
    ├── Extract user_id, company_id
    └── Inject into request state
```

---

## 9. Agent Registration Flow

```
New Agent
  |
  |  POST /api/v1/agents/register
  |  { name, hostname, os, api_key }
  |
  v
Agent Service
  ├── Validate API key
  ├── Create/update agent record
  ├── Generate API key (if new)
  └── Return agent_id + API key
          |
          v
    Agent stores credentials
    Agent starts heartbeat loop
```

---

## 10. Remote Operations Flow (Agent-First)

```
User executes command on remote host
  |
  v
Remote Service
  ├── Check for online agent with remote target
  │     ├── Agent found → Queue command for agent
  │     │                    Agent executes via local connector
  │     │                    Result returned on next heartbeat
  │     └── No agent → Fallback to direct SSH/WinRM
  │
  └── Return result to user
```
