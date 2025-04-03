"""init migration

Revision ID: 8391037b04de
Revises: 
Create Date: 2025-03-30 12:37:22.521491

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.schema import Sequence, CreateSequence

# revision identifiers, used by Alembic.
revision: str = '8391037b04de'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(CreateSequence(Sequence('table_videos_id_seq')))
    op.create_table('videos',
                    sa.Column(
                        'id', sa.INTEGER(),
                        autoincrement=True,
                        nullable=False,
                        unique=True,
                        server_default=sa.text("nextval('table_videos_id_seq')")
                    ),

                    sa.Column('created_at', sa.DateTime, server_default=func.now(), comment='Дата создания записи'),
                    sa.Column('updated_at', sa.DateTime, onupdate=func.now(), comment='Дата изменения записи'),
                    sa.Column('youtube_id', sa.String, unique=True, comment='Youtube ID'),
                    sa.Column('title', sa.String, nullable=False, comment='Название'),
                    sa.Column('channel_title', sa.String, comment='Канал'),
                    sa.Column('published_at', sa.DateTime, comment='Дата публикации'),
                    sa.Column('duration', sa.Interval, comment='Длительность'),
                    sa.Column('view_count', sa.Integer, comment='Просмотры'),
                    sa.Column('like_count', sa.Integer, comment='Лайки'),
                    sa.Column('status', sa.String(30), nullable=False, comment='Статус обработки видео'),
                    )

    op.execute(CreateSequence(Sequence('table_comments_id_seq')))
    op.create_table(
        'comments',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False,
                  server_default=sa.text("nextval('table_comments_id_seq')")),
        sa.Column('created_at', sa.DateTime, comment='Дата создания записи'),
        sa.Column('updated_at', sa.DateTime, comment='Дата изменения записи'),
        sa.Column('text', sa.Text, nullable=False, comment='Текст комментария'),
        sa.Column('like_count', sa.Integer, comment='Лайки'),
        sa.Column('video_id', sa.INTEGER(), nullable=False, comment='Youtube ID'),
    )

    op.create_foreign_key(
        'fk_videos',
        'comments',
        'videos',
        ['video_id'],
        ['id']
    )


def downgrade() -> None:
    op.drop_table('comments')
    op.drop_table('videos')
