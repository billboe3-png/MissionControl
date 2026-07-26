# Monitoring

**Version:** 3.0.0

Mission Control provides built-in health endpoints and dashboard monitoring for all system components.

---

## Health Endpoints

### `/live` — Liveness Check

Returns 200 if the API process is running. Does not verify dependencies.

```bash
curl -s http://localhost:8000/live
```

**Response:**

```json
{
  "status": "alive",
  "timestamp": "2026-07-26T10:30:00Z"
}
```

Use for load balancer health checks and container liveness probes.

---

### `/ready` — Readiness Check

Returns 200 only if all critical subsystems (database, Redis) are reachable.

```bash
curl -s http://localhost:8000/ready
```

**Response:**

```json
{
  "status": "ready",
  "timestamp": "2026-07-26T10:30:00Z",
  "subsystems": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

Use for load balancer readiness probes and deployment gate checks.

---

### `/subsystems` — Detailed Subsystem Health

Returns the health status of every subsystem including plugins, scheduler, and event bus.

```bash
curl -s http://localhost:8000/subsystems
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-07-26T10:30:00Z",
  "subsystems": {
    "database": {
      "status": "healthy",
      "latency_ms": 2,
      "pool": {
        "active": 3,
        "idle": 7,
        "total": 10
      }
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 1,
      "connected_clients": 5,
      "memory_used_mb": 12
    },
    "event_bus": {
      "status": "healthy",
      "subscribers": 8,
      "events_per_minute": 142
    },
    "scheduler": {
      "status": "healthy",
      "running_tasks": 3,
      "next_run": "2026-07-26T10:35:00Z"
    },
    "plugins": {
      "status": "healthy",
      "total": 5,
      "healthy": 5,
      "degraded": 0,
      "unhealthy": 0
    }
  }
}
```

---

### `/version` — Version Info

```bash
curl -s http://localhost:8000/version
```

**Response:**

```json
{
  "version": "3.0.0",
  "edition": "community",
  "python": "3.12.4",
  "fastapi": "0.115.0",
  "database_revision": "a1b2c3d4e5f6"
}
```

---

## Dashboard Health

The React dashboard at port 3000 displays:

- **System overview** — CPU, memory, disk usage across all agents.
- **Agent status grid** — Real-time online/offline/degraded status.
- **Event stream** — Live event feed from the event bus.
- **Plugin health** — Per-plugin status cards.
- **Alert panel** — Active alerts and warnings.

Access the dashboard at `http://localhost:3000` or via your configured reverse proxy URL.

---

## Agent Status Monitoring

### List All Agents

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/agents
```

### Agent Status Values

| Status | Description |
|---|---|
| `online` | Agent is connected and sending heartbeats. |
| `degraded` | Agent is connected but reporting issues (high CPU, low disk, etc.). |
| `offline` | No heartbeat received within the timeout window. |
| `maintenance` | Agent is in maintenance mode (manual flag). |

### Agent Metrics

Each agent reports the following metrics on heartbeat:

- CPU usage (%)
- Memory usage (%)
- Disk usage (%)
- System load (1, 5, 15 minute averages)
- Uptime
- Active plugin count
- Active remote sessions

---

## Event Bus Health

The Redis-backed event bus handles real-time notifications. Monitor via:

```bash
curl -s http://localhost:8000/subsystems | python -c "
import sys, json
data = json.load(sys.stdin)
print(json.dumps(data['subsystems']['event_bus'], indent=2))
"
```

Key metrics:

- **Subscribers** — Number of active event consumers.
- **Events per minute** — Throughput rate.
- **Status** — healthy, degraded, or unhealthy.

---

## Plugin Health

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/plugins/health
```

**Response:**

```json
[
  {
    "name": "zabbix-monitor",
    "type": "hybrid",
    "status": "healthy",
    "uptime_seconds": 86400,
    "last_error": null
  },
  {
    "name": "email-notifier",
    "type": "server",
    "status": "healthy",
    "uptime_seconds": 86400,
    "last_error": null
  }
]
```

---

## Scheduler Health

The internal scheduler manages periodic tasks (cleanup, metrics aggregation, etc.):

```bash
curl -s http://localhost:8000/subsystems | python -c "
import sys, json
data = json.load(sys.stdin)
print(json.dumps(data['subsystems']['scheduler'], indent=2))
"
```

---

## Uptime Monitoring

For external uptime monitoring, use the `/live` and `/ready` endpoints with your monitoring tool:

```bash
# Prometheus blackbox exporter example
# prometheus.yml
scrape_configs:
  - job_name: 'mission-control'
    metrics_path: /live
    static_configs:
      - targets: ['localhost:8000']
```

---

## Alerting

Configure alerts based on health endpoint responses:

1. **API down** — `/live` returns non-200 or connection refused.
2. **Degraded readiness** — `/ready` returns non-200.
3. **Agent offline** — Agent status is `offline` for more than 5 minutes.
4. **Plugin unhealthy** — Any plugin status is `unhealthy`.
5. **Database connection pool exhausted** — Active connections exceed `DATABASE_POOL_SIZE + DATABASE_MAX_OVERFLOW`.
6. **Redis memory high** — Redis memory usage exceeds 80%.

See [Logging](LOGGING.md) for log-based alerting and [Security Hardening](SECURITY_HARDENING.md) for audit alerting.
