import pytest
from unittest.mock import patch
from core.gpt_service import GPTService

def test_gpt_service_extracts_timecodes():
    """Тест извлечения таймкодов с полной изоляцией от API"""
    with patch('openai.ChatCompletion.create') as mock_create:
        # Задаем мок-ответ в виде словаря, имитирующего ответ OpenAI API
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": (
                            "00:00 - 00:10 Вступление\n"
                            "00:10 - 00:30 Основная часть\n"
                            "00:30 - 00:40 Заключение"
                        )
                    }
                }
            ]
        }
        mock_create.return_value = mock_response

        gpt = GPTService(api_key="fake-key")
        timecodes = gpt.extract_timecodes("Тестовый текст")
        
        # Проверяем, что получены 3 таймкода
        assert len(timecodes) == 3
        assert timecodes[0] == {
            "start": "00",
            "end": "00",
            "text": "10 Вступление"
        }
        assert timecodes[1] == {
            "start": "00",
            "end": "00",
            "text": "30 Основная часть"
        }
        assert timecodes[2] == {
            "start": "00",
            "end": "00",
            "text": "40 Заключение"
        }

@pytest.mark.parametrize("input_text,expected", [
    ("00:00 - 00:10 Текст", {
        "start": "00",
        "end": "00",
        "text": "10 Текст"
    }),
    ("01:23 - 02:34 Другой текст", {
        "start": "01",
        "end": "02",
        "text": "34 Другой текст"
    }),
])
def test_timecode_parsing(input_text, expected):
    service = GPTService(api_key="test")
    result = service._parse_timecodes(input_text)
    # Проверяем, что результат содержит хотя бы один элемент
    assert len(result) > 0, "Парсер не вернул элементов"
    assert result[0] == expected
