import pytest
import sys
print(sys.path)

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


from unittest.mock import patch, MagicMock
from core.transcription.service import TranscriptService

@pytest.fixture
def service():
    return TranscriptService()

@patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript')
def test_get_transcript_success(mock_get, service):
    """Тест успешного получения транскрипции"""
    mock_get.return_value = [{'text': 'test', 'start': 0, 'duration': 1}]
    result = service._get_transcript("test_video", ['en'], preserve_formatting=True)
    assert result[0]['text'] == 'test'

@patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript')
def test_get_transcript_disabled(mock_get, service):
    """Тест случая отключенной транскрипции"""
    mock_get.side_effect = Exception("Transcript disabled")
    result = service._get_transcript("test_video", ['en'], preserve_formatting=False)
    assert result is None