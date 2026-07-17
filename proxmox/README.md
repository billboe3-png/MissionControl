# Mission Control — Proxmox LXC Template

Deploy Mission Control as an LXC container on Proxmox VE. The template includes Docker CE, Docker Compose, and a first-boot installer that configures the full stack automatically.

## Quick Start

### Build the template (on a Debian/Ubuntu host or Proxmox node)

```bash
cd proxmox
sudo ./build-template.sh --version 3.0.0
```

### Deploy a new container

**From the Proxmox CLI:**

```bash
# If built on the PVE host, the template is already in the cache
pct create 200 mission-control-v3.0.0-amd64.tar.zst \
  --hostname mission-control \
  --memory 4096 \
  --cores 2 \
  --rootfs local-lvm:8 \
  --net0 name=eth0,bridge=vmbr0,hwaddr=auto,ip=dhcp,type=veth \
  --features nesting=1,fuse=1

# Start the container
pct start 200

# Watch first-boot setup
pct exec 200 -- journalctl -u mission-control -f
```

**From the Mission Control UI:**

1. Navigate to Proxmox > Containers
2. Click "New Container"
3. Select "Mission Control" from the template list
4. Configure resources (CPU, RAM, disk, network)
5. Click "Create & Start"

### Access

After first-boot setup completes (~2-3 minutes):

- **URL:** `http://<container-ip>`
- **Email:** `admin@missioncontrol.local`
- **Password:** `admin`

## Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 8 GB | 20 GB |
| Network | DHCP | Static IP |

**Proxmox features required:** `nesting=1` (for Docker-in-LXC)

## Architecture

```
LXC Container (Debian 12)
├── Docker CE
│   ├── nginx:1.27-alpine      (port 80)
│   ├── backend (FastAPI)      (port 8000, internal)
│   ├── frontend (React/Vite)  (port 3000, internal)
│   ├── postgres:16-alpine     (port 5432, internal)
│   └── redis:7.2-alpine       (port 6379, internal)
├── /opt/mission-control/      (app directory)
│   ├── docker-compose.yml
│   ├── .env                   (auto-generated secrets)
│   ├── backend/
│   ├── frontend/
│   └── nginx/
└── /usr/local/bin/
    ├── mc-status              (show container status)
    ├── mc-logs                (view logs)
    ├── mc-restart             (restart services)
    └── mc-update              (pull updates and rebuild)
```

## First Boot

On first start, the `mission-control.service` systemd unit runs automatically:

1. Waits for Docker daemon to be ready
2. Generates unique secret key and database password
3. Pulls Docker images
4. Builds application containers
5. Starts the full stack
6. Waits for backend health check
7. Marks initialization complete

Monitor progress: `pct exec 200 -- journalctl -u mission-control -f`

## Management

```bash
# Enter the container
pct enter 200

# Check status
mc-status

# View logs
mc-logs
mc-logs backend
mc-logs postgres

# Restart services
mc-restart
mc-restart backend

# Update to latest version
mc-update

# Full stack restart
systemctl restart docker
cd /opt/mission-control && docker compose up -d
```

## Template Builder Options

```bash
sudo ./build-template.sh [OPTIONS]

Options:
  --version VERSION    Mission Control version (default: 3.0.0)
  --storage STORAGE    Proxmox storage target (default: local)
  --branch BRANCH      Git branch to clone (default: main)
  --help, -h           Show this help
```

## Production Hardening

For production deployments:

1. **Use a static IP** — Configure `net0` with a static IP address
2. **Separate storage** — Mount a dedicated volume for PostgreSQL data:
   ```
   mp0: local-lvm:20,mp=/opt/mission-control/data
   ```
3. **Change default password** — Login and change the admin password immediately
4. **Enable HTTPS** — Configure a reverse proxy (Traefik, Caddy) in front of the container
5. **Backup** — Use Proxmox backup or `mc-backup` for database dumps
6. **Resource limits** — Adjust Docker Compose resource limits in `docker-compose.yml`

## Troubleshooting

**Container won't start:**
- Ensure `nesting=1` is set: `pct set 200 --features nesting=1`
- Check Docker is running: `pct exec 200 -- systemctl status docker`

**First boot hangs:**
- Check logs: `pct exec 200 -- journalctl -u mission-control -f`
- Check Docker build: `pct exec 200 -- cd /opt/mission-control && docker compose build`

**Backend health check fails:**
- Check backend logs: `pct exec 200 -- cd /opt/mission-control && docker compose logs backend`
- Verify database: `pct exec 200 -- cd /opt/mission-control && docker compose exec postgres pg_isready`

**Network issues:**
- Verify bridge: `pct exec 200 -- ip addr show eth0`
- Test connectivity: `pct exec 200 -- ping -c 3 1.1.1.1`
