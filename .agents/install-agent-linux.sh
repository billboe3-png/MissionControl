#!/usr/bin/env bash
#
# Mission Control Edge Agent - Linux Installer
#
# Downloads the agent bundle from the Mission Control server, sets up a
# self-contained Python virtualenv, writes config.yaml, and installs the
# agent as a systemd service (mission-control-agent.service).
#
# Supports Debian/Ubuntu (apt), RHEL/Rocky/Alma (dnf/yum), and any distro
# where python3 >= 3.11 with venv is already available.
#
# Usage:
#   sudo ./install-agent-linux.sh [options]
#
# Options (environment variables take precedence):
#   --server <url>      Mission Control server URL
#                       (default: MC_SERVER_URL or https://missioncontrol.optichosting.co.za)
#   --agent-id <id>     Pre-provisioned agent ID (required; MC_AGENT_ID)
#   --api-key <key>     Agent API key (required; MC_API_KEY)
#   --workdir <path>    Agent working directory
#                       (default: MC_WORKDIR or /opt/mission-control-agent)
#   --verify-ssl        Enable TLS certificate verification (default: off)
#   --version           Print version and exit
#
# Examples:
#   sudo ./install-agent-linux.sh --agent-id 3 --api-key mc_agent_...
#   MC_AGENT_ID=3 MC_API_KEY=mc_agent_... sudo ./install-agent-linux.sh
#
set -euo pipefail

SCRIPT_VERSION="3.0.0-rc1"
BUNDLE_URL_PATH_EDGE="/api/v1/edge/%s/bundle/download"
BUNDLE_URL_PATH_LEGACY="/api/v1/agents/%s/bundles/download"

SERVER_URL="${MC_SERVER_URL:-https://missioncontrol.optichosting.co.za}"
AGENT_ID="${MC_AGENT_ID:-}"
API_KEY="${MC_API_KEY:-}"
WORKDIR="${MC_WORKDIR:-/opt/mission-control-agent}"
VERIFY_SSL="${MC_VERIFY_SSL:-false}"

log()  { printf '\033[1;34m[+] %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m[!] %s\033[0m\n' "$*"; }
fail() { printf '\033[1;31m[x] %s\033[0m\n' "$*" >&2; exit 1; }
ok()   { printf '\033[1;32m[ok] %s\033[0m\n' "$*"; }

usage() {
    sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --server)     SERVER_URL="$2"; shift 2 ;;
        --agent-id)   AGENT_ID="$2"; shift 2 ;;
        --api-key)    API_KEY="$2"; shift 2 ;;
        --workdir)    WORKDIR="$2"; shift 2 ;;
        --verify-ssl) VERIFY_SSL="true"; shift ;;
        --version)    echo "install-agent-linux.sh $SCRIPT_VERSION"; exit 0 ;;
        -h|--help)    usage ;;
        *)            fail "Unknown option: $1" ;;
    esac
done

# ------------------------------------------------------------------ #
# Pre-flight checks                                                  #
# ------------------------------------------------------------------ #
[[ "$(id -u)" -eq 0 ]] || fail "This installer must be run as root (sudo)."

[[ -n "$AGENT_ID" ]] || fail "Missing --agent-id (or MC_AGENT_ID env var)."
[[ -n "$API_KEY" ]] || fail "Missing --api-key (or MC_API_KEY env var)."
SERVER_URL="${SERVER_URL%/}"

log "Mission Control Edge Agent Installer v$SCRIPT_VERSION"
log "Server:   $SERVER_URL"
log "Agent ID: $AGENT_ID"
log "WorkDir:  $WORKDIR"

command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1 \
    || fail "Neither curl nor wget is installed. Install one and retry."

# ------------------------------------------------------------------ #
# Detect package manager                                             #
# ------------------------------------------------------------------ #
PKG_MGR=""
if command -v apt-get >/dev/null 2>&1; then
    PKG_MGR="apt"
elif command -v dnf >/dev/null 2>&1; then
    PKG_MGR="dnf"
elif command -v yum >/dev/null 2>&1; then
    PKG_MGR="yum"
fi
[[ -n "$PKG_MGR" ]] && log "Package manager: $PKG_MGR"

