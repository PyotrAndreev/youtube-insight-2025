import re
import os
import time
import logging
import sys
import asyncio
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

# --- Основной класс ---

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)

class VideoProcessor:
    def __init__(self, video_url: str, transcript_service: TranscriptService, gpt_service: GPTServiceOllama, download_dir: Optional[Path] = None):
        self.video_url = video_url
        self.transcript_service = transcript_service
        self.gpt_service = gpt_service
        self.downloaded_path = None
        self.logger = logging.getLogger(__name__)
        self.download_dir = download_dir or Path("downloads")
        self.video_cutter = VideoCutter(output_dir="processed_shorts", download_dir=str(self.download_dir))
        self.events: List[Dict] = []  # <--- собираем события

    @measure_sync_time
    def process(self) -> List[Optional[str]]:
        video_id = self._extract_video_id(self.video_url)

        self.downloaded_path = self.download_video()
        if not self.downloaded_path:
            print("Ошибка при скачивании видео")
            return []

        transcript_file_path = self.get_transcript(video_id)
        if not transcript_file_path:
            print("Ошибка при получении транскрипта")
            return []

        timecodes = asyncio.run(self.process_transcript_with_gpt(transcript_file_path))

        if not timecodes:
            print("Нет подходящих таймкодов после фильтрации.")
            return []

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
                downloaded_filename = f"{info['id']}.mp4"
                return self.download_dir / downloaded_filename
        except Exception as e:
            print(f"Ошибка при скачивании видео: {e}")
            return None

    @measure_sync_time
    def get_transcript(self, video_id: str) -> Optional[str]:
        print(f"Получение транскрипта для видео {video_id}...")
        transcript_file_path = self.transcript_service.get_and_save_transcript(video_id)
        return transcript_file_path

    @measure_async_time
    async def process_transcript_with_gpt(self, transcript_file_path: str) -> List[Dict]:
        try:
            with open(transcript_file_path, 'r', encoding='utf-8') as file:
                transcript_text = file.read()

            timecodes = await self.gpt_service.extract_timecodes(transcript_text)

            banned_words = [
                "подпишитесь", "лайк", "колокольчик", "не забудьте подписаться",
                "ставьте лайк", "поддержите канал", "нажмите на колокольчик",
                "поддержать меня", "ссылка в описании", "ссылку оставлю в описании",
                "смотрите другие видео", "подписывайтесь на канал",
                "подписка", "подпишитесь на канал", "подпишитесь на мой канал",
                "ставьте лайки", "не забудьте поставить лайк", "лайкните это видео",
                "реклама", "спонсор", "спонсор этого видео", "это видео спонсировано",
                "спонсорская интеграция", "рекламная интеграция",
                "благодарим нашего спонсора", "благодаря нашему партнеру",
                "промокод", "партнер", "наш партнер", "рекламная пауза",
                "сотрудничество", "поддержка проекта", "донат", "донаты",
                "переходите по ссылке", "купите", "приобретите", "на сайте",
                "по ссылке в описании", "информация в описании",
                "лучший магазин", "наш магазин", "магазин партнера",
                "поддержите меня донатом", "платная подписка"
            ]

            filtered_timecodes = [
                t for t in timecodes
                if not any(banned_word in t['text'].lower() for banned_word in banned_words)
            ]

            return filtered_timecodes

        except Exception as e:
            print(f"Ошибка при обработке транскрипта с GPT: {e}")
            return []

    @measure_sync_time
    def cut_video(self, timecodes: List[Dict]) -> List[Optional[str]]:
        output_paths = []
        print("Полученные timecodes:")
        for t in timecodes:
            print(t)

        for timecode in timecodes:
            start_time = timecode["start"]
            end_time = timecode["end"]
            clip_text = timecode["text"]

            output_name_raw = f"short_{start_time}-{end_time}.mp4"
            output_name = sanitize_filename(output_name_raw)

            try:
                output_path = self.video_cutter.create_short(
                    input_path=self.downloaded_path,
                    output_name=output_name,
                    start_time=start_time,
                    end_time=end_time
                )
                if output_path:
                    output_paths.append(output_path)
            except Exception as e:
                print(f"Ошибка при создании Shorts: {e}")

        return output_paths

    def dump_events_to_file(self, filename: str = None):
        import json
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            filename = f"video_processor_events_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, indent=2, ensure_ascii=False)
        logger.info(f"События сохранены в файл: {filename}")

# --- Пример запуска ---

def main():
    video_url = "https://www.youtube.com/watch?v=JGRAtRzGWlw"

    saver = TranscriptionSaver(output_dir="transcriptions")
    transcript_service = TranscriptService(saver=saver)
    gpt_service = GPTServiceOllama()

    processor = VideoProcessor(video_url, transcript_service, gpt_service)
    shorts = processor.process()

    if shorts:
        print("Созданы следующие шортсы:")
        for clip in shorts:
            print(clip)
    else:
        print("Процесс обработки не удался.")

    # Сохраняем индивидуальные события
    processor.dump_events_to_file()
    transcript_service.dump_events_to_file()
    saver.dump_events_to_file()

    # Объединяем все события
    all_events = processor.events + transcript_service.events + saver.events

    try:
        gpt_events = gpt_service.events
        all_events += gpt_events
    except Exception:
        pass

    # Сохраняем общий файл
    import json
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    filename = f"full_pipeline_events_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    print(f"Все события пайплайна сохранены в {filename}")


if __name__ == "__main__":
    main()


