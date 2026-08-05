# Mission Control Edge Proxy Deployment Guide

Mission Control uses a **Zabbix-like Server/Proxy/Target topology**:

- **GCE Backend** = Zabbix Server: central config, data storage, API, and web UI
- **Edge Agents** = Zabbix Proxies: lightweight outbound-only collectors with local SQLite buffering
- **Target Hosts** = monitored devices: no Mission Control software installed

## Architecture

```
[Target Hosts] <--SSH/REST/Agentless--> [Edge Proxy/Agent] <--HTTPS--> [GCE Server]
    192.168.10.49                       CORHQROBERTB                 34.35.177.209
    192.168.10.15                       (offline-first)               (source of truth)
```

## Prerequisites

- Windows Server 2019+ or Linux with systemd
- Outbound HTTPS to `missioncontrol.optichosting.co.za:443`
- Outbound SSH/WinRM from proxy to target networks
- Agent ID and API key from GCE backend

## Files

All files are hosted on GCE at `/home/billboe3/`:

```
/home/billboe3/agent-bundle-live.zip    # Agent runtime bundle
/home/billboe3/install-agent.ps1        # Windows one-click installer
/home/billboe3/reinstall-edge-agent.sh  # Linux reinstall script
```

## Windows Deployment

### Option A: One-Click Installer (Recommended)

Run PowerShell as Administrator on the proxy host:

```powershell
# Download installer
curl.exe -k -L -o C:\MissionControlAgent\install-agent.ps1 https://missioncontrol.optichosting.co.za/install-agent.ps1

# Run installer
powershell -ExecutionPolicy Bypass -File C:\MissionControlAgent\install-agent.ps1 -AgentId <AGENT_ID> -ApiKey "<API_KEY>"
```

Parameters:
- `-AgentId`: Numeric agent ID from backend
- `-ApiKey`: Agent API key from backend
- `-PythonPath`: Optional, defaults to Hermes venv Python
- `-WorkDir`: Optional, defaults to `C:\MissionControlAgent`

### Option B: Manual Steps

```powershell
# 1. Create work directory
New-Item -Path C:\MissionControlAgent -ItemType Directory -Force | Out-Null

# 2. Download bundle
curl.exe -k -L -X POST -o C:\MissionControlAgent\agent-bundle-live.zip https://missioncontrol.optichosting.co.za/api/v1/agents/<AGENT_ID>/bundles/download?t=$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())

# 3. Extract bundle
& '<PYTHON_PATH>' -c "import zipfile; zipfile.ZipFile('C:/MissionControlAgent/agent-bundle-live.zip').extractall('C:/MissionControlAgent')"

# 4. Write config.yaml
[System.IO.File]::WriteAllText('C:\MissionControlAgent\config.yaml', @"
server_url: https://missioncontrol.optichosting.co.za
verify_ssl: false
agent_id: <AGENT_ID>
api_key: <API_KEY>
data_dir: C:\MissionControlAgent\data
config_dir: C:\MissionControlAgent
"@)

# 5. Create scheduled task
$action = New-ScheduledTaskAction -Execute '<PYTHON_PATH>' -Argument '-m agent.edge_main' -WorkingDirectory 'C:\MissionControlAgent'
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Seconds 0)
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName 'MissionControlEdgeAgent' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force

# 6. Run and verify
schtasks /Run /TN "MissionControlEdgeAgent"
Start-Sleep -Seconds 20
python C:\MissionControlAgent\check_sync.py
```

### Restart Task Later

```powershell
schtasks /End /TN "MissionControlEdgeAgent"
schtasks /Run /TN "MissionControlEdgeAgent"
```

## Linux Deployment

```bash
# Download reinstall script
curl -k -L -o /tmp/reinstall-edge-agent.sh https://missioncontrol.optichosting.co.za/reinstall-edge-agent.sh
chmod +x /tmp/reinstall-edge-agent.sh

# Run as root
sudo /tmp/reinstall-edge-agent.sh --agent-id <AGENT_ID> --api-key "<API_KEY>"
```

Or manually:

```bash
mkdir -p /opt/mission-control-agent
cd /opt/mission-control-agent

# Download bundle
curl -k -L -X POST -o agent-bundle-live.zip https://missioncontrol.optichosting.co.za/api/v1/agents/<AGENT_ID>/bundles/download?t=$(date +%s)

# Extract
python3 -c "import zipfile; zipfile.ZipFile('agent-bundle-live.zip').extractall('.')"

# Write config
cat > config.yaml << 'EOF'
server_url: https://missioncontrol.optichosting.co.za
verify_ssl: false
agent_id: <AGENT_ID>
api_key: <API_KEY>
data_dir: /opt/mission-control-agent/data
config_dir: /opt/mission-control-agent
EOF

# Install systemd service
cp .agents/packaging/mc-edge-agent.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable mc-edge-agent
systemctl start mc-edge-agent

# Verify
journalctl -u mc-edge-agent -f
```

