# Docker Deployment Guide

Deploy Mission Control using Docker Compose for development and production environments.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                Docker Host                   │
│                                             │
│  ┌─────────────┐  ┌──────────────────────┐ │
│  │   Frontend   │  │      Backend         │ │
│  │   (Vite)     │  │    (FastAPI)         │ │
│  │   Port 3000  │  │    Port 8000         │ │
│  └──────┬───────┘  └──────────┬───────────┘ │
│         │                     │              │
│         │    ┌────────────────┤              │
│         │    │                │              │
│  ┌──────▼────▼───┐  ┌────────▼───────────┐ │
│  │    Nginx      │  │   PostgreSQL        │ │
│  │  (Optional)   │  │   Port 5432         │ │
│  │  Port 80/443  │  └────────────────────┘ │
│  └───────────────┘                          │
│                          ┌────────────────┐ │
│                          │     Redis       │ │
│                          │   Port 6379     │ │
│                          └────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## Prerequisites

- Docker Engine 24.0+
- Docker Compose v2.20+
- 4 GB RAM minimum (8 GB recommended)
- 20 GB disk space

Verify installation:

```bash
docker --version
docker compose version
```

---

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/your-org/mission-control.git
cd mission-control

cp .env.example .env
```

### 2. Edit Environment Variables

```bash
nano .env
```

### 3. Start Services

```bash
docker compose up -d
```

### 4. Verify

```bash
curl http://localhost:8000/api/v1/health
open http://localhost:3000
```

---

## docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: mc-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=${JWT_SECRET}
      - JWT_ALGORITHM=HS256
      - JWT_ACCESS_TOKEN_EXPIRY=3600
      - JWT_REFRESH_TOKEN_EXPIRY=2592000
      - CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:3000}
      - LOG_LEVEL=${LOG_LEVEL:-info}
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - API_KEY_PREFIX=${API_KEY_PREFIX:-mc_agent_}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - backend-storage:/app/storage
      - backend-logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    networks:
      - mc-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: mc-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000/api/v1
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - mc-network

  postgres:
    image: postgres:16-alpine
    container_name: mc-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${DB_USER:-mission_control}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME:-mission_control}
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-mission_control}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - mc-network

  redis:
    image: redis:7-alpine
    container_name: mc-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - mc-network

volumes:
  postgres-data:
  redis-data:
  backend-storage:
  backend-logs:

networks:
  mc-network:
    driver: bridge
```

---

## Production Configuration

### docker-compose.prod.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: mc-backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - JWT_SECRET=${JWT_SECRET}
      - JWT_ALGORITHM=HS256
      - JWT_ACCESS_TOKEN_EXPIRY=3600
      - JWT_REFRESH_TOKEN_EXPIRY=2592000
      - CORS_ORIGINS=${CORS_ORIGINS}
      - LOG_LEVEL=warning
      - ENVIRONMENT=production
      - WORKERS=${WORKERS:-4}
      - GUNICORN_WORKERS=${WORKERS:-4}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - backend-storage:/app/storage
      - backend-logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "5"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    networks:
      - mc-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    container_name: mc-frontend
    restart: always
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=${VITE_API_URL}
    depends_on:
      backend:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "5"
    networks:
      - mc-network

  nginx:
    image: nginx:alpine
    container_name: mc-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    deploy:
      resources:
        limits:
          memory: 256M
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "5"
    networks:
      - mc-network

  postgres:
    image: postgres:16-alpine
    container_name: mc-postgres
    restart: always
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "5"
    networks:
      - mc-network

  redis:
    image: redis:7-alpine
    container_name: mc-redis
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    deploy:
      resources:
        limits:
          memory: 512M
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "5"
    networks:
      - mc-network

volumes:
  postgres-data:
  redis-data:
  backend-storage:
  backend-logs:

