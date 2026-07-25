#!/usr/bin/env bash
# ============================================================================
# Mission Control Agent — Linux Installer
#
# Installs the Mission Control agent on Ubuntu servers (20.04+).
# Copies agent files, creates a venv, installs a systemd service,
# and starts the agent.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/billboe3-png/MissionControl/main/install-agent-linux.sh | sudo bash
#   # or
#   sudo ./install-agent-linux.sh
#   sudo ./install-agent-linux.sh --agent-name prod-01
#   sudo ./install-agent-linux.sh --uninstall
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
AGENT_NAME_DISPLAY=""
SERVER_URL="https://34.35.102.233"
HEARTBEAT_INTERVAL=30
NO_SSL_VERIFY=false
UNINSTALL=false
GIT_REPO="https://github.com/billboe3-png/MissionControl.git"
GIT_BRANCH="develop"

INSTALL_DIR="/opt/mission-control-agent"
CONFIG_DIR="/etc/mission-control-agent"
DATA_DIR="/var/lib/mission-control-agent"
LOG_DIR="/var/log/mission-control-agent"
SERVICE_NAME="mission-control-agent"
SERVICE_USER="mission-control-agent"

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
step()  { echo -e "\n${CYAN}━━━ $* ━━━${NC}"; }
die()   { error "$@"; exit 1; }

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --server-url)        SERVER_URL="$2"; shift 2 ;;
        --agent-name)        AGENT_NAME_DISPLAY="$2"; shift 2 ;;
        --heartbeat-interval) HEARTBEAT_INTERVAL="$2"; shift 2 ;;
        --no-ssl-verify)     NO_SSL_VERIFY=true; shift ;;
        --uninstall)         UNINSTALL=true; shift ;;
        --install-dir)       INSTALL_DIR="$2"; shift 2 ;;
        --git-repo)          GIT_REPO="$2"; shift 2 ;;
        --git-branch)        GIT_BRANCH="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: sudo $0 [OPTIONS]"
            echo ""
            echo "Install Mission Control Agent on Ubuntu servers."
            echo ""
            echo "Options:"
            echo "  --server-url URL        Mission Control server URL (default: https://34.35.102.233)"
            echo "  --agent-name NAME       Display name for this agent (default: hostname)"
            echo "  --heartbeat-interval N  Seconds between heartbeats (default: 30)"
            echo "  --no-ssl-verify         Disable SSL certificate verification"
            echo "  --git-repo URL          Git repository URL (default: GitHub)"
            echo "  --git-branch BRANCH     Git branch (default: develop)"
            echo "  --uninstall             Remove the agent and all files"
            echo "  --install-dir DIR       Install directory (default: /opt/mission-control-agent)"
            echo "  -h, --help              Show this help"
            echo ""
            echo "Examples:"
            echo "  curl -fsSL https://raw.githubusercontent.com/billboe3-png/MissionControl/main/install-agent-linux.sh | sudo bash"
            echo "  sudo $0"
            echo "  sudo $0 --agent-name prod-01"
            echo "  sudo $0 --uninstall"
            exit 0
            ;;
        *) die "Unknown option: $1 (use --help for usage)" ;;
    esac
done

# ---------------------------------------------------------------------------
# Check root
# ---------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    die "This script must be run as root. Use: sudo $0 ..."
fi

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------
if [[ "$UNINSTALL" == "true" ]]; then
    step "Uninstalling Mission Control Agent"

    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        info "Stopping service..."
        systemctl stop "$SERVICE_NAME"
        ok "Service stopped"
    fi

    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        info "Disabling service..."
        systemctl disable "$SERVICE_NAME"
        ok "Service disabled"
    fi

    if [[ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]]; then
        rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
        systemctl daemon-reload
        ok "Service unit removed"
    fi

    for dir in "$INSTALL_DIR" "$CONFIG_DIR" "$DATA_DIR" "$LOG_DIR"; do
        if [[ -d "$dir" ]]; then
            rm -rf "$dir"
            ok "Removed $dir"
        fi
    done

    if id "$SERVICE_USER" &>/dev/null; then
        userdel "$SERVICE_USER" 2>/dev/null || true
        ok "Removed system user $SERVICE_USER"
    fi

    echo ""
    ok "Uninstall complete."
    exit 0
