"""stage106_case_ownership_schema

Revision ID: 8c2f3a1e9d47
Revises: 4f2d8e1c9a7b
Create Date: 2026-06-06

Case ownership schema candidate for Stage 105/106.
This revision is audit-only and intentionally keeps ownership data separate
from recommendation output and shadow audit output.

Downgrade note:
- best-effort drop of the new case ownership table and new case ownership columns
- no data backfill is attempted
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8c2f3a1e9d47'
down_revision: Union[str, None] = '4f2d8e1c9a7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cases', sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('cases', sa.Column('primary_doctor_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('cases', sa.Column('organization_id', sa.String(length=64), nullable=True))
    op.add_column('cases', sa.Column('access_policy_status', sa.String(length=32), nullable=True))
    op.add_column('cases', sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('cases', sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))

    op.create_foreign_key('fk_cases_owner_user_id_users', 'cases', 'users', ['owner_user_id'], ['id'])
    op.create_foreign_key('fk_cases_primary_doctor_id_users', 'cases', 'users', ['primary_doctor_id'], ['id'])
    op.create_foreign_key('fk_cases_created_by_users', 'cases', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_cases_updated_by_users', 'cases', 'users', ['updated_by'], ['id'])

    op.create_index('ix_cases_owner_user_id', 'cases', ['owner_user_id'])
    op.create_index('ix_cases_primary_doctor_id', 'cases', ['primary_doctor_id'])
    op.create_index('ix_cases_organization_id', 'cases', ['organization_id'])
    op.create_index('ix_cases_access_policy_status', 'cases', ['access_policy_status'])
    op.create_index('ix_cases_created_by', 'cases', ['created_by'])
    op.create_index('ix_cases_updated_by', 'cases', ['updated_by'])

    op.create_table(
        'case_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('assignment_id', sa.String(length=128), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_on_case', sa.String(length=64), nullable=False),
        sa.Column('assignment_status', sa.String(length=32), nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name='fk_case_assignments_case_id_cases'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_case_assignments_user_id_users'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], name='fk_case_assignments_assigned_by_users'),
        sa.ForeignKeyConstraint(['revoked_by'], ['users.id'], name='fk_case_assignments_revoked_by_users'),
        sa.UniqueConstraint('assignment_id', name='uq_case_assignments_assignment_id'),
    )
    op.create_index('ix_case_assignments_case_id', 'case_assignments', ['case_id'])
    op.create_index('ix_case_assignments_user_id', 'case_assignments', ['user_id'])
    op.create_index('ix_case_assignments_role_on_case', 'case_assignments', ['role_on_case'])
    op.create_index('ix_case_assignments_assignment_status', 'case_assignments', ['assignment_status'])
    op.create_index('ix_case_assignments_case_user_id', 'case_assignments', ['case_id', 'user_id'])
    op.create_index('ix_case_assignments_case_role_on_case', 'case_assignments', ['case_id', 'role_on_case'])


def downgrade() -> None:
    op.drop_index('ix_case_assignments_case_role_on_case', table_name='case_assignments')
    op.drop_index('ix_case_assignments_case_user_id', table_name='case_assignments')
    op.drop_index('ix_case_assignments_assignment_status', table_name='case_assignments')
    op.drop_index('ix_case_assignments_role_on_case', table_name='case_assignments')
    op.drop_index('ix_case_assignments_user_id', table_name='case_assignments')
    op.drop_index('ix_case_assignments_case_id', table_name='case_assignments')
    op.drop_table('case_assignments')

    op.drop_index('ix_cases_updated_by', table_name='cases')
    op.drop_index('ix_cases_created_by', table_name='cases')
    op.drop_index('ix_cases_access_policy_status', table_name='cases')
    op.drop_index('ix_cases_organization_id', table_name='cases')
    op.drop_index('ix_cases_primary_doctor_id', table_name='cases')
    op.drop_index('ix_cases_owner_user_id', table_name='cases')

    op.drop_constraint('fk_cases_updated_by_users', 'cases', type_='foreignkey')
    op.drop_constraint('fk_cases_created_by_users', 'cases', type_='foreignkey')
    op.drop_constraint('fk_cases_primary_doctor_id_users', 'cases', type_='foreignkey')
    op.drop_constraint('fk_cases_owner_user_id_users', 'cases', type_='foreignkey')

    op.drop_column('cases', 'updated_by')
    op.drop_column('cases', 'created_by')
    op.drop_column('cases', 'access_policy_status')
    op.drop_column('cases', 'organization_id')
    op.drop_column('cases', 'primary_doctor_id')
    op.drop_column('cases', 'owner_user_id')