# ------------------------------------------------------------------ #
# Find a suitable python3 (>= 3.11) with venv support                #
# ------------------------------------------------------------------ #
python_version_ok() {
    local py="$1"
    [[ -x "$py" ]] || return 1
    "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'
}

ensure_python() {
    local candidates=(python3 python3.13 python3.12 python3.11)
    for py in "${candidates[@]}"; do
        if python_version_ok "$(command -v "$py" 2>/dev/null)"; then
            PYTHON="$(command -v "$py")"
            log "Using $PYTHON ($("$PYTHON" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))'))"
            return 0
        fi
    done

    if [[ -z "$PKG_MGR" ]]; then
        fail "No python3 >= 3.11 found and no apt/dnf/yum available to install it."
    fi

    warn "python3 >= 3.11 not found; installing via $PKG_MGR..."
    case "$PKG_MGR" in
        apt)
            export DEBIAN_FRONTEND=noninteractive
            apt-get update -qq
            # Prefer a 3.11+ interpreter package where distros ship one.
            for pkg in python3.13 python3.12 python3.11; do
                if apt-cache show "$pkg" >/dev/null 2>&1; then
                    apt-get install -y -qq "$pkg" "$pkg-venv" "$pkg-pip" 2>/dev/null \
                        || apt-get install -y -qq "$pkg"
                    break
                fi
            done
            # Fall back to distro default python3 (works on 24.04/Debian 12).
            apt-get install -y -qq python3 python3-venv python3-pip
            ;;
        dnf|yum)
            "$PKG_MGR" install -y python3 python3-pip python3-virtualenv 2>/dev/null \
                || "$PKG_MGR" install -y python3 python3-pip
            # RHEL 9 defaults to 3.9; try module streams / newer packages.
            for pkg in python3.13 python3.12 python3.11; do
                if "$PKG_MGR" list available "$pkg" >/dev/null 2>&1; then
                    "$PKG_MGR" install -y "$pkg" "$pkg-pip" 2>/dev/null \
                        || "$PKG_MGR" install -y "$pkg"
                    break
                fi
            done
            ;;
    esac

    for py in python3.13 python3.12 python3.11 python3; do
        if python_version_ok "$(command -v "$py" 2>/dev/null)"; then
            PYTHON="$(command -v "$py")"
            log "Using $PYTHON ($("$PYTHON" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))'))"
            return 0
        fi
    done
    fail "Failed to provision python3 >= 3.11. Install it manually and retry."
}

# ------------------------------------------------------------------ #
# Runtime dependency set (mirrors .agents/requirements.txt)          #
# ------------------------------------------------------------------ #
REQUIREMENTS=(
    "httpx>=0.27.0"
    "psutil>=7.0.0"
    "pydantic>=2.0"
    "pydantic-settings>=2.0"
    "pyyaml>=6.0"
    "packaging>=23.0"
    "docker>=7.0.0"
    "paramiko>=3.0.0"
    "pywinrm>=0.5.0"
)

# ------------------------------------------------------------------ #
# Download & extract bundle                                          #
# ------------------------------------------------------------------ #
download_bundle() {
    local bundle_url
    printf -v bundle_url "%s%s" "$SERVER_URL" "$BUNDLE_URL_PATH_EDGE"
    bundle_url="$(printf "$bundle_url" "$AGENT_ID")"
    local dest="$WORKDIR/agent-bundle-live.zip"
    log "Downloading bundle from $bundle_url"
    if command -v curl >/dev/null 2>&1; then
        # Prefer the authenticated edge endpoint (how the agent self-updates).
        curl -k -L --fail --silent --show-error \
            -H "X-Agent-API-Key: $API_KEY" \
            -o "$dest" "$bundle_url" 2>/dev/null || {
            # Fall back to the legacy unauthenticated agents endpoint.
            printf -v bundle_url "%s%s" "$SERVER_URL" "$BUNDLE_URL_PATH_LEGACY"
            bundle_url="$(printf "$bundle_url" "$AGENT_ID")"
            curl -k -L --fail --silent --show-error -X POST -o "$dest" "$bundle_url" \
                || fail "Bundle download failed from $bundle_url"
        }
    else
        # Prefer the authenticated edge endpoint.
        wget --no-check-certificate -q \
            --header="X-Agent-API-Key: $API_KEY" \
            -O "$dest" "$bundle_url" 2>/dev/null || {
            printf -v bundle_url "%s%s" "$SERVER_URL" "$BUNDLE_URL_PATH_LEGACY"
            bundle_url="$(printf "$bundle_url" "$AGENT_ID")"
            wget --no-check-certificate -q -O "$dest" "$bundle_url" \
                || fail "Bundle download failed from $bundle_url"
        }
    fi
    local size
    size=$(stat -c%s "$dest" 2>/dev/null || echo "?")
    ok "Downloaded bundle ($size bytes)"
}

