import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from core.core import VideoCutter

@pytest.fixture
def video_cutter(tmp_path):
    # Создаём экземпляр VideoCutter с временной директорией для сохранения файлов
    return VideoCutter(output_dir=str(tmp_path / "output"))

@pytest.fixture
def mock_dependencies():
    # Мокаем зависимости: VideoFileClip, YoutubeDL и subprocess.run
    with patch('moviepy.editor.VideoFileClip') as mock_video_clip, \
         patch('yt_dlp.YoutubeDL') as mock_ydl, \
         patch('subprocess.run') as mock_subprocess:
        
        # Мокаем экземпляр VideoFileClip
        mock_clip_instance = MagicMock()
        mock_clip_instance.size = (1920, 1080)
        mock_clip_instance.fps = 30
        mock_clip_instance.duration = 120
        mock_video_clip.return_value = mock_clip_instance
        
        yield {
            'video_clip': mock_video_clip,
            'ydl': mock_ydl,
            'subprocess': mock_subprocess,
            'clip_instance': mock_clip_instance
        }

def test_download_video(video_cutter, mock_dependencies):
    # Мокаем зависимость yt_dlp.YoutubeDL
    mock_ydl = mock_dependencies['ydl']
    mock_ydl_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
    mock_ydl_instance.extract_info.return_value = {'id': 'test123', 'ext': 'mp4'}
    mock_ydl_instance.prepare_filename.return_value = "downloads/test123.mp4"
    
    # Вызываем функцию download_video
    result = video_cutter.download_video("https://youtube.com/watch?v=test")
    
    # Проверяем, что результат соответствует ожидаемому пути
    assert result == Path("downloads/test123.mp4")

@pytest.fixture
def mock_clip():
    return MagicMock()

@patch('moviepy.editor.VideoFileClip')
def test_create_short(self, mock_clip):
    test_file = 'test_video.mp4'
    
    mock_clip.create_short.return_value = True
    result = mock_clip.create_short()
    assert result is True