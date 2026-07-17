"""add company_id and site_id to all tenant tables

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa

revision = "e3f4a5b6c7d8"
down_revision = "d2e3f4a5b6c7"
branch_labels = None
depends_on = None

# Tables that need both company_id and site_id added
TABLES_BOTH = [
    "agents",
    "command_history",
    "command_templates",
    "playbooks",
    "playbook_executions",
    "playbook_steps",
    "playbook_variables",
    "playbook_schedules",
    "scheduled_commands",
    "notes",
    "parking_lot",
    "projects",
    "tasks",
    "audit_trail",
    "event_triggers",
    "execution_logs",
    "resumes",
]

# Tables that already have site_id — only add company_id
TABLES_COMPANY_ONLY = [
    "integration_profiles",
    "remote_hosts",
    "credential_profiles",
]


def _add_company_id(table: str) -> None:
    op.add_column(table, sa.Column("company_id", sa.Integer(), nullable=True))
    op.create_index(f"ix_{table}_company_id", table, ["company_id"])


def _add_site_id(table: str) -> None:
    op.add_column(table, sa.Column("site_id", sa.Integer(), nullable=True))
    op.create_index(f"ix_{table}_site_id", table, ["site_id"])


def upgrade() -> None:
    for table in TABLES_COMPANY_ONLY:
        _add_company_id(table)

    for table in TABLES_BOTH:
        _add_company_id(table)
        _add_site_id(table)


def _drop_site_id(table: str) -> None:
    op.drop_index(f"ix_{table}_site_id", table)
    op.drop_column(table, "site_id")


def _drop_company_id(table: str) -> None:
    op.drop_index(f"ix_{table}_company_id", table)
    op.drop_column(table, "company_id")


def downgrade() -> None:
    for table in TABLES_BOTH:
        _drop_site_id(table)
        _drop_company_id(table)

    for table in TABLES_COMPANY_ONLY:
        _drop_company_id(table)
