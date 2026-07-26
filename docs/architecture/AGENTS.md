# Mission Control — Agents

**Version:** 3.0.0

---

## Overview

Agents are lightweight, self-updating processes that run on managed infrastructure. They collect data, execute commands, and report to the server. The server never initiates connections to agents.

---

## 1. Agent Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Agent Process                     │
│  Python 3.12 · No external dependencies             │
│-----------------------------------------------------│
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Orchestrator │  │   Client     │  │  Config    │ │
│  │  (agent.py)  │  │ (client.py)  │  │(config.py) │ │
│  └──────┬──────┘  └──────────────┘  └────────────┘ │
│         │                                            │
│  ┌──────┴──────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Heartbeat   │  │  Inventory   │  │  Executor  │ │
│  │(heartbeat.py)│  │(inventory.py)│  │(executor.py)│ │
│  └─────────────┘  └──────────────┘  └────────────┘ │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Command     │  │   Remote     │  │  Updater   │ │
│  │ Queue       │  │  Manager     │  │            │ │
│  │(command_q.py)│  │ (remote.py)  │  │(updater.py)│ │
│  └─────────────┘  └──────────────┘  └────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │              Plugin System                       │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │ │
│  │  │ Windows  │ │  Linux   │ │  Docker  │  ...   │ │
│  │  │ Plugin   │ │  Plugin  │ │  Plugin  │        │ │
│  │  └──────────┘ └──────────┘ └──────────┘        │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │              Connectors (fallback)               │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │ │
│  │  │   SSH    │ │  WinRM   │ │PS Remoting│        │ │
│  │  └──────────┘ └──────────┘ └──────────┘        │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 2. Agent Files

### Core

| File | Purpose |
|------|---------|
| `agent.py` | Main orchestrator, lifecycle management |
| `client.py` | HTTP client for server communication |
| `config.py` | Configuration loading and validation |
| `heartbeat.py` | Heartbeat loop implementation |
| `inventory.py` | System inventory collection |
| `executor.py` | Command execution engine |
| `command_queue.py` | Offline command queue management |
| `remote.py` | Remote target relay management |
| `registration.py` | Agent registration with server |
| `updater.py` | Self-update mechanism |
| `logger.py` | Logging configuration |

### Connectors (Fallback)

| File | Purpose |
|------|---------|
| `connectors/base.py` | Abstract connector interface |
| `connectors/ssh.py` | SSH command execution |
| `connectors/winrm_connector.py` | WinRM command execution |
| `connectors/psremoting.py` | PowerShell Remoting execution |

### Plugins

| File | Purpose |
|------|---------|
| `plugins/windows_plugin.py` | Windows system, services, events |
| `plugins/linux_plugin.py` | Linux system, services, journal |
| `plugins/docker_plugin.py` | Docker container monitoring |
| `plugins/hyperv_plugin.py` | Hyper-V VM relay |
| `plugins/zabbix_plugin.py` | Zabbix proxy relay |
| `plugins/ad_plugin.py` | Active Directory collection |
| `plugins/m365_plugin.py` | Microsoft 365 collection |

---

## 3. Agent Services

### Heartbeat

Sends periodic heartbeats to the server with health and metrics.

**Interval:** Configurable (default: 30 seconds)

**Payload:**

```json
{
  "health": "healthy",
  "cpu_percent": 45.2,
  "memory_percent": 62.1,
  "disk_percent": 38.0,
  "agent_version": "3.0.0",
  "active_plugins": "windows,docker"
}
```

**Response:**

```json
{
  "commands": [
    {
      "id": 1,
      "command_type": "powershell",
      "command": "Get-Service",
      "timeout": 300
    }
  ],
  "heartbeat_interval": 30,
  "remote_targets": [
    {
      "id": 1,
      "hostname": "dc01",
      "protocol": "psremoting",
      "username": "admin",
      "password": "..."
    }
  ]
}
```

### Inventory

Collects system inventory on startup and on change.

**Data collected:**

- Operating system (name, version, architecture)
- Hardware (CPU, memory, disks, network adapters)
- Installed software
- Running services
- Network configuration

### Metrics

Reports system metrics with each heartbeat:

- CPU usage (%)
- Memory usage (%)
- Disk usage (%)
- Network I/O (future)

### Health

Reports health status:

| Status | Description |
|--------|-------------|
| `healthy` | All checks passing |
| `warning` | Non-critical issues detected |
| `critical` | Critical issues require attention |

---

## 4. Command Execution

Commands are executed through the executor module.

### Execution Flow

```
1. Receive command from heartbeat response
2. Validate command (type, timeout)
3. Execute via appropriate method:
   - PowerShell (Windows)
   - Bash (Linux)
   - Plugin-specific execution
4. Capture stdout, stderr, exit_code
5. Report result on next heartbeat
```

### Command Types

| Type | Method | Platform |
|------|--------|----------|
| `powershell` | PowerShell execution | Windows |
| `bash` | Bash script execution | Linux |
| `plugin` | Plugin-specific execution | Any |

---

## 5. Plugin Loading

Agents dynamically load plugins based on configuration.

### Plugin Discovery

```python
# config.yaml
plugins:
  - windows      # System collection
  - docker       # Container monitoring
  - hyperv       # VM relay
```

### Plugin Lifecycle

```
1. Load plugin module
2. Validate plugin interface
3. Call plugin.initialize()
4. Plugin starts collecting data
5. Plugin data included in inventory/metrics
```

---

## 6. Offline Mode

When the server is unreachable, the agent operates in offline mode.

### Behavior

- Continues collecting inventory and metrics
- Queues commands and events locally
- Retries connection with exponential backoff
- Sends queued data on reconnect

### Offline Queue

```python
# Stored locally
~/.mission-control-agent/queue/
  ├── commands/
  ├── events/
  └── inventory/
```

---

## 7. Remote Target Relay

Agents can relay data from remote machines they can reach.

### Use Case

Agent on network A can reach:
- Server (via HTTPS)
- Switch A1 (via SSH)
- Firewall A1 (via SSH)

Agent relays data from Switch A1 and Firewall A1 to the server.

### Configuration

```yaml
# Server assigns remote targets via heartbeat response
remote_targets:
  - id: 1
    hostname: switch01
    protocol: ssh
    port: 22
    username: admin
    password: encrypted...
```

---

## 8. Security

### API Key Authentication

Every request to the server includes the API key:

```
X-Agent-API-Key: mc_agent_...
```

### Minimal Privileges

Agents run with minimal system privileges:

- Windows: Standard user (not admin) for collection; admin for service management
- Linux: Standard user for collection; root for service management

### Encrypted Communication

All agent-server communication uses HTTPS/TLS.

---

## 9. Self-Update

Agents can update themselves from the server.

### Process

```
1. Server includes update command in heartbeat response
2. Agent downloads update package
3. Agent verifies package signature
4. Agent stops current version
5. Agent installs update
6. Agent starts new version
7. Agent registers with server
```

---

## 10. Installation

### Windows

```powershell
.\install-agent.ps1 `
  -ServerUrl https://mc.example.com `
  -AgentName "web01" `
  -CompanyName "Acme Corp" `
  -SiteName "Production"
```

### Linux

```bash
sudo ./install-agent-linux.sh \
  --server https://mc.example.com \
  --name web01 \
  --company "Acme Corp" \
  --site "Production"
```

### Configuration File

```yaml
# ~/.config/mission-control-agent/config.yaml
server_url: https://mc.example.com
agent_name: web01
company_name: Acme Corp
site_name: Production
api_key: mc_agent_...
heartbeat_interval: 30
plugins:
  - windows
  - docker
```
