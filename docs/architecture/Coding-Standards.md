# Coding Standards

## Python

### Style
- Follow PEP 8
- Line length: 88 characters (Black/Ruff default)
- Use `ruff` for linting with project configuration
- Import sorting: `ruff` auto-fix (I001)

### Type Hints
- All function parameters must have type hints
- All return types must be annotated
- Use `X | None` instead of `Optional[X]` (Python 3.10+)
- Use `list[X]` instead of `List[X]` (Python 3.9+)

### Naming
| Element | Convention | Example |
|---------|------------|---------|
| Module | snake_case | `plugin_service.py` |
| Class | PascalCase | `PluginService` |
| Function | snake_case | `get_plugin_by_slug()` |
| Variable | snake_case | `plugin_count` |
| Constant | UPPER_SNAKE | `DEFAULT_LIMIT` |
| Private | `_prefix` | `_live_plugins` |
| Boolean | `is_`/`has_`/`can_` prefix | `is_enabled` |

### Exceptions
- Use specific exceptions, never bare `except:`
- Service layer raises `HTTPException` for API errors
- Business logic raises `ValueError` or domain exceptions
- Never swallow exceptions silently

## FastAPI

### Router Conventions
- One router per domain
- Router prefix: `/{domain-name}` (kebab-case)
- Router tag: `["{domain-name}"]`
- Endpoints: `async def`
- Dependencies: `Depends(get_db)`, `Depends(get_current_user)`

### Response Conventions
- `GET` → 200 with response model
- `POST` → 201 Created
- `PUT` → 200 Updated
- `DELETE` → 204 No Content
- Errors → 4xx/5xx with `{"detail": "message"}`

### Schema Conventions
- `{Entity}Create` — POST request body
- `{Entity}Update` — PUT request body (all optional)
- `{Entity}Response` — Single item response
- `{Entity}ListResponse` — List wrapper with `count` and `items`

## SQLAlchemy

### Model Conventions
- Table names: plural snake_case (`plugins`, `remote_hosts`)
- Primary key: `id: Mapped[int]` with `primary_key=True, index=True`
- Timestamps: `created_at`, `updated_at` with UTC defaults
- Multi-tenancy: `company_id`, `site_id` columns (nullable, indexed)
- Boolean flags: `enabled: Mapped[bool]` with default
- String fields: `String(N)` with explicit max length
- Large text: `Text` type
- Sensitive data: `_encrypted` suffix column name

### Repository Conventions
- Static methods, no inheritance
- `db: Session` as first parameter
- Standard CRUD: `get_all`, `get_by_id`, `create`, `update`, `delete`
- Filtering via optional parameters

## Pydantic

### Field Conventions
- Required: `Field(...)` with `min_length`, `max_length`, `description`
- Optional: `Field(None, ...)` or `default=None`
- Secrets: NEVER in response schemas
- Validation: Use `Field(pattern=r"...")` for regex
- Config: `model_config = {"from_attributes": True}` for ORM mode

## React / TypeScript

### Component Conventions
- Functional components only (no class components)
- TypeScript strict mode
- Props interfaces defined in the same file or co-located
- Page components in `pages/` directory
- Shared components in `components/common/`
- Domain components in `components/{domain}/`

### Naming
| Element | Convention | Example |
|---------|------------|---------|
| Component | PascalCase | `PluginCard.tsx` |
| Hook | `use` prefix | `usePlugin.ts` |
| Type/Interface | PascalCase | `PluginResponse` |
| Constant | camelCase | `pluginApiUrl` |
| CSS class | kebab-case | `plugin-card` |

## Folder Structure

```
backend/
├── app/
│   ├── core/           # Config, security, auth
│   ├── db/             # Database, Redis
│   ├── models/db/      # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic request/response
│   ├── repositories/   # Data access layer
│   ├── services/       # Business logic
│   ├── routers/        # FastAPI routers
│   ├── plugins/        # Plugin SDK + installed plugins
│   │   ├── base.py     # PluginSDK ABC
│   │   ├── server.py   # ServerPluginSDK
│   │   ├── agent.py    # AgentPluginSDK
│   │   ├── loader.py   # Dynamic loader
│   │   ├── communication.py  # Message bus
│   │   └── installed/  # Plugin directories
│   └── seed/           # Seed data
├── tests/              # Test files
└── alembic/            # Database migrations
```

## Documentation

- Every public function must have a docstring
- Module-level docstrings for all files
- Type hints serve as documentation
- README.md for each major directory
- Architecture docs in `docs/architecture/`

## Comments

- Explain WHY, not WHAT
- No commented-out code (delete it, use git history)
- TODO comments: `# TODO: description` with ticket reference
- Avoid obvious comments
