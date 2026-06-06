"""stage110_access_audit_events

Revision ID: 4d9c8b2f1a6e
Revises: 220911ea3522
Create Date: 2026-06-06 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4d9c8b2f1a6e'
down_revision = '8c2f3a1e9d47'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'access_audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('access_event_id', sa.String(length=128), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_type', sa.String(length=64), nullable=True),
        sa.Column('actor_role', sa.String(length=32), nullable=True),
        sa.Column('access_mode', sa.String(length=32), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=True),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('trace_id', sa.String(length=96), nullable=True),
        sa.Column('decision', sa.String(length=16), nullable=False),
        sa.Column('denial_reason', sa.String(length=64), nullable=True),
        sa.Column('policy_source', sa.String(length=64), nullable=True),
        sa.Column('request_id', sa.String(length=128), nullable=True),
        sa.Column('route_path', sa.String(length=256), nullable=True),
        sa.Column('method', sa.String(length=16), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name='fk_access_audit_events_actor_user_id_users', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name='fk_access_audit_events_case_id_cases', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], name='fk_access_audit_events_patient_id_patients', ondelete='SET NULL'),
        sa.UniqueConstraint('access_event_id', name='uq_access_audit_events_access_event_id'),
    )
    op.create_index('ix_access_audit_events_actor_user_id', 'access_audit_events', ['actor_user_id'])
    op.create_index('ix_access_audit_events_case_id', 'access_audit_events', ['case_id'])
    op.create_index('ix_access_audit_events_patient_id', 'access_audit_events', ['patient_id'])
    op.create_index('ix_access_audit_events_trace_id', 'access_audit_events', ['trace_id'])
    op.create_index('ix_access_audit_events_resource_type', 'access_audit_events', ['resource_type'])
    op.create_index('ix_access_audit_events_resource_id', 'access_audit_events', ['resource_id'])
    op.create_index('ix_access_audit_events_decision', 'access_audit_events', ['decision'])
    op.create_index('ix_access_audit_events_access_mode', 'access_audit_events', ['access_mode'])
    op.create_index('ix_access_audit_events_created_at', 'access_audit_events', ['created_at'])
    op.create_index('ix_access_audit_events_case_created_at', 'access_audit_events', ['case_id', 'created_at'])
    op.create_index('ix_access_audit_events_actor_created_at', 'access_audit_events', ['actor_user_id', 'created_at'])
    op.create_index('ix_access_audit_events_resource_type_resource_id', 'access_audit_events', ['resource_type', 'resource_id'])
    op.create_index('ix_access_audit_events_decision_created_at', 'access_audit_events', ['decision', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_access_audit_events_decision_created_at', table_name='access_audit_events')
    op.drop_index('ix_access_audit_events_resource_type_resource_id', table_name='access_audit_events')
    op.drop_index('ix_access_audit_events_actor_created_at', table_name='access_audit_events')
    op.drop_index('ix_access_audit_events_case_created_at', table_name='access_audit_events')
    op.drop_index('ix_access_audit_events_created_at', table_name='access_audit_events')
    op.drop_index('ix_access_audit_events_access_mode', table_name='access_audit_events')
    op.drop_index('ix_access_audit_events_decision', table_name='access_audit_events')
    op.drop_index('ix_access_audit_events_resource_id', table_name='access_audit_events')
    op.drop_index('ix_access_audit_events_resource_type', table_name='access_audit_events')
    op.drop_index('ix_access_audit_events_trace_id', table_name='access_audit_events')
    op.drop_index('ix_access_audit_events_patient_id', table_name='access_audit_events')
    op.drop_index('ix_access_audit_events_case_id', table_name='access_audit_events')
    op.drop_index('ix_access_audit_events_actor_user_id', table_name='access_audit_events')
    op.drop_table('access_audit_events')
