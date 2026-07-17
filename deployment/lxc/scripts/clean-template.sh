#!/usr/bin/env bash
# ============================================================================
# Mission Control — Clean Template Script
#
# Prepares an LXC container for conversion into a Proxmox template.
# Clears logs, temp files, history, and zeros free space for optimal
# template compression.
#
# Usage:
#   sudo ./clean-template.sh [--aggressive]
#
# After running this script:
#   1. Shut down the container: pct shutdown <VMID>
#   2. Convert to template: pct template <VMID>
#   3. Clone new instances: pct clone <VMID> <NEW_VMID>
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MC_INSTALL_DIR="/opt/missioncontrol"
AGGRESSIVE=false

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
step()  { echo -e "\n${CYAN}━━━ $* ━━━${NC}"; }

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --aggressive) AGGRESSIVE=true; shift ;;
        --help|-h)
            echo "Usage: $0 [--aggressive]"
            echo ""
            echo "Options:"
            echo "  --aggressive  Zero free space (slower but smaller template)"
            echo "  -h, --help    Show this help"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

step "Mission Control — Template Preparation"

# ---------------------------------------------------------------------------
# Step 1: Stop Mission Control services
# ---------------------------------------------------------------------------
step "Stopping Mission Control Services"

if [[ -d "${MC_INSTALL_DIR}" ]]; then
    cd "${MC_INSTALL_DIR}"
    docker compose down --timeout 10 2>/dev/null || true
    ok "Docker services stopped"
fi

# ---------------------------------------------------------------------------
# Step 2: Clear Docker images and volumes
# ---------------------------------------------------------------------------
step "Cleaning Docker"

# Remove stopped containers
docker container prune -f 2>/dev/null || true

# Remove unused images
docker image prune -af 2>/dev/null || true

# Remove unused volumes
docker volume prune -f 2>/dev/null || true

# Remove build cache
docker builder prune -af 2>/dev/null || true

ok "Docker cleaned"

# ---------------------------------------------------------------------------
# Step 3: Clear logs
# ---------------------------------------------------------------------------
step "Clearing Logs"

# System logs
find /var/log -type f -name "*.log" -exec truncate -s 0 {} \; 2>/dev/null || true
find /var/log -type f -name "*.gz" -delete 2>/dev/null || true
find /var/log -type f -name "*.1" -delete 2>/dev/null || true
find /var/log -type f -name "*.2" -delete 2>/dev/null || true
find /var/log -type f -name "*.3" -delete 2>/dev/null || true

# Journal logs
journalctl --rotate 2>/dev/null || true
journalctl --vacuum-time=1s 2>/dev/null || true

# Docker logs
find /var/lib/docker/containers -name "*-json.log" -exec truncate -s 0 {} \; 2>/dev/null || true

ok "Logs cleared"

# ---------------------------------------------------------------------------
# Step 4: Clear temp files
# ---------------------------------------------------------------------------
step "Clearing Temp Files"

rm -rf /tmp/* 2>/dev/null || true
rm -rf /var/tmp/* 2>/dev/null || true
rm -rf /var/cache/apt/archives/*.deb 2>/dev/null || true

ok "Temp files cleared"

# ---------------------------------------------------------------------------
# Step 5: Clear shell history
# ---------------------------------------------------------------------------
step "Clearing Shell History"

# Root history
history -c 2>/dev/null || true
rm -f /root/.bash_history 2>/dev/null || true
rm -f /root/.cache/powershell/History 2>/dev/null || true

# All user histories
find /home -name ".bash_history" -delete 2>/dev/null || true
find /home -name ".zsh_history" -delete 2>/dev/null || true

# Clear history in current session
unset HISTFILE 2>/dev/null || true

ok "Shell history cleared"

# ---------------------------------------------------------------------------
# Step 6: Clean package cache
# ---------------------------------------------------------------------------
step "Cleaning Package Cache"

apt-get autoremove -y 2>/dev/null || true
apt-get clean 2>/dev/null || true
rm -rf /var/lib/apt/lists/*

ok "Package cache cleaned"

# ---------------------------------------------------------------------------
# Step 7: Clear network configuration (for template)
# ---------------------------------------------------------------------------
step "Resetting Network Configuration"

# Remove DHCP leases
rm -f /var/lib/dhcp/* 2>/dev/null || true
rm -f /var/lib/dhclient/* 2>/dev/null || true

# Remove machine-specific network config
# (Proxmox will inject new config on clone)
if [[ -f /etc/network/interfaces ]]; then
    cat > /etc/network/interfaces << 'NETCFG'
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp
NETCFG
fi

ok "Network reset for template"

# ---------------------------------------------------------------------------
# Step 8: Clear machine IDs
# ---------------------------------------------------------------------------
step "Clearing Machine IDs"

truncate -s 0 /etc/machine-id 2>/dev/null || true
rm -f /var/lib/dbus/machine-id 2>/dev/null || true

ok "Machine IDs cleared"

# ---------------------------------------------------------------------------
# Step 9: Remove SSH host keys
# ---------------------------------------------------------------------------
step "Removing SSH Host Keys"

rm -f /etc/ssh/ssh_host_*

ok "SSH host keys removed"

# ---------------------------------------------------------------------------
# Step 10: Remove state files
# ---------------------------------------------------------------------------
step "Removing State Files"

rm -f /var/lib/mission-control/.initialized 2>/dev/null || true
rm -f /var/lib/mission-control/.setup-complete 2>/dev/null || true
rm -f /var/lib/mission-control/.installed 2>/dev/null || true

ok "State files removed"

# ---------------------------------------------------------------------------
# Step 11: Zero free space (aggressive mode)
# ---------------------------------------------------------------------------
if [[ "${AGGRESSIVE}" == "true" ]]; then
    step "Zeroing Free Space (this may take a while)"

    # Create a large zero file to fill free space
    dd if=/dev/zero of=/zero.fill bs=1M 2>/dev/null || true
    rm -f /zero.fill

    # Sync to disk
    sync

    ok "Free space zeroed (template will compress better)"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
step "Template Preparation Complete"

echo ""
echo -e "${GREEN}Container is ready for template conversion.${NC}"
echo ""
echo "  Next steps:"
echo "    1. Shut down:  pct shutdown <VMID>"
echo "    2. Template:   pct template <VMID>"
echo "    3. Clone:      pct clone <VMID> <NEW_VMID>"
echo "    4. Start:      pct start <NEW_VMID>"
echo "    5. First boot: Mission Control will auto-configure"
echo ""
echo "  The first-boot script will:"
echo "    - Generate unique secrets"
echo "    - Create admin account"
echo "    - Start all services"
echo "    - Display access URL and credentials"
echo ""
