# Release Process

Mission Control follows a versioned release process. The current version is tracked in the `VERSION` file at the repository root.

## Version Scheme

Mission Control uses [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

| Change | Bump | Example |
|--------|------|---------|
| Breaking API changes, new major features | MAJOR | 3.0.0 → 4.0.0 |
| New features, non-breaking changes | MINOR | 3.0.0 → 3.1.0 |
| Bug fixes, security patches | PATCH | 3.0.0 → 3.0.1 |

## Step-by-Step Release

### 1. Ensure all changes are merged to `develop`

```bash
git checkout develop
git pull origin develop
```

Verify the branch is up to date and all PRs are merged.

### 2. Run the full quality gate

```bash
# Backend lint
cd backend
ruff check app/ tests/

# Frontend type check
cd frontend
npx tsc --noEmit

# Frontend build
npm run build

# Backend tests
cd backend
python -m pytest tests/ -v
```

All checks must pass before proceeding.

### 3. Update the VERSION file

```bash
echo "3.1.0" > VERSION
```

### 4. Update CHANGELOG.md

Add a new section at the top of `CHANGELOG.md`:

```markdown
## [3.1.0] - 2026-01-15

### Added
- Feature A: description
- Feature B: description

### Fixed
- Bug fix X: description
- Bug fix Y: description

### Changed
- Change Z: description

### Breaking Changes
- API endpoint `/old` removed, use `/new` instead
```

Use these categories following the [Keep a Changelog](https://keepachangelog.com/) convention:

| Category | When to Use |
|----------|-------------|
| **Added** | New features |
| **Fixed** | Bug fixes |
| **Changed** | Modifications to existing functionality |
| **Removed** | Removed features |
| **Deprecated** | Features marked for future removal |
| **Security** | Vulnerability fixes |

### 5. Merge `develop` into `main`

```bash
git checkout main
git pull origin main
git merge develop
git push origin main
```

### 6. Create a git tag

```bash
git tag -a v3.1.0 -m "Release v3.1.0"
git push origin v3.1.0
```

### 7. Create a GitHub Release

Using the GitHub CLI:

```bash
gh release create v3.1.0 \
  --title "v3.1.0" \
  --notes "## Added
- Feature A
- Feature B

## Fixed
- Bug fix X" \
  --target main
```

Or create the release manually from the GitHub Releases page.

### 8. Deploy to production

The CI pipeline automatically deploys to GCE when changes are pushed to `main`. If you need to deploy manually:

```bash
ssh <deploy-user>@<gce-host>
cd /opt/mission-control
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker compose -f docker-compose.prod.yml restart backend
```

### 9. Verify the deployment

```bash
# Check service health
curl https://<your-domain>/api/v1/health/live

# Check version
curl https://<your-domain>/api/v1/version
```

## Hotfix Releases

For critical production issues:

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/3.0.1

# Make the fix
# ...

# Run tests
cd backend && python -m pytest tests/ -v

# Update VERSION and CHANGELOG
echo "3.0.1" > VERSION
# Edit CHANGELOG.md

# Merge into main
git checkout main
git merge hotfix/3.0.1
git push origin main

# Tag and release
git tag -a v3.0.1 -m "Hotfix v3.0.1"
git push origin v3.0.1

# Also merge back into develop
git checkout develop
git merge hotfix/3.0.1
git push origin develop
```

## Version References in Code

The version string appears in multiple places. When bumping the version, update all of them:

| File | Location |
|------|----------|
| `VERSION` | Root file — single source of truth |
| `backend/app/main.py` | `version="3.0.0"` in `FastAPI()` constructor |
| `frontend/package.json` | `"version": "3.0.0"` |
| `CHANGELOG.md` | New release section |

## Cross-References

- See [CI_CD.md](CI_CD.md) for the automated deployment pipeline.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow.
- See [CHANGELOG.md](../../CHANGELOG.md) for the release history.
- See [DEPLOYMENT.md](../../DEPLOYMENT.md) for deployment instructions.
