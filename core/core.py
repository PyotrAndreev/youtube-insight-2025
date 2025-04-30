import logging
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Optional
from moviepy.editor import VideoFileClip
from moviepy.video.fx import resize
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        self.output_dir = Path(output_dir)
        self.download_dir = Path(download_dir)
        self.segments_dir = Path(segments_dir)
        self.target_width, self.target_height = target_resolution
        self.max_duration = max_duration
        self.ffmpeg_path = ffmpeg_path

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.segments_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)
        self.events: List[dict] = []

    @measure_sync_time
    def download_video(self, video_url: str) -> Optional[Path]:
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

    @measure_sync_time
    def split_video(self, input_path: Path, segment_duration: int = 60) -> List[Path]:
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

    @measure_sync_time
    def create_short(self, input_path: Path, output_name: str = None,
                    start_time: float = 0, end_time: Optional[float] = None,
                    clip_text: Optional[str] = None) -> Optional[Path]:
        if not output_name:
            output_name = f"short_{input_path.stem}.mp4"

        output_path = self.output_dir / output_name

        try:
            with VideoFileClip(str(input_path)) as clip:
                if end_time is not None:
                    clip = clip.subclip(start_time, end_time)
                else:
                    clip = clip.subclip(start_time, start_time + self.max_duration)

                if clip.duration > self.max_duration:
                    clip = clip.subclip(0, self.max_duration)

                scale_factor = self.target_width / clip.size[0]
                new_height = int(clip.size[1] * scale_factor)

                resized_clip = clip.fx(resize.resize, width=self.target_width)

                top_padding = (self.target_height - new_height) // 2
                bottom_padding = self.target_height - new_height - top_padding

                final_clip = resized_clip.margin(
                    top=top_padding,
                    bottom=bottom_padding,
                    opacity=0,
                    color=(0, 0, 0)
                )

                clips = [final_clip]

                if clip_text:
                    # Создаем текстовый клип
                    txt_clip = TextClip(clip_text,
                                        fontsize=50,
                                        font="Arial-Bold",
                                        color="white",
                                        stroke_color="black",
                                        stroke_width=2)

                    txt_clip = txt_clip.set_duration(final_clip.duration)

                    # Бегущая строка: слева направо
                    txt_clip = txt_clip.set_position(lambda t: (
                        self.target_width - int(t * 300) % (self.target_width + txt_clip.w),
                        50
                    ))

                    clips.append(txt_clip)

                composite = CompositeVideoClip(clips, size=(self.target_width, self.target_height))

                composite.write_videofile(
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
        
    @measure_sync_time
    def process_video(
        self,
        video_url: str,
        split_into_segments: bool = False,
        segment_duration: int = 60
    ) -> List[Path]:
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

    def dump_events_to_file(self, filename: str = None):
        import json
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            filename = f"core_videocutter_events_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, indent=2, ensure_ascii=False)
        logger.info(f"События сохранены в файл: {filename}")
