"""add table playlist

Revision ID: 79997c9c11b7
Revises: 0e36d165d1e9
Create Date: 2025-05-10 20:04:42.900287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import Sequence, CreateSequence


# revision identifiers, used by Alembic.
revision: str = '79997c9c11b7'
down_revision: Union[str, None] = '0e36d165d1e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(CreateSequence(Sequence('table_playlists_id_seq')))
    op.create_table('playlists',
                    sa.Column(
                        'id', sa.INTEGER(),
                        autoincrement=True,
                        nullable=False,
                        unique=True,
                        server_default=sa.text("nextval('table_playlists_id_seq')")
                    ),

                    sa.Column('title', sa.String, nullable=False, comment='Название'),
                    sa.Column('youtube_id', sa.String, unique=True, comment='Youtube ID'),
                    sa.Column('published_at', sa.DateTime, comment='Дата публикации'),
                    sa.Column('video_count', sa.BigInteger, comment='Количество видео')
                    )
    op.add_column('videos', sa.Column('playlist_id', sa.Integer(), comment='ID плейлиста'))

    op.create_foreign_key(
        'fk_videos_playlists',
        'videos',
        'playlists',
        ['playlist_id'],
        ['id']
    )


def downgrade() -> None:
    op.drop_column('videos', 'playlist_id')
    op.drop_table('playlists')
