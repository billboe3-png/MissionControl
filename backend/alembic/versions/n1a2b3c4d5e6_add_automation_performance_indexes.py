"""add automation performance indexes

Revision ID: n1a2b3c4d5e6
Revises: m1a2b3c4d5e6
Create Date: 2026-07-16 13:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'n1a2b3c4d5e6'
down_revision: str | Sequence[str] | None = 'm1a2b3c4d5e6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index('ix_playbook_executions_status', 'playbook_executions', ['status'])
    op.create_index('ix_playbook_executions_playbook_id_status', 'playbook_executions', ['playbook_id', 'status'])
    op.create_index('ix_approval_requests_status', 'approval_requests', ['status'])
    op.create_index('ix_audit_trail_entity_type_action', 'audit_trail', ['entity_type', 'action'])
    op.create_index('ix_playbooks_category', 'playbooks', ['category'])
    op.create_index('ix_playbook_schedules_enabled_next_run', 'playbook_schedules', ['enabled', 'next_run'])
    op.create_index('ix_event_triggers_event_type_enabled', 'event_triggers', ['event_type', 'enabled'])


def downgrade() -> None:
    op.drop_index('ix_event_triggers_event_type_enabled', table_name='event_triggers')
    op.drop_index('ix_playbook_schedules_enabled_next_run', table_name='playbook_schedules')
    op.drop_index('ix_playbooks_category', table_name='playbooks')
    op.drop_index('ix_audit_trail_entity_type_action', table_name='audit_trail')
    op.drop_index('ix_approval_requests_status', table_name='approval_requests')
    op.drop_index('ix_playbook_executions_playbook_id_status', table_name='playbook_executions')
    op.drop_index('ix_playbook_executions_status', table_name='playbook_executions')
