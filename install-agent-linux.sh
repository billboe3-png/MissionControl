#!/usr/bin/env bash
# ============================================================================
# Mission Control — Linux Agent Installer (v3.0.0-rc1)
#
# Downloads the Mission Control agent bundle from your server, sets up a
# self-contained Python virtualenv, writes config.yaml, and installs the
# agent as a systemd service (mission-control-agent.service).
#
# The agent polls your Mission Control server every 5-15 seconds for commands
# and sends heartbeats, so the server and this machine need to reach each other
# over HTTP(S). No inbound ports are required on the agent — it only makes
# outbound connections to the server.
#
# TWO PROVISIONING MODES:
#
#   A) Self-registration (easiest):
#        sudo ./install-agent-linux.sh --server https://mc.example.com
#      The agent registers itself with the server and gets an API key
#      automatically. If your Mission Control requires enrollment tokens,
#      add:  --registration-token <token>
#
#   B) Pre-provisioned (create the agent in the Mission Control UI first):
#        sudo ./install-agent-linux.sh --server https://mc.example.com \
#              --agent-id 3 --api-key mc_agent_<64 hex>
#
# Usage:
#   sudo ./install-agent-linux.sh [options]
#
# Options:
#   --server <url>             Mission Control server URL
#                              (default: MC_SERVER_URL or https://missioncontrol.optichosting.co.za)
#   --registration-token <t>   Enrollment/registration token (optional)
#   --agent-id <id>            Pre-provisioned agent ID (optional if self-registering)
#   --api-key <key>            Pre-provisioned API key (optional if self-registering)
#   --agent-name <name>        Agent display name (default: hostname)
#   --workdir <path>           Install dir (default: MC_WORKDIR or /opt/mission-control-agent)
#   --verify-ssl               Enable TLS verification (default: off)
#   --version                  Print version and exit
#   -h, --help                 Show this help
#
# Examples:
#   sudo ./install-agent-linux.sh --server https://missioncontrol.optichosting.co.za
#   sudo ./install-agent-linux.sh --server https://mc.example.com --registration-token abc123
#   sudo ./install-agent-linux.sh --server https://mc.example.com --agent-id 3 --api-key mc_agent_...
# ============================================================================

set -euo pipefail

SCRIPT_VERSION="3.0.0-rc1"
BUNDLE_URL_PATH_EDGE="/api/v1/edge/%s/bundle/download"
BUNDLE_URL_PATH_LEGACY="/api/v1/agents/%s/bundles/download"
REGISTER_URL_PATH="/api/v1/agents/register"
AGENT_PREFIX="mc_agent_"

SERVER_URL="${MC_SERVER_URL:-https://missioncontrol.optichosting.co.za}"
AGENT_ID="${MC_AGENT_ID:-}"
API_KEY="${MC_API_KEY:-}"
REGISTRATION_TOKEN="${MC_REGISTRATION_TOKEN:-}"
AGENT_NAME="${MC_AGENT_NAME:-}"
WORKDIR="${MC_WORKDIR:-/opt/mission-control-agent}"
VERIFY_SSL="${MC_VERIFY_SSL:-false}"
CREDENTIALS_FILE="$WORKDIR/.credentials"

log()  { printf '\033[1;34m[+] %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m[!] %s\033[0m\n' "$*"; }
fail() { printf '\033[1;31m[x] %s\033[0m\n' "$*" >&2; exit 1; }
ok()   { printf '\033[1;32m[ok] %s\033[0m\n' "$*"; }

usage() { sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'; exit 0; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --server)             SERVER_URL="$2"; shift 2 ;;
        --registration-token) REGISTRATION_TOKEN="$2"; shift 2 ;;
        --agent-id)           AGENT_ID="$2"; shift 2 ;;
        --api-key)            API_KEY="$2"; shift 2 ;;
        --agent-name)         AGENT_NAME="$2"; shift 2 ;;
        --workdir)            WORKDIR="$2"; shift 2 ;;
        --verify-ssl)         VERIFY_SSL="true"; shift ;;
        --version)            echo "install-agent-linux.sh $SCRIPT_VERSION"; exit 0 ;;
        -h|--help)            usage ;;
        *)                    fail "Unknown option: $1" ;;
    esac
done

# ------------------------------------------------------------------ #
# Pre-flight checks                                                  #
# ------------------------------------------------------------------ #
[[ "$(id -u)" -eq 0 ]] || fail "This installer must be run as root (sudo)."
SERVER_URL="${SERVER_URL%/}"
command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1 \
    || fail "Neither curl nor wget is installed. Install one and retry."

