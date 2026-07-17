# Mission Control — Installation Guide

## Overview

This guide walks you through installing Mission Control in a Proxmox LXC container. The installer is idempotent — running it twice will not break your installation.

## Prerequisites

### Proxmox Host

- Proxmox VE 7.0+ (tested on 9.2)
- Internet access for Docker image pulls

### LXC Container

| Setting | Value |
|---------|-------|
| OS | Ubuntu 24.04 LTS |
| Type | Unprivileged |
| vCPU | 4 minimum |
| RAM | 8 GB minimum |
| Storage | 80 GB minimum |
| Nesting | Enabled (`features: nesting=1`) |
| Keyctl | Enabled (`features: keyctl=1`) |

See [LXC-REQUIREMENTS.md](LXC-REQUIREMENTS.md) for detailed requirements.

## Step 1: Create the LXC Container

In Proxmox UI or via command line:

```bash
# Create from Ubuntu 24.04 template
pct create 200 local:vztmpl/ubuntu-24.04-standard_24.04.2-1_amd64.tar.zst \
  --hostname mission-control \
  --memory 8192 \
  --cores 4 \
  --rootfs local-lvm:80 \
  --net0 name=eth0,bridge=vmbr0,hwaddr=auto,ip=dhcp

# Enable Docker-required features
pct set 200 -features nesting=1,keyctl=1

# Start the container
pct start 200

# Enter the container
pct enter 200
```

## Step 2: Download the Installer

Inside the LXC container:

```bash
# Install git
apt-get update && apt-get install -y git

# Clone the deployment package
git clone --depth 1 https://github.com/mission-control/mission-control.git /tmp/mc-deploy

# Copy scripts to the install directory
mkdir -p /opt/missioncontrol/scripts
cp /tmp/mc-deploy/deployment/lxc/scripts/*.sh /opt/missioncontrol/scripts/
chmod +x /opt/missioncontrol/scripts/*.sh
```

## Step 3: Run the Installer

```bash
cd /opt/missioncontrol/scripts
sudo ./install.sh
```

The installer will:
1. Create the directory structure
2. Install management scripts
3. Download or copy Docker Compose files
4. Generate secrets and environment configuration
5. Build Docker images
6. Start all services
7. Wait for health checks to pass
8. Create the default admin user

## Step 4: Access Mission Control

After installation completes:

```
URL:      http://<container-ip>
API Docs: http://<container-ip>/api/docs

Login:
  Email:    admin@missioncontrol.local
  Password: admin
```

**Change the default password immediately after first login.**

## Step 5: Verify Installation

```bash
# Check health
mc-health

# Check status
mc-status

# View logs
mc-logs
```

## Post-Installation

### Backup Your .env File

The `.env` file contains your secret key and database password. Back it up:

```bash
cp /opt/missioncontrol/.env /opt/missioncontrol/backups/.env.backup
```

### Configure Static IP (Recommended)

For production, set a static IP:

```bash
# Edit network configuration
nano /etc/network/interfaces

# Set static IP:
auto eth0
iface eth0 inet static
  address 192.168.1.100
  netmask 255.255.255.0
  gateway 192.168.1.1

# Restart networking
systemctl restart networking
```

### Enable HTTPS (Optional)

For TLS termination, update the nginx configuration to use port 443 and provide SSL certificates.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

## Next Steps

- [UPGRADE.md](UPGRADE.md) — Updating Mission Control
- [BACKUP.md](BACKUP.md) — Creating backups
- [RESTORE.md](RESTORE.md) — Restoring from backup
