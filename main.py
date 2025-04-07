import sys
from pathlib import Path
from youtube_shorts_creator import YouTubeShortsCreator

if __name__ == "__main__":
    # Добавляем папку проекта в PYTHONPATH
    sys.path.append(str(Path(__file__).parent))
    
    try:
        creator = YouTubeShortsCreator()
        video_id = "dQw4w9WgXcQ"  # Пример ID видео
        print(f"Начинаем обработку видео {video_id}...")
        
        # Обработка видео
        success, message = creator.process_video(video_id)
        
        if success:
            print(f"Успешно завершено: {message}")
        else:
            print(f"Ошибка: {message}")
            
    except Exception as e:
        print(f"Критическая ошибка: {e}")