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

from deepseek_integration import call_deepseek
from core import VideoCutter
from preview_service import PreviewService
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

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)

class VideoProcessor:
    def __init__(self,
                 video_url: str,
                 transcript_service: TranscriptService,
                 gpt_service: GPTServiceOllama,
                 download_dir: Optional[Path] = None):
        self.video_url = video_url
        self.transcript_service = transcript_service
        self.gpt_service = gpt_service
        self.downloaded_path: Optional[Path] = None
        self.logger = logging.getLogger(__name__)
        self.download_dir = download_dir or Path("downloads")
        self.download_dir.mkdir(exist_ok=True)
        self.video_cutter = VideoCutter(output_dir="processed_shorts", download_dir=str(self.download_dir))
        self.preview_service = PreviewService(self.video_cutter, self.gpt_service, use_gpt=True)
        self.events: List[Dict] = []

    @measure_sync_time
    def process(self) -> List[Optional[str]]:
        video_id = self._extract_video_id(self.video_url)

        # 1) Скачиваем видео
        self.downloaded_path = self.download_video()
        if not self.downloaded_path:
            print("Ошибка при скачивании видео")
            return []

        # 2) Извлекаем аудио для DeepSeek
        audio_file = self.extract_audio(self.downloaded_path)
        if not audio_file:
            print("Ошибка при извлечении аудио")
            return []

        # 3) Получаем популярные сегменты через DeepSeek
        ds_result = call_deepseek(str(audio_file))
        if isinstance(ds_result, dict):
            popular_segments = ds_result.get("popular_segments", [])
        else:
            popular_segments = getattr(ds_result, "popular_segments", [])
        print(f"DeepSeek popular segments: {popular_segments}")

        # 4) создаём превью (1–30 сек) и выводим путь
        preview_clip = self.preview_service.create_preview(self.downloaded_path, video_id)
        if preview_clip:
            print(f"Превью создано: {preview_clip}")

        # 5) Получаем транскрипт
        transcript_file_path = self.get_transcript(video_id)
        if not transcript_file_path:
            print("Ошибка при получении транскрипта")
            return []

        # 6) Анализ у Ollama: передаём транскрипт и аудио-сегменты
        timecodes = asyncio.run(
            self.process_transcript_with_gpt(transcript_file_path, popular_segments)
        )

        if not timecodes:
            print("Нет подходящих таймкодов после фильтрации.")
            return []

        # 7) Нарезаем шорты
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
    def extract_audio(self, video_path: Path) -> Optional[Path]:
        """
        Через ffmpeg из переданного видео (video_path) получаем WAV
        для анализа DeepSeek.
        """
        if not video_path or not video_path.exists():
            return None
        try:
            audio_path = self.download_dir / f"{video_path.stem}.wav"
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-vn', '-ac', '1', '-ar', '44100', str(audio_path)
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return audio_path if audio_path.exists() else None
        except Exception as e:
            self.logger.error(f"Ошибка извлечения аудио: {e}")
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
            # Вызываем Ollama с текстом и аудио-сегментами
            timecodes = await self.gpt_service.extract_timecodes(
                transcript_text,
                popular_segments
            )
            # Фильтрация банных слов
            banned = [w.lower() for w in [
                # ... ваш список банных фраз ...
            ]]
            filtered = [t for t in timecodes if not any(b in t['text'].lower() for b in banned)]
            return filtered
        except Exception as e:
            print(f"Ошибка при обработке транскрипта с GPT: {e}")
            return []

    @measure_sync_time
    def cut_video(self, timecodes: List[Dict]) -> List[Optional[str]]:
        output_paths: List[str] = []
        print("Полученные timecodes:")
        for t in timecodes:
            print(t)
            start, end = t['start'], t['end']
            fname = sanitize_filename(f"short_{start}-{end}.mp4")
            try:
                out = self.video_cutter.create_short(
                    input_path=self.downloaded_path,
                    output_name=fname,
                    start_time=start,
                    end_time=end
                )
                if out:
                    output_paths.append(out)
            except Exception as e:
                print(f"Ошибка при создании Short: {e}")
        return output_paths

    def dump_events_to_file(self, filename: str = None):
        if not filename:
            ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            filename = f"video_processor_events_{ts}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)
        logger.info(f"События сохранены в файл: {filename}")

# --- Пример запуска ---
def main():
    video_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=JGRAtRzGWlw"
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
