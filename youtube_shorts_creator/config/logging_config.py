import logging
from .settings import settings

def configure_logging():
    """Настройка логирования для приложения"""
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            # logging.FileHandler('app.log')  # Можно добавить запись в файл
        ]
    )