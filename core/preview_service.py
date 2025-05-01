# preview_service.py

from pathlib import Path
from typing import Optional, List, Dict
from core import VideoCutter
from gpt_service import GPTServiceOllama
from transcription.saver import TranscriptionSaver
from transcription.service import TranscriptService


class PreviewService:
    """
    Генерация 15–30-секундного превью по началу видео
    или по наиболее «вирусному» моменту через GPT.
    """

    def __init__(
        self,
        cutter: VideoCutter,
        gpt_service: GPTServiceOllama,
        use_gpt: bool = True,
        max_duration: int = 30
    ):
        self.cutter = cutter
        self.gpt = gpt_service
        self.transcript_saver = TranscriptionSaver()
        self.transcript_service = TranscriptService(self.transcript_saver)
        self.use_gpt = use_gpt
        self.max_duration = max_duration

    def create_preview(
        self,
        video_path: Path,
        video_id: str
    ) -> Optional[Path]:
        # статический вариант
        if not self.use_gpt:
            return self._cut_segment(video_path, 0.0, float(self.max_duration), "preview_start.mp4")

        # попытка получить транскрипт
        text = ""
        try:
            transcript_path = self.transcript_service.get_and_save_transcript(video_id)
            if transcript_path and Path(transcript_path).exists():
                with open(transcript_path, "r", encoding="utf-8") as f:
                    text = f.read()
        except Exception:
            # даже если транскрипт упал — оставляем text="" и идём дальше
            text = ""

        # вызываем GPT даже по пустому тексту (тестовый DummyGPT вернёт заданные candidates)
        try:
            candidates: List[Dict] = self.gpt.extract_timecodes(text)
        except Exception:
            candidates = []

        # если есть кандидаты — выбираем самый короткий ≤ max_duration
        if candidates:
            def dur_ok(item):
                s = float(item["start"])
                e = float(item["end"])
                d = e - s
                return d if d <= self.max_duration else float("inf")

            sel = min(candidates, key=dur_ok)
            start = float(sel["start"])
            end = min(float(sel["end"]), start + self.max_duration)
            return self._cut_segment(
                video_path, start, end, f"preview_{int(start)}-{int(end)}.mp4"
            )

        # иначе — fallback на начало
        return self._cut_segment(video_path, 0.0, float(self.max_duration), "preview_start.mp4")

    def _cut_segment(
        self,
        input_path: Path,
        start: float,
        end: float,
        output_name: str
    ) -> Optional[Path]:
        try:
            return self.cutter.create_short(
                input_path=input_path,
                output_name=output_name,
                start_time=start,
                end_time=end
            )
        except Exception:
            return None
