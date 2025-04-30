import os
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

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

class TranscriptionSaver:
    """Класс для сохранения транскрипций видео в файлы"""

    def __init__(self, output_dir: str = "transcriptions"):
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        self.events: List[Dict] = []
        self._setup_logging()

    def _setup_logging(self):
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    @measure_sync_time
    def save_transcription(self, video_id: str, text: str,
                            language: Optional[str] = None,
                            segments: Optional[List[Dict]] = None,
                            timestamp_format: str = "%Y%m%d_%H%M%S") -> Optional[Path]:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime(timestamp_format)
            filename = self._generate_filename(video_id, timestamp, language)
            filepath = self.output_dir / filename
            self._write_file(filepath, text)

            if segments:
                segments_filename = f"{video_id}_{timestamp}_segments.txt"
                segments_path = self.output_dir / segments_filename
                self._save_segments(segments_path, segments)

            self.logger.info(f"Транскрипция сохранена: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Ошибка сохранения транскрипции: {e}", exc_info=True)
            return None

    def _generate_filename(self, video_id: str, timestamp: str, language: Optional[str] = None) -> str:
        filename = f"{video_id}_{timestamp}"
        if language:
            filename += f"_{language}"
        return f"{filename}.txt"

    @measure_sync_time
    def _write_file(self, path: Path, content: str) -> None:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    @measure_sync_time
    def _save_segments(self, path: Path, segments: List[Dict]) -> None:
        with open(path, 'w', encoding='utf-8') as f:
            for segment in segments:
                f.write(f"{segment['start']:.2f}-{segment['end']:.2f}: {segment['text']}\n")

    def dump_events_to_file(self, filename: str = None):
        import json
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            filename = f"saver_events_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, indent=2, ensure_ascii=False)
        logger.info(f"События сохранены в файл: {filename}")
