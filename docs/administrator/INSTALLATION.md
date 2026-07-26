# Installation Guide

**Version:** 3.0.0

---

## System Requirements

### Minimum

| Resource | Requirement |
|---|---|
| CPU | 2 vCPU |
| RAM | 4 GB |
| Disk | 20 GB SSD |
| OS | Ubuntu 22.04 LTS, Windows Server 2022, Proxmox VE 7+ |
| Docker | 24.0+ |
| Docker Compose | v2.20+ |

### Recommended (Production)

| Resource | Requirement |
|---|---|
| CPU | 4 vCPU |
| RAM | 8 GB |
| Disk | 50 GB SSD |
| Network | 1 Gbps |

### Supported Browsers

- Google Chrome 120+
- Mozilla Firefox 121+
- Microsoft Edge 120+
- Apple Safari 17+

---

## Deployment Methods

### 1. Docker Compose (Recommended)

This is the primary and recommended installation method.

#### Step 1: Clone the Repository

```bash
git clone https://github.com/casa/mission-control.git
cd mission-control
```

#### Step 2: Create the Environment File

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```bash
# Required
MISSIONCONTROL_SECRET_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# Database
POSTGRES_DB=missioncontrol
POSTGRES_USER=missioncontrol
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Application
PROJECT_NAME=Mission Control
ENVIRONMENT=production
EDITION=community
```

#### Step 3: Launch Services

**Development mode:**

```bash
docker compose -f docker-compose.yml up -d
```

**Production mode:**

```bash
docker compose -f docker-compose.prod.yml up -d
```

#### Step 4: Verify Installation

```bash
# Check all containers are running
docker compose ps

# Check API health
curl http://localhost:8000/live

# Check readiness
curl http://localhost:8000/ready
```

#### Step 5: Access the Dashboard

Open `http://localhost:3000` in your browser. Complete the first-run setup wizard to create the initial admin account. See [User Management](USER_MANAGEMENT.md) for details.

---

### 2. Ubuntu Manual Installation

For environments where Docker is not available.

#### Prerequisites

```bash
sudo apt update && sudo apt install -y python3.12 python3.12-venv python3-pip \
    postgresql-16 redis-server nginx certbot python3-certbot-nginx
```

#### Application Setup

```bash
# Create service user
sudo useradd -r -s /bin/false missioncontrol
sudo mkdir -p /opt/mission-control
sudo chown missioncontrol:missioncontrol /opt/mission-control

# Clone and install
sudo -u missioncontrol git clone https://github.com/casa/mission-control.git /opt/mission-control
cd /opt/mission-control
sudo -u missioncontrol python3.12 -m venv venv
sudo -u missioncontrol ./venv/bin/pip install -r requirements.txt
```

#### Database Setup

```bash
sudo -u postgres psql -c "CREATE USER missioncontrol WITH PASSWORD 'CHANGE_ME';"
sudo -u postgres psql -c "CREATE DATABASE missioncontrol OWNER missioncontrol;"
```

#### Environment File

Create `/opt/mission-control/.env` with the same variables as the Docker Compose method above, but set:

```bash
POSTGRES_HOST=localhost
REDIS_HOST=localhost
```

#### Systemd Service

Create `/etc/systemd/system/mission-control.service`:

```ini
[Unit]
Description=Mission Control API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=missioncontrol
Group=missioncontrol
WorkingDirectory=/opt/mission-control
EnvironmentFile=/opt/mission-control/.env
ExecStart=/opt/mission-control/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mission-control
```

#### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/mission-control`:

```nginx
server {
    listen 80;
    server_name control.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name control.example.com;

    ssl_certificate /etc/letsencrypt/live/control.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/control.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/mission-control /etc/nginx/sites-enabled/
sudo certbot --nginx -d control.example.com
sudo systemctl reload nginx
```

---

### 3. Proxmox VE LXC Container

#### Create Container

In the Proxmox web UI or via CLI:

