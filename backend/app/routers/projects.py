"""
Mission Control Projects Router

Sprint:
    1.2.1 - Project API Foundation
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import ProjectService, project_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
    dependencies=[Depends(get_current_user)],
)


def get_project_service() -> ProjectService:
    """Provide the shared project service instance."""
    return project_service


@router.get(
    "",
    summary="List projects",
    description="Return all projects managed by Mission Control.",
    response_model=ProjectListResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Projects retrieved successfully.",
            "model": ProjectListResponse,
        },
    },
)
async def list_projects(
    db: Session = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    return await service.get_all(db)


@router.get(
    "/{project_id}",
    summary="Get project",
    description="Return a single project by its identifier.",
    response_model=ProjectResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Project retrieved successfully.",
            "model": ProjectResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Project not found.",
        },
    },
)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await service.get_by_id(db, project_id)


@router.post(
    "",
    summary="Create project",
    description="Create a new project record.",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Project created successfully.",
            "model": ProjectResponse,
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Project name already exists.",
        },
    },
)
async def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await service.create(db, payload)


@router.put(
    "/{project_id}",
    summary="Update project",
    description="Replace project fields for an existing project.",
    response_model=ProjectResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Project updated successfully.",
            "model": ProjectResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Project not found.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Project name already exists.",
        },
    },
)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await service.update(db, project_id, payload)


@router.delete(
    "/{project_id}",
    summary="Delete project",
    description="Remove a project by its identifier.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Project deleted successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Project not found.",
        },
    },
)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
) -> None:
    await service.delete(db, project_id)


@router.post(
    "/{project_id}/close",
    summary="Close project",
    description="Mark a project as inactive without deleting it.",
    response_model=ProjectResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Project closed successfully.",
            "model": ProjectResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Project not found.",
        },
    },
)
async def close_project(
    project_id: int,
    db: Session = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await service.close(db, project_id)
