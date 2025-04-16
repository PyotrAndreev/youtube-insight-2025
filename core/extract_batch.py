import os
import json
from typing import List, Dict
from gpt_service import GPTServiceOllama

TRANSCRIPTS_DIR = "transcriptions"  # Папка с транскриптами
OUTPUT_SUFFIX = "_timecodes.json"  # Суффикс для файлов с результатами

def read_transcript(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def save_timecodes(output_path: str, timecodes: List[Dict]):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(timecodes, f, ensure_ascii=False, indent=2)

def process_all_transcripts():
    service = GPTServiceOllama()
    for filename in os.listdir(TRANSCRIPTS_DIR):
        if not filename.endswith(".txt"):
            continue

        input_path = os.path.join(TRANSCRIPTS_DIR, filename)
        output_path = os.path.join(
            TRANSCRIPTS_DIR,
            filename.replace(".txt", OUTPUT_SUFFIX)
        )

        print(f"Обработка файла: {filename}")
        transcript = read_transcript(input_path)
        timecodes = service.extract_timecodes(transcript)
        save_timecodes(output_path, timecodes)
        print(f"Сохранено: {output_path}")

if __name__ == "__main__":
    process_all_transcripts()
