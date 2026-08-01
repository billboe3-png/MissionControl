# QUALITY GATES

Quality gates are required before any change reaches production.
They are not negotiable.
They are not bypassable for urgency.
They preserve trust in the platform.

## Definition of Done

A change is complete only when all applicable gates are passed.

## Architecture Preserved

- Dependency boundaries respected
- No unauthorized layer bypass
- Service contracts intact
- Data flows validated
- Plugin boundaries maintained
- Agent constraints unchanged

How to verify:
- architecture review approved
- dependency graph unchanged where required
- no circular dependencies introduced
- no server logic moved to agents
- no agent logic moved to server without review

## Tests Pass

- All unit tests pass
- All integration tests pass
- All contract tests pass
- All critical-path end-to-end tests pass
- Flaky tests are eliminated before merge
- New logic includes tests for failure modes

Targets:
- Core logic coverage >= 90%
- Integration paths coverage >= 70%
- Critical user journeys smoke-tested

## Documentation Updated

- README updated for user-facing change
- API schema updated for contract change
- Runbook updated for operational change
- Architecture doc updated for topology change
- Decision log records significant choice

## No Dead Code

- No commented-out blocks
- No unreferenced files
- No unused imports
- No unreachable branches
- No abandoned code paths

Dead code is removed, not left for history.

## No Duplicate Code

- Shared logic extracted
- No copy-pasted implementations across services
- No duplicated error handling without abstraction
- No duplicated retry logic without policy

## Security Maintained

- Input validation present and complete
- All new paths authenticated and authorized
- Secrets not introduced into payloads or logs
- New dependencies scanned for vulnerabilities
- Threat model updated for architecture change
- RBAC reviewed for access expansion
- No new broad-scoped permissions

## Ruff Clean

- Ruff passes with no errors
- Ruff passes with no warnings on targeted files
- No exceptions granted without documented justification

## Compilation Clean

- Python compiles without syntax or import errors
- TypeScript compiles without errors in strict mode
- Frontend build succeeds
- Backend build succeeds

## Deployment Validated

- Deployment runbook exists
- Rollback runbook exists
- Staging deployment validated
- Health checks defined and passing
- Metrics and alerts defined and active
- SRE or operator sign-off obtained

## Performance Acceptable

- Latency regression tested
- Throughput regression tested
- Cache hit rate does not degrade
- Database query count does not increase unexpectedly
- Memory and CPU footprint within budget
- Agent resource usage unchanged without justification

## Production Ready

A change is production-ready when:
- every applicable gate above is passed
- change is reviewed and approved
- security implications are understood
- operational implications are communicated
- risk is accepted by accountable owner
- decision rationale is documented

```text
Tests        [PASS]
Security     [PASS]
Docs         [PASS]
Rollback     [READY]
Approval     [GRANTED]
Owner        [ASSIGNED]
Risk         [ACCEPTED]
────────────────────
STATUS: PRODUCTION READY
```

## Exceptions

Exceptions to quality gates:
- require explicit, time-limited approval
- require compensation plan
- require retrospective review after incident or deployment
- are recorded publicly in decision log

Unconditional exceptions are not permitted.