extract_bundle() {
    log "Extracting bundle..."
    rm -rf "$WORKDIR/agent"
    "$PYTHON" - "$WORKDIR/agent-bundle-live.zip" "$WORKDIR" <<'PYEOF'
import sys, zipfile
zip_path, dest = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(zip_path) as z:
    z.extractall(dest)
    print("Extracted", len(z.namelist()), "files")
PYEOF
}

# ------------------------------------------------------------------ #
# Virtualenv + dependencies                                          #
# ------------------------------------------------------------------ #
setup_venv() {
    if [[ -x "$WORKDIR/venv/bin/python" ]]; then
        log "Reusing existing virtualenv at $WORKDIR/venv"
        VENV_PY="$WORKDIR/venv/bin/python"
        return 0
    fi
    log "Creating virtualenv..."
    "$PYTHON" -m venv "$WORKDIR/venv" || fail "Failed to create virtualenv (python3-venv missing?)"
    VENV_PY="$WORKDIR/venv/bin/python"
    "$VENV_PY" -m pip install --quiet --upgrade pip

    log "Installing dependencies..."
    local req=()
    for dep in "${REQUIREMENTS[@]}"; do req+=("$dep"); done
    "$VENV_PY" -m pip install --quiet "${req[@]}" \
        || fail "Failed to install dependencies"
}

# ------------------------------------------------------------------ #
# Config                                                             #
# ------------------------------------------------------------------ #
write_config() {
    log "Writing config.yaml..."
    mkdir -p "$WORKDIR/data"
    local ssl_line="verify_ssl: ${VERIFY_SSL,,}"
    cat > "$WORKDIR/config.yaml" <<EOF
server_url: $SERVER_URL
$ssl_line
agent_id: $AGENT_ID
api_key: $API_KEY
data_dir: "$WORKDIR/data"
config_dir: "$WORKDIR"
EOF
    chmod 600 "$WORKDIR/config.yaml"
    ok "Config written to $WORKDIR/config.yaml"
}

# ------------------------------------------------------------------ #
# systemd service                                                    #
# ------------------------------------------------------------------ #
install_systemd() {
    local unit="/etc/systemd/system/mission-control-agent.service"
    log "Installing systemd unit..."
    cat > "$unit" <<EOF
[Unit]
Description=Mission Control Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$VENV_PY -m agent.edge_main --config $WORKDIR/config.yaml
WorkingDirectory=$WORKDIR
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable mission-control-agent.service >/dev/null 2>&1 \
        || warn "systemctl enable failed (systemd unavailable?)"
    systemctl restart mission-control-agent.service 2>/dev/null \
        || systemctl start mission-control-agent.service \
        || fail "Failed to start mission-control-agent.service"
}

# ------------------------------------------------------------------ #
# Main                                                               #
# ------------------------------------------------------------------ #
main() {
    mkdir -p "$WORKDIR"
    ensure_python
    download_bundle
    extract_bundle
    setup_venv
    write_config
    install_systemd

    log "Waiting for first heartbeat..."
    sleep 15
    if systemctl is-active --quiet mission-control-agent.service 2>/dev/null; then
        ok "Service is active"
    else
        warn "Service not active yet; check: journalctl -u mission-control-agent"
    fi

    printf '\n\033[1;36m=== Installation Complete ===\033[0m\n'
    echo "  Agent working dir : $WORKDIR"
    echo "  Config            : $WORKDIR/config.yaml"
    echo "  Virtualenv        : $WORKDIR/venv"
    echo "  Service           : mission-control-agent.service"
    echo ""
    echo "  View logs : journalctl -u mission-control-agent -f"
    echo "  Restart   : systemctl restart mission-control-agent"
    echo "  Uninstall : systemctl disable --now mission-control-agent && rm -rf $WORKDIR"
}

main