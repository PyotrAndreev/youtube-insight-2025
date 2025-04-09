import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Settings:
    YOUTUBE_API_KEY = os.getenv("AIzaSyARXkfx4Ib7ZrP7mISQDwrQpXzKswJGBAc")
    OPENAI_API_KEY = os.getenv("XeSmy70BeVFgjsdxLUhAqG5rwJWy0ak3drQoNuJTixN0uznBBrhnqm15yAT3BlbkFJITD0J8THsacZEoAf3AsECShT2H3EXHZsnQEkGu7go2DZ12eifwI8ZdJJxfQsriBlHhgHosglEA")
    FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        if not cls.YOUTUBE_API_KEY:
            raise ValueError("YOUTUBE_API_KEY не установлен")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY не установлен")

settings = Settings()
