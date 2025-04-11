from datetime import datetime

from sqlalchemy import Column, String, Enum, DateTime, Sequence, Integer, Interval, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from db.connect.base import Base
from db.models.comment.comment import Comment
from db.models.video.status import Status


class Video(Base):
    __tablename__ = 'videos'

    field_seq = Sequence('table_videos_id_seq')

    id = Column(Integer, field_seq, server_default=field_seq.next_value(), primary_key=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    youtube_id = Column(String, nullable=False, unique=True)
    title = Column(String)
    channel_title = Column(String)
    published_at = Column(DateTime)
    duration = Column(Interval)
    view_count = Column(Integer)
    like_count = Column(Integer)
    status = Column(Enum(Status), nullable=False)
    comment_count = Column(Integer)
    category_id = Column(Integer)
    tags = Column(JSONB)

    comments = relationship(Comment, back_populates="video")
