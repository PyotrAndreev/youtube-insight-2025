import os
import logging
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

class TranscriptionSaver:
    """Класс для сохранения транскрипций видео в файлы"""

    def __init__(self, output_dir: str = "transcriptions"):
        """
        Инициализация класса
        
        :param output_dir: Директория для сохранения транскрипций
        """
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
    def _setup_logging(self):
        """Настройка логирования"""
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def save_transcription(
        self,
        video_id: str,
        text: str,
        language: Optional[str] = None,
        segments: Optional[List[Dict]] = None,
        timestamp_format: str = "%Y%m%d_%H%M%S"
    ) -> Optional[Path]:
        """
        Сохраняет транскрипцию в текстовый файл
        
        :param video_id: ID видео
        :param text: Текст транскрипции
        :param language: Язык транскрипции
        :param segments: Список сегментов с таймкодами
        :param timestamp_format: Формат временной метки
        :return: Путь к сохраненному файлу или None при ошибке
        """
        try:
            # Создаем директорию если не существует
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Генерируем имя файла
            timestamp = datetime.now().strftime(timestamp_format)
            filename = self._generate_filename(video_id, timestamp, language)
            filepath = self.output_dir / filename
            
            # Сохраняем основной текст
            self._write_file(filepath, text)
            
            # Сохраняем сегменты если есть
            if segments:
                segments_filename = f"{video_id}_{timestamp}_segments.txt"
                segments_path = self.output_dir / segments_filename
                self._save_segments(segments_path, segments)
            
            self.logger.info(f"Транскрипция сохранена: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения транскрипции: {e}", exc_info=True)
            return None

    def _generate_filename(
        self,
        video_id: str,
        timestamp: str,
        language: Optional[str] = None
    ) -> str:
        """Генерирует имя файла для транскрипции"""
        filename = f"{video_id}_{timestamp}"
        if language:
            filename += f"_{language}"
        return f"{filename}.txt"

    def _write_file(self, path: Path, content: str) -> None:
        """Записывает текст в файл"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _save_segments(self, path: Path, segments: List[Dict]) -> None:
        """Сохраняет сегменты транскрипции"""
        with open(path, 'w', encoding='utf-8') as f:
            for segment in segments:
                f.write(f"{segment['start']:.2f}-{segment['end']:.2f}: {segment['text']}\n")
