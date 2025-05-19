from sqlalchemy import Column, String, Sequence, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Sequence, Integer
from db.connect.base import Base
from db.models.video.video import Video


class Playlist(Base):
    __tablename__ = 'playlists'

    field_seq = Sequence('table_playlists_id_seq')

    id = Column(Integer, field_seq, server_default=field_seq.next_value(), primary_key=True)
    youtube_id = Column(String, nullable=False, unique=True)
    title = Column(String)
    video_count = Column(Integer)
    published_at = Column(DateTime)

    videos = relationship(Video, back_populates="playlist")
