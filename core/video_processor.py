import re
import os
import time
import logging
import sys
import asyncio
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional

from core import VideoCutter
from gpt_service import GPTServiceOllama
from transcription.service import TranscriptService
from transcription.saver import TranscriptionSaver

# --- Логгер и декоратор замера времени ---
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


def measure_async_time(func):
    async def wrapper(self, *args, **kwargs):
        start = time.time()
        logger.info(f"[TIMER START] {func.__name__}")
        result = await func(self, *args, **kwargs)
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


def parse_timecode(tc: str) -> float:
    """
    Преобразует строковый таймкод формата "HH:MM:SS" или "MM:SS" в секунды.
    """
    parts = tc.split(':')
    nums = [float(p) for p in parts]
    if len(nums) == 3:
        h, m, s = nums
    elif len(nums) == 2:
        h = 0
        m, s = nums
    else:
        return float(nums[0])
    return h * 3600 + m * 60 + s

class VideoProcessor:
    def __init__(
        self,
        video_url: str,
        transcript_service: TranscriptService,
        gpt_service: GPTServiceOllama,
        download_dir: Optional[Path] = None
    ):
        self.video_url = video_url
        self.transcript_service = transcript_service
        self.gpt_service = gpt_service
        self.downloaded_path: Optional[Path] = None
        self.logger = logging.getLogger(__name__)
        self.download_dir = download_dir or Path("downloads")
        self.download_dir.mkdir(exist_ok=True)
        self.video_cutter = VideoCutter(output_dir="processed_shorts", download_dir=str(self.download_dir))
        self.events: List[Dict] = []

    @measure_sync_time
    def process(self) -> List[Optional[str]]:
        video_id = self._extract_video_id(self.video_url)

        # 1) Скачиваем видео
        self.downloaded_path = self.download_video()
        if not self.downloaded_path:
            print("Ошибка при скачивании видео")
            return []

        # Вместо DeepSeek: используем пустой список сегментов
        popular_segments: List[Dict] = []

        # 2) Получаем транскрипт
        transcript_file_path = self.get_transcript(video_id)
        if not transcript_file_path:
            print("Ошибка при получении транскрипта")
            return []

        # 3) Анализ у Ollama: передаём транскрипт и (пустые) аудио-сегменты
        timecodes = asyncio.run(
            self.process_transcript_with_gpt(transcript_file_path, popular_segments)
        )

        if not timecodes:
            print("Нет подходящих таймкодов после фильтрации.")
            return []

        # 4) Нарезаем шорты
        return self.cut_video(timecodes)

    def _extract_video_id(self, url: str) -> str:
        return url.split("v=")[-1]

    @measure_sync_time
    def download_video(self) -> Optional[Path]:
        try:
            from yt_dlp import YoutubeDL
            ydl_opts = {
                'format': 'mp4',
                'outtmpl': str(self.download_dir / '%(id)s.%(ext)s'),
                'quiet': True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.video_url, download=True)
                filename = f"{info['id']}.mp4"
                return self.download_dir / filename
        except Exception as e:
            print(f"Ошибка при скачивании видео: {e}")
            return None

    @measure_sync_time
    def get_transcript(self, video_id: str) -> Optional[str]:
        print(f"Получение транскрипта для видео {video_id}...")
        return self.transcript_service.get_and_save_transcript(video_id)

    @measure_async_time
    async def process_transcript_with_gpt(
        self,
        transcript_file_path: str,
        popular_segments: List[Dict]
    ) -> List[Dict]:
        try:
            transcript_text = Path(transcript_file_path).read_text(encoding='utf-8')
            timecodes = await self.gpt_service.extract_timecodes(
                transcript_text,
                popular_segments
            )
            return timecodes
        except Exception:
            return []

    @measure_sync_time
    def cut_video(self, timecodes: List[Dict]) -> List[Optional[str]]:
        results: List[Optional[str]] = []
        for tc in timecodes:
            raw_start = tc.get('start', 0)
            raw_end = tc.get('end', raw_start)
            # Конвертация таймкодов в секунды
            start = parse_timecode(raw_start) if isinstance(raw_start, str) else float(raw_start)
            end = parse_timecode(raw_end) if isinstance(raw_end, str) else float(raw_end)
            # Ограничение по максимальной длительности
            max_dur = self.video_cutter.max_duration
            if end - start > max_dur:
                end = start + max_dur
            clip_path = self.video_cutter.create_short(
                input_path=self.downloaded_path,
                output_name=f"short_{int(start)}-{int(end)}.mp4",
                start_time=start,
                end_time=end
            )
            if clip_path:
                results.append(str(clip_path))
        return results


    def dump_events_to_file(self):
        """
        Сохраняет накопленные события таймеров в JSON-файл.
        """
        ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        filename = f"processor_events_{ts}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)
        print(f"События VideoProcessor сохранены в {filename}")

# --- Пример запуска ---
def main():
    video_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=G74W62Fsz3I"
    saver = TranscriptionSaver(output_dir="transcriptions")
    transcript_service = TranscriptService(saver=saver)
    gpt_service = GPTServiceOllama()
    processor = VideoProcessor(video_url, transcript_service, gpt_service)
    shorts = processor.process()
    if shorts:
        print("Созданы шортсы:")
        for clip in shorts:
            print(clip)
    processor.dump_events_to_file()
    transcript_service.dump_events_to_file()
    saver.dump_events_to_file()
    all_events = processor.events + transcript_service.events + saver.events
    try:
        all_events += gpt_service.events
    except Exception:
        pass
    ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    with open(f"full_pipeline_events_{ts}.json", 'w', encoding='utf-8') as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)
    print(f"Все события сохранены в full_pipeline_events_{ts}.json")

if __name__ == "__main__":
    main()
