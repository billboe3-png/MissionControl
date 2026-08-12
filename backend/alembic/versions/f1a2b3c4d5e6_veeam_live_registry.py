"""Veeam plugin: live server registry

Revision ID: f1a2b3c4d5e6
Revises: 6b29cb7f19c9
Create Date: 2026-08-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "6b29cb7f19c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("veeam_backup_servers", sa.Column("edition", sa.String(20), nullable=False, server_default="enterprise"))
    op.add_column("veeam_backup_servers", sa.Column("data_source", sa.String(20), nullable=False, server_default="both"))
    op.add_column("veeam_backup_servers", sa.Column("db_type", sa.String(20), nullable=False, server_default="auto"))
    op.add_column("veeam_backup_servers", sa.Column("column_case", sa.String(20), nullable=False, server_default="pascal"))
    op.add_column("veeam_backup_servers", sa.Column("agent_id", sa.Integer(), nullable=True))
    op.add_column("veeam_backup_servers", sa.Column("target_id", sa.Integer(), nullable=True))
    op.add_column("veeam_backup_servers", sa.Column("last_diagnostic", sa.Text(), nullable=True))
    op.add_column("veeam_backup_servers", sa.Column("legacy_ssh_host", sa.String(500), nullable=True))
    op.add_column("veeam_backup_servers", sa.Column("legacy_ssh_port", sa.Integer(), nullable=True))
    op.add_column("veeam_backup_servers", sa.Column("legacy_ssh_username", sa.String(200), nullable=True))
    op.add_column("veeam_backup_servers", sa.Column("legacy_ssh_password_encrypted", sa.Text(), nullable=True))

    op.create_foreign_key("fk_veeam_backup_servers_agent", "veeam_backup_servers", "agents", ["agent_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_veeam_backup_servers_target", "veeam_backup_servers", "agent_remote_targets", ["target_id"], ["id"], ondelete="SET NULL")

    # Backfill from integration_profiles where integration_type == 'veeam'.
    # Existing url/username/encrypted_password are renamed to rest_* here —
    # the rename CREATES rest_*; do NOT add_column them or Alembic fails
    # with a duplicate-column error.
    op.alter_column("veeam_backup_servers", "url", new_column_name="rest_url")
    op.alter_column("veeam_backup_servers", "username", new_column_name="rest_username")
    op.alter_column("veeam_backup_servers", "encrypted_password", new_column_name="rest_password_encrypted")

    # Legacy url/username were NOT NULL, but community-only backfill rows have
    # NULL rest_url/rest_username. Relax nullability or the backfill INSERT fails.
    op.alter_column("veeam_backup_servers", "rest_url", nullable=True)
    op.alter_column("veeam_backup_servers", "rest_username", nullable=True)

    op.execute("""
    INSERT INTO veeam_backup_servers (
        name, edition, data_source, db_type, column_case,
        rest_url, rest_username, rest_password_encrypted,
        verify_ssl, timeout, enabled, status,
        legacy_ssh_host, legacy_ssh_port, legacy_ssh_username,
        legacy_ssh_password_encrypted,
        created_at, updated_at
    )
    SELECT
        p.name,
        CASE WHEN p.base_url IS NOT NULL AND p.base_url != '' THEN 'enterprise' ELSE 'community' END,
        COALESCE(p.data_source, 'both'),
        'auto',
        'pascal',
        NULLIF(p.base_url, ''),
        p.username,
        p.encrypted_secret,
        p.verify_ssl,
        COALESCE(p.timeout, 30),
        p.enabled,
        'unknown',
        NULLIF(p.ssh_host, ''),
        p.ssh_port,
        NULLIF(p.ssh_username, ''),
        p.ssh_password_encrypted,
        p.created_at,
        p.updated_at
    FROM integration_profiles p
    WHERE p.integration_type = 'veeam'
      AND NOT EXISTS (
        SELECT 1 FROM veeam_backup_servers v WHERE v.name = p.name
      )
    """)


def downgrade() -> None:
    op.execute("""
    DELETE FROM veeam_backup_servers
    WHERE last_diagnostic IS NULL AND rest_url IS NULL AND legacy_ssh_host IS NULL
    """)
    op.drop_constraint("fk_veeam_backup_servers_target", "veeam_backup_servers", type_="foreignkey")
    op.drop_constraint("fk_veeam_backup_servers_agent", "veeam_backup_servers", type_="foreignkey")
    for col in (
        "edition", "data_source", "db_type", "column_case", "agent_id", "target_id",
        "last_diagnostic", "legacy_ssh_host", "legacy_ssh_port", "legacy_ssh_username",
        "legacy_ssh_password_encrypted",
    ):
        op.drop_column("veeam_backup_servers", col)
    op.alter_column("veeam_backup_servers", "rest_password_encrypted", new_column_name="encrypted_password")
    op.alter_column("veeam_backup_servers", "rest_username", new_column_name="username")
    op.alter_column("veeam_backup_servers", "rest_url", new_column_name="url")
