import re
import time
import random
import psycopg2
import googleapiclient.discovery
from datetime import datetime, timedelta

# === Конфигурация ===
API_KEY = "AIzaSyA4__CEwYmsgaFqjmQ0epUntSUgWtNUffM"
DB_PARAMS = {
  "dbname": "postgres",
  "user": "postgres",
  "password": "penis",
  "host": "localhost",
  "port": "5432"
}

# Подключение к YouTube API
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)

# === Фильтры поиска ===
SEARCH_QUERIES = [
    "gaming", "music", "tech", "science", "football",
    "cars", "movies", "fashion", "news", "education"
]  # Случайные категории для поиска

def get_random_channels():
    """Ищет случайные популярные каналы на YouTube"""
    query = random.choice(SEARCH_QUERIES)  # Берём случайную тему

    request = youtube.search().list(
        part="snippet",
        type="channel",
        q=query,
        maxResults=5  # Берём 5 случайных каналов
    )
    response = request.execute()

    channels = []
    for item in response["items"]:
        channel_id = item["snippet"]["channelId"]
        channels.append(channel_id)

    return channels


def get_channel_info(channel_id):
    """Получает информацию о канале: название, описание, подписчиков."""
    request = youtube.channels().list(part="snippet,statistics", id=channel_id)
    response = request.execute()

    if response["items"]:
        item = response["items"][0]
        snippet = item["snippet"]
        statistics = item["statistics"]

        name = snippet["title"]
        description = snippet["description"]
        subscribers = int(statistics.get("subscriberCount", 0))

        return name, description, subscribers
    return None, None, None


def extract_contacts(text):
    """Извлекает email, ссылки и Telegram-аккаунты из текста."""
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    all_links = re.findall(r"https?://[^\s]+", text)

    telegram_links = [link for link in all_links if "t.me" in link or "telegram.me" in link]
    other_links = [link for link in all_links if link not in telegram_links]

    return emails, telegram_links, other_links


def save_to_db(data):
    """Сохраняет список данных в PostgreSQL."""
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    for record in data:
        cursor.execute("""
            INSERT INTO bloggers (channel_id, name, description, subscribers, emails, telegram_links, other_links)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (channel_id) 
            DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                subscribers = EXCLUDED.subscribers,
                emails = EXCLUDED.emails,
                telegram_links = EXCLUDED.telegram_links,
                other_links = EXCLUDED.other_links;
        """, record)

    conn.commit()
    cursor.close()
    conn.close()


def run_scraper():
    """Запускает сбор данных с ограничением по времени (4 часа)."""
    start_time = datetime.now()
    stop_time = start_time + timedelta(hours=4)  # Скрипт остановится через 4 часа

    while datetime.now() < stop_time:
        print("\n Поиск случайных YouTube-каналов...")
        channels = get_random_channels()
        all_data = []

        for channel_id in channels:
            name, description, subscribers = get_channel_info(channel_id)
            if not name or subscribers < 1_000_000:
                print(f" Пропущен {channel_id} ({subscribers} подписчиков)")
                continue  # Пропускаем, если подписчиков < 1 млн

            print(f" Найден канал: {name} ({subscribers} подписчиков)")

            emails, telegram_links, other_links = extract_contacts(description)
            all_data.append((channel_id, name, description, subscribers, emails, telegram_links, other_links))

        if all_data:
            save_to_db(all_data)
            print("Данные сохранены в БД!")

        print(" Ожидание перед следующим запросом...")
        time.sleep(random.randint(30, 60))  # Спим 30-60 сек, чтобы не забанили API

    print("\n 4 часа прошли! Скрипт завершён.")


if __name__ == "__main__":
    run_scraper()
