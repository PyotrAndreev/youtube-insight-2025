import yt_dlp
import os
from moviepy.editor import VideoFileClip
from typing import Optional
from pathlib import Path

class YouTubeShortsCreator:
    def __init__(self):
        self.output_dir = "processed_shorts"
        self.download_dir = "downloads"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.download_dir, exist_ok=True)

    def process_video(self, video_id: str):
        print(f"Обрабатываю видео: {video_id}")
        
        # 1. Скачивание видео
        input_path = self._download_video(video_id)
        if not input_path:
            print(" Не удалось скачать видео")
            return None
        
        # 2. Создание Shorts
        output_path = os.path.join(self.output_dir, f"short_{video_id}.mp4")
        if self._create_short(input_path, output_path):
            print(f" Готовый Shorts сохранён: {output_path}")
            return output_path
        
        print(" Не удалось создать Shorts")
        return None

    def _download_video(self, video_id: str) -> Optional[str]:
        """Скачивание видео с YouTube"""
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': os.path.join(self.download_dir, f'%(id)s.%(ext)s'),
            'quiet': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://youtu.be/{video_id}", download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            print(f"Ошибка скачивания: {e}")
            return None

    def _create_short(self, input_path: str, output_path: str) -> bool:
        """Создание вертикального Shorts"""
        try:
            if not os.path.exists(input_path):
                print(f"Файл {input_path} не найден")
                return False
                
            with VideoFileClip(input_path) as clip:
                # Обрезка до 60 секунд
                if clip.duration > 60:
                    clip = clip.subclip(0, 60)
                
                # Вертикальный формат (9:16)
                final_clip = clip.resize(height=1920).crop(
                    x1=clip.w/2 - 540,
                    width=1080,
                    height=1920
                )
                
                # Экспорт
                final_clip.write_videofile(
                    output_path,
                    codec="libx264",
                    audio_codec="aac",
                    fps=30,
                    threads=4,
                    preset="fast"
                )
                return True
        except Exception as e:
            print(f"Ошибка обработки видео: {e}")
            return False