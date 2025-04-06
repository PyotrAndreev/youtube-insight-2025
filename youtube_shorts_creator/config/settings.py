import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Settings:
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        if not cls.YOUTUBE_API_KEY:
            raise ValueError("YOUTUBE_API_KEY не установлен")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY не установлен")

settings = Settings()