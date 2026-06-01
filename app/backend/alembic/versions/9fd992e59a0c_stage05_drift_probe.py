"""stage05_drift_probe

Revision ID: 9fd992e59a0c
Revises: a9d28e4978dd
Create Date: 2026-06-01 00:29:37.394808

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9fd992e59a0c'
down_revision: Union[str, None] = 'a9d28e4978dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
