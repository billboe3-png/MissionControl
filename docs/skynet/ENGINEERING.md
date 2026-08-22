# ENGINEERING

## Production-First Engineering

Production behavior is the only final arbiter of correctness.
Staging, labs, and simulations are necessary but never sufficient.
Every change must be evaluated against its production impact before merge.

```text
RULE 1: If it cannot run in production, it is not complete
RULE 2: If it cannot roll back safely, it is not safe
RULE 3: If it cannot be monitored, it is not production-ready
RULE 4: If it cannot be debugged under pressure, it is not built correctly
```

## Clean Architecture

Structure systems around:
- Entities independent of frameworks
- Use cases independent of delivery mechanism
- Delivery mechanism isolated in outer layers
- Clear dependency boundaries
- Testable core logic

Violations are bugs in architecture, not shortcuts.

## Refactoring

Refactoring is continuous.
Technical debt is treated like security debt:
it compounds silently and fails catastrophically under load.

Principles:
- Small, reversible changes
- Behavior preservation
- Continuous test coverage
- No rewrites without measurement

## Maintainability

Code is written once and read hundreds of times.
Optimize for the reader, not the author.

Requirements:
- Single-responsibility functions and classes
- Predictable naming
- Explicit over implicit
- No clever tricks without comments
- No dead code paths

## Observability

Every component must emit:
- Structured logs
- Measurable metrics
- Traceable events
- Health signals

Observability requirements:
- No silent fallbacks
- No swallowed exceptions
- No unbounded retries
- No undiagnosed failures

## Reliability

Design for failure first.
Then design for recovery.
Then design for recovery under load.
Then design for recovery under adversarial conditions.

## Performance

Measure before optimizing.
Profile before tuning.
Benchmark before shipping.
Regression suites must cover latency-critical paths.

## Scalability

Scale horizontally before vertically.
Scale stateless services before stateful.
Scale read throughput before write.
Scale by domain boundary, not by contingency.

## Enterprise Readiness

Every capability must work at enterprise scale:
- Multi-tenant data isolation
- Role-based access
- Audit trails
- Support models
- Change control
- Disaster recovery

## Backward Compatibility

Never break API contracts without deprecation.
Deprecation must:
- Announce timeline
- Provide migration path
- Emit usage warnings
- Maintain old path until deprecated window closes

## Documentation

Documentation is part of delivery.
No feature is complete without:
- Architecture description
- API contract
- Operational runbook
- Troubleshooting guide

Documentation rot is technical debt.

## Testing

Test strategy:
- Unit tests for core logic
- Integration tests for boundaries
- Contract tests for APIs
- End-to-end tests for critical flows
- Chaos tests for failure modes

Every bug fix requires a regression test.
Every new feature includes tests before merge.

## Code Ownership

Owners:
- Author
- Reviewer
- Operator

Ownership continues after merge.
Developers who ship must also monitor and respond.

## Continuous Improvement

Every deployment is feedback.
Every incident is data.
Every optimization is validated.

Decisions are reversed when evidence demands.
Opinions are secondary to evidence.

## Technical Debt Reduction

Debt is tracked, prioritized, and repaid continuously.
All debt carries:
- Owner
- Severity
- Remediation plan
- Timeline

Accumulation without repayment is architectural negligence.
