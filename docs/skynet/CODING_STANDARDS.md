# CODING_STANDARDS

## Python

### Style
- PEP 8 with black formatting and strict ruff
- Maximum line length: 100
- No mutable default arguments
- Explicit is better than implicit
- Type hints required on all public interfaces

### Structure
```text
module.py
├── module docstring
├── imports (stdlib, third-party, local)
├── constants
├── classes
├── functions
└── __main__ guard
```

### Requirements
- Type-safe by default
- Fail-fast validation
- Reproducible dependency resolution
- No hidden magic

## FastAPI

- Routers separated by domain
- Dependencies explicitly declared
- Schemas in `app/schemas/`
- Services in `app/services/`
- All routes covered by tests
- Errors mapped to consistent shapes
- Request IDs propagated
- Structured logging per endpoint

## SQLAlchemy

- All schema changes via Alembic migrations
- Never alter schema without migration
- Models in `app/models/db/`
- Repositories for data access
- Services contain business logic
- All queries parameterized
- No raw SQL without review

## Pydantic

- Validation at boundary only
- Never validate repeatedly within core logic
- Schemas must be explicit and complete
- Examples included for all fields
- No dynamic field creation in production paths

## Alembic

- Migration scripts named with timestamp or sequence
- Upgrade and downgrade always both implemented
- Migrations tested before merge
- No destructive downgrades in production
- Migration failures abort deployment

## React

- Functional components only
- Hooks with clear dependency arrays
- State lifted only when necessary
- No hidden side effects
- Explicit loading and error states

## TypeScript

- Strict mode enabled
- No `any` in production code
- Interfaces for data contracts
- Enums for constrained sets
- Explicit return types on public functions

## Plugin SDK

- Plugins implement declared interface
- No silent failure; log clearly
- Versioned and signed
- Metadata required
- Health and readiness reported
- Graceful fallback when disabled

## Agent SDK

- Outbound-only communication
- Local-only plugin loading
- No inbound listeners
- Cached offline behavior
- Bounded retries and exponential backoff
- Explicit API key authentication
- Heartbeat timing configurable but bounded

## REST APIs

- JSON request/response bodies
- Consistent error shapes
- Rate limiting on all endpoints
- CORS explicitly configured
- Authentication on every protected path
- Authorization checked server-side
- Pagination on all list endpoints
- ETags or cache headers where appropriate

## Logging

- Structured JSON in production
- Context attached per request
- Never log secrets
- Never log raw request bodies without scrubbing
- Log levels respected:
  - DEBUG for internal trace
  - INFO for operational events
  - WARNING for recoverable anomalies
  - ERROR for failures requiring attention
  - CRITICAL for data loss or security events

## Typing

- Type hints everywhere public
- No implicit unions via `None` checks without typing intent
- Generic types explicit
- Protocol classes for interfaces
- Never cast to silence typechecker without justification

## Documentation

- Docstrings on every public function, class, and module
- README for every service
- ADR for every significant architectural decision
- Changelog for every release
- Inline comments explain why, not what

## Testing

- Tests first where feasible
- Tests minimal but complete
- No flaky tests in CI
- Test coverage targets:
  - Core logic: >= 90%
  - Integration paths: >= 70%
  - UI critical flows: smoke + critical paths
- No test depends on execution order
- No test depends on time unless mocked

## Error Handling

- Errors are typed and explicit
- Operational errors vs programmer errors separated
- No silent swallowing
- Upstream callers must handle documented failures
- Circuit breakers on external dependencies
- Retry budgets defined and bounded

## Performance

- Profiling before optimization
- No N+1 queries
- Batching for bulk operations
- Caching invalidated explicitly
- Connection pooling required for all database access

## Security

- Input validation at every boundary
- Output encoding where required
- Secrets lifecycle managed
- Dependencies scanned
- Authentication checked per request
- Authorization checked per resource

## Naming Conventions

- Python: `snake_case` for functions, variables, modules
- TypeScript: `camelCase` for variables, `PascalCase` for types
- API URLs: lowercase with hyphens
- Database tables: lowercase snake_case
- Files match primary symbol name
- Boolean prefixes: `is_`, `has_`, `can_`, `should_`

## Folder Structure

```text
/app
  /core
  /db
  /models
  /repositories
  /services
  /routers
  /schemas
  /plugins
/frontend
  /src
    /components
    /pages
    /services
    /utils
/.agents
  /agent
    /plugins
/tests
  /unit
  /integration
  /contract
```

## Review Checklist

- Tests added and passing
- Security implications reviewed
- Performance impact measured
- Documentation updated
- Migration included if schema changed
- Changelog updated
- Backward compatibility checked
- Observability added
- Rollback plan defined
