import re
import os
import logging
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from gpt_service import GPTServiceOllama
from typing import List, Optional
import asyncio
from gpt_service import GPTServiceOllama
from transcription.service import TranscriptService
from transcription.saver import TranscriptionSaver

project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)

class VideoProcessor:
    def __init__(self, video_url: str, transcript_service: TranscriptService, gpt_service: GPTServiceOllama):
        self.video_url = video_url
        self.transcript_service = transcript_service
        self.gpt_service = gpt_service
        self.downloaded_path = None
        self.logger = logging.getLogger(__name__)  # Инициализация логгера

    def process(self) -> List[Optional[str]]:
        """Основной метод обработки видео"""
        video_id = self._extract_video_id(self.video_url)

        # Скачивание видео
        self.downloaded_path = self.download_video()
        if not self.downloaded_path:
            print("Ошибка при скачивании видео")
            return []

        # Получаем транскрипт
        transcript_file_path = self.get_transcript(video_id)
        if not transcript_file_path:
            print("Ошибка при получении транскрипта")
            return []

        # Обрабатываем транскрипт с помощью GPT
        timecodes = asyncio.run(self.process_transcript_with_gpt(transcript_file_path))

        # Если нет подходящих таймкодов, сообщаем об этом
        if not timecodes:
            print("Нет подходящих таймкодов после фильтрации.")
            return []

        # Нарезаем видео по таймкодам
        return self.cut_video(timecodes)


    def _extract_video_id(self, url: str) -> str:
        """Извлечение ID видео из URL"""
        return url.split("v=")[-1]

    def download_video(self) -> Optional[str]:
        """Заглушка для скачивания видео"""
        print(f"Скачивание видео {self.video_url}...")
        # Здесь нужно подключить реальный код для скачивания видео
        return "path/to/downloaded_video.mp4"

    def get_transcript(self, video_id: str) -> Optional[str]:
        """Получение транскрипта с использованием TranscriptService"""
        print(f"Получение транскрипта для видео {video_id}...")
        transcript_file_path = self.transcript_service.get_and_save_transcript(video_id)
        return transcript_file_path

    async def process_transcript_with_gpt(self, transcript_file_path: str) -> List[Dict]:
        try:
            # Чтение транскрипта
            with open(transcript_file_path, 'r', encoding='utf-8') as file:
                transcript_text = file.read()

            # Извлечение таймкодов с GPT
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

            # Фильтруем запрещенные слова из таймкодов
            filtered_timecodes = [
                t for t in timecodes
                if not any(banned_word in t['text'].lower() for banned_word in banned_words)
            ]

            return filtered_timecodes

        except Exception as e:
            print(f"Ошибка при обработке транскрипта с GPT: {e}")
            return []

    def cut_video(self, timecodes: List[Dict]) -> List[Optional[str]]:
            """Нарезка видео по таймкодам и логирование процесса"""
            self.logger.info(f"Нарезка видео по таймкодам: {timecodes}")
            
            short_files = []
            
            for i, timecode in enumerate(timecodes):
                short_filename = f"short_{i}.mp4"
                self.logger.info(f"Загружается шортс: {short_filename}")
                # Здесь должен быть код для фактической нарезки видео.
                # Пример:
                short_files.append(short_filename)
                self.logger.info(f"Шортс {short_filename} загружен.")
            
            self.logger.info(f"Все шортсы успешно созданы. Они находятся в папке: {self.downloaded_path}")
            return short_files
    

def main():
    video_url = "https://www.youtube.com/watch?v=pkADX9b9i8A"
    
    # Сервис для транскрипции и GPT
    saver = TranscriptionSaver(output_dir="transcriptions")
    transcript_service = TranscriptService(saver=saver)
    gpt_service = GPTServiceOllama()
    
    # Обработка видео
    processor = VideoProcessor(video_url, transcript_service, gpt_service)
    shorts = processor.process()

    if shorts:
        print("Созданы следующие шортсы:")
        for clip in shorts:
            print(clip)
    else:
        print("Процесс обработки не удался.")

if __name__ == "__main__":
    main()