# Determine agent name from hostname if not provided
if [[ -z "$AGENT_NAME" ]]; then
    AGENT_NAME="$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo "linux-agent")"
fi

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
            for pkg in python3.13 python3.12 python3.11; do
                if apt-cache show "$pkg" >/dev/null 2>&1; then
                    apt-get install -y -qq "$pkg" "$pkg-venv" "$pkg-pip" 2>/dev/null \
                        || apt-get install -y -qq "$pkg"
                    break
                fi
            done
            apt-get install -y -qq python3 python3-venv python3-pip
            ;;
        dnf|yum)
            "$PKG_MGR" install -y python3 python3-pip python3-virtualenv 2>/dev/null \
                || "$PKG_MGR" install -y python3 python3-pip
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
# Ensure python3-venv / ensurepip is present                          #
# ------------------------------------------------------------------ #
venv_supported() {
    local py="$1"
    "$py" -m venv --help >/dev/null 2>&1 || return 1
    "$py" -c 'import ensurepip' >/dev/null 2>&1
}

ensure_venv() {
    if venv_supported "$PYTHON"; then
        return 0
    fi
    warn "python3-venv / ensurepip missing; installing it via $PKG_MGR..."
    local pyver
    pyver="$(basename "$PYTHON")"   # python3, python3.12, python3.11, ...
    case "$PKG_MGR" in
        apt)
            export DEBIAN_FRONTEND=noninteractive
            apt-get install -y -qq "$pyver-venv" 2>/dev/null \
                || apt-get install -y -qq python3-venv 2>/dev/null \
                || apt-get install -y -qq python3.12-venv
            ;;
        dnf|yum)
            "$PKG_MGR" install -y python3-virtualenv 2>/dev/null \
                || "$PKG_MGR" install -y "$pyver-virtualenv"
            ;;
    esac
    venv_supported "$PYTHON" || fail "venv/ensurepip support unavailable for $PYTHON. Install python3-venv (Debian/Ubuntu) or python3-virtualenv (RHEL) and retry."
    ok "venv support ready"
}

