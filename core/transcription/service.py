from typing import List, Dict, Optional
import logging
import time
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    VideoUnavailable
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def measure_sync_time(func):
    def wrapper(self, *args, **kwargs):
        start = time.time()
        logger.info(f"[TIMER START] {func.__name__}")
        result = func(self, *args, **kwargs)
        end = time.time()
        duration = end - start
        logger.info(f"[TIMER END] {func.__name__} | Duration: {duration:.3f}s")
        if hasattr(self, 'events'):
            self.events.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start)),
                "function": func.__name__,
                "duration_sec": duration
            })
        return result
    return wrapper

class TranscriptService:
    """Сервис для работы с транскрипциями YouTube видео"""
    
    def __init__(self, saver=None):
        self.saver = saver
        self.events: List[Dict] = []

    @measure_sync_time
    def get_and_save_transcript(self, video_id: str,
                                languages: List[str] = ['ru', 'en'],
                                preserve_formatting: bool = False) -> Optional[Path]:
        transcript = self._get_transcript(video_id, languages, preserve_formatting)
        if not transcript or not self.saver:
            return None

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

    @measure_sync_time
    def _get_transcript(self, video_id: str,
                        languages: List[str],
                        preserve_formatting: bool) -> Optional[List[Dict]]:
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

    def dump_events_to_file(self, filename: str = None):
        import json
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            filename = f"service_events_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, indent=2, ensure_ascii=False)
        logger.info(f"События сохранены в файл: {filename}")
