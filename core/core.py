import logging
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
from moviepy.editor import VideoFileClip
from moviepy.video.fx import resize, crop

class VideoCutter:
    """Класс для нарезки и обработки видео."""
    
    def __init__(
        self,
        output_dir: str = "processed_shorts",
        download_dir: str = "downloads",
        segments_dir: str = "video_segments",
        target_resolution: Tuple[int, int] = (1080, 1920),
        max_duration: int = 60,
        ffmpeg_path: str = "ffmpeg"
    ):
        """
        Инициализация VideoCutter.
        
        :param output_dir: Папка для сохранения обработанных видео
        :param download_dir: Папка для загруженных видео
        :param segments_dir: Папка для сегментов видео
        :param target_resolution: Целевое разрешение (ширина, высота)
        :param max_duration: Максимальная длительность Shorts (в секундах)
        :param ffmpeg_path: Путь к ffmpeg
        """
        self.output_dir = Path(output_dir)
        self.download_dir = Path(download_dir)
        self.segments_dir = Path(segments_dir)
        self.target_width, self.target_height = target_resolution
        self.max_duration = max_duration
        self.ffmpeg_path = ffmpeg_path
        
        # Создаем необходимые директории
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.segments_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)

    def download_video(self, video_url: str) -> Optional[Path]:
        """Скачивает видео с YouTube."""
        try:
            from yt_dlp import YoutubeDL
            
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': str(self.download_dir / '%(id)s.%(ext)s'),
                'quiet': True,
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                return Path(ydl.prepare_filename(info))
                
        except Exception as e:
            self.logger.error(f"Ошибка при скачивании видео: {e}")
            return None

    def split_video(self, input_path: Path, segment_duration: int = 60) -> List[Path]:
        """Разделяет видео на сегменты."""
        output_template = str(self.segments_dir / f"{input_path.stem}-%03d{input_path.suffix}")
        
        cmd = [
            self.ffmpeg_path,
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
            return list(self.segments_dir.glob(f"{input_path.stem}-*{input_path.suffix}"))
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Ошибка при разделении видео: {e}")
            return []

    def create_short(self, input_path: Path, output_name: str = None, 
                     start_time: float = 0, end_time: Optional[float] = None) -> Optional[Path]:
        """Создает вертикальное видео Shorts с горизонтальным контентом и черными полосами."""
        if not output_name:
            output_name = f"short_{input_path.stem}.mp4"
            
        output_path = self.output_dir / output_name

        try:
            with VideoFileClip(str(input_path)) as clip:
                if end_time is not None:
                    clip = clip.subclip(start_time, end_time)
                else:
                    clip = clip.subclip(start_time, start_time + self.max_duration)
                # Ограничиваем длительность
                if clip.duration > self.max_duration:
                    clip = clip.subclip(0, self.max_duration)

                # Масштабируем по ширине (чтобы занять всю ширину 1080)
                scale_factor = self.target_width / clip.size[0]
                new_height = int(clip.size[1] * scale_factor)

                resized_clip = clip.fx(resize.resize, width=self.target_width)

                # Добавим черные полосы сверху и снизу
                top_padding = (self.target_height - new_height) // 2
                bottom_padding = self.target_height - new_height - top_padding

                final_clip = resized_clip.margin(
                    top=top_padding,
                    bottom=bottom_padding,
                    opacity=0,  # 0 = черный фон
                    color=(0, 0, 0)
                )

                final_clip = final_clip.set_position("center")

                final_clip.write_videofile(
                    str(output_path),
                    codec='libx264',
                    fps=clip.fps,
                    threads=4,
                    preset='fast',
                    audio_codec='aac',
                    ffmpeg_params=['-movflags', '+faststart']
                )

            return output_path

        except Exception as e:
            self.logger.error(f"Ошибка при создании Shorts: {e}")
            return None

    def process_video(
        self,
        video_url: str,
        split_into_segments: bool = False,
        segment_duration: int = 60
    ) -> List[Path]:
        """Основной метод обработки видео."""
        input_path = self.download_video(video_url)
        if not input_path:
            return []
            
        results = []
        
        if split_into_segments:
            segments = self.split_video(input_path, segment_duration)
            for segment in segments:
                output_path = self.create_short(segment)
                if output_path:
                    results.append(output_path)
        else:
            output_path = self.create_short(input_path)
            if output_path:
                results.append(output_path)
                
        return results
    