"""stage33b_model_lifecycle_enum_expansion

Revision ID: 4c7f2e3a9d10
Revises: 073789431b21
Create Date: 2026-06-02

This migration expands the model lifecycle enum to the Stage 32 frozen set
and adds the minimum audit fields plus a partial unique index for default
version selection.

Downgrade note:
- downgrade is best-effort only
- new states such as shadow/canary/default/offline_evaluated collapse to
  approved on downgrade
- archived collapses to revoked on downgrade
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4c7f2e3a9d10'
down_revision: Union[str, None] = '073789431b21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_MODEL_APPROVAL_STATE_VALUES = (
    'draft',
    'offline_evaluated',
    'approved',
    'shadow',
    'canary',
    'default',
    'deprecated',
    'archived',
)

OLD_MODEL_APPROVAL_STATE_VALUES = (
    'draft',
    'approved',
    'deprecated',
    'revoked',
)


def upgrade() -> None:
    # Audit / lineage fields for lifecycle operations.
    op.add_column('model_versions', sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('model_versions', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('model_versions', sa.Column('promoted_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('model_versions', sa.Column('promoted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('model_versions', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('model_versions', sa.Column('rollback_from_version_id', postgresql.UUID(as_uuid=True), nullable=True))

    op.create_foreign_key(
        'fk_model_versions_approved_by_users',
        'model_versions',
        'users',
        ['approved_by'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_model_versions_promoted_by_users',
        'model_versions',
        'users',
        ['promoted_by'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_model_versions_rollback_from_version_id_model_versions',
        'model_versions',
        'model_versions',
        ['rollback_from_version_id'],
        ['id'],
    )

    # Rebuild the enum so the live type matches the frozen Stage 32 lifecycle.
    # Existing revoked rows are mapped to archived during the cast; current
    # production data has zero revoked rows, but the mapping is kept defensive.
    op.execute('ALTER TYPE modelapprovalstate RENAME TO modelapprovalstate_v33b_old')
    op.execute(
        """
        CREATE TYPE modelapprovalstate AS ENUM (
            'draft',
            'offline_evaluated',
            'approved',
            'shadow',
            'canary',
            'default',
            'deprecated',
            'archived'
        )
        """
    )
    op.execute(
        """
        ALTER TABLE model_versions
        ALTER COLUMN approval_state TYPE modelapprovalstate
        USING (
            CASE
                WHEN approval_state::text = 'revoked' THEN 'archived'
                ELSE approval_state::text
            END
        )::modelapprovalstate
        """
    )
    op.execute('DROP TYPE modelapprovalstate_v33b_old')

    # Default version rule: one default per model_id.
    op.create_index(
        'uq_model_versions_one_default_per_model',
        'model_versions',
        ['model_id'],
        unique=True,
        postgresql_where=sa.text("approval_state = 'default'::modelapprovalstate"),
    )


def downgrade() -> None:
    # Remove the default-version guard first so downgrade casts do not conflict.
    op.drop_index('uq_model_versions_one_default_per_model', table_name='model_versions')

    # Best-effort lossless downgrade is not possible for the full Stage 32
    # lifecycle. We collapse operational states back to approved.
    op.execute('ALTER TYPE modelapprovalstate RENAME TO modelapprovalstate_v33b_new')
    op.execute(
        """
        CREATE TYPE modelapprovalstate AS ENUM (
            'draft',
            'approved',
            'deprecated',
            'revoked'
        )
        """
    )
    op.execute(
        """
        ALTER TABLE model_versions
        ALTER COLUMN approval_state TYPE modelapprovalstate
        USING (
            CASE
                WHEN approval_state::text = 'archived' THEN 'revoked'
                WHEN approval_state::text = 'deprecated' THEN 'deprecated'
                WHEN approval_state::text = 'draft' THEN 'draft'
                ELSE 'approved'
            END
        )::modelapprovalstate
        """
    )
    op.execute('DROP TYPE modelapprovalstate_v33b_new')

    op.drop_constraint('fk_model_versions_rollback_from_version_id_model_versions', 'model_versions', type_='foreignkey')
    op.drop_constraint('fk_model_versions_promoted_by_users', 'model_versions', type_='foreignkey')
    op.drop_constraint('fk_model_versions_approved_by_users', 'model_versions', type_='foreignkey')

    op.drop_column('model_versions', 'rollback_from_version_id')
    op.drop_column('model_versions', 'archived_at')
    op.drop_column('model_versions', 'promoted_at')
    op.drop_column('model_versions', 'promoted_by')
    op.drop_column('model_versions', 'approved_at')
    op.drop_column('model_versions', 'approved_by')
