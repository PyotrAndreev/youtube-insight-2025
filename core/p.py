from video_processor import VideoCutter

def test_video_processing():
    # Создаем экземпляр VideoCutter
    cutter = VideoCutter(
        output_dir="test_processed_shorts",
        download_dir="test_downloads",
        segments_dir="test_video_segments",
        target_resolution=(1080, 1920),
        max_duration=60  # Ограничиваем длину короткого видео
    )

    video_url = "https://www.youtube.com/watch?v=zPrwTpo4TiM&t=246s"  # Пример URL видео на YouTube

    # Обработка видео: скачивание, нарезка, создание шортсов
    shorts = cutter.process_video(video_url, split_into_segments=True, segment_duration=60)

    if shorts:
        print(f"Создано {len(shorts)} шортсов:")
        for short in shorts:
            print(f"→ {short}")
    else:
        print("Процесс обработки видео завершился с ошибкой.")

# Запуск теста
test_video_processing()
