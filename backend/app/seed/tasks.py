"""Seed default tasks."""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.project import Project
from app.models.db.task import Task


def seed(db: Session) -> bool:
    """Insert default tasks when the table is empty."""
    count = db.scalar(select(func.count(Task.id)))
    if count > 0:
        return False

    projects = db.scalars(select(Project).order_by(Project.id)).all()
    if not projects:
        raise RuntimeError("Projects must be seeded before tasks.")

    project_map = {project.name: project for project in projects}
    now = datetime.utcnow()

    task_definitions = [
        (
            "Mission Control",
            "Wire dashboard to PostgreSQL",
            "Connect dashboard services to live database queries for projects and tasks.",
            "in_progress",
            "high",
        ),
        (
            "Mission Control",
            "Implement database seeding",
            "Add modular seed framework and idempotent seed runners for development data.",
            "completed",
            "high",
        ),
        (
            "UnitSphere",
            "Provision core services",
            "Deploy foundational UnitSphere services across the target environment.",
            "pending",
            "high",
        ),
        (
            "UnitSphere",
            "Validate cross-service connectivity",
            "Run integration checks between UnitSphere microservices and shared infrastructure.",
            "pending",
            "medium",
        ),
        (
            "Infrastructure Upgrade",
            "Replace legacy network switches",
            "Schedule and execute switch replacements in the primary data centre.",
            "in_progress",
            "high",
        ),
        (
            "Infrastructure Upgrade",
            "Migrate DNS to new servers",
            "Move internal DNS zones to the upgraded resolver cluster with rollback plan.",
            "pending",
            "medium",
        ),
        (
            "Automation Scripts",
            "Build deployment wrapper script",
            "Create a reusable PowerShell wrapper for consistent application deployments.",
            "in_progress",
            "medium",
        ),
        (
            "Automation Scripts",
            "Add CI lint automation",
            "Integrate lint checks into the quality gate pipeline for backend and frontend.",
            "pending",
            "low",
        ),
    ]

    tasks = []
    for project_name, title, description, status, priority in task_definitions:
        project = project_map.get(project_name)
        if project is None:
            continue

        tasks.append(
            Task(
                project_id=project.id,
                title=title,
                description=description,
                status=status,
                priority=priority,
                created_at=now,
                updated_at=now,
            )
        )

    if not tasks:
        raise RuntimeError("No matching projects found for task seed data.")

    db.add_all(tasks)
    db.commit()
    return True
