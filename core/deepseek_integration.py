import os
import requests
import tempfile
import librosa
import soundfile as sf
from typing import List, Dict, Optional

class call_deepseek:
    """
    Сервис для работы с DeepSeek API: анализ всего аудио или отдельных сегментов.
    """

    def __init__(self,
                 api_key: Optional[str] = 'sk-d0d3c590942846278ce321946af2bbc9',
                 endpoint: Optional[str] = None,
                 timeout: int = 30):
        # Инициализация ключа и endpoint
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.endpoint = endpoint or 'https://api.deepseek.ai/process'
        self.timeout = timeout

    def _call_api(self, audio_path: str) -> Dict:
        """
        Отправить аудиофайл в DeepSeek и вернуть JSON-ответ.
        При ошибке возвращает пустой словарь.
        """
        try:
            with open(audio_path, 'rb') as f:
                files = {'audio': f}
                headers = {'X-API-Key': self.api_key}
                resp = requests.post(self.endpoint, files=files, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
                return resp.json()
        except requests.RequestException as e:
            # Логируем ошибку и возвращаем пустое значение
            print(f"DeepSeek API error for {audio_path}: {e}")
            return {}

    def analyze_full_audio(self, audio_path: str) -> List[Dict]:
        """
        Проанализировать весь аудиофайл и вернуть список популярных сегментов.
        Формат сегмента: {'start': float, 'end': float, 'score': float}
        """
        data = self._call_api(audio_path)
        return data.get('popular_segments', [])

    def analyze_segments(self,
                         audio_path: str,
                         transcript_segments: List[Dict]) -> List[Dict]:
        """
        Для каждого отрезка из транскрипта (список с 'start' и 'end')
        вырезает аудио и запрашивает DeepSeek, возвращает список сегментов с оценками.
        Каждый элемент: {'start': float, 'end': float, 'popularity_score': float}
        """
        results = []
        for seg in transcript_segments:
            start = float(seg.get('start', 0))
            end = float(seg.get('end', 0))
            # Вырезать сегмент в TMP файл
            try:
                y, sr = librosa.load(audio_path, sr=None, offset=start, duration=end-start)
                tmp_fd, tmp_path = tempfile.mkstemp(suffix='.wav')
                os.close(tmp_fd)
                sf.write(tmp_path, y, sr)
            except Exception as e:
                print(f"Error extracting audio segment {start}-{end}: {e}")
                continue

            # Запрос DeepSeek
            resp = self._call_api(tmp_path)
            score = resp.get('popularity_score', 0.0)
            # Удалить временный файл
            try:
                os.remove(tmp_path)
            except OSError:
                pass

            results.append({
                'start': start,
                'end': end,
                'popularity_score': score
            })
        return results
