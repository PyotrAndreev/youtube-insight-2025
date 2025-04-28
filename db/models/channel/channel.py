from sqlalchemy import Column, String, Sequence, Integer
from sqlalchemy.orm import relationship

from db.connect.base import Base
from db.models.video.video import Video


class Channel(Base):
    __tablename__ = 'channels'

    field_seq = Sequence('table_channels_id_seq')

    id = Column(Integer, field_seq, server_default=field_seq.next_value(), primary_key=True)
    youtube_id = Column(String, nullable=False, unique=True)
    title = Column(String)
    view_count = Column(Integer)
    video_count = Column(Integer)
    subscriber_count = Column(Integer)

    videos = relationship(Video, back_populates="channel")
