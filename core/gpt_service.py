import subprocess
from typing import List, Dict

class GPTServiceOllama:
    def __init__(self, model: str = "llama3"):
        self.model = model

    def extract_timecodes(self, transcript_text: str) -> List[Dict]:
        """
        Извлекает таймкоды из транскрипта с помощью локальной модели Ollama.
        """
        prompt = self._build_prompt(transcript_text)

        try:
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt.encode("utf-8"),
                capture_output=True,
                timeout=60  # на всякий случай
            )
            content = result.stdout.decode("utf-8")
            return self._parse_timecodes(content)
        except Exception as e:
            print(f"[Ollama] Ошибка при извлечении таймкодов: {e}")
            return []

    def _build_prompt(self, transcript_text: str) -> str:
        return (
            "Ты — эксперт по YouTube Shorts.\n"
            "на основе транскрипта интервью выдели интересные моменты.\n"
            "Формат вывода:\n"
            "00:00 - 00:10 Вступление\n"
            "00:10 - 00:25 Интересный момент про карьеру\n"
            "00:25 - 00:35 Шутка\n"
            "Используй такой формат строго! Вот текст:\n\n"
            f"{transcript_text}"
        )

    def _parse_timecodes(self, gpt_response: str) -> List[Dict]:
        timecodes = []
        for line in gpt_response.splitlines():
            line = line.strip()
            if not line or " - " not in line:
                continue
            left, right = line.split(" - ", 1)
            left_tokens = left.split(":")
            if not left_tokens:
                continue
            start = left_tokens[0]

            right_tokens = right.split(" ", 1)
            if len(right_tokens) < 2:
                continue
            time_token = right_tokens[0]
            description = right_tokens[1]
            time_token_parts = time_token.split(":")
            if not time_token_parts:
                continue
            end = time_token_parts[0]
            remainder = " ".join(time_token_parts[1:]).strip()
            text = (remainder + " " + description).strip()
            timecodes.append({
                "start": start,
                "end": end,
                "text": text
            })
        return timecodes
