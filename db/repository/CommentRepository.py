from typing import Optional

from sqlalchemy import Sequence

from db.models.comment.comment import Comment


class CommentRepository:
    def __init__(self, session):
        self.session = session

    def save(self, comment: Comment) -> Comment:
        self.session.add(comment)
        self.session.commit()
        return comment

    def get_by_video_id(self, video_id: int):
         return self.session.query(Comment).filter(Comment.video_id == video_id).all()