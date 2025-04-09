import logging
from pathlib import Path
from typing import Optional
from PIL import Image
from moviepy import VideoFileClip
from moviepy import *
from moviepy.video.fx import *
from moviepy.video.fx import Resize

# Настроим логирование
logger = logging.getLogger(__name__)

class YouTubeShortsCreator:
    def __init__(self):
        self.output_dir = Path("processed_shorts")
        self.download_dir = Path("downloads")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def process_video(self, video_id: str):
        print(f"Обрабатываю видео: {video_id}")

        # 1. Скачивание видео
        input_path = self._download_video(video_id)
        if not input_path:
            print("Не удалось скачать видео")
            return None

        # 2. Создание Shorts
        output_path = self.output_dir / f"short_{video_id}.mp4"
        if self._create_short(input_path, output_path):
            print(f"Готовый Shorts сохранён: {output_path}")
            return output_path

        print("Не удалось создать Shorts")
        return None

    def _download_video(self, video_id: str) -> Optional[Path]:
        """Скачивание видео с YouTube"""
        import yt_dlp  # Импортируем yt_dlp
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': str(self.download_dir / '%(id)s.%(ext)s'),
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://youtu.be/{video_id}", download=True)
                return Path(ydl.prepare_filename(info))
        except Exception as e:
            logger.error(f"Ошибка скачивания: {e}")
            return None

    def _create_short(self, input_path: Path, output_path: Path) -> bool:
        """Создание вертикального Shorts"""
        try:
            if not input_path.exists():
                logger.error(f"Файл {input_path} не найден")
                return False

            with VideoFileClip(str(input_path)) as clip:
                # Обрезка до 60 секунд
                if clip.duration > 60:
                    clip = clip.subclipped(0, 60)

                # Проверка, если видео уже в формате 9:16, можно пропустить обрезку
                if clip.size[0] != 1080 or clip.size[1] != 1920:
                    # Вертикальный формат (9:16) с указанием фильтра ресэмплинга
                    clip = clip.with_effects([Resize.resizer(height=1920)])
                    clip = clip.crop(x1=(clip.w - 1080) / 2, width=1080, height=1920)
                
                # Экспорт видео
                clip.write_videofile(
                    str(output_path),
                    codec="libx264",
                    audio_codec="aac",
                    fps=30,
                    threads=4,
                    preset="fast"
                )
                return True
        except Exception as e:
            logger.error(f"Ошибка обработки видео: {e}")
            return False
