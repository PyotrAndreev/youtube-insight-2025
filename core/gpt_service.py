import asyncio
import re
from typing import List, Dict

class GPTServiceOllama:
    def __init__(self, model: str = "llama3"):
        self.model = model
        self.semaphore = asyncio.Semaphore(3)

    async def _call_ollama(self, prompt: str) -> str:
        cmd = [
            "ollama", "run", self.model,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate(input=prompt.encode())

        if stderr:
            print(f"Ошибка Ollama: {stderr.decode()}")

        return stdout.decode()

    async def _limited_call(self, prompt: str) -> str:
        async with self.semaphore:
            return await self._call_ollama(prompt)

    async def extract_timecodes(self, transcript_text: str) -> List[Dict]:
        parts = self.split_transcript(transcript_text)
        tasks = []

        for part in parts:
            prompt = self._build_prompt(part)
            tasks.append(self._limited_call(prompt))

        responses = await asyncio.gather(*tasks)

        timecodes = []
        for response in responses:
            timecodes.extend(self._parse_timecodes(response))

        return timecodes

    def split_transcript(self, transcript: str, max_length: int = 2000) -> List[str]:
        return [transcript[i:i + max_length] for i in range(0, len(transcript), max_length)]

    def _build_prompt(self, transcript_text: str) -> str:
        return (
            "Ты — эксперт по созданию вирусных YouTube Shorts.\n"
            "Проанализируй транскрипт видео и найди самые вовлекающие моменты.\n"
            "Формат вывода:\n"
            "00:30 - 01:00 Шокирующее признание\n"
            "01:10 - 01:50 Смешной момент\n\n"
            "Вот транскрипт:\n\n"
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
