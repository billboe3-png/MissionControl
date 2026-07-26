# Mission Control Webhook System

Configure outbound webhooks to receive real-time event notifications from Mission Control.

---

## Overview

Webhooks deliver HTTP POST requests to your endpoints when events occur in Mission Control. Each webhook can subscribe to one or more event types, and payloads include a cryptographic signature for verification.

---

## Creating a Webhook

### Via API

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/webhooks \
  -d '{
    "url": "https://hooks.example.com/mission-control",
    "events": ["agent.offline", "alert.created", "command.completed"],
    "secret": "whsec_your_signing_secret_here",
    "description": "Ops team notifications",
    "active": true
  }'
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "wh_a1b2c3d4",
    "url": "https://hooks.example.com/mission-control",
    "events": ["agent.offline", "alert.created", "command.completed"],
    "secret": "whsec_****",
    "description": "Ops team notifications",
    "active": true,
    "created_at": "2026-07-26T10:00:00Z",
    "deliveries": {
      "total": 0,
      "successful": 0,
      "failed": 0
    }
  }
}
```

The `secret` is only fully shown at creation. Store it securely — you will need it to verify signatures.

---

## Event Types

### Agent Events

| Event | Description |
|-------|-------------|
| `agent.registered` | New agent registered |
| `agent.online` | Agent came online |
| `agent.offline` | Agent went offline |
| `agent.heartbeat.missed` | Agent missed heartbeat threshold |
| `agent.config.updated` | Agent configuration changed |
| `agent.removed` | Agent deregistered |

### Command Events

| Event | Description |
|-------|-------------|
| `command.created` | New command queued |
| `command.started` | Agent began executing command |
| `command.completed` | Command finished successfully |
| `command.failed` | Command execution failed |
| `command.timed_out` | Command exceeded timeout |

### Alert Events

| Event | Description |
|-------|-------------|
| `alert.created` | New alert triggered |
| `alert.acknowledged` | Alert acknowledged by user |
| `alert.resolved` | Alert resolved |
| `alert.escalated` | Alert escalated |

### System Events

| Event | Description |
|-------|-------------|
| `system.backup.completed` | Backup finished |
| `system.backup.failed` | Backup failed |
| `system.update.available` | New version available |
| `system.integration.error` | Integration error occurred |

### Site Events

| Event | Description |
|-------|-------------|
| `site.created` | New site added |
| `site.updated` | Site details changed |
| `site.agent.status` | Agent status changed at site |

### Automation Events

| Event | Description |
|-------|-------------|
| `automation.rule.triggered` | Automation rule fired |
| `automation.rule.failed` | Rule execution failed |

### Inventory Events

| Event | Description |
|-------|-------------|
| `inventory.low_stock` | Low stock threshold breached |
| `inventory.item_added` | New item added |
| `inventory.item_removed` | Item removed |

### User Events

| Event | Description |
|-------|-------------|
| `user.created` | New user created |
| `user.role_changed` | User role modified |
| `user.session.created` | New login session |
| `user.password.changed` | Password changed |

### Wildcard

Subscribe to all events:

```json
{
  "events": ["*"]
}
```

---

## Payload Format

All webhook deliveries use HTTP POST with JSON body:

```json
{
  "id": "dlv_x1y2z3",
  "event": "agent.offline",
  "timestamp": "2026-07-26T10:30:00Z",
  "webhook_id": "wh_a1b2c3d4",
  "data": {
    "agent_id": "agt_x1y2z3",
    "agent_name": "Server Agent 01",
    "site_id": "site_x1y2z3",
    "site_name": "Cape Town DC",
    "last_heartbeat": "2026-07-26T10:25:00Z",
    "offline_duration_seconds": 300,
    "reason": "heartbeat_missed"
  },
  "metadata": {
    "company_id": "comp_x1y2z3",
    "environment": "production"
  }
}
```

### Event-Specific Payload Examples

#### Agent Offline

```json
{
  "id": "dlv_x1y2z3",
  "event": "agent.offline",
  "timestamp": "2026-07-26T10:30:00Z",
  "data": {
    "agent_id": "agt_x1y2z3",
    "agent_name": "Server Agent 01",
    "last_heartbeat": "2026-07-26T10:25:00Z",
    "offline_duration_seconds": 300
  }
}
```

#### Command Completed

```json
{
  "id": "dlv_a1b2c3d4",
  "event": "command.completed",
  "timestamp": "2026-07-26T10:32:00Z",
  "data": {
    "command_id": "cmd_x1y2z3",
    "agent_id": "agt_x1y2z3",
    "type": "script",
    "status": "success",
    "duration_ms": 1250,
    "output": "uptime: 42 days",
    "started_at": "2026-07-26T10:31:58Z",
    "completed_at": "2026-07-26T10:32:00Z"
  }
}
```

#### Alert Created

```json
{
  "id": "dlv_e5f6g7h8",
  "event": "alert.created",
  "timestamp": "2026-07-26T10:35:00Z",
  "data": {
    "alert_id": "alr_x1y2z3",
    "severity": "critical",
    "title": "Disk usage above 90%",
    "agent_id": "agt_x1y2z3",
    "agent_name": "Server Agent 01",
    "site_name": "Cape Town DC",
    "metric": "disk_usage_percent",
    "value": 93.2,
    "threshold": 90,
    "message": "Disk usage on /dev/sda1 is 93.2%"
  }
}
```

---

## Request Headers

Every webhook delivery includes these headers:

```
POST /your-endpoint HTTP/1.1
Host: hooks.example.com
Content-Type: application/json
X-MC-Event: agent.offline
X-MC-Delivery: dlv_x1y2z3
X-MC-Webhook-ID: wh_a1b2c3d4
X-MC-Timestamp: 1719398400
X-MC-Signature: sha256=a1b2c3d4e5f6...
User-Agent: MissionControl-Webhook/1.0
```

| Header | Description |
|--------|-------------|
| `X-MC-Event` | Event type that triggered the delivery |
| `X-MC-Delivery` | Unique delivery ID for deduplication and retry |
| `X-MC-Webhook-ID` | ID of the webhook configuration |
| `X-MC-Timestamp` | Unix timestamp of the event |
| `X-MC-Signature` | HMAC-SHA256 signature for verification |

---

## Security: HMAC Signature Verification

### Generating the Signature

Mission Control signs each payload with HMAC-SHA256 using your webhook secret:

```
signature = HMAC-SHA256(secret, raw_request_body)
```

The signature is sent as: `sha256=<hex_digest>`

### Verification Example (Python)

```python
import hmac
import hashlib

