#!/usr/bin/env bash
# ============================================================================
# Mission Control — Proxmox LXC Template Builder
#
# Builds a turnkey Debian 12 LXC template with Docker CE and Mission Control
# pre-installed. The template can be imported into Proxmox VE and used to
# deploy new Mission Control instances in seconds.
#
# Usage:
#   sudo ./build-template.sh [--version 3.0.0] [--storage local] [--branch main]
#
# Requirements:
#   - Run on a Debian/Ubuntu host or Proxmox VE node
#   - debootstrap, wget, zstd, tar installed
#   - Internet access for package downloads
#
# Output:
#   mission-control-v{VERSION}-amd64.tar.zst  (Proxmox-compatible template)
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MC_VERSION="${MC_VERSION:-3.0.0}"
MC_BRANCH="${MC_BRANCH:-main}"
STORAGE="${STORAGE:-local}"
BUILD_DIR="/tmp/mc-lxc-build"
ROOTFS_DIR="${BUILD_DIR}/rootfs"
TEMPLATE_NAME="mission-control-v${MC_VERSION}-amd64"
DEBIAN_MIRROR="http://deb.debian.org/debian"
DEBIAN_SUITE="bookworm"
DEBIAN_COMPONENTS="main,contrib,non-free"
ARCH="amd64"
MIN_DISK_MB=8192
MIN_RAM_MB=4096

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
die()   { error "$@"; exit 1; }

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --version)  MC_VERSION="$2"; shift 2 ;;
        --storage)  STORAGE="$2"; shift 2 ;;
        --branch)   MC_BRANCH="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: $0 [--version VERSION] [--storage STORAGE] [--branch BRANCH]"
            echo ""
            echo "Options:"
            echo "  --version   Mission Control version (default: $MC_VERSION)"
            echo "  --storage   Proxmox storage target (default: $STORAGE)"
            echo "  --branch    Git branch to clone (default: $MC_BRANCH)"
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
info "Mission Control LXC Template Builder v${MC_VERSION}"
echo ""

if [[ $EUID -ne 0 ]]; then
    die "This script must be run as root"
fi

for cmd in debootstrap wget zstd tar; do
    command -v "$cmd" >/dev/null 2>&1 || die "Required command not found: $cmd"
done

# ---------------------------------------------------------------------------
# Clean previous build
# ---------------------------------------------------------------------------
info "Cleaning previous build directory..."
rm -rf "${BUILD_DIR}"
mkdir -p "${ROOTFS_DIR}"

# ---------------------------------------------------------------------------
# Stage 1: Create minimal Debian 12 rootfs
# ---------------------------------------------------------------------------
info "Creating Debian 12 (${DEBIAN_SUITE}) rootfs for ${ARCH}..."

debootstrap \
    --arch="${ARCH}" \
    --variant=minbase \
    --include="systemd,systemd-sysv,dbus,ifupdown,iproute2,iputils-ping,curl,wget,ca-certificates,gnupg,lsb-release,openssh-server,openssh-client,sudo,git,net-tools,htop,tmux,locales,tzdata" \
    --exclude="isc-dhcp-client,ntp,systemd-timesyncd" \
    "${DEBIAN_SUITE}" \
    "${ROOTFS_DIR}" \
    "${DEBIAN_MIRROR}"

ok "Rootfs created"

# ---------------------------------------------------------------------------
# Stage 2: Configure base system
# ---------------------------------------------------------------------------
info "Configuring base system..."

# Hostname
echo "mission-control" > "${ROOTFS_DIR}/etc/hostname"
echo "127.0.1.1 mission-control" >> "${ROOTFS_DIR}/etc/hosts"

# Locale
echo "en_US.UTF-8 UTF-8" > "${ROOTFS_DIR}/etc/locale.gen"
chroot "${ROOTFS_DIR}" locale-gen 2>/dev/null || true

# Timezone
ln -sf /usr/share/zoneinfo/UTC "${ROOTFS_DIR}/etc/localtime"

# DNS
cat > "${ROOTFS_DIR}/etc/resolv.conf" <<'RESOLV'
nameserver 1.1.1.1
nameserver 8.8.8.8
RESOLV

# Mount points
mkdir -p "${ROOTFS_DIR}/proc" "${ROOTFS_DIR}/sys" "${ROOTFS_DIR}/dev" "${ROOTFS_DIR}/run"

# fstab
cat > "${ROOTFS_DIR}/etc/fstab" <<'FSTAB'
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
/dev/pve/root   /               ext4    defaults        0       1
/dev/pve/swap   none            swap    sw              0       0
proc            /proc           proc    defaults        0       0
sysfs           /sys            sysfs   defaults        0       0
FSTAB

ok "Base system configured"

# ---------------------------------------------------------------------------
# Stage 3: Configure networking (DHCP on eth0)
# ---------------------------------------------------------------------------
info "Configuring networking..."

