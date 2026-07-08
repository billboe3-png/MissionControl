from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import (
    dashboard,
    doctor,
    docker,
    git,
    health,
    projects,
    status,
    version,
)

settings = get_settings()

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