def verify_webhook_signature(
    payload_body: bytes,
    signature_header: str,
    secret: str
) -> bool:
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    expected = f"sha256={expected_signature}"
    return hmac.compare_digest(expected, signature_header)
```

### Verification Example (Node.js)

```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payloadBody, signatureHeader, secret) {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payloadBody)
    .digest('hex');

  const expected = `sha256=${expectedSignature}`;
  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(signatureHeader)
  );
}
```

### Verification Example (Go)

```go
func verifyWebhookSignature(payloadBody []byte, signatureHeader string, secret string) bool {
    mac := hmac.New(sha256.New, []byte(secret))
    mac.Write(payloadBody)
    expected := "sha256=" + hex.EncodeToString(mac.Sum(nil))
    return hmac.Equal([]byte(expected), []byte(signatureHeader))
}
```

---

## Retry Policy

Failed deliveries are retried with exponential backoff:

| Attempt | Delay | Total Time |
|---------|-------|------------|
| 1 | Immediate | 0s |
| 2 | 30 seconds | 30s |
| 3 | 2 minutes | 2m 30s |
| 4 | 5 minutes | 7m 30s |
| 5 | 15 minutes | 22m 30s |
| 6 | 30 minutes | 52m 30s |
| 7 | 1 hour | 1h 52m 30s |
| 8 | 2 hours | 3h 52m 30s |
| 9 | 4 hours | 7h 52m 30s |
| 10 | 8 hours | 15h 52m 30s |

After 10 failed attempts, the delivery is marked as `failed` and no further retries are made. The event is logged in the audit trail.

### Successful Response

A delivery is considered successful if the endpoint responds with HTTP 2xx within 30 seconds.

### Failed Delivery

```json
{
  "status": "error",
  "error": {
    "code": "DELIVERY_FAILED",
    "message": "Endpoint returned HTTP 500 after 10 attempts"
  }
}
```

---

## Retry a Failed Delivery

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/webhooks/wh_a1b2c3d4/retry/dlv_x1y2z3
```

