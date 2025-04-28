"""add columns to videos table

Revision ID: 5665eb79eb58
Revises: 8391037b04de
Create Date: 2025-04-04 21:25:28.505682

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5665eb79eb58'
down_revision: Union[str, None] = '8391037b04de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('videos', sa.Column('comment_count', sa.Integer(), comment='Количество комментариев'))
    op.add_column('videos', sa.Column('category_id', sa.Integer(), comment='Id категории'))
    op.add_column('videos', sa.Column('tags', sa.JSON, comment='Теги'))


def downgrade() -> None:
    op.drop_column('videos', 'comment_count')
    op.drop_column('videos', 'category_id')
    op.drop_column('videos', 'tags')
