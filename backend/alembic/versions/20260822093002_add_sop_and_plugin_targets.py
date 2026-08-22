"""add_sop_and_plugin_targets

Revision ID: 20260822093002
Revises: 20260814094746
Create Date: 2026-08-22 09:30:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260822093002'
down_revision: Union[str, None] = '20260814094746'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sop_categories',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('sop_categories.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_table(
        'sops',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('site_id', sa.Integer(), sa.ForeignKey('sites.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('title', sa.String(500), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('sop_categories.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('approved_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='draft', index=True),
        sa.Column('current_version', sa.String(50), nullable=True),
        sa.Column('review_date', sa.DateTime(), nullable=True, index=True),
        sa.Column('approval_date', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('audience', sa.Text(), nullable=True),
        sa.Column('responsibilities', sa.Text(), nullable=True),
        sa.Column('prerequisites', sa.Text(), nullable=True),
        sa.Column('required_permissions', sa.Text(), nullable=True),
        sa.Column('required_tools', sa.Text(), nullable=True),
        sa.Column('procedure', sa.Text(), nullable=True),
        sa.Column('decision_points', sa.Text(), nullable=True),
        sa.Column('validation', sa.Text(), nullable=True),
        sa.Column('troubleshooting', sa.Text(), nullable=True),
        sa.Column('escalation', sa.Text(), nullable=True),
        sa.Column('rollback', sa.Text(), nullable=True),
        sa.Column('safety_requirements', sa.Text(), nullable=True),
        sa.Column('references', sa.Text(), nullable=True),
        sa.Column('related_sops', sa.Text(), nullable=True),
    )
    op.create_table(
        'sop_versions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('sop_id', sa.Integer(), sa.ForeignKey('sops.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='draft', index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content_type', sa.String(30), nullable=False, server_default='user_provided', index=True),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('audience', sa.Text(), nullable=True),
        sa.Column('responsibilities', sa.Text(), nullable=True),
        sa.Column('prerequisites', sa.Text(), nullable=True),
        sa.Column('required_permissions', sa.Text(), nullable=True),
        sa.Column('required_tools', sa.Text(), nullable=True),
        sa.Column('procedure', sa.Text(), nullable=True),
        sa.Column('decision_points', sa.Text(), nullable=True),
        sa.Column('validation', sa.Text(), nullable=True),
        sa.Column('troubleshooting', sa.Text(), nullable=True),
        sa.Column('escalation', sa.Text(), nullable=True),
        sa.Column('rollback', sa.Text(), nullable=True),
        sa.Column('safety_requirements', sa.Text(), nullable=True),
        sa.Column('references', sa.Text(), nullable=True),
        sa.Column('related_sops', sa.Text(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), index=True),
        sa.Column('approved_by', sa.String(200), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'sop_sources',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('sop_id', sa.Integer(), sa.ForeignKey('sops.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('source_name', sa.String(500), nullable=False),
        sa.Column('source_type', sa.String(20), nullable=False, index=True),
        sa.Column('source_hash', sa.String(128), nullable=True, index=True),
        sa.Column('source_size_bytes', sa.Integer(), nullable=True),
        sa.Column('source_author', sa.String(300), nullable=True),
        sa.Column('source_version', sa.String(100), nullable=True),
        sa.Column('source_pages', sa.String(200), nullable=True),
        sa.Column('source_sections', sa.Text(), nullable=True),
        sa.Column('imported_by', sa.String(200), nullable=True),
        sa.Column('imported_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('processing_error', sa.Text(), nullable=True),
    )
    op.create_table(
        'sop_approvals',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('sop_id', sa.Integer(), sa.ForeignKey('sops.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('sop_version_id', sa.Integer(), sa.ForeignKey('sop_versions.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('approver_name', sa.String(200), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('acted_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_table(
        'sop_audit_events',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('sop_id', sa.Integer(), sa.ForeignKey('sops.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('sop_version_id', sa.Integer(), sa.ForeignKey('sop_versions.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('company_id', sa.Integer(), nullable=True, index=True),
        sa.Column('site_id', sa.Integer(), nullable=True, index=True),
        sa.Column('action', sa.String(50), nullable=False, index=True),
        sa.Column('actor', sa.String(200), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('source', sa.String(200), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), index=True),
    )
    op.add_column('agents', sa.Column('enabled_plugins', sa.Text(), nullable=True))
    op.add_column('agent_remote_targets', sa.Column('target_plugins', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('agents', 'enabled_plugins')
    op.drop_column('agent_remote_targets', 'target_plugins')
    op.drop_table('sop_audit_events')
    op.drop_table('sop_approvals')
    op.drop_table('sop_sources')
    op.drop_table('sop_versions')
    op.drop_table('sop_categories')
    op.drop_table('sops')
