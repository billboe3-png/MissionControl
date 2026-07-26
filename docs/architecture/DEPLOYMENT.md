# Mission Control — Deployment

**Version:** 3.0.0

---

## Overview

Mission Control supports multiple deployment models. The same codebase runs everywhere — the deployment model is a configuration choice, not a code fork.

---

## 1. Docker Compose (Development / Community)

The primary deployment method for community edition.

### Requirements

- Docker Engine 24+
- Docker Compose v2
- 2 CPU cores, 4GB RAM minimum
- Port 8000 (API), 3000 (Dashboard)

### Structure

```
docker-compose.yml          # Development
docker-compose.prod.yml     # Production (GCE, self-hosted)
```

### Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `backend` | Python 3.12 | 8000 | FastAPI server |
| `frontend` | Node 20 / Nginx | 3000 | React dashboard |
| `postgres` | PostgreSQL 16 | 5432 | Database |
| `redis` | Redis 7 | 6379 | Cache / queue |

### Quick Start

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your settings

# Start all services
docker compose up -d

# Access
# Dashboard: http://localhost:3000
# API: http://localhost:8000/api/v1
# Docs: http://localhost:8000/api/docs
```

### Environment Variables

See `.env.example` for all configuration options. Key variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MISSIONCONTROL_SECRET_KEY` | Yes | — | Fernet key for encryption |
| `POSTGRES_DB` | No | `mission_control` | Database name |
| `POSTGRES_USER` | No | `mission_control` | Database user |
| `POSTGRES_PASSWORD` | No | `mission_control` | Database password |
| `POSTGRES_HOST` | No | `postgres` | Database host |
| `REDIS_HOST` | No | `redis` | Redis host |
| `EDITION` | No | `community` | Server edition |
| `ENVIRONMENT` | No | `development` | Environment |

---

## 2. Google Cloud Platform

Production deployment on GCE.

### Infrastructure

| Resource | Specification |
|----------|--------------|
| **Instance** | `e2-medium` (2 vCPU, 4GB RAM) |
| **OS** | Ubuntu 22.04 LTS |
| **Zone** | `africa-south1-b` |
| **Disk** | 20GB SSD |

### Deployment

```bash
# SSH into GCE instance
ssh billboe3@<INSTANCE_IP>

# Navigate to project
cd /opt/MissionControl

# Pull latest code
git pull origin main

# Build and deploy
sudo docker compose -f docker-compose.prod.yml up -d --build backend frontend
```

### Production Configuration

Production uses `docker-compose.prod.yml` which:
- Disables debug mode
- Enables CORS for production domains
- Configures connection pooling
- Sets appropriate timeouts

---

## 3. LXC (Proxmox)

Lightweight containerized deployment on Proxmox VE.

### Structure

```
deployment/lxc/docker/docker-compose.yml
```

### Requirements

- Proxmox VE 7+
- LXC container (Ubuntu 22.04)
- 2 CPU cores, 4GB RAM
- Docker Engine installed in container

---

## 4. AWS (Future)

Planned deployment on AWS.

### Target Architecture

```
ALB (Application Load Balancer)
    |
    ├── ECS Fargate (Mission Control Server)
    ├── RDS PostgreSQL (db.t3.medium)
    ├── ElastiCache Redis (cache.t3.micro)
    └── S3 (plugin storage)
```

---

## 5. Azure (Future)

Planned deployment on Azure.

### Target Architecture

```
Azure Load Balancer
    |
    ├── Azure Container Instances (Mission Control Server)
    ├── Azure Database for PostgreSQL
    ├── Azure Cache for Redis
    └── Azure Blob Storage (plugin storage)
```

---

## 6. Enterprise Edition

Enterprise deployments share the same codebase with additional configuration.

### Enterprise Features

| Feature | Community | Enterprise |
|---------|-----------|------------|
| Agent management | Unlimited | Unlimited |
| Multi-tenant | Yes | Yes |
| Plugin marketplace | Yes | Yes |
| AI operations | Yes | Yes |
| Automation | Yes | Yes |
| HA cluster | No | Yes |
| Multi-region agents | No | Yes |
| SSO/SAML | No | Yes |
| RBAC expansion | Basic | Advanced |
| Audit compliance | Basic | SIEM integration |
| Support | Community | Enterprise |

### Enterprise Deployment

```bash
# Set edition flag
EDITION=enterprise

# Additional enterprise configuration
# (loaded from environment or config file)
```

---

## 7. Agent Deployment

Agents run on managed infrastructure, independent of the server deployment.

### Windows Agent

```powershell
# Install
.\install-agent.ps1 -ServerUrl https://mc.example.com -Name "web01"

# Service registration
# Agent runs as Windows Service
```

### Linux Agent

```bash
# Install
sudo ./install-agent-linux.sh --server https://mc.example.com --name web01

# Systemd service
sudo systemctl enable mission-control-agent
sudo systemctl start mission-control-agent
```

### Agent Configuration

```yaml
# ~/.config/mission-control-agent/config.yaml
server_url: https://mc.example.com
agent_name: web01
api_key: mc_agent_...
heartbeat_interval: 30
plugins:
  - windows    # or linux
  - docker
```

---

## 8. Networking

### Port Requirements

| Port | Direction | Purpose |
|------|-----------|---------|
| 8000 | Inbound | API (FastAPI) |
| 3000 | Inbound | Dashboard (Nginx) |
| 5432 | Internal | PostgreSQL |
| 6379 | Internal | Redis |
| 443 | Outbound | Agent → Server (HTTPS) |
| 22 | Outbound | SSH fallback |
| 5985/5986 | Outbound | WinRM fallback |

### Firewall Rules

```
# Server
allow 8000,3000 from anywhere
allow 5432,6379 from internal only

# Agent
allow 443 outbound to server
allow 22 outbound to managed hosts (SSH fallback)
```

---

## 9. Backup and Recovery

### Database Backup

```bash
# Manual backup
docker exec postgres pg_dump -U mission_control mission_control > backup.sql

# Automated (cron)
0 2 * * * docker exec postgres pg_dump -U mission_control mission_control | gzip > /backups/mc_$(date +\%Y\%m\%d).sql.gz
```

### Restore

```bash
# Restore from backup
cat backup.sql | docker exec -i postgres psql -U mission_control mission_control
```

### Plugin Backup

Plugins are stored in the database. Backup the database to preserve plugin configuration.

---

## 10. Monitoring the Server

### Health Endpoints

```
GET /api/v1/health/live     → {"status": "ok"}
GET /api/v1/health/ready    → {"status": "ready", "checks": {...}}
GET /api/v1/health/subsystems → {"status": "healthy", "subsystems": {...}}
GET /api/v1/version         → {"version": "3.0.0", "edition": "community", ...}
```

### Metrics

- Request count and latency (via logging middleware)
- Rate limiting (per-IP sliding window)
- Agent online/offline counts
- Automation execution counts
