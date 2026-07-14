from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import (
    dashboard,
    docker,
    doctor,
    git,
    health,
    notes,
    parking_lot,
    projects,
    remote,
    resume,
    status,
    tasks,
    version,
)

try:
    settings = get_settings()
except Exception as exc:
    from app.core.startup_check import _fail

    _fail(
        message=f"Configuration error: {exc}",
        instruction=(
            "Check your .env file and ensure MISSIONCONTROL_SECRET_KEY "
            "is set to a valid Fernet key.\n"
            "\n"
            "Generate one using:\n"
            "\n"
            '  python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        ),
    )

app = FastAPI(
    title=settings.project_name,
    version="0.1.1",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# API Routers
# ------------------------------------------------------------------

app.include_router(health.router, prefix="/api/v1")
app.include_router(version.router, prefix="/api/v1")
app.include_router(status.router, prefix="/api/v1")
app.include_router(doctor.router, prefix="/api/v1")
app.include_router(docker.router, prefix="/api/v1")
app.include_router(git.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(notes.router, prefix="/api/v1")
app.include_router(resume.router, prefix="/api/v1")
app.include_router(parking_lot.router, prefix="/api/v1")
app.include_router(remote.router, prefix="/api/v1")


@app.get("/api/v1")
async def api_root() -> dict[str, str]:
    """
    Mission Control API Root
    """
    return {
        "name": settings.project_name,
        "status": "online",
        "environment": settings.environment,
        "version": "0.1.1",
    }
