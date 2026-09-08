"""
Veeam Plugin SQLAlchemy Models

Tables for caching Veeam B&R data locally:
- veeam_backup_servers: registered Veeam server connections
- veeam_repositories: cached backup repository inventory
- veeam_jobs: cached backup/replication/copy job state
- veeam_job_runs: cached individual job session runs
- veeam_restore_points: cached restore point inventory
- veeam_licenses: cached license information
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class VeeamBackupServer(Base):
    """Registered Veeam B&R server connection."""

    __tablename__ = "veeam_backup_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True, name="rest_url")
    username: Mapped[str | None] = mapped_column(String(200), nullable=True, name="rest_username")
    encrypted_password: Mapped[str | None] = mapped_column(Text, nullable=True, name="rest_password_encrypted")
    verify_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    timeout: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    edition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Legacy SSH fields (deprecated)
    legacy_ssh_host: Mapped[str | None] = mapped_column(String(200), nullable=True)
    legacy_ssh_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    legacy_ssh_username: Mapped[str | None] = mapped_column(String(200), nullable=True)
    legacy_ssh_password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Database connection settings for SSH+SQL bridge
    ssh_host: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ssh_port: Mapped[int] = mapped_column(Integer, nullable=False, default=22)
    ssh_username: Mapped[str | None] = mapped_column(String(200), nullable=True)
    encrypted_ssh_password: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(String(20), nullable=False, default="both")
    db_type: Mapped[str] = mapped_column(String(20), nullable=False, default="postgresql")  # postgresql, mssql
    column_case: Mapped[str] = mapped_column(String(20), nullable=False, default="pascal")  # pascal, snake (for MSSQL)

    # Agent/Target association
    agent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_diagnostic: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class VeeamRepository(Base):
    """Cached backup repository inventory."""

    __tablename__ = "veeam_repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("veeam_backup_servers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    veeam_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    path: Mapped[str | None] = mapped_column(Text, nullable=True)
    repo_type: Mapped[str] = mapped_column(String(50), nullable=False, default="local")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="online")
    total_space_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    free_space_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used_space_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_immutability_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class VeeamJob(Base):
    """Cached backup job state."""

    __tablename__ = "veeam_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("veeam_backup_servers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    veeam_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, default="backup")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_result: Mapped[str | None] = mapped_column(String(30), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    schedule_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class VeeamJobRun(Base):
    """Individual job session run for history tracking."""

    __tablename__ = "veeam_job_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("veeam_backup_servers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("veeam_jobs.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    veeam_session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="running")
    result: Mapped[str] = mapped_column(String(30), nullable=False, default="none")
    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    read_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transferred_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )


class VeeamRestorePoint(Base):
    """Cached restore point inventory."""

    __tablename__ = "veeam_restore_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("veeam_backup_servers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    veeam_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    vm_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    vm_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    repository_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    repository_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    restore_point_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    point_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )


class VeeamLicense(Base):
    """Cached Veeam license information."""

    __tablename__ = "veeam_licenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("veeam_backup_servers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    edition: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expiration_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    license_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    used_licenses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_licenses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )


class VeeamSnapshot(Base):
    """Hourly snapshot of a live Veeam dataset for instant cache reads."""

    __tablename__ = "veeam_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("veeam_backup_servers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    dataset: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("server_id", "dataset", name="uq_veeam_snapshots_server_dataset"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