# ------------------------------------------------------------------ #
# Self-registration (mode A)                                         #
# ------------------------------------------------------------------ #
register_agent() {
    # Reuse credentials saved on a previous (possibly interrupted) run
    if [[ -f "$CREDENTIALS_FILE" ]]; then
        log "Reusing credentials from $CREDENTIALS_FILE"
        AGENT_ID="${AGENT_ID:-$(sed -n 's/^AGENT_ID=//p' "$CREDENTIALS_FILE")}"
        API_KEY="${API_KEY:-$(sed -n 's/^API_KEY=//p' "$CREDENTIALS_FILE")}"
    fi

    if [[ -n "$AGENT_ID" && -n "$API_KEY" ]]; then
        log "Using pre-provisioned agent ID $AGENT_ID / API key"
        mkdir -p "$WORKDIR"
        save_credentials
        return 0
    fi

    local ip
    ip="$(ip -4 addr show 2>/dev/null | grep -oP 'inet \K[0-9.]+' | grep -v '^127.' | head -1 || true)"
    [[ -z "$ip" ]] && ip="$(hostname -I 2>/dev/null | awk '{print $1}' || echo "")"

    local payload
    if [[ -n "$REGISTRATION_TOKEN" ]]; then
        payload="{\"name\":\"$AGENT_NAME\",\"hostname\":\"$AGENT_NAME\",\"operating_system\":\"Linux\",\"os_version\":\"$(uname -r)\",\"ip_address\":\"$ip\",\"agent_version\":\"$SCRIPT_VERSION\",\"registration_token\":\"$REGISTRATION_TOKEN\"}"
    else
        payload="{\"name\":\"$AGENT_NAME\",\"hostname\":\"$AGENT_NAME\",\"operating_system\":\"Linux\",\"os_version\":\"$(uname -r)\",\"ip_address\":\"$ip\",\"agent_version\":\"$SCRIPT_VERSION\"}"
    fi

    local url="${SERVER_URL}${REGISTER_URL_PATH}"
    log "Registering agent with $url (name: $AGENT_NAME)..."

    local resp http_code
    local curl_args=(-k -L --silent --show-error -o /tmp/mc-register-resp.json -w '%{http_code}' -X POST -H "Content-Type: application/json" -d "$payload")
    http_code="$(curl "${curl_args[@]}" "$url")" || fail "Registration request failed against $url"
    resp="$(cat /tmp/mc-register-resp.json)"

    if [[ "$http_code" != "201" ]]; then
        if printf '%s' "$resp" | grep -q "registration_token" 2>/dev/null; then
            fail "Server says '$AGENT_NAME' is already registered. Re-run with the existing agent:  --agent-id <ID> --api-key mc_agent_...  (or $0 --help)"
        fi
        fail "Registration failed (HTTP $http_code): $resp"
    fi

    log "Server response: $resp"

    AGENT_ID="$(printf '%s' "$resp" | grep -oP '"agent_id":\s*\K[0-9]+' | head -1 || true)"
    API_KEY="$(printf '%s' "$resp" | grep -oP '"api_key":\s*"\K[^"]+' | head -1 || true)"

    [[ -n "$AGENT_ID" ]] || fail "Could not parse agent_id from registration response."
    [[ -n "$API_KEY" ]] || fail "Could not parse api_key from registration response."

    ok "Agent registered — ID: $AGENT_ID"
    save_credentials
    return 0
}

# ------------------------------------------------------------------ #
# Persist credentials so re-runs don't force a second registration  #
# ------------------------------------------------------------------ #
save_credentials() {
    if [[ -z "$AGENT_ID" || -z "$API_KEY" ]]; then
        return 0
    fi
    mkdir -p "$WORKDIR"
    cat > "$CREDENTIALS_FILE" <<EOF
# Mission Control agent credentials (chmod 600)
# Do not share this file. Created by install-agent-linux.sh $SCRIPT_VERSION.
AGENT_ID=$AGENT_ID
API_KEY=$API_KEY
EOF
    chmod 600 "$CREDENTIALS_FILE"
    ok "Credentials saved to $CREDENTIALS_FILE (chmod 600)"
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
        curl -k -L --fail --silent --show-error \
            -H "X-Agent-API-Key: $API_KEY" \
            -o "$dest" "$bundle_url" 2>/dev/null || {
            printf -v bundle_url "%s%s" "$SERVER_URL" "$BUNDLE_URL_PATH_LEGACY"
            bundle_url="$(printf "$bundle_url" "$AGENT_ID")"
            curl -k -L --fail --silent --show-error -X POST -o "$dest" "$bundle_url" \
                || fail "Bundle download failed from $bundle_url"
        }
    else
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
    if [[ -x "$WORKDIR/venv/bin/python" ]] && "$WORKDIR/venv/bin/python" -c 'import yaml' >/dev/null 2>&1; then
        log "Reusing existing virtualenv at $WORKDIR/venv"
        VENV_PY="$WORKDIR/venv/bin/python"
        return 0
    fi
    # A venv that exists but can't import the core deps is leftover from an
    # interrupted previous run (e.g. ensurepip missing) — rebuild it fresh.
    if [[ -e "$WORKDIR/venv" ]]; then
        warn "Removing incomplete virtualenv from a previous run..."
        rm -rf "$WORKDIR/venv"
    fi
    ensure_venv
    log "Creating virtualenv..."
    if ! "$PYTHON" -m venv "$WORKDIR/venv"; then
        warn "Initial venv creation failed; ensuring python3-venv and retrying..."
        ensure_venv
        "$PYTHON" -m venv "$WORKDIR/venv" || fail "Failed to create virtualenv (python3-venv missing?)"
    fi
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
    log "Mission Control Edge Agent Installer v$SCRIPT_VERSION"
    log "Server:   $SERVER_URL"
    log "WorkDir:  $WORKDIR"

    mkdir -p "$WORKDIR"
    ensure_python
    register_agent
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
    echo "  Agent ID          : $AGENT_ID"
    echo "  Server            : $SERVER_URL"
    echo "  Agent working dir : $WORKDIR"
    echo "  Config            : $WORKDIR/config.yaml"
    echo "  Virtualenv        : $WORKDIR/venv"
    echo "  Service           : mission-control-agent.service"
    echo ""
    echo "  The agent polls $SERVER_URL every 5-15s for commands."
    echo "  It will appear in the Mission Control UI under Agents."
    echo ""
    echo "  View logs : journalctl -u mission-control-agent -f"
    echo "  Restart   : systemctl restart mission-control-agent"
    echo "  Verify    : curl -sk -H 'X-Agent-API-Key: $API_KEY' '$SERVER_URL/api/v1/edge/$AGENT_ID/config'"
    echo "  Uninstall : systemctl disable --now mission-control-agent && rm -rf $WORKDIR"
}

main