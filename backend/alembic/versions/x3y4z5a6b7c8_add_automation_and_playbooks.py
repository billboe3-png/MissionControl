"""add automation and playbooks tables

Revision ID: x3y4z5a6b7c8
Revises: y2z3a4b5c6d7
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa

revision = "x3y4z5a6b7c8"
down_revision = "y2z3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "playbooks",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("auto_rollback", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default=sa.text("3600")),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_by", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "playbook_steps",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("playbook_id", sa.Integer(), sa.ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("step_type", sa.String(50), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False, server_default="ssh"),
        sa.Column("command", sa.Text(), nullable=False),
        sa.Column("target_host", sa.String(500), nullable=True),
        sa.Column("shell", sa.String(20), nullable=True),
        sa.Column("working_directory", sa.String(500), nullable=True),
        sa.Column("environment_variables", sa.Text(), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default=sa.text("300")),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("continue_on_failure", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rollback_command", sa.Text(), nullable=True),
        sa.Column("step_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "playbook_executions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("playbook_id", sa.Integer(), sa.ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("mode", sa.String(20), nullable=False, server_default="live"),
        sa.Column("trigger_type", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("triggered_by", sa.String(200), nullable=True),
        sa.Column("variables_used", sa.Text(), nullable=True),
        sa.Column("steps_total", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("steps_completed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("steps_failed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("steps_skipped", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("rollback_status", sa.String(30), nullable=True),
        sa.Column("rollback_output", sa.Text(), nullable=True),
        sa.Column("approval_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("approval_status", sa.String(30), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "playbook_variables",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("playbook_id", sa.Integer(), sa.ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("variable_type", sa.String(30), nullable=False, server_default="string"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sensitive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("default_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "approval_workflows",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("playbook_id", sa.Integer(), sa.ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("required_approvers", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("approver_roles", sa.Text(), nullable=True),
        sa.Column("auto_approve_on_timeout", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("timeout_minutes", sa.Integer(), nullable=False, server_default=sa.text("60")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "approval_requests",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("execution_id", sa.Integer(), sa.ForeignKey("playbook_executions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("approval_workflows.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("requested_by", sa.String(200), nullable=True),
        sa.Column("approved_by", sa.String(200), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=True),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "execution_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("execution_id", sa.Integer(), sa.ForeignKey("playbook_executions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("step_id", sa.Integer(), sa.ForeignKey("playbook_steps.id", ondelete="SET NULL"), nullable=True),
        sa.Column("level", sa.String(20), nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "audit_trail",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False, index=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(50), nullable=False, index=True),
        sa.Column("actor", sa.String(200), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True, index=True),
    )

    op.create_table(
        "playbook_schedules",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("playbook_id", sa.Integer(), sa.ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("cron_expression", sa.String(100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("variables_override", sa.Text(), nullable=True),
        sa.Column("last_run", sa.DateTime(), nullable=True),
        sa.Column("next_run", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "event_triggers",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("playbook_id", sa.Integer(), sa.ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False, index=True),
        sa.Column("conditions", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_triggered", sa.DateTime(), nullable=True),
        sa.Column("trigger_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("event_triggers")
    op.drop_table("playbook_schedules")
    op.drop_table("audit_trail")
    op.drop_table("execution_logs")
    op.drop_table("approval_requests")
    op.drop_table("approval_workflows")
    op.drop_table("playbook_variables")
    op.drop_table("playbook_executions")
    op.drop_table("playbook_steps")
    op.drop_table("playbooks")