## Verification

After deployment, verify the proxy is reporting:

```powershell
# Windows
python C:\MissionControlAgent\check_sync.py

# Linux
python3 /opt/mission-control-agent/check_sync.py
```

Expected output:
```
Total rows: <increasing>
Latest timestamp: <current UTC time>
id=<n> dir=push-heartbeat endpoint=https://missioncontrol.optichosting.co.za/api/v1/edge/<id>/heartbeat status=200 error=
id=<n> dir=push-inventory endpoint=https://missioncontrol.optichosting.co.za/api/v1/edge/<id>/inventory status=200 error=
id=<n> dir=pull-config endpoint=https://missioncontrol.optichosting.co.za/api/v1/edge/<id>/config status=200 error=
```

## Backend Configuration

### 1. Create Agent in Backend

Via UI: **Settings → Agents → Add Agent**

Or via API:

```bash
curl -k -X POST https://missioncontrol.optichosting.co.za/api/v1/agents \
  -H "Authorization: Bearer <ADMIN_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"name":"CORHQROBERTB","platform":"windows","ip_address":"192.168.11.137"}'
```

### 2. Add Remote Targets

Targets define what the proxy can reach:

```bash
curl -k -X POST https://missioncontrol.optichosting.co.za/api/v1/agents/1/remote-targets \
  -H "Authorization: Bearer <ADMIN_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CORHQVEEAM",
    "hostname": "192.168.10.49",
    "protocol": "ssh",
    "port": 22,
    "username": "kg\\administrator",
    "tags": "Veeam"
  }'
```

### 3. Add Integration Profiles

Integration profiles store credentials the proxy uses to collect data:

```bash
curl -k -X POST https://missioncontrol.optichosting.co.za/api/v1/integration-profiles \
  -H "Authorization: Bearer <ADMIN_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Veeam B&R Server",
    "integration_type": "veeam",
    "base_url": "https://192.168.10.49:9419",
    "username": "kg\\administrator",
    "password": "<PASSWORD>",
    "ssh_host": "192.168.10.49",
    "ssh_port": 22,
    "ssh_username": "kg\\administrator",
    "ssh_password": "<PASSWORD>",
    "verify_ssl": false
  }'
```

## Topology Visualization

View the Server → Proxy → Target hierarchy in the web UI:

**Fleet Workspace → Topology** (`/agents/topology`)

This page renders:
- **Server node** (GCE backend)
- **Proxy nodes** (deployed edge agents)
- **Target nodes** (remote hosts reachable via each proxy)

## Troubleshooting

### Agent not syncing

```powershell
# Check task status
schtasks /Query /TN "MissionControlEdgeAgent" /FO LIST

# Check manually
python C:\MissionControlAgent\check_sync.py

# View event logs
Get-EventLog -LogName System -Source "Service Control Manager" -Newest 5
```

### Veeam plugin returns empty data

The Veeam PowerShell module may not load in non-interactive SSH sessions. Check if the module is available:

```powershell
ssh kg\administrator@192.168.10.49 "powershell -NoProfile -NonInteractive -Command 'Import-Module Veeam.Backup.PowerShell; Get-VBRJob | Select-Object -First 1 | ConvertTo-Json -Compress'"
```

If `Import-Module` fails, use the full module path:

```powershell
ssh kg\administrator@192.168.10.49 "powershell -NoProfile -NonInteractive -Command 'Import-Module \"C:\Program Files\Veeam\Backup and Replication\Console\Veeam.Backup.PowerShell.psd1\"; Get-VBRJob | Select-Object -First 1 | ConvertTo-Json -Compress'"
```

### Stuck service in deletion queue

```powershell
# Force delete via registry
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\MissionControlEdgeAgent" /f

# Reboot if still stuck
shutdown /r /t 10
```

### SSL/TLS issues

- GCE nginx uses RSA certificates for Windows Schannel compatibility
- Set `verify_ssl: false` in `config.yaml` for self-signed certs
- Public IP `34.35.177.209` must be used, not private `10.218.0.4`

## Next Proxy Deployment Checklist

- [ ] Create agent record in backend with unique `AgentId`
- [ ] Generate API key for the agent
- [ ] Download `agent-bundle-live.zip` and `install-agent.ps1` from GCE
- [ ] Run installer on proxy host
- [ ] Verify sync log shows `status=200`
- [ ] Add remote targets for networks behind this proxy
- [ ] Add integration profiles for services on those targets
- [ ] Verify topology page shows new proxy and its targets
