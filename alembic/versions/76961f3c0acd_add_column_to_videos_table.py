"""add column to videos table

Revision ID: 76961f3c0acd
Revises: c431df42ef03
Create Date: 2025-04-21 08:08:11.051238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76961f3c0acd'
down_revision: Union[str, None] = 'c431df42ef03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('videos', sa.Column('subscribers_count', sa.Integer(), comment='Количество подписчиков на канале'))
    op.add_column('videos', sa.Column('manual_category', sa.String(), comment='Категория, к которой относится видео. Самоопределенная, не ютубовская'))



def downgrade() -> None:
    op.drop_column('videos', 'subscribers_count')
    op.drop_column('videos', 'manual_category')
