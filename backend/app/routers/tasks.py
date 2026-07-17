"""
Mission Control Tasks Router

Sprint:
    1.2.2 - Task API Foundation
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.task_service import TaskService, task_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
    dependencies=[Depends(get_current_user)],
)


def get_task_service() -> TaskService:
    """Provide the shared task service instance."""
    return task_service


@router.get(
    "",
    summary="List tasks",
    description="Return all tasks managed by Mission Control.",
    response_model=TaskListResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Tasks retrieved successfully.",
            "model": TaskListResponse,
        },
    },
)
async def list_tasks(
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> TaskListResponse:
    return await service.get_all(db)


@router.get(
    "/{task_id}",
    summary="Get task",
    description="Return a single task by its identifier.",
    response_model=TaskResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Task retrieved successfully.",
            "model": TaskResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Task not found.",
        },
    },
)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return await service.get_by_id(db, task_id)


@router.post(
    "",
    summary="Create task",
    description="Create a new task record.",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Task created successfully.",
            "model": TaskResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Project not found.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Task already exists in the project.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
    },
)
async def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return await service.create(db, payload)


@router.put(
    "/{task_id}",
    summary="Update task",
    description="Replace task fields for an existing task.",
    response_model=TaskResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Task updated successfully.",
            "model": TaskResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Task or project not found.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Task already exists in the project.",
        },
    },
)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return await service.update(db, task_id, payload)


@router.delete(
    "/{task_id}",
    summary="Delete task",
    description="Remove a task by its identifier.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Task deleted successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Task not found.",
        },
    },
)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> None:
    await service.delete(db, task_id)
