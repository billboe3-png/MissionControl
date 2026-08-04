# Mission Control Edge Agent - Complete Reinstall Script
# For local always-on Linux server
# Run as root or with sudo

set -euo pipefail

AGENT_USER="mc-agent"
AGENT_GROUP="mc-agent"
INSTALL_DIR="/opt/mc-agent"
DATA_DIR="/var/lib/mc-agent"
LOG_DIR="/var/log/mc-agent"
CONFIG_FILE="/etc/mc-agent/config.yaml"
SYSTEMD_UNIT="/etc/systemd/system/mc-edge-agent.service"

echo "=== Mission Control Edge Agent - Complete Reinstall ==="
echo ""

# Stop and disable existing service if present
if systemctl is-active --quiet mc-edge-agent 2>/dev/null; then
    echo "[*] Stopping existing mc-edge-agent service..."
    systemctl stop mc-edge-agent || true
fi
if systemctl is-enabled --quiet mc-edge-agent 2>/dev/null; then
    echo "[*] Disabling existing mc-edge-agent service..."
    systemctl disable mc-edge-agent || true
fi

# Remove old files
echo "[*] Removing old installation..."
rm -rf "$INSTALL_DIR"
rm -rf "$DATA_DIR"
rm -rf "$LOG_DIR"
rm -rf "$CONFIG_FILE"
rm -f "$SYSTEMD_UNIT"
userdel "$AGENT_USER" 2>/dev/null || true
groupdel "$AGENT_GROUP" 2>/dev/null || true

# Create fresh directories
echo "[*] Creating fresh directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$LOG_DIR"

# Create agent user
echo "[*] Creating agent user..."
if ! id "$AGENT_USER" &>/dev/null; then
    groupadd --system "$AGENT_GROUP"
    useradd --system --gid "$AGENT_GROUP" --home-dir "$INSTALL_DIR" --shell /bin/false "$AGENT_USER"
fi
chown -R "$AGENT_USER:$AGENT_GROUP" "$INSTALL_DIR" "$DATA_DIR" "$LOG_DIR"

# Install system dependencies
echo "[*] Installing system dependencies..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3.11 python3.11-venv python3-pip curl >/dev/null 2>&1

# Create Python virtual environment
echo "[*] Creating Python virtual environment..."
sudo -u "$AGENT_USER" python3.11 -m venv "$INSTALL_DIR/venv"
sudo -u "$AGENT_USER" "$INSTALL_DIR/venv/bin/pip" install --quiet httpx psutil pydantic pydantic-settings pyyaml packaging paramiko pywinrm pysnmp

# Download agent package
echo "[*] Downloading agent package..."
curl -sk https://missioncontrol.optichosting.co.za/api/v1/agents/1/bundles/download -o "$INSTALL_DIR/agent-bundle.zip"
curl -sk https://missioncontrol.optichosting.co.za/api/v1/agents/debug/install-agent.bat -o "$INSTALL_DIR/install-agent.bat"

# Extract agent bundle
echo "[*] Extracting agent bundle..."
sudo -u "$AGENT_USER" unzip -q "$INSTALL_DIR/agent-bundle.zip" -d "$INSTALL_DIR/agent"
chown -R "$AGENT_USER:$AGENT_GROUP" "$INSTALL_DIR/agent"

# Create config file
echo "[*] Creating configuration..."
echo "Enter API key for agent (from Mission Control UI):"
read -s AGENT_API_KEY
echo ""
if [ -z "$AGENT_API_KEY" ]; then
    echo "[-] API key is required. Exiting."
    exit 1
fi

cat > "$CONFIG_FILE" <<EOF
# Mission Control Edge Agent Configuration
server_url: https://missioncontrol.optichosting.co.za
agent_id: 1
api_key: $AGENT_API_KEY
heartbeat_interval: 60
inventory_interval: 120
verify_ssl: true
log_level: INFO
data_dir: $DATA_DIR
EOF

chown root:root "$CONFIG_FILE"
chmod 640 "$CONFIG_FILE"

# Install systemd service
echo "[*] Installing systemd service..."
cat > "$SYSTEMD_UNIT" <<'EOF'
[Unit]
Description=Mission Control Edge Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=mc-agent
Group=mc-agent
Environment="MC_CONFIG_FILE=/etc/mc-agent/config.yaml"
Environment="MC_LOG_FILE=/var/log/mc-agent/agent.log"
ExecStart=/opt/mc-agent/venv/bin/python3 -m agent --config /etc/mc-agent/config.yaml
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mc-edge-agent

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/var/lib/mc-agent /var/log/mc-agent

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mc-edge-agent

# Start service
echo "[*] Starting edge agent..."
systemctl start mc-edge-agent

# Wait for startup
sleep 5

# Verify
echo ""
echo "=== Installation Complete ==="
echo "Service status:"
systemctl status mc-edge-agent --no-pager || true
echo ""
echo "Recent logs:"
journalctl -u mc-edge-agent -n 20 --no-pager || true
echo ""
echo "Next steps:"
echo "  1. Verify agent appears online in Mission Control UI"
echo "  2. Test config pull: curl -H 'X-Agent-API-Key: <key>' https://missioncontrol.optichosting.co.za/api/v1/edge/1/config"
echo "  3. Monitor logs: journalctl -u mc-edge-agent -f"
echo ""
echo "Runbook: /opt/MissionControl/docs/edge-agent-test-runbook.md"