---

## Testing Webhooks

Send a test payload to verify your endpoint is configured correctly:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/webhooks/wh_a1b2c3d4/test
```

This sends a `webhook.test` event:

```json
{
  "id": "dlv_test_001",
  "event": "webhook.test",
  "timestamp": "2026-07-26T10:00:00Z",
  "data": {
    "message": "This is a test webhook delivery",
    "webhook_id": "wh_a1b2c3d4"
  }
}
```

---

## Delivery Logs

View delivery history for a webhook:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/webhooks/wh_a1b2c3d4/logs
```

```json
{
  "status": "success",
  "data": [
    {
      "delivery_id": "dlv_x1y2z3",
      "event": "agent.offline",
      "status": "success",
      "response_code": 200,
      "duration_ms": 145,
      "attempts": 1,
      "created_at": "2026-07-26T10:30:00Z"
    },
    {
      "delivery_id": "dlv_a1b2c3d4",
      "event": "command.completed",
      "status": "failed",
      "response_code": 500,
      "duration_ms": 30000,
      "attempts": 10,
      "last_error": "Endpoint returned HTTP 500",
      "created_at": "2026-07-26T10:15:00Z"
    }
  ]
}
```

---

## Managing Webhooks

### List Webhooks

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/webhooks
```

### Update Webhook

```bash
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/webhooks/wh_a1b2c3d4 \
  -d '{
    "events": ["agent.offline", "alert.created", "command.completed", "system.backup.failed"],
    "active": true
  }'
```

### Delete Webhook

```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/webhooks/wh_a1b2c3d4
```

### Disable Without Deleting

```bash
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/webhooks/wh_a1b2c3d4 \
  -d '{"active": false}'
```

---

## Troubleshooting

### Webhook Not Receiving Events

1. Verify the webhook is active: `GET /api/v1/webhooks` — check `active: true`
2. Confirm the event type is in the webhook's `events` list
3. Check delivery logs for errors: `GET /api/v1/webhooks/{id}/logs`
4. Ensure your endpoint is reachable from the Mission Control server
5. Test with `POST /api/v1/webhooks/{id}/test`

### Signature Verification Failing

1. Ensure you are reading the raw request body, not a parsed version
2. Verify the secret matches: `GET /api/v1/webhooks` — re-create if lost
3. Check that you are using the full `X-MC-Signature` header value
4. Compare clock sync — `X-MC-Timestamp` should be within 5 minutes

### Endpoint Returning Errors

1. Check your endpoint logs during the delivery window
2. Ensure the endpoint returns HTTP 2xx within 30 seconds
3. Verify TLS certificate is valid (no self-signed certs for external endpoints)
4. Check for firewall or security group blocking Mission Control server IP

### High Latency

1. Check `duration_ms` in delivery logs
2. Ensure your endpoint processes quickly and returns 200 immediately
3. Defer heavy processing to a background job queue
4. Consider geographic proximity — Africa-South1 region for GCE deployments

---

## Rate Limits

Webhook deliveries are rate-limited to prevent abuse:

- Maximum 100 deliveries per webhook per minute
- Maximum 1000 deliveries per company per minute
- Failed deliveries do not count against the rate limit

---

## Related Documentation

- [REST_API.md](./REST_API.md) — Webhooks API endpoints
- [AUTHENTICATION.md](./AUTHENTICATION.md) — HMAC signing concepts
- [HEARTBEAT_API.md](./HEARTBEAT_API.md) — Agent events that trigger webhooks
- [DEPLOYMENT_DOCKER.md](./DEPLOYMENT_DOCKER.md) — Webhook environment configuration
