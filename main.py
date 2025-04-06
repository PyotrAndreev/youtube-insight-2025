import sys
from pathlib import Path

# Добавляем папку проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from youtube_shorts_creator import YouTubeShortsCreator

if __name__ == "__main__":
    try:
        creator = YouTubeShortsCreator()
        creator.process_video("dQw4w9WgXcQ")  # Пример ID видео
    except Exception as e:
        print(f"Ошибка: {e}")