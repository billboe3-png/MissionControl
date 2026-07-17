# API Standards

## Base URL

All API endpoints are under `/api/v1/`.

## Authentication

- JWT Bearer tokens for user authentication
- API keys for service-to-service authentication
- Agent API keys for agent authentication (`X-Agent-API-Key` header)

## Endpoints

### Naming
- Resources: plural nouns (`/plugins`, `/agents`, `/sites`)
- Sub-resources: nested (`/sites/{id}/agents`)
- Actions: verbs as sub-resources (`/plugins/{id}/enable`)
- No verbs in base URLs

### HTTP Methods
| Method | Usage | Status Code |
|--------|-------|-------------|
| GET | Read resource(s) | 200 |
| POST | Create resource | 201 |
| PUT | Full update | 200 |
| PATCH | Partial update | 200 |
| DELETE | Remove resource | 204 |

### Query Parameters
- Filtering: `?enabled=true&execution_target=server`
- Pagination: `?page=1&per_page=50`
- Search: `?q=search+term`
- Sorting: `?sort=created_at&order=desc`

### Request Bodies
- Content-Type: `application/json`
- Validation via Pydantic schemas
- Required fields marked with `...`
- Optional fields have defaults

### Response Format

**Single resource:**
```json
{
  "id": 1,
  "slug": "zabbix",
  "name": "Zabbix Monitoring",
  "version": "1.0.0"
}
```

**List resource:**
```json
{
  "count": 2,
  "items": [...]
}
```

**Error:**
```json
{
  "detail": "Plugin not found"
}
```

### Rate Limiting
- Default: 60 requests/minute per IP
- Auth endpoints: 5 requests/minute per IP
- Health/version/agent endpoints: unlimited
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`

## Versioning

API version is in the URL path: `/api/v1/`.

Breaking changes require a new major version (`/api/v2/`).

## Documentation

- OpenAPI docs at `/api/docs`
- ReDoc at `/api/redoc`
- OpenAPI JSON at `/api/openapi.json`
- Every endpoint must have a docstring (becomes OpenAPI description)
