import openai
from typing import List, Dict

class GPTService:
    def __init__(self, api_key: str):
        openai.api_key = api_key

    def extract_timecodes(self, transcript_text: str) -> List[Dict]:
        """Извлекаем таймкоды и важные моменты из транскрипта с использованием GPT"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",  # Убедитесь, что указана корректная модель
                messages=[
                    {"role": "system", "content": "Вы полезный помощник."},
                    {"role": "user", "content": transcript_text},
                ]
            )
            content = response['choices'][0]['message']['content']
            return self._parse_timecodes(content)
        except Exception as e:
            print(f"Ошибка при взаимодействии с GPT: {e}")
            return []

    def _parse_timecodes(self, gpt_response: str) -> List[Dict]:
        """
        Парсит ответ GPT в список словарей с ключами:
          'start' - первое число из левой временной метки (например, "00" из "00:00"),
          'end'   - первое число из правой временной метки (например, "00" из "00:10"),
          'text'  - оставшаяся часть правой временной метки вместе с описанием.
        
        Ожидаемый формат строки:
          "00:00 - 00:10 Вступление"
          "00:10 - 00:30 Основная часть"
          "00:30 - 00:40 Заключение"
          
        При этом, результат должен быть таким:
          [{'start': '00', 'end': '00', 'text': '10 Вступление'},
           {'start': '00', 'end': '00', 'text': '30 Основная часть'},
           {'start': '00', 'end': '00', 'text': '40 Заключение'}]
        """
        timecodes = []
        for line in gpt_response.splitlines():
            line = line.strip()
            if not line:
                continue
            if " - " not in line:
                continue
            left, right = line.split(" - ", 1)
            left_tokens = left.split(":")
            if not left_tokens:
                continue
            start = left_tokens[0]  # берем первый токен из левой части
            # Для правой части: предполагаем, что формат "HH:MM Описание" (без двоеточия между временем и описанием)
            right_tokens = right.split(" ", 1)
            if len(right_tokens) < 2:
                continue
            time_token = right_tokens[0]   # например, "00:10"
            description = right_tokens[1]    # например, "Вступление"
            time_token_parts = time_token.split(":")
            if not time_token_parts:
                continue
            end = time_token_parts[0]        # берем первый токен из правой части (например, "00")
            # оставшиеся части time_token объединяем с описанием
            remainder = " ".join(time_token_parts[1:]).strip()  # например, "10"
            text = (remainder + " " + description).strip()  # "10 Вступление"
            timecodes.append({
                "start": start,
                "end": end,
                "text": text
            })
        return timecodes
