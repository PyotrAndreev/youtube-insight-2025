from transcription.service import TranscriptService
import re
from core import VideoCutter
from transcription.saver import TranscriptionSaver
from typing import List, Optional, Dict
from gpt_service import GPTServiceOllama
from yt_dlp import YoutubeDL

import sys
import os
from pathlib import Path

project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)

class VideoProcessor:
    """Класс для обработки видео: скачивание, транскрипция, GPT-анализ, нарезка"""

    def __init__(self, video_url: str, gpt_service, segment_duration: int = 60):
        self.video_url = video_url
        self.gpt_service = gpt_service
        self.segment_duration = segment_duration

        self.download_dir = Path("downloads")
        self.download_dir.mkdir(exist_ok=True)
        self.downloaded_path: Optional[Path] = None

        self.transcription_saver = TranscriptionSaver()
        self.transcript_service = TranscriptService(self.transcription_saver)
        self.video_cutter = VideoCutter()

    def process(self) -> List[Optional[str]]:
        """Основной метод обработки видео"""
        video_id = self._extract_video_id(self.video_url)

        # Скачиваем видео
        self.downloaded_path = self.download_video()
        if not self.downloaded_path:
            print("Ошибка при скачивании видео")
            return []

        # Получаем транскрипт
        transcript_file_path = self.get_transcript(video_id)
        if not transcript_file_path:
            return []

        # Обрабатываем транскрипт с GPT
        timecodes = self.process_transcript_with_gpt(transcript_file_path)

        # Нарезаем видео по таймкодам
        return self.cut_video(timecodes)

    def _extract_video_id(self, video_url: str) -> str:
        return video_url.split("v=")[-1]

    def download_video(self) -> Optional[Path]:
        """Скачивает видео и возвращает путь к файлу"""
        try:
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

    def get_transcript(self, video_id: str) -> Optional[str]:
        try:
            return self.transcript_service.get_and_save_transcript(video_id)
        except Exception as e:
            print(f"Ошибка при получении транскрипта: {e}")
            return None

    def process_transcript_with_gpt(self, transcript_file_path: str) -> List[Dict]:
        try:
            with open(transcript_file_path, 'r', encoding='utf-8') as file:
                transcript_text = file.read()
            timecodes = self.gpt_service.extract_timecodes(transcript_text)

            # Расширенный список рекламных фраз
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

            # Фильтруем все плохие сегменты
            filtered_timecodes = [
                t for t in timecodes
                if not any(banned_word in t['text'].lower() for banned_word in banned_words)
            ]

            return filtered_timecodes

        except Exception as e:
            print(f"Ошибка при обработке транскрипта с GPT: {e}")
            return []


    def cut_video(self, timecodes: List[Dict]) -> List[Optional[str]]:
        """Нарезаем видео по таймкодам, полученным от GPT"""
        output_paths = []
        print("Полученные timecodes:")
        for t in timecodes:
            print(t)
        
        for timecode in timecodes:
            if not isinstance(timecode, dict) or not all(k in timecode for k in ("start", "end", "text")):
                print(f"Пропущен некорректный формат timecode: {timecode}")
                continue


        for timecode in timecodes:
            start_time = timecode["start"]
            end_time = timecode["end"]
            clip_text = timecode["text"]
            
            # Формируем корректное имя файла
            output_name_raw = f"short_{start_time}-{end_time}.mp4"
            output_name = sanitize_filename(output_name_raw)
            
            try:
                output_path = self.video_cutter.create_short(
                    input_path=str(self.downloaded_path),
                    output_name=output_name,
                    start_time=start_time,
                    end_time=end_time
                )

                if output_path:
                    output_paths.append(output_path)
            except Exception as e:
                print(f"Ошибка при создании Shorts: {e}")
        
        return output_paths



def main():
    video_url = "https://www.youtube.com/watch?v=Y2yOa8j4UTc"
    gpt_service = GPTServiceOllama()
    processor = VideoProcessor(video_url, gpt_service)
    shorts = processor.process()

    if shorts:
        print("Созданы следующие шортсы:")
        for clip in shorts:
            print(clip)
    else:
        print("Процесс обработки https://www.youtube.com/watch?v=yeLFUvOfUt0")


if __name__ == "__main__":
    main()
