from typing import Optional
from db.models.video.video import Video
from db.models.comment.comment import Comment


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