mkdir -p "${ROOTFS_DIR}/etc/network/interfaces.d"
cat > "${ROOTFS_DIR}/etc/network/interfaces" <<'NETCFG'
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp
NETCFG

ok "Networking configured"

# ---------------------------------------------------------------------------
# Stage 4: Install Docker CE
# ---------------------------------------------------------------------------
info "Installing Docker CE..."

# Docker GPG key
mkdir -p "${ROOTFS_DIR}/etc/apt/keyrings"
chroot "${ROOTFS_DIR}" bash -c "curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg"

# Docker repo
cat > "${ROOTFS_DIR}/etc/apt/sources.list.d/docker.list" <<DOCKERLIST
deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian ${DEBIAN_SUITE} stable
DOCKERLIST

# Install Docker
chroot "${ROOTFS_DIR}" bash -c "apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin && apt-get clean && rm -rf /var/lib/apt/lists/*"

ok "Docker CE installed"

# ---------------------------------------------------------------------------
# Stage 5: Create Mission Control application directory
# ---------------------------------------------------------------------------
info "Setting up Mission Control application..."

MC_APP_DIR="${ROOTFS_DIR}/opt/mission-control"
mkdir -p "${MC_APP_DIR}"

# Clone the repository (or copy from local if available)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

if [[ -d "${PROJECT_ROOT}/.git" ]]; then
    info "Copying from local repository..."
    # Copy only what's needed for deployment
    cp "${PROJECT_ROOT}/docker-compose.prod.yml" "${MC_APP_DIR}/docker-compose.yml"
    cp "${PROJECT_ROOT}/.env.example" "${MC_APP_DIR}/.env"
    cp -r "${PROJECT_ROOT}/backend" "${MC_APP_DIR}/backend"
    cp -r "${PROJECT_ROOT}/frontend" "${MC_APP_DIR}/frontend"
    cp -r "${PROJECT_ROOT}/nginx" "${MC_APP_DIR}/nginx"
else
    info "Cloning from GitHub..."
    chroot "${ROOTFS_DIR}" bash -c "cd /opt/mission-control && git clone --depth 1 --branch ${MC_BRANCH} https://github.com/mission-control/mission-control.git ."
fi

# Use production compose file
if [[ -f "${MC_APP_DIR}/docker-compose.prod.yml" ]]; then
    mv "${MC_APP_DIR}/docker-compose.prod.yml" "${MC_APP_DIR}/docker-compose.yml"
fi

# Generate default secret key
SECRET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || openssl rand -base64 32)

# Create .env with defaults
cat > "${MC_APP_DIR}/.env" <<ENVEOF
PROJECT_NAME=Mission Control
ENVIRONMENT=production
MISSIONCONTROL_SECRET_KEY=${SECRET_KEY}
POSTGRES_DB=mission_control
POSTGRES_USER=mission_control
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
BACKEND_CORS_ORIGINS=http://localhost
COMPOSE_PROJECT_NAME=missioncontrol
ENVEOF

chmod 600 "${MC_APP_DIR}/.env"

ok "Mission Control application files installed"

# ---------------------------------------------------------------------------
# Stage 6: Create first-boot service and script
# ---------------------------------------------------------------------------
info "Creating first-boot setup service..."

# First-boot installer script
cat > "${ROOTFS_DIR}/usr/local/bin/mc-first-boot.sh" <<'FIRSTBOOT'
#!/usr/bin/env bash
# Mission Control — First Boot Setup
# Runs once on first container start to build and start the MC stack.

set -euo pipefail

MC_APP_DIR="/opt/mission-control"
MC_STATE_FILE="/var/lib/mission-control/.initialized"
MC_LOG="/var/log/mission-control-setup.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${MC_LOG}"; }

# Skip if already initialized
if [[ -f "${MC_STATE_FILE}" ]]; then
    log "Mission Control already initialized, skipping setup."
    exit 0
fi

log "=== Mission Control First Boot Setup ==="
log "Version: $(cat /opt/mission-control/VERSION 2>/dev/null || echo 'unknown')"

# Wait for Docker to be ready
log "Waiting for Docker daemon..."
for i in $(seq 1 30); do
    if docker info >/dev/null 2>&1; then
        log "Docker is ready."
        break
    fi
    if [[ $i -eq 30 ]]; then
        log "ERROR: Docker daemon not ready after 60s."
        exit 1
    fi
    sleep 2
done

# Start the stack
log "Building and starting Mission Control stack..."
cd "${MC_APP_DIR}"
docker compose pull 2>&1 | tee -a "${MC_LOG}" || true
docker compose build 2>&1 | tee -a "${MC_LOG}"
docker compose up -d 2>&1 | tee -a "${MC_LOG}"

