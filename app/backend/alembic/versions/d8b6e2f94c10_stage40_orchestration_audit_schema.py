"""stage40_orchestration_audit_schema

Revision ID: d8b6e2f94c10
Revises: 4c7f2e3a9d10
Create Date: 2026-06-02

This migration adds the orchestration audit schema from the Stage 39 contract.
It is intentionally audit-only and does not touch case trace/evidence tables.

Downgrade note:
- downgrade is best-effort and only drops the new orchestration audit tables
- no data backfill is attempted
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd8b6e2f94c10'
down_revision: Union[str, None] = '4c7f2e3a9d10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ORCHESTRATION_RUNTIME_STATES = (
    'planned',
    'running',
    'completed',
    'failed',
    'cancelled',
    'timeout',
)


def upgrade() -> None:
    op.create_table(
        'orchestration_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('orchestration_run_id', sa.String(length=96), nullable=False),
        sa.Column('trace_id', sa.String(length=96), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mode', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('requested_task', sa.String(length=128), nullable=False),
        sa.Column('candidate_agents_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('clinical_context_refs_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('modality_refs_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('runtime_options_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('idempotency_key', sa.String(length=160), nullable=True),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('result_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('runtime_stub', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('error_detail_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name='fk_orchestration_runs_case_id_cases'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], name='fk_orchestration_runs_patient_id_patients'),
        sa.UniqueConstraint('orchestration_run_id', name='uq_orchestration_runs_orchestration_run_id'),
    )
    op.create_index('ix_orchestration_runs_trace_id', 'orchestration_runs', ['trace_id'])
    op.create_index('ix_orchestration_runs_case_id', 'orchestration_runs', ['case_id'])
    op.create_index('ix_orchestration_runs_patient_id', 'orchestration_runs', ['patient_id'])
    op.create_index('ix_orchestration_runs_status_started_at', 'orchestration_runs', ['status', 'started_at'])
    op.create_index('ix_orchestration_runs_started_at', 'orchestration_runs', ['started_at'])

    op.create_table(
        'orchestration_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('step_id', sa.String(length=96), nullable=False),
        sa.Column('trace_id', sa.String(length=96), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('orchestration_run_id', sa.String(length=96), nullable=False),
        sa.Column('parent_step_id', sa.String(length=96), nullable=True),
        sa.Column('step_type', sa.String(length=64), nullable=False),
        sa.Column('step_name', sa.String(length=128), nullable=True),
        sa.Column('step_index', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('agent_code', sa.String(length=64), nullable=True),
        sa.Column('agent_version', sa.String(length=128), nullable=True),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('result_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('runtime_stub', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('error_detail_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name='fk_orchestration_steps_case_id_cases'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], name='fk_orchestration_steps_patient_id_patients'),
        sa.ForeignKeyConstraint(['orchestration_run_id'], ['orchestration_runs.orchestration_run_id'], name='fk_orchestration_steps_orchestration_run_id_orchestration_runs'),
        sa.ForeignKeyConstraint(['parent_step_id'], ['orchestration_steps.step_id'], name='fk_orchestration_steps_parent_step_id_orchestration_steps'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], name='fk_orchestration_steps_model_version_id_model_versions'),
        sa.UniqueConstraint('step_id', name='uq_orchestration_steps_step_id'),
    )
    op.create_index('ix_orchestration_steps_trace_id', 'orchestration_steps', ['trace_id'])
    op.create_index('ix_orchestration_steps_case_id', 'orchestration_steps', ['case_id'])
    op.create_index('ix_orchestration_steps_orchestration_run_id', 'orchestration_steps', ['orchestration_run_id'])
    op.create_index('ix_orchestration_steps_run_step_index', 'orchestration_steps', ['orchestration_run_id', 'step_index'])
    op.create_index('ix_orchestration_steps_agent_code', 'orchestration_steps', ['agent_code'])
    op.create_index('ix_orchestration_steps_model_version_id', 'orchestration_steps', ['model_version_id'])
    op.create_index('ix_orchestration_steps_status_started_at', 'orchestration_steps', ['status', 'started_at'])
    op.create_index('ix_orchestration_steps_started_at', 'orchestration_steps', ['started_at'])

    op.create_table(
        'agent_invocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('agent_invocation_id', sa.String(length=96), nullable=False),
        sa.Column('trace_id', sa.String(length=96), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('orchestration_run_id', sa.String(length=96), nullable=False),
        sa.Column('step_id', sa.String(length=96), nullable=False),
        sa.Column('agent_code', sa.String(length=64), nullable=False),
        sa.Column('agent_version', sa.String(length=128), nullable=True),
        sa.Column('endpoint_id', sa.String(length=96), nullable=True),
        sa.Column('endpoint_url', sa.String(length=512), nullable=True),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('response_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('runtime_stub', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('error_detail_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name='fk_agent_invocations_case_id_cases'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], name='fk_agent_invocations_patient_id_patients'),
        sa.ForeignKeyConstraint(['orchestration_run_id'], ['orchestration_runs.orchestration_run_id'], name='fk_agent_invocations_orchestration_run_id_orchestration_runs'),
        sa.ForeignKeyConstraint(['step_id'], ['orchestration_steps.step_id'], name='fk_agent_invocations_step_id_orchestration_steps'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], name='fk_agent_invocations_model_version_id_model_versions'),
        sa.UniqueConstraint('agent_invocation_id', name='uq_agent_invocations_agent_invocation_id'),
    )
    op.create_index('ix_agent_invocations_trace_id', 'agent_invocations', ['trace_id'])
    op.create_index('ix_agent_invocations_case_id', 'agent_invocations', ['case_id'])
    op.create_index('ix_agent_invocations_orchestration_run_id', 'agent_invocations', ['orchestration_run_id'])
    op.create_index('ix_agent_invocations_step_id', 'agent_invocations', ['step_id'])
    op.create_index('ix_agent_invocations_agent_code', 'agent_invocations', ['agent_code'])
    op.create_index('ix_agent_invocations_model_version_id', 'agent_invocations', ['model_version_id'])
    op.create_index('ix_agent_invocations_status_started_at', 'agent_invocations', ['status', 'started_at'])
    op.create_index('ix_agent_invocations_started_at', 'agent_invocations', ['started_at'])

    op.create_table(
        'orchestration_conflicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('conflict_id', sa.String(length=96), nullable=False),
        sa.Column('trace_id', sa.String(length=96), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('orchestration_run_id', sa.String(length=96), nullable=False),
        sa.Column('step_id', sa.String(length=96), nullable=True),
        sa.Column('conflict_type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=True),
        sa.Column('resolution_strategy', sa.String(length=64), nullable=True),
        sa.Column('resolution_summary', sa.Text(), nullable=True),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('result_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('runtime_stub', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('error_detail_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name='fk_orchestration_conflicts_case_id_cases'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], name='fk_orchestration_conflicts_patient_id_patients'),
        sa.ForeignKeyConstraint(['orchestration_run_id'], ['orchestration_runs.orchestration_run_id'], name='fk_orch_conflicts_run'),
        sa.ForeignKeyConstraint(['step_id'], ['orchestration_steps.step_id'], name='fk_orchestration_conflicts_step_id_orchestration_steps'),
        sa.UniqueConstraint('conflict_id', name='uq_orchestration_conflicts_conflict_id'),
    )
    op.create_index('ix_orchestration_conflicts_trace_id', 'orchestration_conflicts', ['trace_id'])
    op.create_index('ix_orchestration_conflicts_case_id', 'orchestration_conflicts', ['case_id'])
    op.create_index('ix_orchestration_conflicts_orchestration_run_id', 'orchestration_conflicts', ['orchestration_run_id'])
    op.create_index('ix_orchestration_conflicts_status_started_at', 'orchestration_conflicts', ['status', 'started_at'])
    op.create_index('ix_orchestration_conflicts_started_at', 'orchestration_conflicts', ['started_at'])

    op.create_table(
        'llm_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('summary_id', sa.String(length=96), nullable=False),
        sa.Column('trace_id', sa.String(length=96), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('orchestration_run_id', sa.String(length=96), nullable=False),
        sa.Column('step_id', sa.String(length=96), nullable=True),
        sa.Column('agent_invocation_id', sa.String(length=96), nullable=True),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('summary_type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=True),
        sa.Column('summary_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('runtime_stub', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('error_detail_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name='fk_llm_summaries_case_id_cases'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], name='fk_llm_summaries_patient_id_patients'),
        sa.ForeignKeyConstraint(['orchestration_run_id'], ['orchestration_runs.orchestration_run_id'], name='fk_llm_summaries_orchestration_run_id_orchestration_runs'),
        sa.ForeignKeyConstraint(['step_id'], ['orchestration_steps.step_id'], name='fk_llm_summaries_step_id_orchestration_steps'),
        sa.ForeignKeyConstraint(['agent_invocation_id'], ['agent_invocations.agent_invocation_id'], name='fk_llm_summaries_agent_invocation_id_agent_invocations'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], name='fk_llm_summaries_model_version_id_model_versions'),
        sa.UniqueConstraint('summary_id', name='uq_llm_summaries_summary_id'),
    )
    op.create_index('ix_llm_summaries_trace_id', 'llm_summaries', ['trace_id'])
    op.create_index('ix_llm_summaries_case_id', 'llm_summaries', ['case_id'])
    op.create_index('ix_llm_summaries_orchestration_run_id', 'llm_summaries', ['orchestration_run_id'])
    op.create_index('ix_llm_summaries_model_version_id', 'llm_summaries', ['model_version_id'])
    op.create_index('ix_llm_summaries_status_started_at', 'llm_summaries', ['status', 'started_at'])
    op.create_index('ix_llm_summaries_started_at', 'llm_summaries', ['started_at'])

    # llm_summaries uses the structured summary shape:
    # summary_text + summary_json + step_id + agent_invocation_id + model_version_id.


def downgrade() -> None:
    op.drop_index('ix_llm_summaries_started_at', table_name='llm_summaries')
    op.drop_index('ix_llm_summaries_status_started_at', table_name='llm_summaries')
    op.drop_index('ix_llm_summaries_model_version_id', table_name='llm_summaries')
    op.drop_index('ix_llm_summaries_orchestration_run_id', table_name='llm_summaries')
    op.drop_index('ix_llm_summaries_case_id', table_name='llm_summaries')
    op.drop_index('ix_llm_summaries_trace_id', table_name='llm_summaries')
    op.drop_table('llm_summaries')

    op.drop_index('ix_orchestration_conflicts_started_at', table_name='orchestration_conflicts')
    op.drop_index('ix_orchestration_conflicts_status_started_at', table_name='orchestration_conflicts')
    op.drop_index('ix_orchestration_conflicts_orchestration_run_id', table_name='orchestration_conflicts')
    op.drop_index('ix_orchestration_conflicts_case_id', table_name='orchestration_conflicts')
    op.drop_index('ix_orchestration_conflicts_trace_id', table_name='orchestration_conflicts')
    op.drop_table('orchestration_conflicts')

    op.drop_index('ix_agent_invocations_started_at', table_name='agent_invocations')
    op.drop_index('ix_agent_invocations_status_started_at', table_name='agent_invocations')
    op.drop_index('ix_agent_invocations_model_version_id', table_name='agent_invocations')
    op.drop_index('ix_agent_invocations_agent_code', table_name='agent_invocations')
    op.drop_index('ix_agent_invocations_step_id', table_name='agent_invocations')
    op.drop_index('ix_agent_invocations_orchestration_run_id', table_name='agent_invocations')
    op.drop_index('ix_agent_invocations_case_id', table_name='agent_invocations')
    op.drop_index('ix_agent_invocations_trace_id', table_name='agent_invocations')
    op.drop_table('agent_invocations')

    op.drop_index('ix_orchestration_steps_started_at', table_name='orchestration_steps')
    op.drop_index('ix_orchestration_steps_status_started_at', table_name='orchestration_steps')
    op.drop_index('ix_orchestration_steps_model_version_id', table_name='orchestration_steps')
    op.drop_index('ix_orchestration_steps_agent_code', table_name='orchestration_steps')
    op.drop_index('ix_orchestration_steps_run_step_index', table_name='orchestration_steps')
    op.drop_index('ix_orchestration_steps_orchestration_run_id', table_name='orchestration_steps')
    op.drop_index('ix_orchestration_steps_case_id', table_name='orchestration_steps')
    op.drop_index('ix_orchestration_steps_trace_id', table_name='orchestration_steps')
    op.drop_table('orchestration_steps')

    op.drop_index('ix_orchestration_runs_started_at', table_name='orchestration_runs')
    op.drop_index('ix_orchestration_runs_status_started_at', table_name='orchestration_runs')
    op.drop_index('ix_orchestration_runs_patient_id', table_name='orchestration_runs')
    op.drop_index('ix_orchestration_runs_case_id', table_name='orchestration_runs')
    op.drop_index('ix_orchestration_runs_trace_id', table_name='orchestration_runs')
    op.drop_table('orchestration_runs')