networks:
  mc-network:
    driver: bridge
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_PASSWORD` | PostgreSQL password | `secure_db_pass_123` |
| `JWT_SECRET` | JWT signing secret (min 32 chars) | `your-256-bit-secret` |
| `REDIS_PASSWORD` | Redis authentication password | `secure_redis_pass` |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_USER` | `mission_control` | PostgreSQL username |
| `DB_NAME` | `mission_control` | PostgreSQL database name |
| `DB_PORT` | `5432` | PostgreSQL port |
| `REDIS_PORT` | `6379` | Redis port |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| `LOG_LEVEL` | `info` | Log level (`debug`, `info`, `warning`, `error`) |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `WORKERS` | `4` | Gunicorn worker processes |
| `API_KEY_PREFIX` | `mc_agent_` | API key prefix for agents |
| `VITE_API_URL` | `http://localhost:8000/api/v1` | Backend URL for frontend |

### Generate Secrets

```bash
# Generate JWT secret
openssl rand -base64 48

# Generate DB password
openssl rand -base64 32

# Generate Redis password
openssl rand -base64 32
```

---

## Volumes

| Volume | Purpose |
|--------|---------|
| `postgres-data` | PostgreSQL database files |
| `redis-data` | Redis persistence files |
| `backend-storage` | Uploaded files, reports, backups |
| `backend-logs` | Application logs |

### Backup Volumes

```bash
# Backup PostgreSQL
docker exec mc-postgres pg_dump -U mission_control mission_control > backup_$(date +%Y%m%d).sql

# Backup Redis
docker exec mc-redis redis-cli -a $REDIS_PASSWORD BGSAVE

# Backup storage
docker run --rm -v mc-backend-storage:/data -v $(pwd):/backup alpine \
  tar czf /backup/storage_$(date +%Y%m%d).tar.gz -C /data .
```

---

## SSL/TLS Configuration

### Using Let's Encrypt with Nginx

```nginx
# nginx/nginx.conf
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Obtain Certificates

```bash
# Using certbot with Docker
docker run --rm -v $(pwd)/nginx/ssl:/etc/letsencrypt \
  certbot/certbot certonly --webroot \
  --webroot-path=/var/lib/letsencrypt \
  -d your-domain.com
```

---

## Scaling

### Horizontal Scaling (Backend)

```bash
docker compose up -d --scale backend=3
```

When scaling, use a load balancer (Nginx) to distribute traffic:

```nginx
upstream backend {
    server backend-1:8000;
    server backend-2:8000;
    server backend-3:8000;
}
```

### Worker Scaling

Increase Gunicorn workers for a single container:

```bash
WORKERS=8 docker compose up -d backend
```

Rule of thumb: `workers = (2 * CPU cores) + 1`

---

## Maintenance Commands

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail 100 backend
```

### Restart Services

```bash
# Restart backend
docker compose restart backend

# Restart all
docker compose restart
```

### Update

```bash
# Pull latest images and rebuild
docker compose pull
docker compose build --no-cache
docker compose up -d

# Run migrations if needed
docker compose exec backend python -m alembic upgrade head
```

### Database Migrations

```bash
# Run migrations
docker compose exec backend python -m alembic upgrade head

# Create new migration
docker compose exec backend python -m alembic revision --autogenerate -m "description"

# Rollback
docker compose exec backend python -m alembic downgrade -1
```

### Shell Access

```bash
# Backend shell
docker compose exec backend bash

# PostgreSQL shell
docker compose exec postgres psql -U mission_control

# Redis CLI
docker compose exec redis redis-cli -a $REDIS_PASSWORD
```

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker compose logs backend

# Common issues:
# - Database not ready → Check postgres healthcheck
# - Missing env vars → Verify .env file
# - Port conflict → Change port mapping
```

### Database Connection Failed

```bash
# Verify PostgreSQL is running
docker compose ps postgres

# Test connection
docker compose exec postgres pg_isready -U mission_control

# Check credentials
docker compose exec backend env | grep DATABASE_URL
```

### Memory Issues

```bash
# Check container stats
docker stats

# Increase Docker Desktop memory limit (Settings → Resources)
# Minimum: 4 GB for all services
```

---

## Related Documentation

- [AUTHENTICATION.md](./AUTHENTICATION.md) — JWT and API key setup
- [DEPLOYMENT_GCE.md](./DEPLOYMENT_GCE.md) — Google Cloud deployment
- [DEPLOYMENT_KUBERNETES.md](./DEPLOYMENT_KUBERNETES.md) — Kubernetes deployment
- [REST_API.md](./REST_API.md) — API endpoint reference
