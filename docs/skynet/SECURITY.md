# SECURITY

## Zero Trust

Trust is not a network property.
Trust is an authenticated, authorized, encrypted relationship between explicitly identified identities.

Every request:
- must authenticate
- must authorize
- must encrypt in transit
- must log identity and outcome
- must fail closed if any control cannot be evaluated

## Least Privilege

Every component, service, agent, user, and plugin operates at minimum required privilege.
No elevated access without documented justification and time-bounded approval.

Principles:
- Users get only their granted roles
- Services get only the data they query
- Plugins get only the files they need
- Agents get only the targets they are configured for

Privilege escalation is automatic security review.

## Secrets

Secrets are:
- Always encrypted at rest
- Always encrypted in transit
- Always scoped to minimum required access
- Always rotated on schedule and on compromise suspicion
- Never reused across environments
- Never logged
- Never exposed in UI or API responses

Secrets lifecycle is automated wherever possible.
Manual rotation requires dual approval.

## Certificates

Certificates are:
- Monitored continuously
- Renewed automatically before expiry
- Validated on every connection
- Rotated on key compromise
- Never self-signed in production unless managed by platform

Certificate failures trigger immediate alerts.

## RBAC

Role-based access control governs every user-facing action.
Roles map to:
- visibility
- execution rights
- modification rights
- approval authority
- audit visibility

Roles are:
- Default-deny
- Explicitly granted
- Discoverable and auditable
- Time-bounded where appropriate

## JWT

JWT tokens:
- Carry identity and claims only
- Use short expiry
- Refresh via validated rotation
- All endpoints validate scopes independently
- Blacklisted on revocation event
- Never use unsecured verification algorithms

## API Keys

API keys:
- Used for agent authentication server-side
- Issued on registration
- Stored hashed in database
- Rotated on security event
- Revocable immediately
- Never shared between agents
- Never logged in full

## Plugin Verification

Every plugin delivered through the marketplace must:
- Include integrity signature
- Include author and version metadata
- Pass security review before publication
- Be sandboxed at runtime
- Operate within declared permission scope
- Be revertible to prior version

Installed plugins are tracked and auditable.

## Supply Chain Security

Supply chain controls cover:
- base images
- package dependencies
- build pipelines
- signing
- SBOM generation
- vulnerability scanning
- allowed registries

Any compromise triggers immediate assessment and rollback decision.

## Encryption

- TLS 1.2 minimum in all directions
- Data encrypted at rest for all sensitive stores
- Secrets encrypted with platform-managed keys
- Key rotation automated
- Old key material retained only during transition

## Logging

All security-relevant events are logged:
- authentication success/failure
- authorization success/failure
- permission changes
- secret access
- remote target interactions
- plugin installs and removals
- configuration changes
- admin actions

Logs are protected from tampering and lifecycle-managed.

## Audit

Audit records:
- are immutable
- include actor identity
- include target resource
- include action and outcome
- include timing
- are retained per policy
- are queryable by authorized operators

Audit failures are treated as operational failures.

## Secure Coding

Secure coding rules:
- input validation on every boundary
- output encoding where required
- parameterized queries everywhere
- shallow payload limits
- bounded recursion
- no arbitrary deserialization
- no command concatenation without sanitization
- no credential leakage in memory or caches
- no sensitive data in error messages

## Threat Modeling

Every major feature and architectural change undergoes threat modeling:
- asset identification
- threat actor profiles
- attack surface inventory
- mitigations prioritized by risk
- residual risk acceptance documented

Threat model updates accompany significant platform changes.
