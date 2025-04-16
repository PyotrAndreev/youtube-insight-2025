import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.video_processor import VideoCutter

def test_process_youtube_video():
    cutter = VideoCutter(
        output_dir="test_outputs",
        download_dir="test_downloads",
        segments_dir="test_segments",
        max_duration=30  # ограничим длину ролика
    )

    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # можешь заменить на свой

    results = cutter.process_video(
        video_url=test_url,
        split_into_segments=False
    )

    if results:
        print(f"Успешно создано {len(results)} видео:")
        for path in results:
            print("→", path)
    else:
        print("Обработка завершилась без результата.")
