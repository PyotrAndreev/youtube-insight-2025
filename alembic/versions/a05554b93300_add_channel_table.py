"""add channel table

Revision ID: a05554b93300
Revises: 5665eb79eb58
Create Date: 2025-04-22 17:18:42.209914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import Sequence, CreateSequence

# revision identifiers, used by Alembic.
revision: str = 'a05554b93300'
down_revision: Union[str, None] = '5665eb79eb58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(CreateSequence(Sequence('table_channels_id_seq')))
    op.create_table('channels',
                    sa.Column(
                        'id', sa.INTEGER(),
                        autoincrement=True,
                        nullable=False,
                        unique=True,
                        server_default=sa.text("nextval('table_channels_id_seq')")
                    ),

                    sa.Column('title', sa.String, nullable=False, comment='Название'),
                    sa.Column('youtube_id', sa.String, unique=True, comment='Youtube ID'),
                    sa.Column('view_count', sa.BigInteger,  comment='Количество просмотров'),
                    sa.Column('subscriber_count', sa.Integer, comment='Количество подписчиков'),
                    sa.Column('video_count', sa.Integer, comment='Youtube ID'),
                    )
    op.add_column('videos', sa.Column('channel_id', sa.Integer(), comment='ID канала'))

    op.create_foreign_key(
        'fk_videos_channels',
        'videos',
        'channels',
        ['channel_id'],
        ['id']
    )

def downgrade() -> None:
    op.drop_column('videos', 'channel_id')
    op.drop_table('channels')