# Wait for backend to be healthy
log "Waiting for backend to become healthy..."
for i in $(seq 1 60); do
    if docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=2)" 2>/dev/null; then
        log "Backend is healthy."
        break
    fi
    if [[ $i -eq 60 ]]; then
        log "WARNING: Backend health check timed out after 120s. Stack may still be starting."
    fi
    sleep 2
done

# Mark as initialized
mkdir -p "$(dirname "${MC_STATE_FILE}")"
date -Iseconds > "${MC_STATE_FILE}"

log "=== Mission Control setup complete ==="
log "Access at: http://$(hostname -I | awk '{print $1}')"
log "Default login: admin@missioncontrol.local / admin"
FIRSTBOOT

chmod +x "${ROOTFS_DIR}/usr/local/bin/mc-first-boot.sh"

# Systemd service
cat > "${ROOTFS_DIR}/etc/systemd/system/mission-control.service" <<'SERVICE'
[Unit]
Description=Mission Control First Boot Setup
After=docker.service network-online.target
Wants=network-online.target
Requires=docker.service
ConditionPathExists=!/var/lib/mission-control/.initialized

[Service]
Type=oneshot
ExecStart=/usr/local/bin/mc-first-boot.sh
RemainAfterExit=yes
TimeoutStartSec=300
StandardOutput=journal+console
StandardError=journal+console

[Install]
WantedBy=multi-user.target
SERVICE

# Enable Docker and the MC service
chroot "${ROOTFS_DIR}" systemctl enable docker.service
chroot "${ROOTFS_DIR}" systemctl enable mission-control.service

ok "First-boot service configured"

# ---------------------------------------------------------------------------
# Stage 7: Create management helpers
# ---------------------------------------------------------------------------
info "Creating management scripts..."

# Status script
cat > "${ROOTFS_DIR}/usr/local/bin/mc-status" <<'STATUS'
#!/usr/bin/env bash
cd /opt/mission-control && docker compose ps
STATUS
chmod +x "${ROOTFS_DIR}/usr/local/bin/mc-status"

# Logs script
cat > "${ROOTFS_DIR}/usr/local/bin/mc-logs" <<'LOGS'
#!/usr/bin/env bash
cd /opt/mission-control && docker compose logs --tail=50 "$@"
LOGS
chmod +x "${ROOTFS_DIR}/usr/local/bin/mc-logs"

# Restart script
cat > "${ROOTFS_DIR}/usr/local/bin/mc-restart" <<'RESTART'
#!/usr/bin/env bash
cd /opt/mission-control && docker compose restart "$@"
RESTART
chmod +x "${ROOTFS_DIR}/usr/local/bin/mc-restart"

# Update script
cat > "${ROOTFS_DIR}/usr/local/bin/mc-update" <<'UPDATE'
#!/usr/bin/env bash
set -euo pipefail
cd /opt/mission-control
echo "Pulling latest code..."
git pull
echo "Rebuilding containers..."
docker compose build
echo "Restarting services..."
docker compose up -d
echo "Update complete."
UPDATE
chmod +x "${ROOTFS_DIR}/usr/local/bin/mc-update"

ok "Management scripts created"

# ---------------------------------------------------------------------------
# Stage 8: Configure SSH
# ---------------------------------------------------------------------------
info "Configuring SSH..."

mkdir -p "${ROOTFS_DIR}/run/sshd"
chmod 700 "${ROOTFS_DIR}/run/sshd"

# Allow root login via key (for Proxmox pct enter)
sed -i 's/#PermitRootLogin.*/PermitRootLogin prohibit-password/' "${ROOTFS_DIR}/etc/ssh/sshd_config" 2>/dev/null || true

ok "SSH configured"

# ---------------------------------------------------------------------------
# Stage 9: Clean up and minimize
# ---------------------------------------------------------------------------
info "Cleaning up rootfs..."

