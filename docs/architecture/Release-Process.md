# Release Process

## Release Lifecycle

### Development
- Active development on `main` branch
- All changes go through PR review
- Quality gates must pass before merge

### Alpha
- Internal testing release
- Feature complete but may have bugs
- Not for production use
- Tagged: `v3.1.0-alpha.1`

### Beta
- External testing release
- Feature complete, known issues documented
- May be used in non-production environments
- Tagged: `v3.1.0-beta.1`

### Release Candidate
- Code freeze, no new features
- Only bug fixes and documentation updates
- Candidate for stable release
- Tagged: `v3.1.0-rc.1`

### Stable
- Production-ready release
- Full test suite passing
- Documentation complete
- Tagged: `v3.1.0`

### Long Term Support (LTS)
- Major versions receive LTS designation
- Minimum 2 years of security patches
- Critical bug fixes only after initial support period

### Emergency Hotfix
- Critical security or data loss issues
- Fast-tracked through review
- Released as patch version
- Tagged: `v3.0.1`

### Security Patch
- Security vulnerability fixes
- Released as soon as possible
- May be backported to previous major versions
- Tagged: `v3.0.1` (security)

## Versioning Strategy

| Component | Versioning | Example |
|-----------|-----------|---------|
| Core platform | `MAJOR.MINOR.PATCH` | 3.1.0 |
| Plugin SDK | `MAJOR.MINOR.PATCH` | 3.0.0 |
| Individual plugins | `MAJOR.MINOR.PATCH` | 1.2.3 |
| Database migrations | Sequential revision | `a1b2c3d4e5f6` |

## Plugin Release Process

1. Plugin author updates version in `plugin.json`
2. Plugin author updates CHANGELOG
3. Plugin submitted for certification (official/certified)
4. Automated validation (manifest, compatibility)
5. Security review (if official/certified)
6. Published to marketplace
7. Existing installations notified of update

## Release Checklist

- [ ] All tests pass (pytest, ruff, tsc, npm build)
- [ ] Database migrations tested
- [ ] CHANGELOG updated
- [ ] Version bumped in all relevant files
- [ ] Documentation updated
- [ ] Security review completed
- [ ] Performance benchmarks run
- [ ] Backward compatibility verified
- [ ] Release notes drafted
- [ ] Git tag created
