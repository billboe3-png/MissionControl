# Testing Standards

## Test Categories

### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Fast execution (< 100ms per test)
- No database or network calls

### Integration Tests
- Test service-to-repository interactions
- Use in-memory SQLite database
- Test complete business logic flows

### API Tests
- Test HTTP request/response cycle
- Use FastAPI TestClient
- Test authentication and authorization
- Test error responses

### Frontend Tests
- TypeScript type checking (`tsc --noEmit`)
- Component rendering tests
- Build verification (`npm run build`)

### Plugin Tests
- Test plugin registration and lifecycle
- Test SDK interface compliance
- Test plugin configuration
- Test plugin marketplace integration

### Agent Tests
- Test agent registration and heartbeat
- Test command dispatch and results
- Test inventory collection
- Test plugin communication

### Automation Tests
- Test playbook execution
- Test variable substitution
- Test approval workflows
- Test scheduling and triggers

## Coverage Targets

| Category | Minimum | Target |
|----------|---------|--------|
| Overall | 80% | 90% |
| Core services | 90% | 95% |
| API endpoints | 100% | 100% |
| Plugin SDK | 95% | 100% |
| Repository layer | 85% | 90% |

## Quality Gates

Every code change MUST pass:

1. **pytest** — All tests pass (0 failures)
2. **ruff check** — No new linting errors
3. **tsc --noEmit** — TypeScript compiles without errors
4. **npm run build** — Frontend builds successfully

Run after EVERY phase:
```bash
docker compose exec -T backend python -m pytest tests/ -q
docker compose exec -T backend ruff check app/ tests/
cd frontend && npx tsc --noEmit && npm run build
```

## CI/CD

GitHub Actions runs on every push and PR:

1. Backend: ruff lint + pytest
2. Frontend: TypeScript check + build

See `.github/workflows/ci.yml`.