fi

# ---------------------------------------------------------------------------
# Validate required args
# ---------------------------------------------------------------------------
if [[ -z "$SERVER_URL" ]]; then
    die "Server URL is required. Use: sudo $0 --server-url http://<server-ip>:8000"
fi

if [[ -z "$AGENT_NAME_DISPLAY" ]]; then
    AGENT_NAME_DISPLAY="$(hostname)"
fi

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Mission Control Agent Installer${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# ---------------------------------------------------------------------------
# Step 1: Check / Install Python
# ---------------------------------------------------------------------------
step "Checking Python"

find_python() {
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            local ver
            ver=$("$cmd" --version 2>&1 | grep -oP '3\.\d+')
            if [[ -n "$ver" ]]; then
                local minor
                minor=$(echo "$ver" | cut -d. -f2)
                if [[ "$minor" -ge 11 ]]; then
                    echo "$cmd"
                    return 0
                fi
            fi
        fi
    done
    return 1
}

PYTHON_CMD=""
if PYTHON_CMD=$(find_python); then
    ok "Python found: $PYTHON_CMD ($($PYTHON_CMD --version 2>&1))"
else
    info "Python 3.11+ not found. Installing via apt..."

    apt-get update -qq
    apt-get install -y -qq python3 python3-pip python3-venv python3-dev

    if PYTHON_CMD=$(find_python); then
        ok "Python installed: $PYTHON_CMD ($($PYTHON_CMD --version 2>&1))"
    else
        die "Python installation failed. Install python3 manually: sudo apt install python3 python3-pip python3-venv"
    fi
fi

# ---------------------------------------------------------------------------
# Step 2: Install build dependencies
# ---------------------------------------------------------------------------
step "Installing build dependencies"

apt-get install -y -qq gcc libffi-dev python3-dev python3-venv 2>/dev/null || {
    warn "Some build dependencies may be missing (non-fatal)"
}

# ---------------------------------------------------------------------------
# Step 3: Create system user
# ---------------------------------------------------------------------------
step "Creating system user"

if id "$SERVICE_USER" &>/dev/null; then
    ok "User $SERVICE_USER already exists"
else
    useradd --system --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER"
    ok "Created system user $SERVICE_USER"
fi

# ---------------------------------------------------------------------------
# Step 4: Stop existing service
# ---------------------------------------------------------------------------
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    info "Stopping existing service..."
    systemctl stop "$SERVICE_NAME"
    ok "Service stopped"
fi

# ---------------------------------------------------------------------------
# Step 5: Clone repo and copy agent files
# ---------------------------------------------------------------------------
step "Installing agent files"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_SOURCE="$SCRIPT_DIR/.agents"

# If running from a git clone, use local files
if [[ -d "$AGENT_SOURCE" ]]; then
    info "Using local agent files from $AGENT_SOURCE"
else
    # Clone from git
    info "Cloning agent from $GIT_REPO (branch: $GIT_BRANCH)..."
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    apt-get install -y -qq git >/dev/null 2>&1
    git clone --depth 1 --branch "$GIT_BRANCH" "$GIT_REPO" "$TEMP_DIR/repo" 2>&1
    AGENT_SOURCE="$TEMP_DIR/repo/.agents"
fi

if [[ ! -d "$AGENT_SOURCE" ]]; then
    die "Agent source not found at $AGENT_SOURCE"
fi

if [[ -d "$INSTALL_DIR" ]]; then
    info "Cleaning previous installation..."
    rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"
cp -r "$AGENT_SOURCE/agent" "$INSTALL_DIR/agent"
if [[ -d "$AGENT_SOURCE/skills" ]]; then
    cp -r "$AGENT_SOURCE/skills" "$INSTALL_DIR/skills"
fi
cp "$AGENT_SOURCE/pyproject.toml" "$INSTALL_DIR/"
cp "$AGENT_SOURCE/requirements.txt" "$INSTALL_DIR/"

ok "Agent files copied to $INSTALL_DIR"

# ---------------------------------------------------------------------------
# Step 6: Create virtual environment + install dependencies
# ---------------------------------------------------------------------------
step "Setting up Python environment"

python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip

"$INSTALL_DIR/venv/bin/pip" install --quiet \
    httpx psutil pydantic pydantic-settings pyyaml packaging docker paramiko

# Install the agent package itself (editable not needed for production)
cd "$INSTALL_DIR"
"$INSTALL_DIR/venv/bin/pip" install --quiet --no-deps -e . 2>/dev/null || {
    # Fallback: just ensure the package is importable via PYTHONPATH
    ok "Package install skipped (will use PYTHONPATH)"
}

cd /

ok "Python dependencies installed"

# ---------------------------------------------------------------------------
# Step 7: Create directories
# ---------------------------------------------------------------------------
step "Creating directories"

mkdir -p "$CONFIG_DIR" "$DATA_DIR" "$LOG_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR" "$LOG_DIR"
chmod 700 "$CONFIG_DIR"

ok "Directories created"

# ---------------------------------------------------------------------------
# Step 8: Write config file
# ---------------------------------------------------------------------------
step "Writing configuration"

CONFIG_FILE="$CONFIG_DIR/config.yaml"

if [[ -f "$CONFIG_FILE" ]]; then
    info "Backing up existing config to ${CONFIG_FILE}.bak"
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
fi

SSL_VERIFY="true"
if [[ "$NO_SSL_VERIFY" == "true" ]]; then
    SSL_VERIFY="false"
fi

cat > "$CONFIG_FILE" << EOF
# Mission Control Agent Configuration
# Installed: $(date -Iseconds)

server_url: "$SERVER_URL"
agent_name: "$AGENT_NAME_DISPLAY"
heartbeat_interval: $HEARTBEAT_INTERVAL
inventory_interval: 300
remote_inventory_interval: 300
verify_ssl: $SSL_VERIFY
log_level: "INFO"
log_file: "$LOG_DIR/agent.log"
command_timeout: 60
reconnect_delay: 5
max_reconnect_delay: 300
offline_buffer_max: 1000
EOF

chmod 640 "$CONFIG_FILE"
ok "Config written to $CONFIG_FILE"

# ---------------------------------------------------------------------------
# Step 9: Create systemd service
# ---------------------------------------------------------------------------
step "Creating systemd service"

cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Mission Control Agent
Documentation=file://${INSTALL_DIR}/README.md
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
ExecStart=${INSTALL_DIR}/venv/bin/python -m agent --config ${CONFIG_DIR}/config.yaml
WorkingDirectory=${INSTALL_DIR}

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR $LOG_DIR
PrivateTmp=true

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
ok "Service unit created"

# ---------------------------------------------------------------------------
# Step 10: Enable and start service
# ---------------------------------------------------------------------------
step "Starting agent"

systemctl enable "$SERVICE_NAME" --quiet
systemctl start "$SERVICE_NAME"

sleep 2

if systemctl is-active --quiet "$SERVICE_NAME"; then
    ok "Agent is running"
else
    warn "Agent may not have started. Check: journalctl -u $SERVICE_NAME -f"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "  Agent name:     $AGENT_NAME_DISPLAY"
echo "  Server:         $SERVER_URL"
echo "  Install dir:    $INSTALL_DIR"
echo "  Config:         $CONFIG_FILE"
echo "  Logs (journald): journalctl -u $SERVICE_NAME -f"
echo "  Logs (file):     $LOG_DIR/agent.log"
echo ""
echo "  The agent will register with the server on first"
echo "  heartbeat and appear in the Agents page."
echo ""
echo "  Management commands:"
echo "    sudo systemctl status $SERVICE_NAME"
echo "    sudo systemctl restart $SERVICE_NAME"
echo "    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "  To uninstall: sudo $0 --uninstall"
echo ""
