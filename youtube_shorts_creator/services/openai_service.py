import logging
import openai
from typing import List, Optional

from ..models.video_data import VideoAnalysis
from ..config.settings import settings

logger = logging.getLogger(__name__)

openai.api_key = settings.OPENAI_API_KEY

class OpenAIService:
    @staticmethod
    def analyze_transcript(transcript: str) -> Optional[VideoAnalysis]:
        """Анализ транскрипции с помощью OpenAI"""
        try:
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты помощник для анализа видео контента. "
                            "Выдели ключевые моменты и сгенерируй краткое содержание."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            "Проанализируй транскрипцию видео и:\n"
                            "1. Выдели 3-5 самых интересных моментов\n"
                            "2. Создай краткое содержание (до 100 слов)\n"
                            "3. Предложи 5 релевантных тегов\n\n"
                            f"Транскрипция:\n{transcript}"
                        )
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Парсинг ответа (можно улучшить)
            parts = content.split("\n\n")
            key_points = [p.strip() for p in parts[0].split("\n")[1:] if p.strip()]
            summary = parts[1].split(":")[1].strip() if len(parts) > 1 else None
            tags = [t.strip() for t in parts[2].split(",")] if len(parts) > 2 else None
            
            return VideoAnalysis(
                key_points=key_points,
                summary=summary,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Ошибка анализа транскрипции: {e}")
            return None