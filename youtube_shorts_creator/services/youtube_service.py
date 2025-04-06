import logging
from typing import Dict, List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled

from ..models.video_data import VideoDetails, VideoSegment
from ..config.settings import settings

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        self.client = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
    
    def get_video_details(self, video_id: str) -> Optional[VideoDetails]:
        """Получение метаданных видео"""
        try:
            request = self.client.videos().list(
                id=video_id,
                part='snippet,statistics,contentDetails'
            )
            response = request.execute()
            
            if not response.get('items'):
                logger.warning(f"Видео {video_id} не найдено")
                return None
                
            item = response['items'][0]
            snippet = item['snippet']
            stats = item['statistics']
            
            return VideoDetails(
                id=video_id,
                title=snippet['title'],
                description=snippet['description'],
                duration=item['contentDetails']['duration'],
                view_count=int(stats.get('viewCount', 0)),
                like_count=int(stats.get('likeCount', 0)),
                thumbnail_url=snippet['thumbnails']['high']['url']
            )
            
        except HttpError as e:
            logger.error(f"Ошибка YouTube API: {e}")
            return None
    
    def get_transcript(self, video_id: str) -> Optional[List[VideoSegment]]:
        """Получение транскрипции видео"""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return [
                VideoSegment(
                    start_time=entry['start'],
                    end_time=entry['start'] + entry['duration'],
                    text=entry['text']
                )
                for entry in transcript
            ]
        except TranscriptsDisabled:
            logger.warning(f"Транскрипция отключена для видео {video_id}")
            return None
        except Exception as e:
            logger.error(f"Ошибка получения транскрипции: {e}")
            return None