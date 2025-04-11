from typing import List, Dict, Optional
from utils.logger import setup_logger
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    VideoUnavailable
)

logger = setup_logger(__name__)

class TranscriptService:
    """Сервис для работы с транскрипциями YouTube видео"""
    
    def __init__(self, saver=None):
        """
        :param saver: Экземпляр TranscriptionSaver для сохранения результатов
        """
        self.saver = saver
        
    def get_and_save_transcript(
        self,
        video_id: str,
        languages: List[str] = ['ru', 'en'],
        preserve_formatting: bool = False
    ) -> Optional[Path]:
        """
        Получает и сохраняет транскрипцию
        
        :return: Путь к сохраненному файлу или None
        """
        transcript = self._get_transcript(video_id, languages, preserve_formatting)
        if not transcript or not self.saver:
            return None
            
        # Конвертируем транскрипцию в текст и сегменты
        full_text = "\n".join([t['text'] for t in transcript])
        segments = [{
            'start': t['start'],
            'end': t['start'] + t['duration'],
            'text': t['text']
        } for t in transcript]
        
        return self.saver.save_transcription(
            video_id=video_id,
            text=full_text,
            language=languages[0] if languages else None,
            segments=segments
        )

    def _get_transcript(
        self,
        video_id: str,
        languages: List[str],
        preserve_formatting: bool
    ) -> Optional[List[Dict]]:
        """Внутренний метод для получения транскрипции"""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=languages,
                preserve_formatting=preserve_formatting
            )
            logger.info(f"Получена транскрипция для видео {video_id}")
            return transcript
        except TranscriptsDisabled:
            logger.warning(f"Транскрипция отключена для видео {video_id}")
        except VideoUnavailable:
            logger.error(f"Видео {video_id} не существует или недоступно")
        except Exception as e:
            logger.error(f"Ошибка при получении транскрипции: {str(e)}")
        return None

    @staticmethod
    def get_manual_video_ids() -> List[str]:
        """Возвращает предопределенный список ID видео"""
        return ["dQw4w9WgXcQ", "9bZkp7q19f0", "kJQP7kiw5Fk"]