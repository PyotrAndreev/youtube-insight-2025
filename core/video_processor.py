from transcription.service import TranscriptService
from core import VideoCutter
from transcription.saver import TranscriptionSaver
from typing import List, Optional, Dict
from gpt_service import GPTServiceOllama
from transcription.service import TranscriptService

import sys
import os

project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_path not in sys.path:
    sys.path.insert(0, project_path)



class VideoProcessor:
    """Класс для обработки видео: транскрибирование, обработка с GPT, нарезка на шорты"""
    
    def __init__(self, video_url: str, gpt_service, segment_duration: int = 60):
        """
        Инициализация VideoProcessor
        
        :param video_url: Ссылка на видео
        :param gpt_service: Экземпляр сервиса GPT для анализа транскрипта
        :param segment_duration: Продолжительность сегментов для нарезки
        """
        self.video_url = video_url
        self.gpt_service = gpt_service
        self.segment_duration = segment_duration
        
        # Сервисы
        self.transcription_saver = TranscriptionSaver()
        self.transcript_service = TranscriptService(self.transcription_saver)
        self.video_cutter = VideoCutter()
    
    def process(self) -> List[Optional[str]]:
        """Основной метод обработки видео"""
        video_id = self._extract_video_id(self.video_url)
        
        # Шаг 1: Получаем транскрипт
        transcript_file_path = self.get_transcript(video_id)
        if not transcript_file_path:
            return []
        
        # Шаг 2: Отправляем транскрипт в GPT для получения таймкодов
        timecodes = self.process_transcript_with_gpt(transcript_file_path)
        
        # Шаг 3: Нарезаем видео на шорты
        return self.cut_video(timecodes)
    
    def _extract_video_id(self, video_url: str) -> str:
        """Извлекаем ID видео из URL"""
        return video_url.split("v=")[-1]
    
    def get_transcript(self, video_id: str) -> Optional[str]:
        """Получаем транскрипт видео"""
        try:
            return self.transcript_service.get_and_save_transcript(video_id)
        except Exception as e:
            print(f"Ошибка при получении транскрипта: {e}")
            return None
    
    def process_transcript_with_gpt(self, transcript_file_path: str) -> List[Dict]:
        """Обрабатываем транскрипт с использованием GPT для извлечения таймкодов"""
        try:
            with open(transcript_file_path, 'r', encoding='utf-8') as file:
                transcript_text = file.read()
            
            # Используем GPT-сервис для извлечения таймкодов
            timecodes = self.gpt_service.extract_timecodes(transcript_text)
            return timecodes
        except Exception as e:
            print(f"Ошибка при обработке транскрипта с GPT: {e}")
            return []
    
    def cut_video(self, timecodes: List[Dict]) -> List[Optional[str]]:
        """Нарезаем видео по таймкодам, полученным от GPT"""
        output_paths = []
        
        for timecode in timecodes:
            start_time = timecode["start"]
            end_time = timecode["end"]
            clip_text = timecode["text"]
            
            # Создаем новый файл шорта для каждого таймкода
            output_path = self.video_cutter.create_short(
                input_path=self.video_url,  # Это должно быть скачанное видео
                output_name=f"short_{start_time}-{end_time}.mp4"
            )
            if output_path:
                output_paths.append(output_path)
        
        return output_paths


# Функция main, запускающая весь процесс:
def main():
    
    # Укажите URL видео для обработки
    video_url = "https://www.youtube.com/watch?v=6tSIkOL3uBI"
    # Укажите ваш API-ключ для OpenAI
    gpt_api_key = os.environ.get("OPENAI_API_KEY")
    # Инициализируем GPT-сервис
    gpt_service = GPTServiceOllama()
    
    # Создаем процессор видео
    processor = VideoProcessor(video_url, gpt_service)
    
    # Запускаем процесс обработки
    shorts = processor.process()
    
    if shorts:
        print("Созданы следующие шортсы:")
        for clip in shorts:
            print(clip)
    else:
        print("Процесс обработки видео завершился с ошибкой.")

if __name__ == "__main__":
    main()