import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from youtube_shorts_creator import YouTubeShortsCreator

if __name__ == "__main__":
    creator = YouTubeShortsCreator()
    result_path = creator.process_video("mPG32p8oEnA")
    
    if result_path:
        print(f" Готовый Shorts сохранён по пути:\n{result_path}")
        print("Откройте этот файл в медиаплеере или загрузите в YouTube")
    else:
        print(" Не удалось создать Shorts")