```bash
pct create 200 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
    --hostname mission-control \
    --memory 4096 \
    --cores 2 \
    --rootfs local-lvm:20 \
    --net0 name=eth0,bridge=vmbr0,ip=192.168.1.200/24,gw=192.168.1.1
```

#### Inside the Container

```bash
# Install Docker
apt update && apt install -y docker.io docker-compose-v2
systemctl enable --now docker

# Follow the Docker Compose installation steps above
```

---

### 4. Google Cloud (GCE)

```bash
# Create instance
gcloud compute instances create mission-control \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --disk-size=50 \
    --tags=mission-control

# Open firewall ports
gcloud compute firewall-rules create allow-mission-control \
    --allow=tcp:80,tcp:443,tcp:3000,tcp:8000 \
    --target-tags=mission-control

# SSH in and follow Docker Compose steps
gcloud compute ssh mission-control
```

---

### 5. AWS EC2

```bash
# Launch instance via CLI or console
# Use Amazon Linux 2023 or Ubuntu 22.04 AMI
# Instance type: t3.medium (2 vCPU, 4 GB RAM)
# Security group: allow ports 80, 443, 3000, 8000

# SSH in and follow Docker Compose steps
ssh -i key.pem ubuntu@<public-ip>
```

---

### 6. Azure VM

```bash
# Create VM
az vm create \
    --resource-group mission-control-rg \
    --name mission-control \
    --image Ubuntu2204 \
    --size Standard_B2s \
    --admin-username azureuser \
    --ssh-key-value ~/.ssh/id_rsa.pub

# Open ports
az vm open-port --resource-group mission-control-rg --name mission-control --port 80
az vm open-port --resource-group mission-control-rg --name mission-control --port 443
```

---

## `.env.example` Reference

```bash
# ===========================================
# Mission Control Environment Configuration
# ===========================================

# --- Application ---
PROJECT_NAME=Mission Control
ENVIRONMENT=production
EDITION=community
COMPOSE_PROJECT_NAME=missioncontrol

# --- Security ---
MISSIONCONTROL_SECRET_KEY=CHANGE_ME

# --- PostgreSQL ---
POSTGRES_DB=missioncontrol
POSTGRES_USER=missioncontrol
POSTGRES_PASSWORD=CHANGE_ME
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# --- Redis ---
REDIS_HOST=redis
REDIS_PORT=6379

# --- SQLAlchemy ---
DATABASE_ECHO=false
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# --- Remote Access ---
TERMINAL_MAX_SESSIONS=10
SSH_CONNECT_TIMEOUT=10
SSH_COMMAND_TIMEOUT=30
SSH_IDLE_TIMEOUT=300
WINRM_CONNECT_TIMEOUT=10
WINRM_OPERATION_TIMEOUT=30
REMOTE_MAX_COMMAND_TIMEOUT=300
REMOTE_RETRY_COUNT=3
REMOTE_CONNECTION_POOL_SIZE=5

# --- Active Directory ---
AD_SERVER=
AD_PORT=389
AD_USE_SSL=false
AD_USERNAME=
AD_PASSWORD=
AD_BASE_DN=

# --- Microsoft 365 ---
M365_TENANT_ID=
M365_CLIENT_ID=
M365_CLIENT_SECRET=

# --- Zabbix ---
ZABBIX_URL=
ZABBIX_USERNAME=
ZABBIX_PASSWORD=
ZABBIX_VERIFY_SSL=true
ZABBIX_TIMEOUT=30
ZABBIX_RETRIES=3

# --- Rate Limiting ---
rate_limit_per_minute=60
rate_limit_auth_per_minute=10

# --- CORS ---
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

---

## Post-Installation Checklist

- [ ] Admin account created via first-run wizard
- [ ] HTTPS configured and verified
- [ ] Agent deployed to at least one managed host (see [Agent Deployment](AGENT_DEPLOYMENT.md))
- [ ] Database backups configured (see [Backup and Restore](BACKUP_AND_RESTORE.md))
- [ ] Monitoring alerts configured (see [Monitoring](MONITORING.md))
- [ ] Firewall rules applied (see [Security Hardening](SECURITY_HARDENING.md))
