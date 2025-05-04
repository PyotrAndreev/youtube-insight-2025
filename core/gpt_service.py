import asyncio
import logging
import time
import re
import json
from typing import List, Dict

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Декораторы замеров ---
def measure_async_time(func):
    async def wrapper(self, *args, **kwargs):
        start = time.time()
        logger.info(f"[TIMER START] {func.__name__}")
        result = await func(self, *args, **kwargs)
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


class GPTServiceOllama:
    def __init__(self, model: str = "llama3"):
        self.model = model
        self.semaphore = asyncio.Semaphore(2)
        self.events: List[Dict] = []

    @measure_async_time
    async def _call_ollama(self, prompt: str) -> str:
        cmd = ["ollama", "run", self.model]
        print("==== ОТПРАВЛЯЕМ ПРОМПТ ====")
        print(prompt[:2000])
        print("===========================")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate(input=prompt.encode())
        if stderr:
            print(f"Ошибка Ollama: {stderr.decode()}")
        response = stdout.decode()
        print("==== ОТВЕТ МОДЕЛИ ====")
        print(response)
        print("======================")
        return response

    @measure_async_time
    async def _limited_call(self, prompt: str) -> str:
        async with self.semaphore:
            return await self._call_ollama(prompt)

    @measure_async_time
    async def extract_timecodes(
        self,
        transcript_text: str,
        popular_segments: List[Dict],
        batch_size: int = 2
    ) -> List[Dict]:
        """
        Анализ транскрипта и популярных аудиосегментов.
        Возвращает список таймкодов и описаний.
        """
        parts = self.split_transcript(transcript_text)
        timecodes: List[Dict] = []
        for i in range(0, len(parts), batch_size):
            batch = parts[i:i+batch_size]
            tasks = [
                self._limited_call(
                    self._build_prompt(part, popular_segments)
                )
                for part in batch
            ]
            results = await asyncio.gather(*tasks)
            for idx, response in enumerate(results):
                parsed = self._parse_timecodes(response)
                if not parsed:
                    print(f"[ВНИМАНИЕ] Парсер не нашёл таймкодов в ответе {i+idx+1}.")
                timecodes.extend(parsed)
            await asyncio.sleep(0.1)
        return timecodes

    @measure_sync_time
    def split_transcript(self, transcript: str, max_length: int = 2000) -> List[str]:
        return [transcript[i:i + max_length] for i in range(0, len(transcript), max_length)]

    @measure_sync_time
    def _build_prompt(
        self,
        transcript_text: str,
        popular_segments: List[Dict]
    ) -> str:
        segments_str = json.dumps(popular_segments, ensure_ascii=False)
        return (
            "Ты – эксперт по созданию вирусных видео. У тебя есть расшифровка (транскрипт) длинного видео и некоторые аудио-подсказки. Твоя задача – найти 2–3 фрагмента, которые можно вырезать в формат коротких видео (15–30 секунд) и которые наверняка понравятся зрителям и станут популярными.\n"

            "Виральные фрагменты – это моменты, которые вызывают сильный отклик у зрителя. Обращай внимание на:\n"  
            "- **Эмоции**: смех, удивление, восторг, шок, ярость в речи. Если в тексте есть слова вроде «невероятно», «я в шоке», или пометки [СМЕХ], [ОВАЦИИ], – это явные признаки.  \n"
            "- **Неожиданный поворот или инсайт**: что-то случилось внезапно, раскрылась интрига, прозвучала очень важная мысль.  \n"
            "- **Реакцию и энергичность**: герой повысил голос, сменил интонацию, аудитория ахнула или рассмеялась, заиграла драматичная музыка.\n"

            "Входные данные: транскрипт с указанием времени и пометками аудио (например, [СМЕХ], [Музыка]):\n"
            "Формат вывода (каждая строка):\n"
            "<мм:сс> - <мм:сс> Описание момента\n\n"
            "Проанализируй транскрипт и аудио-сигналы и выбери **три лучших момента** (укажи таймкоды начала и конца каждого). Каждый выбор обоснуй: чем этот фрагмент способен «зацепить» зрителя (эмоция, юмор, шок или инсайт).\n\n"
            f"{transcript_text}"
        )

    @measure_sync_time
    def _parse_timecodes(self, gpt_response: str) -> List[Dict]:
        timecodes: List[Dict] = []
        pattern = r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s+(.+)"
        for line in gpt_response.splitlines():
            match = re.match(pattern, line.strip())
            if match:
                start, end, text = match.groups()
                timecodes.append({
                    "start": start.strip(),
                    "end": end.strip(),
                    "text": text.strip()
                })
        return timecodes

    def dump_events_to_file(self, filename: str = None):
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            filename = f"gpt_events_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, indent=2, ensure_ascii=False)
        logger.info(f"События сохранены в файл: {filename}")
