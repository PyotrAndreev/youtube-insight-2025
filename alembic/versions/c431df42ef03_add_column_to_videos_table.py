"""add column to videos table

Revision ID: c431df42ef03
Revises: 5665eb79eb58
Create Date: 2025-04-06 20:43:59.714591

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c431df42ef03'
down_revision: Union[str, None] = '5665eb79eb58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
