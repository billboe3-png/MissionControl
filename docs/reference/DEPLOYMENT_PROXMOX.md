# Proxmox LXC Deployment Guide

Deploy Mission Control to a Proxmox VE host using Linux Containers (LXC) for lightweight, efficient resource usage.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│               Proxmox VE Host                        │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │         LXC Container (Ubuntu 22.04)          │   │
│  │         mission-control-prod                   │   │
│  │         IP: 192.168.1.100                     │   │
│  │                                               │   │
│  │  ┌──────────┐  ┌────────────────────────┐   │   │
│  │  │  Nginx   │  │  Docker Compose         │   │   │
│  │  │  :80/443 │──│  Backend :8000          │   │   │
│  │  └──────────┘  │  Frontend :3000         │   │   │
│  │                │  PostgreSQL :5432        │   │   │
│  │                │  Redis :6379             │   │   │
│  │                └────────────────────────┘   │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │         ZFS Storage / Thin Pool              │   │
│  │         (Snapshots & Backups)                │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Proxmox VE 7.0+ (8.0 recommended)
- Storage backend: ZFS, ZFS-over-LVM, or thin provisioning
- Network bridge configured (typically `vmbr0`)
- Container template: Ubuntu 22.04

---

## Step 1: Download Container Template

```bash
# Download Ubuntu 22.04 template
pveam update
pveam available | grep ubuntu-22.04
pveam download local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

---

## Step 2: Create LXC Container

### Via Command Line

```bash
# Create container
pct create 200 /local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname mission-control-prod \
  --ostype ubuntu \
  --arch amd64 \
  --cores 4 \
  --memory 8192 \
  --swap 2048 \
  --rootfs local-lvm:32 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.100/24,gw=192.168.1.1,firewall=1 \
  --nameserver 1.1.1.1 \
  --searchdomain local \
  --onboot 1 \
  --startup "order=1" \
  --unprivileged 0 \
  --features "nesting=1,keyctl=1"

# Set root password
pct set 200 --password $(openssl rand -base64 16)

# Start container
pct start 200
```

### Via Web UI

1. Navigate to **Create CT** in Proxmox VE
2. Set container ID to `200`
3. Set hostname to `mission-control-prod`
4. Set password
5. Select template: `ubuntu-22.04-standard_22.04-1_amd64.tar.zst`
6. Set storage to `local-lvm`, size: 32 GB
7. Set cores: 4, memory: 8192 MB, swap: 2048 MB
8. Set network: Bridge `vmbr0`, static IP `192.168.1.100/24`, gateway `192.168.1.1`
9. Enable **nesting** and **keyctl** features
10. Confirm and create

---

## Step 3: Resource Allocation

### Recommended Specs

| Workload | Cores | RAM | Disk | Use Case |
|----------|-------|-----|------|----------|
| Small | 2 | 4 GB | 20 GB | < 10 agents |
| Medium | 4 | 8 GB | 32 GB | 10-50 agents |
| Large | 8 | 16 GB | 50 GB | 50-200 agents |
| XLarge | 16 | 32 GB | 100 GB | 200+ agents |

### Adjust Resources

```bash
# Stop container
pct stop 200

# Increase CPU cores
pct set 200 --cores 8

# Increase memory
pct set 200 --memory 16384

# Expand root disk (if using local-lvm)
pct resize 200 rootfs +20G

# Start container
pct start 200
```

---

## Step 4: Install Docker Inside LXC

### Enter Container

```bash
pct enter 200
```

### Install Docker

```bash
# Update system
apt update && apt upgrade -y

# Install prerequisites
apt install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable Docker
systemctl enable docker
systemctl start docker

# Verify
docker --version
docker compose version
```

### Fix LXC Docker Compatibility

If Docker fails to start due to storage driver issues:

```bash
# Check storage driver
docker info | grep "Storage Driver"

# If overlay2 fails, use vfs (less efficient but works in LXC)
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  }
}
EOF

systemctl restart docker
```

---

## Step 5: Deploy Mission Control

### Clone Repository

```bash
cd /opt
git clone https://github.com/your-org/mission-control.git
cd mission-control
```

### Configure Environment

```bash
cp .env.example .env

# Generate secrets
JWT_SECRET=$(openssl rand -base64 48)
DB_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

cat > .env << EOF
DB_USER=mission_control
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=mission_control
DB_PORT=5432

REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_PORT=6379

JWT_SECRET=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRY=3600
JWT_REFRESH_TOKEN_EXPIRY=2592000

CORS_ORIGINS=https://your-domain.com
LOG_LEVEL=warning
ENVIRONMENT=production
WORKERS=4

VITE_API_URL=https://your-domain.com/api/v1
API_KEY_PREFIX=mc_agent_
EOF
```

### Start Services

```bash
docker compose -f docker-compose.prod.yml up -d

# Verify
docker compose ps
curl http://localhost:8000/api/v1/health
```

---

## Step 6: Configure Reverse Proxy

### Nginx Configuration

```bash
apt install -y nginx

cat > /etc/nginx/sites-available/mission-control << 'EOF'
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
EOF

ln -s /etc/nginx/sites-available/mission-control /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

### SSL with Let's Encrypt

```bash
apt install -y certbot python3-certbot-nginx

certbot --nginx \
  -d your-domain.com \
  -d www.your-domain.com \
  --non-interactive \
  --agree-tos \
  --email admin@your-domain.com

# Auto-renew
crontab -l | { cat; echo "0 0 1 * * certbot renew --quiet --post-hook 'systemctl reload nginx'"; } | crontab -
```

