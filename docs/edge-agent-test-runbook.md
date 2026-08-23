# Mission Control Edge Agent - Test Runbook

## Local Linux Server Reinstall

### Prerequisites
- Always-on Linux server with internet access
- SSH access to the server
- sudo privileges

### Step 1: Prepare local server
```bash
ssh user@local-server
sudo mkdir -p /opt/mc-agent
sudo useradd -r -s /bin/false mc-agent || true
sudo chown mc-agent:mc-agent /opt/mc-agent
```

### Step 2: Download edge agent package
```bash
cd /opt/mc-agent
curl -k https://missioncontrol.optichosting.co.za/api/v1/agents/debug/install-agent.bat -o install.sh
chmod +x install.sh
```

### Step 3: Install dependencies
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip
```

### Step 4: Install agent
```bash
cd /opt/mc-agent
sudo -u mc-agent python3.11 -m venv venv
source venv/bin/activate
pip install httpx psutil pydantic pydantic-settings pyyaml packaging
```

### Step 5: Configure agent
Create `/etc/mc-agent/config.yaml`:
```yaml
server_url: https://missioncontrol.optichosting.co.za
agent_id: 1
api_key: <AGENT_API_KEY>
heartbeat_interval: 60
inventory_interval: 120
verify_ssl: true
log_level: INFO
data_dir: /var/lib/mc-agent
```

### Step 6: Install systemd service
```bash
sudo cp .agents/packaging/mc-edge-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mc-edge-agent
```

### Step 7: Verify installation
```bash
sudo systemctl status mc-edge-agent
journalctl -u mc-edge-agent -f
```

### Step 8: Test config pull
```bash
curl -k -H "X-Agent-API-Key: <AGENT_API_KEY>" \
  https://missioncontrol.optichosting.co.za/api/v1/edge/1/config
```

---

## Windows Reinstall with .exe Installer

### Prerequisites
- Windows 10/11 Server
- Administrator access
- Python 3.11+ will be installed by the EXE

### Step 1: Download installer
Download `mc-edge-agent-setup.exe` from:
```
https://missioncontrol.optichosting.co.za/api/v1/agents/debug/mc-edge-agent-setup.exe
```

### Step 2: Run installer
1. Double-click `mc-edge-agent-setup.exe`
2. Accept UAC prompt
3. Enter server URL: `https://missioncontrol.optichosting.co.za`
4. Enter agent name (defaults to computer name)
5. Click "Install"

### Step 3: Verify service
```powershell
Get-Service -Name "MissionControlEdgeAgent"
# or
sc.exe qc MissionControlEdgeAgent
```

### Step 4: Check logs
```powershell
Get-Content "C:\Program Files\MC Edge Agent\logs\agent.log" -Tail 20
# or
Get-Content "C:\Program Files\MC Edge Agent\logs\service-stdout.log" -Tail 20
```

---

## Testing Checklist

### Backend Verification
- [ ] Backend healthy: `curl https://missioncontrol.optichosting.co.za/api/v1/health/live`
- [ ] Edge config endpoint responds: `curl -H "X-Agent-API-Key: <KEY>" https://missioncontrol.optichosting.co.za/api/v1/edge/1/config`
- [ ] Edge inventory endpoint accepts data: `POST /api/v1/edge/1/inventory`

### Edge Agent Verification
- [ ] Service running: `systemctl status mc-edge-agent` or `Get-Service MissionControlEdgeAgent`
- [ ] Logs show config pull success
- [ ] Logs show heartbeat push success
- [ ] Logs show inventory collection
- [ ] Local SQLite created: `/var/lib/mc-agent/edge.db` or `C:\Program Files\MC Edge Agent\data\edge.db`

### Integration Tests
- [ ] Pull config from cloud
- [ ] Run local plugin collection
- [ ] Push inventory to cloud
- [ ] Verify data appears in Mission Control UI
- [ ] Test offline mode: disconnect network, verify local collection continues
- [ ] Test online resume: reconnect network, verify config pull and data push resume

---

## Rollback Procedure

### Linux
```bash
sudo systemctl stop mc-edge-agent
sudo systemctl disable mc-edge-agent
sudo rm /etc/systemd/system/mc-edge-agent.service
sudo rm -rf /opt/mc-agent
sudo userdel mc-agent
```

### Windows
```powershell
# Run uninstaller from Add/Remove Programs
# OR manually:
sc.exe stop MissionControlEdgeAgent
sc.exe delete MissionControlEdgeAgent
Remove-Item -Recurse "C:\Program Files\MC Edge Agent"
```

---

## Support

- Backend logs: `docker compose logs backend`
- Edge logs: `journalctl -u mc-edge-agent -f` or `C:\Program Files\MC Edge Agent\logs\`
- Config: `/etc/mc-agent/config.yaml` or `C:\Program Files\MC Edge Agent\config.yaml`
- Database: `/var/lib/mc-agent/edge.db` or `C:\Program Files\MC Edge Agent\data\edge.db`
