# Agent Deployment

**Version:** 3.0.0

The Mission Control agent is a lightweight Python 3.12 daemon with no external dependencies beyond the Python standard library. It runs on managed hosts and communicates with the API server via API key authentication.

---

## System Requirements

| Resource | Minimum |
|---|---|
| Python | 3.12+ |
| RAM | 50 MB |
| Disk | 10 MB |
| Network | Access to API server on port 8000 |

---

## Agent Installation

### Windows (PowerShell)

```powershell
# Download the agent
Invoke-WebRequest -Uri "https://releases.missioncontrol.example.com/agent/latest/mission-control-agent.zip" -OutFile "$env:TEMP\mc-agent.zip"

# Extract to Program Files
Expand-Archive -Path "$env:TEMP\mc-agent.zip" -DestinationPath "C:\Program Files\MissionControlAgent" -Force

# Install as Windows Service
& "C:\Program Files\MissionControlAgent\mc-agent.exe" install

# Start the service
& "C:\Program Files\MissionControlAgent\mc-agent.exe" start
```

### Linux (bash)

```bash
# Download the agent
curl -fsSL https://releases.missioncontrol.example.com/agent/latest/mission-control-agent.tar.gz -o /tmp/mc-agent.tar.gz

# Extract and install
sudo mkdir -p /opt/mission-control-agent
sudo tar -xzf /tmp/mc-agent.tar.gz -C /opt/mission-control-agent

# Create config directory
mkdir -p ~/.config/mission-control-agent

# Install as systemd service
sudo cp /opt/mission-control-agent/mission-control-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mission-control-agent
```

---

## Configuration File

The agent configuration is stored at `~/.config/mission-control-agent/config.yaml`:

```yaml
# Mission Control Agent Configuration
server:
  # API server URL
  url: "https://control.example.com"

  # API key for authentication (obtained from the dashboard)
  api_key: "mc_api_key_your_key_here"

  # Company and site assignment
  company_id: 1
  site_id: 1

agent:
  # Unique identifier for this agent (auto-generated if omitted)
  id: "agent-prod-01"

  # Display name
  name: "Production Server 01"

  # Tags for grouping and filtering
  tags:
    - "production"
    - "web-server"
    - "us-east-1"

  # How often to send heartbeats (seconds)
  heartbeat_interval: 30

  # Agent listen port for plugin communication
  listen_port: 9100

logging:
  # Log level: debug, info, warning, error
  level: "info"

  # Log file path (empty for stdout only)
  file: "/var/log/mission-control-agent/agent.log"

  # Maximum log file size before rotation (MB)
  max_size: 50

  # Number of rotated log files to keep
  max_files: 5

remote:
  # Enable SSH connections
  ssh_enabled: true

  # Enable WinRM connections
  winrm_enabled: false

  # Maximum concurrent remote sessions
  max_sessions: 10

  # SSH key path for remote connections
  ssh_key_path: "~/.ssh/id_rsa"

proxy:
  # Enable offline mode — queue commands when server is unreachable
  offline_mode: true

  # Maximum queued commands in offline mode
  max_queue_size: 1000

  # Retry interval when reconnecting (seconds)
  retry_interval: 60
```

---

## Agent Registration

### Step 1: Generate an API Key

```bash
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "agent-prod-01", "expires_days": 365}'
```

The response includes the key value. Store it securely — it is shown only once.

### Step 2: Configure the Agent

Set the `api_key` in the agent's `config.yaml` to the value from Step 1.

### Step 3: Start the Agent

```bash
# Linux
sudo systemctl start mission-control-agent

# Windows
& "C:\Program Files\MissionControlAgent\mc-agent.exe" start
```

### Step 4: Verify Registration

Check the dashboard under **Sites → [Your Site] → Agents**. The new agent should appear with a status of **Online**.

Alternatively, check via API:

```bash
curl http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer <admin-token>"
```

---

## API Key Authentication

All agent-to-server communication is authenticated via API keys sent in the `X-API-Key` header:

```
X-API-Key: mc_api_key_your_key_here
```

API keys are scoped to a company and can optionally be scoped to a specific agent. Keys can be:

- Created with an expiration date
- Revoked immediately
- Listed and managed from **Settings → API Keys**

```bash
# Revoke a compromised key
curl -X DELETE http://localhost:8000/api/v1/api-keys/3 \
  -H "Authorization: Bearer <admin-token>"
```

---

## Heartbeat

Agents send heartbeat signals to the API server at the configured interval (default: 30 seconds). The heartbeat includes:

- Agent status (online/degraded/offline)
- System metrics (CPU, memory, disk)
- Plugin status
- Uptime

If the server does not receive a heartbeat within 3x the configured interval (90 seconds default), the agent is marked as **Offline** in the dashboard.

See [Monitoring](MONITORING.md) for health endpoint details and [Troubleshooting](TROUBLESHOOTING.md) for heartbeat issues.

---

## Agent Updates

### Manual Update

```bash
# Linux
sudo systemctl stop mission-control-agent
curl -fsSL https://releases.missioncontrol.example.com/agent/latest/mission-control-agent.tar.gz -o /tmp/mc-agent.tar.gz
sudo tar -xzf /tmp/mc-agent.tar.gz -C /opt/mission-control-agent
sudo systemctl start mission-control-agent
```

### Auto-Update

Configure auto-update in `config.yaml`:

```yaml
updates:
  auto_update: true
  check_interval: 3600  # Check every hour
  channel: "stable"     # stable or beta
```

When auto-update is enabled, the agent checks for new versions at the configured interval and downloads updates automatically. Updates are applied on the next agent restart.

---

## Offline Mode

When the API server is unreachable, the agent enters offline mode if `offline_mode: true` is configured. In offline mode:

1. Remote commands are queued locally (up to `max_queue_size`).
2. Heartbeats continue attempting to reconnect.
3. When connectivity is restored, queued commands are executed and results are sent to the server.

Offline mode is useful for agents on intermittent networks or during server maintenance windows.

---

## Troubleshooting

### Agent Won't Start

```bash
# Check agent logs
tail -f /var/log/mission-control-agent/agent.log

# Verify config syntax
python3 -c "import yaml; yaml.safe_load(open('/root/.config/mission-control-agent/config.yaml'))"

# Test API connectivity
curl -H "X-API-Key: your_key_here" http://control.example.com/api/v1/health
```

### Agent Shows Offline

1. Check network connectivity from the agent host to the API server.
2. Verify the API key is valid and not expired.
3. Check that the agent's `company_id` and `site_id` match a valid company and site.
4. Review agent logs for connection errors.

### Commands Not Executing

1. Verify remote access is enabled in the agent config.
2. Check SSH/WinRM credentials and connectivity.
3. Review the `max_sessions` limit.
4. Check `REMOTE_MAX_COMMAND_TIMEOUT` on the server.

See [Troubleshooting](TROUBLESHOOTING.md) for comprehensive diagnostic procedures.
