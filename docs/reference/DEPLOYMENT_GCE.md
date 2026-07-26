# Google Cloud Engine (GCE) Deployment

Deploy Mission Control to Google Cloud Engine using Compute Engine VMs with Docker.

---

## Architecture

```
┌──────────────────────────────────────────────┐
│           GCE Project: d45cb447              │
│           Region: africa-south1-b            │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  VM Instance: mission-control-prod     │  │
│  │  IP: 34.35.177.209                     │  │
│  │  OS: Ubuntu 22.04 LTS                  │  │
│  │                                         │  │
│  │  ┌──────────┐  ┌──────────────────┐   │  │
│  │  │  Nginx   │  │  Docker Compose  │   │  │
│  │  │  :80/443 │──│  Backend :8000   │   │  │
│  │  └──────────┘  │  Frontend :3000  │   │  │
│  │                │  PostgreSQL       │   │  │
│  │                │  Redis            │   │  │
│  │                └──────────────────┘   │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Firewall │  │  Cloud   │  │  Cloud   │  │
│  │  Rules   │  │  DNS     │  │  Storage │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└──────────────────────────────────────────────┘
```

---

## Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed and authenticated
- Domain name (optional, for SSL)

### Install gcloud CLI

```bash
# Linux/macOS
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Windows
# Download installer from https://cloud.google.com/sdk/docs/install
```

### Authenticate

```bash
gcloud auth login
gcloud config set project d45cb447-615c-4280-b8c0
```

---

## Step 1: Create the VM Instance

```bash
gcloud compute instances create mission-control-prod \
  --zone=africa-south1-b \
  --machine-type=e2-standard-4 \
  --network-interface=network-tier=PREMIUM,subnet=default \
  --maintenance-policy=MIGRATE \
  --provisioning-model=STANDARD \
  --service-account=mission-control-sa@d45cb447-615c-4280-b8c0.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --create-disk=auto-delete=yes,boot=yes,device-name=mission-control-prod,image=projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts,mode=rw,size=50,type=projects/d45cb447-615c-4280-b8c0/zones/africa-south1-b/diskTypes/pd-ssd \
  --no-shielded-secure-boot \
  --shielded-vtpm \
  --shielded-integrity-monitoring \
  --reservation-affinity=any \
  --tags=mission-control,http-server,https-server
```

### VM Specifications

| Setting | Value |
|---------|-------|
| Name | `mission-control-prod` |
| Zone | `africa-south1-b` |
| Machine Type | `e2-standard-4` (4 vCPU, 16 GB RAM) |
| Disk | 50 GB SSD |
| OS | Ubuntu 22.04 LTS |
| External IP | `34.35.177.209` |

---

## Step 2: Configure Firewall Rules

```bash
# Allow HTTP
gcloud compute firewall-rules create allow-http \
  --allow tcp:80 \
  --target-tags=http-server \
  --description="Allow HTTP traffic"

# Allow HTTPS
gcloud compute firewall-rules create allow-https \
  --allow tcp:443 \
  --target-tags=https-server \
  --description="Allow HTTPS traffic"

# Allow SSH
gcloud compute firewall-rules create allow-ssh \
  --allow tcp:22 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=mission-control \
  --description="Allow SSH access"

# Allow agent connections (API key auth)
gcloud compute firewall-rules create allow-agents \
  --allow tcp:8000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=mission-control \
  --description="Allow agent API connections"
```

### Verify Firewall Rules

```bash
gcloud compute firewall-rules list --filter="targetTags:mission-control"
```

---

## Step 3: SSH and Install Docker

```bash
# SSH into the VM
gcloud compute ssh billboe3@34.35.177.209 --zone=africa-south1-b
```

### Install Docker Engine

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install prerequisites
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

### Optimize for Production

```bash
# Configure Docker daemon
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  },
  "storage-driver": "overlay2",
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 65536
    }
  }
}
EOF

sudo systemctl restart docker
```

---

## Step 4: Deploy Mission Control

### Clone Repository

```bash
cd /home/billboe3
git clone https://github.com/your-org/mission-control.git
cd mission-control
```

### Configure Environment

```bash
cp .env.example .env

# Generate secure secrets
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

## Step 5: SSL with Let's Encrypt

### Install Certbot

```bash
sudo apt install -y certbot
```

### Obtain Certificate

```bash
sudo certbot certonly --standalone \
  -d your-domain.com \
  -d www.your-domain.com \
  --email admin@your-domain.com \
  --agree-tos \
  --non-interactive
```

### Configure Nginx with SSL

```bash
sudo tee /etc/nginx/sites-available/mission-control << 'EOF'
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
    ssl_prefer_server_ciphers on;

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

