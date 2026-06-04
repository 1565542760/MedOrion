"""stage65_shadow_audit_schema

Revision ID: 7a3b2d1f4c60
Revises: d8b6e2f94c10
Create Date: 2026-06-04

Shadow audit storage candidate for Stage 64/65.
This revision is audit-only and intentionally keeps shadow results outside
case trace/evidence by default.

Downgrade note:
- best-effort drop of the new shadow audit tables only
- no data backfill is attempted
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7a3b2d1f4c60'
down_revision: Union[str, None] = 'd8b6e2f94c10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'shadow_inference_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('shadow_run_id', sa.String(length=96), nullable=False),
        sa.Column('trace_id', sa.String(length=96), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('artifact_hash', sa.String(length=128), nullable=False),
        sa.Column('adapter_code', sa.String(length=64), nullable=False),
        sa.Column('model_input_schema_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('input_snapshot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('runtime_env_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('runtime_stub', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('not_for_diagnosis', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.BigInteger(), nullable=True),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('error_detail_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.UniqueConstraint('shadow_run_id', name='uq_shadow_runs_shadow_run_id'),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name='fk_shadow_runs_case'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], name='fk_shadow_runs_patient'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], name='fk_shadow_runs_modelver'),
    )
    op.create_index('ix_shadow_runs_trace', 'shadow_inference_runs', ['trace_id'])
    op.create_index('ix_shadow_runs_case', 'shadow_inference_runs', ['case_id'])
    op.create_index('ix_shadow_runs_patient', 'shadow_inference_runs', ['patient_id'])
    op.create_index('ix_shadow_runs_modelver', 'shadow_inference_runs', ['model_version_id'])
    op.create_index('ix_shadow_runs_status', 'shadow_inference_runs', ['status'])
    op.create_index('ix_shadow_runs_started', 'shadow_inference_runs', ['started_at'])
    op.create_index('ix_shadow_runs_case_start', 'shadow_inference_runs', ['case_id', 'started_at'])
    op.create_index('ix_shadow_runs_trace_modelver', 'shadow_inference_runs', ['trace_id', 'model_version_id'])

    op.create_table(
        'shadow_inference_outputs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('output_id', sa.String(length=96), nullable=False),
        sa.Column('shadow_run_id', sa.String(length=96), nullable=False),
        sa.Column('trace_id', sa.String(length=96), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prediction_raw_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('prediction_probability_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('candidate_label', sa.String(length=128), nullable=True),
        sa.Column('confidence_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('uncertainty_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('limitations_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('input_quality_flags_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.UniqueConstraint('output_id', name='uq_shadow_outs_output_id'),
        sa.ForeignKeyConstraint(['shadow_run_id'], ['shadow_inference_runs.shadow_run_id'], name='fk_shadow_outs_shadow_run'),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name='fk_shadow_outs_case'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], name='fk_shadow_outs_modelver'),
    )
    op.create_index('ix_shadow_outs_trace', 'shadow_inference_outputs', ['trace_id'])
    op.create_index('ix_shadow_outs_case', 'shadow_inference_outputs', ['case_id'])
    op.create_index('ix_shadow_outs_modelver', 'shadow_inference_outputs', ['model_version_id'])
    op.create_index('ix_shadow_outs_shadow_run', 'shadow_inference_outputs', ['shadow_run_id'])


def downgrade() -> None:
    op.drop_index('ix_shadow_outs_shadow_run', table_name='shadow_inference_outputs')
    op.drop_index('ix_shadow_outs_modelver', table_name='shadow_inference_outputs')
    op.drop_index('ix_shadow_outs_case', table_name='shadow_inference_outputs')
    op.drop_index('ix_shadow_outs_trace', table_name='shadow_inference_outputs')
    op.drop_table('shadow_inference_outputs')

    op.drop_index('ix_shadow_runs_trace_modelver', table_name='shadow_inference_runs')
    op.drop_index('ix_shadow_runs_case_start', table_name='shadow_inference_runs')
    op.drop_index('ix_shadow_runs_started', table_name='shadow_inference_runs')
    op.drop_index('ix_shadow_runs_status', table_name='shadow_inference_runs')
    op.drop_index('ix_shadow_runs_modelver', table_name='shadow_inference_runs')
    op.drop_index('ix_shadow_runs_patient', table_name='shadow_inference_runs')
    op.drop_index('ix_shadow_runs_case', table_name='shadow_inference_runs')
    op.drop_index('ix_shadow_runs_trace', table_name='shadow_inference_runs')
    op.drop_table('shadow_inference_runs')