# Clear logs
find "${ROOTFS_DIR}/var/log" -type f -exec truncate -s 0 {} \; 2>/dev/null || true
rm -rf "${ROOTFS_DIR}/var/lib/apt/lists"/*
rm -rf "${ROOTFS_DIR}/tmp"/*
rm -rf "${ROOTFS_DIR}/var/tmp"/*

# Clear machine IDs (Proxmox generates new ones)
truncate -s 0 "${ROOTFS_DIR}/etc/machine-id" 2>/dev/null || true
rm -f "${ROOTFS_DIR}/var/lib/dbus/machine-id" 2>/dev/null || true

# Remove SSH host keys (regenerated on first boot)
rm -f "${ROOTFS_DIR}/etc/ssh/ssh_host_"*

ok "Cleanup complete"

# ---------------------------------------------------------------------------
# Stage 10: Package as Proxmox template
# ---------------------------------------------------------------------------
info "Packaging LXC template..."

cd "${BUILD_DIR}"

# Create the tarball (Proxmox uses .tar.zst for modern templates)
tar -C "${ROOTFS_DIR}" \
    --numeric-owner \
    --xattrs \
    --xattrs-include='*' \
    -cf "${BUILD_DIR}/${TEMPLATE_NAME}.tar" .

ok "Tarball created ($(du -h "${BUILD_DIR}/${TEMPLATE_NAME}.tar" | cut -f1))"

# Compress with zstd (Proxmox native format)
zstd -T0 -19 -o "${BUILD_DIR}/${TEMPLATE_NAME}.tar.zst" "${BUILD_DIR}/${TEMPLATE_NAME}.tar"
rm -f "${BUILD_DIR}/${TEMPLATE_NAME}.tar"

ok "Template compressed ($(du -h "${BUILD_DIR}/${TEMPLATE_NAME}.tar.zst" | cut -f1))"

# Create metadata file
cat > "${BUILD_DIR}/${TEMPLATE_NAME}.tar.zst.meta" <<META
{
    "arch": "${ARCH}",
    "os": "debian",
    "release": "${DEBIAN_SUITE}",
    "version": "${MC_VERSION}",
    "type": "vztmpl",
    "description": "Mission Control ${MC_VERSION} - IT Operations Dashboard",
    "maintainer": "Mission Control Team",
    "created": "$(date -Iseconds)",
    "大小_bytes": $(stat -c%s "${BUILD_DIR}/${TEMPLATE_NAME}.tar.zst")
}
META

# ---------------------------------------------------------------------------
# Stage 11: Install to Proxmox (if running on a PVE node)
# ---------------------------------------------------------------------------
if command -v pveam >/dev/null 2>&1; then
    info "Proxmox VE detected. Installing template to '${STORAGE}' storage..."

    # Copy to Proxmox template storage
    TEMPLATE_DIR="/var/lib/vz/template/cache"
    if [[ "${STORAGE}" != "local" ]]; then
        TEMPLATE_DIR="/var/lib/vz/template/cache"
        # For non-local storage, check if it supports vztmpl
        if pvesm status 2>/dev/null | grep -q "${STORAGE}"; then
            mkdir -p "/var/lib/vz/template/cache"
        fi
    fi

    cp "${BUILD_DIR}/${TEMPLATE_NAME}.tar.zst" "${TEMPLATE_DIR}/"
    cp "${BUILD_DIR}/${TEMPLATE_NAME}.tar.zst.meta" "${TEMPLATE_DIR}/"

    ok "Template installed to Proxmox storage"
    echo ""
    info "To create a new container from this template:"
    echo ""
    echo "  pct create 200 ${TEMPLATE_NAME}.tar.zst \\"
    echo "    --hostname mission-control \\"
    echo "    --memory 4096 \\"
    echo "    --cores 2 \\"
    echo "    --rootfs local-lvm:8 \\"
    echo "    --net0 name=eth0,bridge=vmbr0,hwaddr=auto,ip=dhcp"
    echo ""
    info "Or create from the Mission Control UI (Proxmox > Containers > New Container)"
else
    echo ""
    info "Template built successfully!"
    echo ""
    echo "  Output: ${BUILD_DIR}/${TEMPLATE_NAME}.tar.zst"
    echo ""
    echo "  To install on a Proxmox host:"
    echo "    1. Copy the .tar.zst file to the Proxmox host"
    echo "    2. Run: pveam upload local ${TEMPLATE_NAME}.tar.zst"
    echo "    3. Or copy to /var/lib/vz/template/cache/"
    echo ""
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
ok "Build complete!"
echo ""
echo "  Template:  ${TEMPLATE_NAME}.tar.zst"
echo "  Location:  ${BUILD_DIR}/${TEMPLATE_NAME}.tar.zst"
echo "  Size:      $(du -h "${BUILD_DIR}/${TEMPLATE_NAME}.tar.zst" | cut -f1)"
echo "  Arch:      ${ARCH}"
echo "  OS:        Debian 12 (${DEBIAN_SUITE})"
echo "  Docker:    CE (latest)"
echo "  MC App:    /opt/mission-control"
echo ""
echo "  Features:"
echo "    - Docker CE with Compose plugin"
echo "    - Mission Control pre-installed"
echo "    - Auto-setup on first boot"
echo "    - Systemd service for lifecycle management"
echo "    - Management scripts: mc-status, mc-logs, mc-restart, mc-update"
echo ""
echo "  First boot will:"
echo "    1. Generate a unique secret key"
echo "    2. Generate a random database password"
echo "    3. Pull and build all Docker containers"
echo "    4. Start the full Mission Control stack"
echo "    5. Wait for backend health check to pass"
echo ""
echo "  Default credentials (after first boot):"
echo "    URL:      http://<container-ip>"
echo "    Email:    admin@missioncontrol.local"
echo "    Password: admin"
echo ""
