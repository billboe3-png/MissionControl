"""
Docker Plugin SQLAlchemy Models

Tables for caching Docker data locally:
- docker_hosts: registered Docker hosts
- docker_containers: cached container inventory
- docker_images: cached image inventory
- docker_volumes: cached volume inventory
- docker_networks: cached network inventory
- docker_compose_stacks: cached Compose stack inventory
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class DockerHost(Base):
    """Registered Docker host connection."""

    __tablename__ = "docker_hosts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    hostname: Mapped[str] = mapped_column(String(300), nullable=False)
    docker_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    api_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    os: Mapped[str | None] = mapped_column(String(100), nullable=True)
    kernel: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cpu_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    memory_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class DockerContainer(Base):
    """Cached Docker container inventory."""

    __tablename__ = "docker_containers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    host_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("docker_hosts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    container_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    image: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    restart_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cpu_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    memory_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    memory_usage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    network_rx: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    network_tx: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    health: Mapped[str | None] = mapped_column(String(20), nullable=True)
    compose_project: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class DockerImage(Base):
    """Cached Docker image inventory."""

    __tablename__ = "docker_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    host_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("docker_hosts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    image_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    repository: Mapped[str] = mapped_column(String(500), nullable=False)
    tag: Mapped[str] = mapped_column(String(100), nullable=False, default="latest")
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    in_use: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cached_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
    )


class DockerVolume(Base):
    """Cached Docker volume inventory."""

    __tablename__ = "docker_volumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    host_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("docker_hosts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    driver: Mapped[str] = mapped_column(String(50), nullable=False, default="local")
    mount_point: Mapped[str] = mapped_column(Text, nullable=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cached_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
    )


class DockerNetwork(Base):
    """Cached Docker network inventory."""

    __tablename__ = "docker_networks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    host_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("docker_hosts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    network_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    driver: Mapped[str] = mapped_column(String(50), nullable=False, default="bridge")
    scope: Mapped[str] = mapped_column(String(50), nullable=False, default="local")
    connected_containers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cached_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
    )


class DockerComposeStack(Base):
    """Cached Docker Compose stack inventory."""

    __tablename__ = "docker_compose_stacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    host_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("docker_hosts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    project_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    services: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    running: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    cached_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
    )
