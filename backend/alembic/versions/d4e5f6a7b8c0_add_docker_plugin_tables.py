"""add_docker_plugin_tables

Revision ID: d4e5f6a7b8c0
Revises: c3d4e5f6a7b9
Create Date: 2026-07-27

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c0"
down_revision: str | None = "c3d4e5f6a7b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "docker_hosts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("hostname", sa.String(300), nullable=False),
        sa.Column("docker_version", sa.String(50), nullable=True),
        sa.Column("api_version", sa.String(20), nullable=True),
        sa.Column("os", sa.String(100), nullable=True),
        sa.Column("kernel", sa.String(100), nullable=True),
        sa.Column("cpu_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("memory_total", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("online", sa.Boolean(), nullable=False, server_default=sa.text("false"), index=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "docker_containers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("host_id", sa.Integer(), sa.ForeignKey("docker_hosts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("container_id", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("image", sa.String(500), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("state", sa.String(20), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("restart_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("cpu_pct", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("memory_pct", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("memory_usage", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("network_rx", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("network_tx", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("health", sa.String(20), nullable=True),
        sa.Column("compose_project", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "docker_images",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("host_id", sa.Integer(), sa.ForeignKey("docker_hosts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("image_id", sa.String(64), nullable=False, index=True),
        sa.Column("repository", sa.String(500), nullable=False),
        sa.Column("tag", sa.String(100), nullable=False, server_default=sa.text("'latest'")),
        sa.Column("size", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at_ts", sa.DateTime(), nullable=True),
        sa.Column("in_use", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("cached_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "docker_volumes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("host_id", sa.Integer(), sa.ForeignKey("docker_hosts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(300), nullable=False, index=True),
        sa.Column("driver", sa.String(50), nullable=False, server_default=sa.text("'local'")),
        sa.Column("mount_point", sa.Text(), nullable=True),
        sa.Column("size", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("cached_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "docker_networks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("host_id", sa.Integer(), sa.ForeignKey("docker_hosts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("network_id", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("driver", sa.String(50), nullable=False, server_default=sa.text("'bridge'")),
        sa.Column("scope", sa.String(50), nullable=False, server_default=sa.text("'local'")),
        sa.Column("connected_containers", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("cached_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "docker_compose_stacks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("host_id", sa.Integer(), sa.ForeignKey("docker_hosts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("project_name", sa.String(300), nullable=False, index=True),
        sa.Column("services", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("running", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("failed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(30), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("cached_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("docker_compose_stacks")
    op.drop_table("docker_networks")
    op.drop_table("docker_volumes")
    op.drop_table("docker_images")
    op.drop_table("docker_containers")
    op.drop_table("docker_hosts")
