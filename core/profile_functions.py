import cProfile
import pstats
import io
import os
from pathlib import Path
from video_processor import VideoProcessor
from core import VideoCutter
from transcription.service import TranscriptService
from transcription.saver import TranscriptionSaver
from gpt_service import GPTService

def profile_function(func, *args, **kwargs):
    """
    Оборачивает вызов функции с профилированием и возвращает (результат, статистику).
    """
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()
    
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats("cumtime")
    stats.print_stats()
    return result, stream.getvalue()

def main():
    # Параметры для тестирования
    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    test_video_id = "mPG32p8oEnA"
    test_transcript_text = "00:00 - 00:10 Вступление\n00:10 - 00:30 Основная часть\n00:30 - 00:40 Заключение"
    gpt_api_key = "YOUR_OPENAI_API_KEY"  # Подставьте действительный ключ или используйте тестовый

    # Пример: профилирование функции скачивания видео
    vc = VideoCutter()
    # Если видео не нужно реально скачивать при тестировании, можно создать мок или использовать небольшой тестовый файл.
    download_result, download_stats = profile_function(vc.download_video, test_video_url)
    with open("download_video_profile.txt", "w", encoding="utf-8") as f:
        f.write(download_stats)

    # Пример: профилирование функции создания шортса
    # Для профилирования create_short предполагается, что у вас уже есть локальный файл видео
    test_input_path = Path("downloads") / f"{test_video_id}.mp4"
    if test_input_path.exists():
        short_result, short_stats = profile_function(vc.create_short, test_input_path, "test_short.mp4")
        with open("create_short_profile.txt", "w", encoding="utf-8") as f:
            f.write(short_stats)
    else:
        print("Тестовый видеофайл не найден для create_short.")

    # Пример: профилирование получения транскрипта
    saver = TranscriptionSaver()
    ts = TranscriptService(saver)
    transcript_result, transcript_stats = profile_function(ts._get_transcript, test_video_id, ['ru', 'en'], False)
    with open("get_transcript_profile.txt", "w", encoding="utf-8") as f:
        f.write(transcript_stats)

    # Пример: профилирование извлечения таймкодов с помощью GPTService
    gpt_service = GPTService(api_key=gpt_api_key)
    gpt_result, gpt_stats = profile_function(gpt_service.extract_timecodes, test_transcript_text)
    with open("extract_timecodes_profile.txt", "w", encoding="utf-8") as f:
        f.write(gpt_stats)

    # Итоговое сообщение
    print("Профилирование завершено. Результаты сохранены в следующие файлы:")
    print("  download_video_profile.txt")
    print("  create_short_profile.txt (если тестовый файл найден)")
    print("  get_transcript_profile.txt")
    print("  extract_timecodes_profile.txt")

if __name__ == "__main__":
    main()
