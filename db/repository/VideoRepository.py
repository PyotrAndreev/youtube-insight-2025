from typing import Optional
from db.models.video.video import Video


class VideoRepository:
    def __init__(self, session):
        self.session = session

    def save(self, video: Video) -> Video:
        self.session.add(video)
        self.session.commit()
        return video

    def get_by_youtube_id(self, youtube_id: str) -> Optional[Video]:
        return self.session.query(Video).filter(Video.youtube_id == youtube_id).first()

    def get_by_id(self, video_id: int) -> Optional[Video]:
        return self.session.query(Video).filter(Video.id == video_id).first()

    def get_by_id_above(self, video_id: int):
        return self.session.query(Video).filter(Video.id >= video_id).order_by(Video.id.asc()).all()

    def get_by_id_category(self, category_id: int):
        if category_id == -1:
            return self.session.query(Video).filter(Video.id >= 0).order_by(Video.id.asc()).all()
        return self.session.query(Video).filter(Video.category_id == category_id).order_by(Video.id.asc()).all()

