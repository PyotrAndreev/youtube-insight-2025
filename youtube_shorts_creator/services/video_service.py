import os
import logging
from typing import Tuple, Optional
from pathlib import Path

try:
    from moviepy.editor import VideoFileClip
    import imageio_ffmpeg
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False

from ..config.settings import settings
from ..models.video_data import VideoSegment

logger = logging.getLogger(__name__)

class VideoService:
    def __init__(self):
        if not HAS_MOVIEPY:
            raise ImportError("MoviePy не установлен")
        
        # Настройка FFmpeg
        if hasattr(settings, 'FFMPEG_PATH'):
            os.environ["IMAGEIO_FFMPEG_EXE"] = settings.FFMPEG_PATH
    
    def create_clip(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        end_time: float,
        **kwargs
    ) -> Tuple[bool, str]:
        """Создание клипа из видео"""
        if not os.path.exists(input_path):
            return False, f"Файл {input_path} не найден"
        
        try:
            with VideoFileClip(input_path) as video:
                # Проверка и корректировка времени
                if end_time > video.duration:
                    end_time = video.duration
                    logger.warning(f"Конечное время скорректировано до {end_time}")
                
                if start_time >= end_time:
                    return False, "Начальное время должно быть меньше конечного"
                
                # Создание клипа
                clip = video.subclip(start_time, end_time)
                
                # Параметры экспорта
                export_params = {
                    'codec': 'libx264',
                    'audio_codec': 'aac',
                    'fps': 30,
                    'threads': 4,
                    'preset': 'fast',
                    'logger': None
                }
                export_params.update(kwargs)
                
                clip.write_videofile(output_path, **export_params)
                return True, f"Клип успешно сохранен как {output_path}"
                
        except Exception as e:
            error_msg = f"Ошибка создания клипа: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def find_interesting_segments(
        self,
        segments: List[VideoSegment],
        max_segments: int = 3,
        min_duration: float = 5.0,
        max_duration: float = 15.0
    ) -> List[VideoSegment]:
        """Выбор интересных сегментов на основе анализа транскрипции"""
        # Здесь можно добавить логику выбора сегментов
        # Пока возвращаем первые подходящие по длительности
        result = []
        for segment in segments:
            duration = segment.end_time - segment.start_time
            if min_duration <= duration <= max_duration:
                result.append(segment)
                if len(result) >= max_segments:
                    break
        return result
    