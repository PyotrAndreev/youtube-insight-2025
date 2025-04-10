import re
import os
import psycopg2
import googleapiclient.discovery
import googleapiclient.errors
import time

# === Конфигурация ===
API_KEYS = [
    "AIzaSyCgD1sEnkyE1Y2HiUbvLAhcGTQmoVxHgEM",
    "AIzaSyArCq3wAS8YREs7ME2zO2NHBseOPk3hW68",
    "AIzaSyC6rje03dcBKNPQn9FHbYS8m2sqdyA1gFs",
    "AIzaSyBf2tAVKLoACIietQcSW420mK01xxoC3Yo",
    "AIzaSyDEsT3VsJqPDeoxxgxBvSN6sBacbcEt35o",
    "AIzaSyA4__CEwYmsgaFqjmQ0epUntSUgWtNUffM",
    "AIzaSyAOO8lfBWlWMugxbix8dn4SuA1oQNLveFI"
]
DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "klon",
    "host": "localhost",
    "port": "5432"
}

# Файл для хранения обработанных channel_id
CACHE_FILE = "processed_ids.txt"

# Функция для загрузки кэша из файла
def load_processed_ids():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

# Функция для сохранения нового channel_id в файл
def append_processed_id(channel_id):
    with open(CACHE_FILE, "a", encoding="utf-8") as f:
        f.write(channel_id + "\n")

# Загружаем ранее обработанные channel_id
processed_ids = load_processed_ids()

# Подключение к YouTube API
def build_youtube_api(api_key):
    return googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

# Получение списка каналов с более чем 1 миллион подписчиков
def get_channels_with_min_subscribers(youtube, min_subscribers=1000000):
    channels = []
    request = youtube.search().list(
        part="snippet",
        type="channel",
        maxResults=5
    )
    try:
        while request:
            response = request.execute()
            for item in response.get("items", []):
                channel_id = item["snippet"]["channelId"]
                channel_name = item["snippet"]["channelTitle"]
                channel_subscribers = get_channel_subscriber_count(youtube, channel_id)
                if channel_subscribers >= min_subscribers:
                    channels.append({
                        "id": channel_id,
                        "name": channel_name,
                        "subscribers": channel_subscribers,
                        "description": item["snippet"].get("description", ""),
                        "handle": item["snippet"].get("channelTitle", "")
                    })
            request = youtube.search().list_next(request, response)
        print(f"Найдено {len(channels)} каналов.")
        return channels
    except googleapiclient.errors.HttpError as e:
        print(f"Ошибка при запросе данных YouTube API: {e}")
        return channels

# Получение количества подписчиков канала
def get_channel_subscriber_count(youtube, channel_id):
    try:
        request = youtube.channels().list(
            part="statistics",
            id=channel_id
        )
        response = request.execute()
        if response.get("items"):
            return int(response["items"][0]["statistics"].get("subscriberCount", 0))
    except googleapiclient.errors.HttpError as e:
        print(f"Ошибка при получении статистики для {channel_id}: {e}")
    return 0

# Извлечение контактов (email, Telegram ссылки и другие ссылки)
def extract_contacts(text):
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    all_links = re.findall(r"https?://[^\s]+", text)
    telegram_links = [link for link in all_links if "t.me" in link or "telegram.me" in link]
    other_links = [link for link in all_links if link not in telegram_links]
    return emails, telegram_links, other_links

# Сохранение данных канала в базу данных
def save_to_db(channel_id, handle, name, description, subscribers, emails, telegram_links, other_links):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bloggers (channel_id, handle, name, description, subscribers, emails, telegram_links, other_links)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (channel_id)
            DO UPDATE SET
                handle = EXCLUDED.handle,
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                subscribers = EXCLUDED.subscribers,
                emails = EXCLUDED.emails,
                telegram_links = EXCLUDED.telegram_links,
                other_links = EXCLUDED.other_links;
        """, (channel_id, handle, name, description, subscribers, emails, telegram_links, other_links))

        conn.commit()
        cursor.close()
        conn.close()
        print(f"Данные канала {name} успешно сохранены в базу данных.")
    except Exception as e:
        print(f"Ошибка при сохранении данных канала {name}: {e}")
# Обработка всех API ключей
def analyze_youtube(api_keys):
    for api_key in api_keys:
        youtube = build_youtube_api(api_key)
        try:
            channels = get_channels_with_min_subscribers(youtube)
            for channel in channels:
                emails, telegram_links, other_links = extract_contacts(channel["description"])
                save_to_db(
                    channel["id"], 
                    channel["handle"], 
                    channel["name"], 
                    channel["description"], 
                    channel["subscribers"], 
                    emails, 
                    telegram_links, 
                    other_links
                )
                print(f"Сохранен канал: {channel['name']} с {channel['subscribers']} подписчиков.")
            # Задержка между переключением ключей для снижения нагрузки на квоту
            time.sleep(60)
        except googleapiclient.errors.HttpError as e:
            print(f"Ошибка API для ключа {api_key}: {e}")
            continue

if __name__ == "__main__":
    analyze_youtube(API_KEYS)