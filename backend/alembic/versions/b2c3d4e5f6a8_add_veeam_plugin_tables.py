"""add_veeam_plugin_tables

Revision ID: b2c3d4e5f6a8
Revises: x3y4z5a6b7c8
Create Date: 2026-07-27

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a8"
down_revision: str | None = "x3y4z5a6b7c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "veeam_backup_servers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("username", sa.String(200), nullable=False),
        sa.Column("encrypted_password", sa.Text(), nullable=True),
        sa.Column("verify_ssl", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("timeout", sa.Integer(), nullable=False, server_default=sa.text("30")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true"), index=True),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "veeam_repositories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("server_id", sa.Integer(), sa.ForeignKey("veeam_backup_servers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("veeam_id", sa.String(100), nullable=False, index=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("path", sa.Text(), nullable=True),
        sa.Column("repo_type", sa.String(50), nullable=False, server_default=sa.text("'local'")),
        sa.Column("status", sa.String(30), nullable=False, server_default=sa.text("'online'")),
        sa.Column("total_space_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("free_space_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("used_space_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_immutability_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "veeam_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("server_id", sa.Integer(), sa.ForeignKey("veeam_backup_servers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("veeam_id", sa.String(100), nullable=False, index=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("job_type", sa.String(50), nullable=False, server_default=sa.text("'backup'")),
        sa.Column("status", sa.String(30), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_result", sa.String(30), nullable=True),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("next_run_at", sa.String(50), nullable=True),
        sa.Column("schedule_info", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "veeam_job_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("server_id", sa.Integer(), sa.ForeignKey("veeam_backup_servers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("veeam_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("veeam_session_id", sa.String(100), nullable=False, index=True),
        sa.Column("status", sa.String(30), nullable=False, server_default=sa.text("'running'")),
        sa.Column("result", sa.String(30), nullable=False, server_default=sa.text("'none'")),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("stopped_at", sa.DateTime(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("processed_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("read_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("transferred_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "veeam_restore_points",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("server_id", sa.Integer(), sa.ForeignKey("veeam_backup_servers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("veeam_id", sa.String(100), nullable=False, index=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("vm_name", sa.String(300), nullable=True),
        sa.Column("vm_id", sa.String(100), nullable=True),
        sa.Column("repository_id", sa.String(100), nullable=True),
        sa.Column("repository_name", sa.String(300), nullable=True),
        sa.Column("restore_point_type", sa.String(50), nullable=True),
        sa.Column("created_at_ts", sa.DateTime(), nullable=True),
        sa.Column("point_size_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "veeam_licenses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("server_id", sa.Integer(), sa.ForeignKey("veeam_backup_servers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("edition", sa.String(100), nullable=True),
        sa.Column("expiration_date", sa.String(50), nullable=True),
        sa.Column("license_type", sa.String(100), nullable=True),
        sa.Column("used_licenses", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_licenses", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("veeam_licenses")
    op.drop_table("veeam_restore_points")
    op.drop_table("veeam_job_runs")
    op.drop_table("veeam_jobs")
    op.drop_table("veeam_repositories")
    op.drop_table("veeam_backup_servers")
