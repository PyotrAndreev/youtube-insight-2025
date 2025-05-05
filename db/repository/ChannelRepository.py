from typing import Optional
from db.models.channel.channel import Channel


class ChannelRepository:
    def __init__(self, session):
        self.session = session

    def save(self, channel: Channel) -> Channel:
        self.session.add(channel)
        self.session.commit()
        return channel

    def find_by_title(self, title: str) -> Optional[Channel]:
        return self.session.query(Channel).filter(Channel.title == title).first()

    def get_by_id(self, channel_id: int) -> Optional[Channel]:
        return self.session.query(Channel).filter(Channel.id == channel_id).first()

    def get_by_id_above(self, channel_id: int):
        return self.session.query(Channel).filter(Channel.id >= channel_id).order_by(Channel.id.asc()).all()

    def get_by_youtube_id(self, youtube_id: str) -> Optional[Channel]:
        return self.session.query(Channel).filter(Channel.youtube_id == youtube_id).first()