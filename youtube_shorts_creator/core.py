import logging
import subprocess
import os
from pathlib import Path
from datetime import datetime
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.fx import all as vfx
from moviepy.video.fx import resize, crop
import yt_dlp

# Настроим логирование
logger = logging.getLogger(__name__)

# Папки для хранения файлов
download_dir = Path("downloads")
download_dir.mkdir(parents=True, exist_ok=True)

segments_dir = Path("video_segments")
segments_dir.mkdir(parents=True, exist_ok=True)

output_dir = Path("processed_shorts")
output_dir.mkdir(parents=True, exist_ok=True)

# Параметры обработки
ffmpeg_path = "ffmpeg"  # Убедитесь, что ffmpeg установлен и доступен в PATH
segment_duration = 60  # Продолжительность сегмента в секундах
target_width = 1080
target_height = 1920
max_duration = 60  # Максимальная длительность видео для Shorts в секундах

def download_video(video_url: str) -> Path:
    """Скачивает видео с YouTube по URL."""
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': str(download_dir / '%(id)s.%(ext)s'),
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            return Path(ydl.prepare_filename(info))
    except Exception as e:
        logger.error(f"Ошибка при скачивании видео: {e}")
        return None

def split_video(input_path: Path, segment_duration: int) -> list:
    """Разделяет видео на сегменты."""
    output_template = str(segments_dir / f"{input_path.stem}-%03d{input_path.suffix}")
    cmd = [
        ffmpeg_path,
        '-i', str(input_path),
        '-c:v', 'copy',
        '-c:a', 'copy',
        '-f', 'segment',
        '-segment_time', str(segment_duration),
        '-reset_timestamps', '1',
        output_template
    ]
    try:
        subprocess.run(cmd, check=True)
        return list(segments_dir.glob(f"{input_path.stem}-*{input_path.suffix}"))
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при разделении видео: {e}")
        return []

def create_short(input_path: Path, output_path: Path) -> bool:
    """Создает вертикальное видео (9:16) для Shorts."""
    try:
        with VideoFileClip(str(input_path)) as clip:
            original_width, original_height = clip.size
            fps = clip.fps

            # Ограничиваем длительность видео
            if clip.duration > max_duration:
                clip = clip.subclip(0, max_duration)

            # Масштабируем по высоте и обрезаем по ширине
            scale_factor = target_height / original_height
            scaled_width = int(original_width * scale_factor)
            x_center = scaled_width // 2
            x1 = x_center - (target_width // 2)
            x2 = x_center + (target_width // 2)

            final_clip = clip.fx(resize.resize, height=target_height) \
                               .fx(crop.crop, x1=x1, y1=0, x2=x2, y2=target_height)

            final_clip.write_videofile(
                str(output_path),
                codec='libx264',
                fps=fps,
                threads=4,
                preset='fast',
                audio_codec='aac',
                ffmpeg_params=['-movflags', '+faststart']
            )
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании Shorts: {e}")
        return False

def process_video(video_url: str, split_into_segments: bool = False, segment_duration: int = 60):
    """Основная функция обработки видео."""
    input_path = download_video(video_url)
    if not input_path:
        logger.error("Не удалось скачать видео.")
        return

    if split_into_segments:
        segments = split_video(input_path, segment_duration)
        for segment in segments:
            output_path = output_dir / f"short_{segment.stem}.mp4"
            if create_short(segment, output_path):
                logger.info(f"Готовый Shorts сохранён: {output_path}")
    else:
        output_path = output_dir / f"short_{input_path.stem}.mp4"
        if create_short(input_path, output_path):
            logger.info(f"Готовый Shorts сохранён: {output_path}")

# Пример использования
video_url = 'https://www.youtube.com/watch?v=your_video_id'
process_video(video_url, split_into_segments=True, segment_duration=60)
