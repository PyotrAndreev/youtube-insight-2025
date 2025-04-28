"""add column to video table

Revision ID: 0e36d165d1e9
Revises: a05554b93300
Create Date: 2025-04-23 20:47:42.638433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e36d165d1e9'
down_revision: Union[str, None] = 'a05554b93300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('videos', sa.Column('manual_category', sa.String(), comment='Название категории не ютубовской, а собственной'))


def downgrade() -> None:
    op.drop_column('videos', 'manual_category')
