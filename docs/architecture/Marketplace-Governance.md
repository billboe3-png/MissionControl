# Marketplace Governance

Rules for plugin marketplace submission, review, and lifecycle management.

## Submission Process

### 1. Pre-Submission Checklist

Before submitting a plugin to the marketplace, the author must verify:

- [ ] Plugin manifest is valid and complete
- [ ] Plugin passes `missioncontrol plugin validate`
- [ ] All SDK interfaces are used correctly (no private API access)
- [ ] Plugin declares `min_core_version` compatibility
- [ ] Required permissions are declared in manifest
- [ ] No hardcoded secrets, credentials, or internal URLs
- [ ] Plugin has been tested against the declared core version range

### 2. Submission

1. Author pushes plugin to a public repository or uploads a release archive
2. Submission form completed with:
   - Plugin slug, name, version, description
   - Repository URL or upload archive
   - Execution target (server / agent / hybrid)
   - Category and tags
   - Author name and contact
3. Automated validation pipeline runs

### 3. Automated Validation

The CI pipeline validates:

| Check | Description |
|-------|-------------|
| Manifest schema | All required fields present and correctly typed |
| SDK compliance | Only public SDK interfaces used |
| No dangerous patterns | No `os.system`, no raw SQL, no network calls outside SDK |
| Version format | Semantic versioning (MAJOR.MINOR.PATCH) |
| Core compatibility | `min_core_version` is a valid released version |
| Documentation | README with usage instructions |
| License | Compatible open-source license |

### 4. Security Review

Manual or automated security review:

- No credential logging or exposure
- No unsafe deserialization
- No path traversal vulnerabilities
- No injection vulnerabilities
- Proper error handling (no stack traces to users)
- Input validation on all external data

### 5. Compatibility Testing

- Tested against current core version
- Tested against `min_core_version`
- No conflicts with existing official plugins
- Resource usage within acceptable limits

### 6. Publication

- Plugin published to marketplace catalog
- Metadata indexed for search
- Health monitoring enabled
- Installation count tracked

## Review SLA

| Submission Type | Review Time |
|----------------|-------------|
| Official plugin | Expedited (internal) |
| Certified plugin | 5 business days |
| Community plugin | 10 business days |
| Security patch | 1 business day |

## Quality Tiers

### Official

- Maintained by Mission Control team
- Full test coverage required
- Security reviewed on every release
- SLA: supported with platform releases

### Certified

- Third-party, reviewed by Mission Control
- Test coverage > 80% required
- Security reviewed on initial submission
- SLA: supported within 48 hours for critical issues

### Community

- Third-party, self-published
- Automated validation only
- No manual security review
- SLA: best effort

### Private

- Organization-internal plugins
- Not published to marketplace
- Bypasses certification process
- Same SDK compliance rules apply

## Versioning Rules

### Plugin Version

Plugins follow semantic versioning:

- **MAJOR**: Breaking changes to plugin behavior or configuration schema
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, backward-compatible

### Core Compatibility

- Plugins declare `min_core_version` and optionally `max_core_version`
- Core platform loads plugins only within compatible range
- Incompatible plugins are disabled with a clear error message

### Upgrade Path

1. Plugin author releases new version
2. Marketplace notifies administrators of available update
3. Admin reviews changelog and approves update
4. Plugin is updated (zero-downtime for server plugins)
5. Agent plugins are deployed on next agent heartbeat

## Deprecation Process

1. Author submits deprecation request
2. Marketplace marks plugin as "Deprecated" with notice
3. Existing installations receive deprecation warning
4. 90-day notice period before removal
5. Migration guide published (if alternative exists)
6. Plugin removed from marketplace catalog
7. Existing installations continue to function

## Revocation Process

Immediate removal (no 90-day notice) when:

- Security vulnerability discovered and not patched
- Plugin violates marketplace policies
- Plugin contains malware or malicious code
- Legal requirements (DMCA, court order)

## Metrics and Monitoring

### Plugin Health

- Installation count
- Update adoption rate
- Error rate (from plugin health reports)
- Average response time impact

### Marketplace Health

- Total plugins by category
- Active vs deprecated ratio
- Average review time
- Submission rejection rate

## Policy Enforcement

### Automated

- CI validation on every plugin release
- Nightly security scan of published plugins
- Compatibility testing against core releases

### Manual

- Security review for certified tier
- Policy compliance audit (quarterly)
- Community plugin spot checks

## Appeals Process

1. Author receives rejection or revocation notice
2. Author may appeal within 14 days
3. Appeal reviewed by Architecture Board
4. Decision communicated within 7 days
5. Decision is final
