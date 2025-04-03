from datetime import datetime

from sqlalchemy import Column, String, DateTime, Sequence, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

from db.connect.base import Base


class Comment(Base):
    __tablename__ = 'comments'

    field_seq = Sequence('table_comments_id_seq')

    id = Column(Integer, field_seq, server_default=field_seq.next_value(), primary_key=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    text = Column(String)
    like_count = Column(Integer)
    video_id = Column(Integer, ForeignKey("videos.id"))

    video = relationship('Video', back_populates='comments')
