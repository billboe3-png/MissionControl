# Performance Tuning

**Version:** 3.0.0

---

## Database Tuning

### Connection Pool

The SQLAlchemy connection pool is configured via environment variables:

| Variable | Default | Production Recommended |
|---|---|---|
| `DATABASE_POOL_SIZE` | 5 | 10–20 |
| `DATABASE_MAX_OVERFLOW` | 10 | 20–40 |

**Formula:** `total_max_connections = DATABASE_POOL_SIZE + DATABASE_MAX_OVERFLOW`

Ensure PostgreSQL's `max_connections` is at least equal to `total_max_connections` multiplied by the number of API worker processes.

```bash
# Check current PostgreSQL max_connections
docker exec missioncontrol-postgres-1 psql -U missioncontrol -c "SHOW max_connections;"

# For 4 workers with pool_size=10, max_overflow=20:
# 4 × (10 + 20) = 120 connections needed
# Set max_connections to at least 120
```

To modify PostgreSQL max_connections, add to `docker-compose.prod.yml`:

```yaml
services:
  postgres:
    command: >
      postgres
      -c max_connections=150
      -c shared_buffers=1GB
      -c effective_cache_size=3GB
      -c work_mem=16MB
      -c maintenance_work_mem=256MB
```

### Query Performance

```bash
# Enable slow query logging
docker exec missioncontrol-postgres-1 psql -U missioncontrol -c "
SET log_min_duration_statement = 1000;  -- Log queries > 1 second
"
```

For persistent slow query logging, add to the PostgreSQL command:

```yaml
command: >
  postgres
  -c log_min_duration_statement=1000
  -c log_statement=none
```

### Index Optimization

The 29-table schema includes standard indexes. If query performance degrades:

```bash
# Analyze table statistics
docker exec missioncontrol-postgres-1 psql -U missioncontrol -c "ANALYZE;"

# Check index usage
docker exec missioncontrol-postgres-1 psql -U missioncontrol -c "
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;"
```

---

## Redis Caching

Redis serves multiple functions — caching, rate limiting, session storage, and the event bus. Optimize based on usage:

### Memory

```bash
# Check Redis memory usage
docker exec missioncontrol-redis-1 redis-cli INFO memory

# Check memory fragmentation ratio
docker exec missioncontrol-redis-1 redis-cli INFO memory | grep mem_fragmentation_ratio
```

- **Fragmentation ratio < 1.0** — Redis is swapping. Increase available memory.
- **Fragmentation ratio > 1.5** — Memory is fragmented. Restart Redis to defragment.

### Eviction Policy

Redis uses `allkeys-lru` eviction by default. This is appropriate for caching workloads. Configure in `docker-compose.prod.yml`:

```yaml
services:
  redis:
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### Connection Pool

```bash
# Check connected clients
docker exec missioncontrol-redis-1 redis-cli INFO clients
```

Redis default max clients is 10,000. Increase if needed:

```yaml
services:
  redis:
    command: redis-server --maxclients 20000
```

---

## Connection Pooling

### API Server

For high-traffic deployments, tune the Uvicorn worker count:

```bash
# Docker Compose
docker compose -f docker-compose.prod.yml run --rm api uvicorn app.main:app \
  --host 0.0.0.0 --port 8000 \
  --workers 4 \
  --loop uvloop \
  --http httptools
```

**Rule of thumb:** `workers = 2 × CPU_cores + 1`

### Remote Connection Pool

The remote connection pool (SSH/WinRM) is configured via:

| Variable | Default | Production Recommended |
|---|---|---|
| `REMOTE_CONNECTION_POOL_SIZE` | 5 | 10–20 |
| `TERMINAL_MAX_SESSIONS` | 10 | 20–50 |

---

## Rate Limiting

Rate limiting protects against abuse and ensures fair resource usage:

| Variable | Default | Production Recommended |
|---|---|---|
| `rate_limit_per_minute` | 60 | 120–300 |
| `rate_limit_auth_per_minute` | 10 | 5–10 |

For high-traffic environments with many agents, increase `rate_limit_per_minute` to accommodate concurrent agent heartbeats and data submissions.

See [Security Hardening](SECURITY_HARDENING.md) for rate limiting security considerations.

---

## Production Sizing Recommendations

### Small Deployment (1–50 agents)

| Resource | Value |
|---|---|
| CPU | 2 vCPU |
| RAM | 4 GB |
| Workers | 2 |
| DB pool size | 5 |
| DB max overflow | 10 |
| Redis memory | 128 MB |

### Medium Deployment (50–500 agents)

| Resource | Value |
|---|---|
| CPU | 4 vCPU |
| RAM | 8 GB |
| Workers | 4 |
| DB pool size | 10 |
| DB max overflow | 20 |
| Redis memory | 256 MB |
| PostgreSQL max_connections | 100 |

### Large Deployment (500–5000 agents)

| Resource | Value |
|---|---|
| CPU | 8 vCPU |
| RAM | 16 GB |
| Workers | 8 |
| DB pool size | 20 |
| DB max overflow | 40 |
| Redis memory | 512 MB |
| PostgreSQL max_connections | 200 |
| Dedicated PostgreSQL and Redis instances |

### Extra Large (5000+ agents)

Consider separating PostgreSQL and Redis onto dedicated hosts. Use a load balancer in front of multiple API instances. Use read replicas for PostgreSQL.

---

## Benchmarking

```bash
# API response time baseline
for i in $(seq 1 100); do
  curl -s -o /dev/null -w "%{time_total}\n" \
    -H "Authorization: Bearer <token>" \
    http://localhost:8000/api/v1/agents
done | awk '{sum+=$1; count++} END {print "Avg:", sum/count*1000, "ms"}'
```

---

## Monitoring Performance

Use the `/subsystems` endpoint to track key metrics:

```bash
curl -s http://localhost:8000/subsystems | python -c "
import sys, json
data = json.load(sys.stdin)
db = data['subsystems']['database']
print(f\"DB pool: {db['pool']['active']}/{db['pool']['total']} active\")
print(f\"DB latency: {db['latency_ms']}ms\")
redis = data['subsystems']['redis']
print(f\"Redis latency: {redis['latency_ms']}ms\")
print(f\"Redis memory: {redis['memory_used_mb']}MB\")
"
```

See [Monitoring](MONITORING.md) for complete health endpoint documentation and [Logging](LOGGING.md) for request-level performance tracking.
