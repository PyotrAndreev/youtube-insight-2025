import pytest
from unittest.mock import patch
from core.transcription.saver import TranscriptionSaver

@pytest.fixture
def saver(tmp_path):
    return TranscriptionSaver(output_dir=str(tmp_path))

def test_save_transcription(saver, tmp_path):
    """Тест сохранения транскрипции"""
    with patch('core.transcription.saver.datetime') as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "041057"
        path = saver.save_transcription(
            video_id="test123",
            text="Test content",
            language="en"
        )
    
    assert path.exists()
    assert path.name.endswith("_en.txt")
    assert path.read_text() == "Test content"
