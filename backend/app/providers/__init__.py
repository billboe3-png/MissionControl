"""
Mission Control Dashboard Providers

Each provider encapsulates a single domain of dashboard data.
Providers are stateless and called by the DashboardService orchestrator.
"""

from app.providers.health_provider import HealthProvider
from app.providers.note_provider import NoteProvider
from app.providers.parking_lot_provider import ParkingLotProvider
from app.providers.project_provider import ProjectProvider
from app.providers.remote_provider import RemoteProvider
from app.providers.resume_provider import ResumeProvider
from app.providers.task_provider import TaskProvider

__all__ = [
    "HealthProvider",
    "NoteProvider",
    "ParkingLotProvider",
    "ProjectProvider",
    "RemoteProvider",
    "ResumeProvider",
    "TaskProvider",
]
