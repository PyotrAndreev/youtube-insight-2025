import subprocess
import re
from typing import List, Dict

class GPTServiceOllama:
    def __init__(self, model: str = "llama3"):
        self.model = model

    def extract_timecodes(self, transcript_text: str) -> List[Dict]:
        parts = self.split_transcript(transcript_text)

        timecodes = []
        for part in parts:
            prompt = self._build_prompt(part)
            try:
                print(f"Обрабатываем часть текста (длина: {len(part)} символов)...")
                result = subprocess.run(
                    ["ollama", "run", self.model],
                    input=prompt.encode("utf-8"),
                    capture_output=True,
                    timeout=360
                )
                content = result.stdout.decode("utf-8")
                print(f"Ответ от Ollama: {content[:500]}...")
                timecodes.extend(self._parse_timecodes(content))
            except subprocess.TimeoutExpired:
                print("[Ollama] Превышено время ожидания.")
            except subprocess.CalledProcessError as e:
                print(f"[Ollama] Ошибка в процессе: {e}")
            except Exception as e:
                print(f"[Ollama] Ошибка: {e}")
        return timecodes

    def _build_prompt(self, transcript_text: str) -> str:
        return (
            "Ты — эксперт по созданию вирусных YouTube Shorts.\n"
            "фраза должна быть завершенной"
            "Проанализируй транскрипт видео и найди самые вовлекающие и интересные моменты, "
            "которые можно вырезать как отдельные шортсы.\n\n"
            "Критерии отбора:\n"
            "- Длительность от 30 до 60 секунд\n"
            "- Вовлечённость: эмоции, юмор, резонансные темы, неожиданные повороты, сильные высказывания\n"
            "- Самодостаточность: каждый момент должен быть логически завершённым и понятным без контекста\n\n"
            "Формат вывода строго такой:\n"
            "00:30 - 01:00 Шокирующее признание\n"
            "01:10 - 01:50 Смешной момент с реакцией\n"
            "02:00 - 02:45 Сильная мотивационная речь\n\n"
            "Вот транскрипт видео:\n\n"
            f"{transcript_text}"
        )


    def _parse_timecodes(self, gpt_response: str) -> List[Dict]:
        timecodes = []
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

    def split_transcript(self, transcript: str, max_length: int = 2000) -> List[str]:
        return [transcript[i:i + max_length] for i in range(0, len(transcript), max_length)]
