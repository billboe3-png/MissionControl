# Company and Site Management

**Version:** 3.0.0

---

## Multi-Tenant Model

Mission Control uses a three-tier hierarchy for multi-tenant data isolation:

```
Company (Tenant)
  └── Site (Location)
        └── Agent (Managed Host)
```

- **Company** — Top-level organizational unit. All data, users, agents, and plugins are scoped to a company.
- **Site** — A physical or logical location within a company (e.g., data center, office, cloud region).
- **Agent** — A managed host running the Mission Control agent, assigned to a specific site.

Each company's data is fully isolated. Queries, API responses, and dashboard views are automatically filtered by the authenticated user's company scope.

---

## Company Management

### Creating a Company

```bash
curl -X POST http://localhost:8000/api/v1/companies \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "description": "Primary tenant",
    "settings": {
      "max_sites": 50,
      "max_agents_per_site": 100
    }
  }'
```

### Listing Companies

```bash
curl http://localhost:8000/api/v1/companies \
  -H "Authorization: Bearer <admin-token>"
```

### Updating a Company

```bash
curl -X PUT http://localhost:8000/api/v1/companies/1 \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp (Updated)"}'
```

### Deleting a Company

Deleting a company soft-deletes the tenant and all associated sites and agents. This action is irreversible after the retention period.

```bash
curl -X DELETE http://localhost:8000/api/v1/companies/1 \
  -H "Authorization: Bearer <admin-token>"
```

---

## Site Management

### Creating a Site

```bash
curl -X POST http://localhost:8000/api/v1/sites \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Primary Data Center",
    "company_id": 1,
    "location": "New York, NY",
    "description": "Main production data center"
  }'
```

### Listing Sites

```bash
# List all sites for the authenticated user's company
curl http://localhost:8000/api/v1/sites \
  -H "Authorization: Bearer <admin-token>"

# List sites for a specific company
curl http://localhost:8000/api/v1/sites?company_id=1 \
  -H "Authorization: Bearer <admin-token>"
```

### Updating a Site

```bash
curl -X PUT http://localhost:8000/api/v1/sites/1 \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "NYC Data Center", "location": "New York, NY, USA"}'
```

### Deleting a Site

```bash
curl -X DELETE http://localhost:8000/api/v1/sites/1 \
  -H "Authorization: Bearer <admin-token>"
```

Sites with active agents cannot be deleted. Reassign or remove agents first.

---

## Data Isolation

Mission Control enforces tenant isolation at the application layer:

- All database queries include a `company_id` filter.
- API endpoints validate that the authenticated user has access to the requested resource.
- Agents are scoped to a single site within a single company.
- Plugin data is isolated per company.
- Events on the event bus are scoped to the company context.

### Isolation Guarantees

| Resource | Isolation Scope |
|---|---|
| Users | Company |
| Sites | Company |
| Agents | Site |
| Plugins | Company |
| Events | Company |
| Audit logs | Company |
| API keys | Company |

---

## Tenant Scoping for Users

Users can be assigned to one or more companies and sites:

```bash
# Assign user to multiple sites
curl -X PUT http://localhost:8000/api/v1/users/2 \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 1,
    "site_ids": [1, 2, 3]
  }'
```

A user's effective permissions are the intersection of their role and their site assignments. A user assigned to Site A cannot see agents or data from Site B, even if they have the `admin` role.

---

## Company Settings

Each company can have custom settings:

```json
{
  "max_sites": 50,
  "max_agents_per_site": 100,
  "max_plugins": 20,
  "session_timeout_minutes": 30,
  "allow_api_keys": true,
  "allow_remote_terminal": true
}
```

Enterprise edition supports additional settings for compliance, audit retention, and SSO configuration.

---

## Default Company

The first company created during the setup wizard is the **default company**. It cannot be deleted while any users, agents, or sites exist under it. The default company is used for the initial admin account and serves as the root tenant.

See [Installation](INSTALLATION.md) for the setup wizard and [User Management](USER_MANAGEMENT.md) for user-to-company assignments.
