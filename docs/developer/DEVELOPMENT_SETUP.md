# Development Setup

Step-by-step instructions for getting Mission Control running locally.

## 1. Clone the Repository

```bash
git clone <repository-url>
cd MissionControl
```

## 2. Create the Environment File

```bash
cp .env.example .env
```

Generate a Fernet key and paste it into `.env` as `MISSIONCONTROL_SECRET_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

The stack will not start without a valid `MISSIONCONTROL_SECRET_KEY`.

## 3. Start Infrastructure Services

PostgreSQL and Redis run in Docker even for local development:

```bash
docker compose up -d postgres redis
```

Wait for the health checks to pass:

```bash
docker compose ps
```

Both `postgres` and `redis` should show `healthy`.

## 4. Backend Setup

### Create a virtual environment

```bash
cd backend
python -m venv .venv
```

Activate it:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

The `.env` file at the project root is shared. The backend reads `POSTGRES_HOST=postgres` by default. For local development without Docker for the app server, override the database URL:

```bash
export POSTGRES_HOST=localhost
export REDIS_HOST=localhost
```

Or create `backend/.env` with:

```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Run database migrations

```bash
cd backend
alembic upgrade head
```

### Seed the database

```bash
python -m app.seed.runner
```

This creates the default admin user and any required seed data. The seeder is idempotent — safe to run multiple times.

### Start the backend server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is now available at:
- API: http://localhost:8000/api/v1
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/api/redoc

## 5. Frontend Setup

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs at http://localhost:5173 with hot module replacement.

## 6. Full Docker Stack (Alternative)

If you prefer to run everything in Docker:

```bash
docker compose up -d
```

This starts all five services: nginx (port 80), backend, frontend, postgres, and redis.

The backend entrypoint automatically runs migrations and seeds the database on first start.

### Docker commands

```bash
# View running services
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop everything
docker compose down

# Stop and remove volumes (fresh start)
docker compose down -v
```

## 7. Verify the Setup

### Backend health check

```bash
curl http://localhost:8000/api/v1/health/live
```

### Frontend

Open http://localhost:5173 in your browser. You should see the login page.

### Lint check

```bash
# Backend
cd backend
ruff check app/ tests/

# Frontend
cd frontend
npx tsc --noEmit
```

## 8. IDE Configuration

### VS Code

The project includes VS Code workspace settings. Open the `MissionControl` folder as a workspace for recommended extensions and tasks.

### Recommended extensions

- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- ESLint (dbaeumer.vscode-eslint)
- Tailwind CSS IntelliSense (bradlc.vscode-tailwindcss)

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MISSIONCONTROL_SECRET_KEY` | **Yes** | — | Fernet key for credential encryption |
| `POSTGRES_DB` | No | `mission_control` | Database name |
| `POSTGRES_USER` | No | `mission_control` | Database user |
| `POSTGRES_PASSWORD` | No | `mission_control` | Database password |
| `POSTGRES_HOST` | No | `postgres` | Database host |
| `POSTGRES_PORT` | No | `5432` | Database port |
| `REDIS_HOST` | No | `redis` | Redis host |
| `REDIS_PORT` | No | `6379` | Redis port |
| `BACKEND_CORS_ORIGINS` | No | `http://localhost,http://localhost:3000,http://localhost:5173` | CORS origins |
| `RATE_LIMIT_PER_MINUTE` | No | `60` | General rate limit |
| `RATE_LIMIT_AUTH_PER_MINUTE` | No | `5` | Login rate limit |

## Troubleshooting

### "Configuration error: MISSIONCONTROL_SECRET_KEY"

The `.env` file is missing or `MISSIONCONTROL_SECRET_KEY` is set to `CHANGE_ME`. Generate a real key and update the file.

### PostgreSQL connection refused

Ensure Docker is running and the postgres container is healthy:

```bash
docker compose ps postgres
docker compose logs postgres
```

### Port 8000 already in use

Stop the existing process or use a different port:

```bash
uvicorn app.main:app --reload --port 8001
```

Update `BACKEND_CORS_ORIGINS` in `.env` to include the new port.

### Alembic migration conflicts

If you encounter merge conflicts in migration files:

```bash
cd backend
alembic merge -m "merge heads" <head1> <head2>
alembic upgrade head
```

## Next Steps

- Read [CODING_STANDARDS.md](CODING_STANDARDS.md) before writing code.
- Read [BACKEND.md](BACKEND.md) or [FRONTEND.md](FRONTEND.md) depending on your focus area.
- Read [TESTING.md](TESTING.md) to set up the test suite.
