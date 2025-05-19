from typing import Optional

from db.models.playlist.playlist import Playlist


class PlaylistRepository:
    def __init__(self, session):
        self.session = session

    def save(self, playlist: Playlist) -> Playlist:
        self.session.add(playlist)
        self.session.commit()
        return playlist

    def get_by_youtube_id(self, youtube_id: str) -> Optional[Playlist]:
        return self.session.query(Playlist).filter(Playlist.youtube_id == youtube_id).first()

    def get_by_id(self, playlist_id: int) -> Optional[Playlist]:
        return self.session.query(Playlist).filter(Playlist.id == playlist_id).first()