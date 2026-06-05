"""stage100_case_model_input_snapshots

Revision ID: 4f2d8e1c9a7b
Revises: 7a3b2d1f4c60
Create Date: 2026-06-05

Case model input snapshot storage candidate for Stage 99/100.
This revision is audit-only and intentionally keeps input provenance separate
from recommendation output and shadow audit output.

Downgrade note:
- best-effort drop of the new snapshot table only
- no data backfill is attempted
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4f2d8e1c9a7b'
down_revision: Union[str, None] = '7a3b2d1f4c60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'case_model_input_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('input_snapshot_id', sa.String(length=128), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trace_id', sa.String(length=96), nullable=False),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_input_schema_id', sa.String(length=128), nullable=False),
        sa.Column('disease_task_feature_set_id', sa.String(length=128), nullable=False),
        sa.Column('preprocess_artifact_ref', sa.String(length=512), nullable=True),
        sa.Column('mapped_features_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('missing_features_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('defaulted_features_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('doctor_provided_features_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('source_refs_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('validation_status', sa.String(length=64), nullable=False),
        sa.Column('current_assessment_status', sa.String(length=64), nullable=False),
        sa.Column('insufficient_data_for_assessment', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('runtime_stub', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('not_for_diagnosis', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint('input_snapshot_id', name='uq_case_model_input_snapshots_input_snapshot_id'),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name='fk_case_model_input_snapshots_case'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], name='fk_case_model_input_snapshots_patient'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], name='fk_case_model_input_snapshots_modelver'),
    )
    op.create_index('ix_case_model_input_snapshots_case_id', 'case_model_input_snapshots', ['case_id'])
    op.create_index('ix_case_model_input_snapshots_patient_id', 'case_model_input_snapshots', ['patient_id'])
    op.create_index('ix_case_model_input_snapshots_trace_id', 'case_model_input_snapshots', ['trace_id'])
    op.create_index('ix_case_model_input_snapshots_model_version_id', 'case_model_input_snapshots', ['model_version_id'])
    op.create_index('ix_case_model_input_snapshots_case_created_at', 'case_model_input_snapshots', ['case_id', 'created_at'])
    op.create_index('ix_case_model_input_snapshots_trace_model_version', 'case_model_input_snapshots', ['trace_id', 'model_version_id'])


def downgrade() -> None:
    op.drop_index('ix_case_model_input_snapshots_trace_model_version', table_name='case_model_input_snapshots')
    op.drop_index('ix_case_model_input_snapshots_case_created_at', table_name='case_model_input_snapshots')
    op.drop_index('ix_case_model_input_snapshots_model_version_id', table_name='case_model_input_snapshots')
    op.drop_index('ix_case_model_input_snapshots_trace_id', table_name='case_model_input_snapshots')
    op.drop_index('ix_case_model_input_snapshots_patient_id', table_name='case_model_input_snapshots')
    op.drop_index('ix_case_model_input_snapshots_case_id', table_name='case_model_input_snapshots')
    op.drop_table('case_model_input_snapshots')