---

## Step 7: Proxmox Backup

### Configure Proxmox Backup

1. Navigate to **Datacenter → Storage → Add → Directory**
2. Set ID: `backup`
3. Set directory: `/mnt/backup`
4. Enable **Content: VZDump backup file**

### Schedule Backups

```bash
# Create backup job
cat > /etc/pve/vzdump.conf << 'EOF'
storage: backup
mode: snapshot
compress: zstd
prune: keep-last=7,keep-daily=7,keep-weekly=4,keep-monthly=6
EOF
```

### Configure via Web UI

1. Navigate to **Datacenter → Backup → Add**
2. Select storage: `backup`
3. Set schedule: `daily, 02:00`
4. Set mode: `Snapshot`
5. Set retention: `keep-last=7, keep-daily=7`
6. Select container: `200 (mission-control-prod)`

### Manual Backup

```bash
# Backup container
vzdump 200 --storage backup --compress zstd

# List backups
ls -la /mnt/vz/dump/
```

### Restore from Backup

```bash
# Stop container
pct stop 200

# Restore
pct restore 200 /mnt/vz/dump/vzdump-lxc-200-*.tar.zst \
  --storage local-lvm

# Start container
pct start 200
```

---

## Step 8: Snapshots

### Create Snapshot

```bash
# Create snapshot before updates
pct snapshot 200 pre-update-20260726

# List snapshots
pct listsnapshot 200
```

### Rollback Snapshot

```bash
# Rollback to snapshot
pct rollback 200 pre-update-20260726

# Start container
pct start 200
```

### Delete Snapshot

```bash
pct delsnapshot 200 pre-update-20260726
```

---

## Step 9: Network Configuration

### Static IP (Already Set)

The container was created with a static IP. To modify:

```bash
pct stop 200

# Change IP
pct set 200 --net0 name=eth0,bridge=vmbr0,ip=192.168.1.101/24,gw=192.168.1.1,firewall=1

pct start 200
```

### Proxmox Firewall

```bash
# Enable Proxmox firewall
pct set 200 --firewall 1

# Configure rules via Web UI or
cat > /etc/pve/lxc/200.conf << 'EOF'
# Container firewall rules
EOF
```

### Firewall via Web UI

1. Navigate to **Datacenter → Firewall → Add**
2. Add rules for ports 80, 443, 8000
3. Apply to container `200`

---

## Step 10: Monitoring and Maintenance

### Container Status

```bash
# Container status
pct status 200

# Container resources
pct exec 200 -- free -h
pct exec 200 -- df -h
```

### Docker Monitoring

```bash
pct exec 200 -- docker stats
```

### Update Mission Control

```bash
pct enter 200
cd /opt/mission-control

# Create snapshot first
exit
pct snapshot 200 pre-update
pct enter 200

# Update
cd /opt/mission-control
git pull origin main
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```

### Log Management

```bash
# View container logs
pct exec 200 -- journalctl -u docker -f

# View application logs
pct exec 200 -- docker compose -f /opt/mission-control/docker-compose.prod.yml logs -f backend
```

---

## Resource Monitoring Script

```bash
cat > /opt/monitor-mc.sh << 'SCRIPT'
#!/bin/bash
echo "=== Mission Control LXC Resource Usage ==="
echo "Container: $(pct status 200)"
echo ""
echo "=== CPU & Memory ==="
pct exec 200 -- top -bn1 | head -5
echo ""
echo "=== Disk Usage ==="
pct exec 200 -- df -h /
echo ""
echo "=== Docker Containers ==="
pct exec 200 -- docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "=== Network Connections ==="
pct exec 200 -- ss -tlnp | grep -E ':(80|443|8000|3000|5432|6379)\s'
SCRIPT

chmod +x /opt/monitor-mc.sh
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check container logs
pct exec 200 -- dmesg | tail -20

# Verify storage
pct status 200

# Check if required features are enabled
pct config 200 | grep -E '(nesting|keyctl)'
```

### Docker Fails to Start in LXC

```bash
# Ensure nesting is enabled
pct set 200 --features "nesting=1,keyctl=1"

# Restart container
pct restart 200

# Check Docker service
pct exec 200 -- systemctl status docker
pct exec 200 -- journalctl -u docker -n 50
```

### Performance Issues

```bash
# Check if using correct storage driver
pct exec 200 -- docker info | grep "Storage Driver"

# Enable I/O limits
pct set 200 --rootfs local-lvm:32,iops_limit=10000,iothread=1

# Check CPU usage
pct exec 200 -- mpstat 1 5
```

---

## Cost Estimation (Self-Hosted)

| Resource | Specification | Cost |
|----------|---------------|------|
| Proxmox Host | Existing hardware | $0 |
| Storage | ZFS pool allocation | $0 (allocated) |
| Network | Existing infrastructure | $0 |
| Power | Estimated 50W additional | ~$5/month |
| **Total** | | **~$5/month** |

---

## Related Documentation

- [DEPLOYMENT_DOCKER.md](./DEPLOYMENT_DOCKER.md) — Docker Compose reference
- [AUTHENTICATION.md](./AUTHENTICATION.md) — JWT and API key setup
- [HEARTBEAT_API.md](./HEARTBEAT_API.md) — Agent heartbeat configuration
- [REST_API.md](./REST_API.md) — API endpoint reference