sudo ln -s /etc/nginx/sites-available/mission-control /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Auto-Renew Certificate

```bash
sudo tee /etc/cron.d/certbot << 'EOF'
0 0,12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF
```

---

## Step 6: Backup Configuration

### Automated Database Backups

```bash
sudo tee /opt/mission-control/backup.sh << 'SCRIPT'
#!/bin/bash
set -e

BACKUP_DIR="/opt/backups/mission-control"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker exec mc-postgres pg_dump -U mission_control mission_control | \
  gzip > $BACKUP_DIR/db_${DATE}.sql.gz

# Redis backup
docker exec mc-redis redis-cli -a $REDIS_PASSWORD BGSAVE

# Storage backup
docker run --rm -v mc-backend-storage:/data -v $BACKUP_DIR:/backup alpine \
  tar czf /backup/storage_${DATE}.tar.gz -C /data .

# Upload to Google Cloud Storage
gsutil cp $BACKUP_DIR/db_${DATE}.sql.gz gs://mission-control-backups/db/
gsutil cp $BACKUP_DIR/storage_${DATE}.tar.gz gs://mission-control-backups/storage/

# Cleanup local backups older than 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
SCRIPT

sudo chmod +x /opt/mission-control/backup.sh
```

### Schedule Backups

```bash
sudo tee /etc/cron.d/mc-backup << 'EOF'
0 2 * * * root /opt/mission-control/backup.sh >> /var/log/mission-control-backup.log 2>&1
EOF
```

### Create GCS Bucket

```bash
gsutil mb -l africa-south1 gs://mission-control-backups
gsutil lifecycle set /dev/stdin gs://mission-control-backups << 'JSON'
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 30}
    }
  ]
}
JSON
```

---

## Step 7: Monitoring

### Enable Cloud Monitoring

```bash
# Install the Ops Agent
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install
```

### Configure Log Collection

```bash
sudo tee /etc/google-cloud-ops-agent/config.yaml << 'EOF'
logging:
  receivers:
    docker_logs:
      type: files
      include_paths:
        - /var/lib/docker/containers/**/*-json.log
    nginx_access:
      type: files
      include_paths:
        - /var/log/nginx/access.log
    nginx_error:
      type: files
      include_paths:
        - /var/log/nginx/error.log
    mission_control:
      type: files
      include_paths:
        - /opt/mission-control/logs/*.log
  service:
    pipelines:
      default_pipeline:
        receivers: [docker_logs, nginx_access, nginx_error, mission_control]

metrics:
  receivers:
    hostmetrics:
      type: hostmetrics
      collection_interval: 60s
  service:
    pipelines:
      default_pipeline:
        receivers: [hostmetrics]
EOF

sudo systemctl restart google-cloud-ops-agent
```

### Create Uptime Check

```bash
gcloud monitoring uptime create \
  --display-name="Mission Control Health" \
  --resource-type=uptime-url \
  --hostname=your-domain.com \
  --path=/api/v1/health \
  --check-interval=60 \
  --timeout=10
```

### Set Up Alerting

```bash
gcloud alpha monitoring policies create \
  --notification-channels="YOUR_CHANNEL_ID" \
  --condition-display-name="VM CPU High" \
  --condition-filter='metric.type="compute.googleapis.com/instance/cpu/utilization" AND resource.type="gce_instance"' \
  --condition-threshold-value=0.8 \
  --condition-threshold-duration=300s
```

---

## Maintenance

### SSH Access

```bash
gcloud compute ssh billboe3@34.35.177.209 --zone=africa-south1-b
```

### Update Mission Control

```bash
cd /home/billboe3/mission-control
git pull origin main
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```

### View Logs

```bash
docker compose -f docker-compose.prod.yml logs -f backend
sudo tail -f /var/log/nginx/access.log
```

### Resource Monitoring

```bash
# Docker stats
docker stats

# System resources
htop

# Disk usage
df -h
docker system df
```

---

## Cost Estimation

| Resource | Specification | Monthly Cost (approx) |
|----------|---------------|----------------------|
| e2-standard-4 | 4 vCPU, 16 GB RAM | ~$120 |
| 50 GB SSD | Persistent disk | ~$10 |
| Static IP | Regional external IP | ~$7 |
| Network | Egress (100 GB) | ~$12 |
| **Total** | | **~$149/month** |

---

## Related Documentation

- [DEPLOYMENT_DOCKER.md](./DEPLOYMENT_DOCKER.md) — Docker Compose reference
- [AUTHENTICATION.md](./AUTHENTICATION.md) — JWT and API key setup
- [HEARTBEAT_API.md](./HEARTBEAT_API.md) — Agent heartbeat configuration
- [REST_API.md](./REST_API.md) — API endpoint reference
