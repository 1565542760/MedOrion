
"""stage125_case_imaging_inputs

Revision ID: b9c6a5d4e3f2
Revises: 4d9c8b2f1a6e
Create Date: 2026-06-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'b9c6a5d4e3f2'
down_revision = '4d9c8b2f1a6e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'case_imaging_inputs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('input_asset_id', sa.String(length=128), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trace_id', sa.String(length=96), nullable=False),
        sa.Column('modality', sa.String(length=32), nullable=False),
        sa.Column('source_type', sa.String(length=32), nullable=False),
        sa.Column('storage_uri', sa.String(length=1024), nullable=False),
        sa.Column('deidentified', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('not_for_diagnosis', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('provenance_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('quality_flags_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name='fk_case_imaging_inputs_case_id_cases'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], name='fk_case_imaging_inputs_patient_id_patients'),
        sa.PrimaryKeyConstraint('id', name='pk_case_imaging_inputs'),
        sa.UniqueConstraint('input_asset_id', name='uq_case_imaging_inputs_input_asset_id'),
    )
    op.create_index('ix_case_imaging_inputs_case_id', 'case_imaging_inputs', ['case_id'], unique=False)
    op.create_index('ix_case_imaging_inputs_patient_id', 'case_imaging_inputs', ['patient_id'], unique=False)
    op.create_index('ix_case_imaging_inputs_trace_id', 'case_imaging_inputs', ['trace_id'], unique=False)
    op.create_index('ix_case_imaging_inputs_modality', 'case_imaging_inputs', ['modality'], unique=False)
    op.create_index('ix_case_imaging_inputs_source_type', 'case_imaging_inputs', ['source_type'], unique=False)
    op.create_index('ix_case_imaging_inputs_created_at', 'case_imaging_inputs', ['created_at'], unique=False)
    op.create_index('ix_case_imaging_inputs_case_created_at', 'case_imaging_inputs', ['case_id', 'created_at'], unique=False)
    op.create_index('ix_case_imaging_inputs_trace_modality', 'case_imaging_inputs', ['trace_id', 'modality'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_case_imaging_inputs_trace_modality', table_name='case_imaging_inputs')
    op.drop_index('ix_case_imaging_inputs_case_created_at', table_name='case_imaging_inputs')
    op.drop_index('ix_case_imaging_inputs_created_at', table_name='case_imaging_inputs')
    op.drop_index('ix_case_imaging_inputs_source_type', table_name='case_imaging_inputs')
    op.drop_index('ix_case_imaging_inputs_modality', table_name='case_imaging_inputs')
    op.drop_index('ix_case_imaging_inputs_trace_id', table_name='case_imaging_inputs')
    op.drop_index('ix_case_imaging_inputs_patient_id', table_name='case_imaging_inputs')
    op.drop_index('ix_case_imaging_inputs_case_id', table_name='case_imaging_inputs')
    op.drop_table('case_imaging_inputs')
