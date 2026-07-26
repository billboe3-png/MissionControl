# CI/CD Pipeline

Mission Control uses GitHub Actions for continuous integration and deployment.

## Pipeline Overview

```
Push to main/develop or manual trigger
    │
    ▼
┌─────────────────────┐
│  Lint (ruff)        │  Backend Python linting
├─────────────────────┤
│  Type Check (tsc)   │  Frontend TypeScript checking
├─────────────────────┤
│  Build (frontend)   │  Production frontend build
├─────────────────────┤
│  Test (pytest)      │  Backend test suite
├─────────────────────┤
│  Deploy (SSH)       │  Push to GCE server
└─────────────────────┘
```

## Workflow File

The pipeline is defined in `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install ruff
        run: pip install ruff

      - name: Run ruff lint
        run: ruff check backend/app/ backend/tests/

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install frontend dependencies
        working-directory: frontend
        run: npm ci

      - name: TypeScript type check
        working-directory: frontend
        run: npx tsc --noEmit

  build:
    runs-on: ubuntu-latest
    needs: [lint, typecheck]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install and build frontend
        working-directory: frontend
        run: |
          npm ci
          npm run build

  test:
    runs-on: ubuntu-latest
    needs: [lint]
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: mission_control_test
          POSTGRES_USER: mission_control
          POSTGRES_PASSWORD: mission_control
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7.2-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      POSTGRES_HOST: localhost
      POSTGRES_PORT: 5432
      POSTGRES_DB: mission_control_test
      POSTGRES_USER: mission_control
      POSTGRES_PASSWORD: mission_control
      REDIS_HOST: localhost
      REDIS_PORT: 6379
      MISSIONCONTROL_SECRET_KEY: ${{ secrets.MISSIONCONTROL_SECRET_KEY }}
      TESTING: "1"

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install backend dependencies
        working-directory: backend
        run: pip install -r requirements.txt

      - name: Run database migrations
        working-directory: backend
        run: alembic upgrade head

      - name: Run tests
        working-directory: backend
        run: python -m pytest tests/ -v --tb=short

  deploy:
    runs-on: ubuntu-latest
    needs: [build, test]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to GCE
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_SSH_KEY }}
          script: |
            cd /opt/mission-control
            git pull origin main
            docker compose -f docker-compose.prod.yml up -d --build
            docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
            docker compose -f docker-compose.prod.yml restart backend
```

## Triggers

| Trigger | Branches | Purpose |
|---------|----------|---------|
| `push` | `main`, `develop` | Run pipeline on every push |
| `pull_request` | `main`, `develop` | Validate PRs before merge |
| `workflow_dispatch` | (manual) | Trigger manually from the Actions tab |

## Job Dependencies

```
lint ─────┬──► build ──┬──► deploy (main only)
typecheck ┘            │
test ──────────────────┘
```

- `lint` and `typecheck` run in parallel.
- `build` waits for both `lint` and `typecheck`.
- `test` waits for `lint` only (it does not need the frontend build).
- `deploy` waits for both `build` and `test`, and only runs on pushes to `main`.

## Secrets

The following secrets must be configured in GitHub repository settings:

| Secret | Purpose |
|--------|---------|
| `MISSIONCONTROL_SECRET_KEY` | Fernet key for test credential encryption |
| `DEPLOY_HOST` | SSH hostname or IP of the GCE server |
| `DEPLOY_USER` | SSH username for deployment |
| `DEPLOY_SSH_KEY` | SSH private key for deployment |

## Local Quality Gate

Run the same checks locally before pushing:

```bash
# Backend lint
cd backend
ruff check app/ tests/

# Frontend type check
cd frontend
npx tsc --noEmit

# Frontend build
cd frontend
npm run build

# Backend tests
cd backend
python -m pytest tests/ -v
```

## Deployment Flow

The deploy job runs only on pushes to `main`:

1. SSH into the GCE server.
2. Pull the latest code from `main`.
3. Rebuild and restart Docker containers with `docker compose up -d --build`.
4. Run any pending Alembic migrations.
5. Restart the backend to pick up changes.

This is a simple push-based deployment. There is no staging environment — `develop` is used for integration testing before merging to `main`.

## Cross-References

- See [RELEASE_PROCESS.md](RELEASE_PROCESS.md) for cutting releases.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for the PR workflow.
- See [TESTING.md](TESTING.md) for the test suite details.
- See [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for local development.
