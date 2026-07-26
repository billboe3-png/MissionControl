# Logging

**Version:** 3.0.0

---

## Log Format

Mission Control uses structured JSON logging for all application logs:

```json
{
  "timestamp": "2026-07-26T10:30:00.123Z",
  "level": "INFO",
  "logger": "missioncontrol.api.access",
  "message": "Request completed",
  "request_id": "req_abc123",
  "method": "GET",
  "path": "/api/v1/agents",
  "status_code": 200,
  "duration_ms": 45,
  "user_id": 2,
  "company_id": 1
}
```

All logs include a `timestamp`, `level`, `logger`, and `message` field. Request logs include additional context.

---

## Log Levels

| Level | Description | When to Use |
|---|---|---|
| `DEBUG` | Detailed diagnostic information. | Development and troubleshooting only. |
| `INFO` | Normal operational messages. | Default level for production. |
| `WARNING` | Unexpected conditions that don't prevent operation. | Monitor for potential issues. |
| `ERROR` | Failures that affect functionality. | Requires investigation. |
| `CRITICAL` | System-level failures requiring immediate action. | System may be unusable. |

Set the log level via the `ENVIRONMENT` variable:

- `development` → DEBUG level
- `production` → INFO level

---

## Log Locations

### Docker Compose

Logs are written to stdout/stderr and captured by the Docker logging driver:

```bash
# View logs for a specific service
docker compose -f docker-compose.prod.yml logs api
docker compose -f docker-compose.prod.yml logs postgres
docker compose -f docker-compose.prod.yml logs redis

# Follow logs in real-time
docker compose -f docker-compose.prod.yml logs -f api

# View last 1000 lines
docker compose -f docker-compose.prod.yml logs --tail=1000 api

# Save logs to file
docker compose -f docker-compose.prod.yml logs api > /var/log/mission-control-api.log 2>&1
```

### Manual Install

Application logs are written to stdout and captured by systemd journal:

```bash
# View API logs
journalctl -u mission-control -f

# View last 500 lines
journalctl -u mission-control -n 500

# View logs since a specific time
journalctl -u mission-control --since "2026-07-26 08:00:00"

# View logs with priority filter
journalctl -u mission-control -p err
```

### Agent Logs

By default, agent logs are written to the path specified in `config.yaml`:

```yaml
logging:
  file: "/var/log/mission-control-agent/agent.log"
```

If no file is configured, logs go to stdout and are captured by systemd:

```bash
journalctl -u mission-control-agent -f
```

---

## Structured Logging

All log messages are structured with consistent field names:

| Field | Description |
|---|---|
| `timestamp` | ISO 8601 timestamp with milliseconds. |
| `level` | Log level. |
| `logger` | Dotted logger name (e.g., `missioncontrol.api.access`). |
| `message` | Human-readable message. |
| `request_id` | Unique request identifier (for request-scoped logs). |
| `user_id` | Authenticated user ID (when applicable). |
| `company_id` | Tenant company ID (when applicable). |

---

## Request Logging Middleware

Every API request is logged with:

- Method and path
- Response status code
- Response time in milliseconds
- Client IP address
- User agent string
- Authenticated user (if applicable)

Example access log:

```json
{
  "timestamp": "2026-07-26T10:30:00.456Z",
  "level": "INFO",
  "logger": "missioncontrol.api.access",
  "message": "GET /api/v1/agents 200 OK",
  "request_id": "req_xyz789",
  "method": "GET",
  "path": "/api/v1/agents",
  "status_code": 200,
  "duration_ms": 32,
  "client_ip": "192.168.1.50",
  "user_agent": "Mozilla/5.0 Chrome/120",
  "user_id": 2
}
```

### Excluding Paths from Access Logs

Health check endpoints (`/live`, `/ready`) are logged at DEBUG level to reduce noise in production. They can be fully excluded via configuration.

---

## Agent Logging

Agents log with the same structured format. Agent logs include:

- Connection attempts and results
- Heartbeat sent/received
- Command execution (start, completion, errors)
- Plugin lifecycle events
- Configuration changes

### Log Rotation

Configure rotation in the agent's `config.yaml`:

```yaml
logging:
  file: "/var/log/mission-control-agent/agent.log"
  max_size: 50      # MB
  max_files: 5      # Keep 5 rotated files
```

For systemd-managed agents, journald handles rotation automatically. Configure retention in `/etc/systemd/journald.conf`:

```ini
[Journal]
SystemMaxUse=500M
MaxRetentionSec=30day
```

---

## Log Aggregation

For production deployments, ship logs to a centralized system:

### Fluentd

```xml
<source>
  @type docker
  @label @missioncontrol
</source>

<label @missioncontrol>
  <match docker.**>
    @type elasticsearch
    host elasticsearch.example.com
    port 9200
    index_name mission-control
  </match>
</label>
```

### Logstash

```ruby
input {
  docker {
    container_labels => ["com.docker.compose.project=missioncontrol"]
  }
}

filter {
  json {
    source => "message"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch.example.com:9200"]
    index => "mission-control-%{+YYYY.MM.dd}"
  }
}
```

---

## Querying Logs

### Using Grep

```bash
# Find all errors
docker compose logs api 2>&1 | grep '"level":"ERROR"'

# Find logs for a specific user
docker compose logs api 2>&1 | grep '"user_id":2'

# Find slow requests (>1000ms)
docker compose logs api 2>&1 | grep '"duration_ms":[0-9]\{4,\}'

# Find authentication failures
docker compose logs api 2>&1 | grep '"path":"/api/v1/auth/login"' | grep '"status_code":4'
```

### Using jq

```bash
# Pretty-print all error logs
docker compose logs api 2>&1 | jq 'select(.level == "ERROR")'

# Count requests per endpoint
docker compose logs api 2>&1 | jq -r '.path' | sort | uniq -c | sort -rn

# Find the slowest requests
docker compose logs api 2>&1 | jq 'select(.duration_ms > 500)' | head -20
```

See [Monitoring](MONITORING.md) for health-based alerting and [Performance](PERFORMANCE.md) for log-driven performance analysis.
