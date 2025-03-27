import re
import psycopg2
import googleapiclient.discovery

# === Конфигурация ===
API_KEY = "AIzaSyA4__CEwYmsgaFqjmQ0epUntSUgWtNUffM"
DB_PARAMS = {
  "dbname": "your_db_name",
  "user": "your_db_user",
  "password": "your_db_password",
  "host": "localhost",
  "port": "5432"
}

# Подключение к YouTube API
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)


def get_channel_id_by_handle(handle):
  """Получает ID канала по его хэндлу (@username)."""
  if not handle.startswith("@"):
    return None

  request = youtube.search().list(
      part="snippet",
      type="channel",
      q=handle,
      maxResults=1
  )
  response = request.execute()
  if response["items"]:
    return response["items"][0]["snippet"]["channelId"]
  return None


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


def save_to_db(channel_id, handle, name, description, subscribers, emails, telegram_links, other_links):
  """Сохраняет данные в PostgreSQL."""
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


def analyze_youtube(channel_handle_or_id):
  """Анализирует YouTube-канал и сохраняет в БД."""
  print(f"\n Анализируем: {channel_handle_or_id}")

  # Если передали @handle, получаем ID
  if channel_handle_or_id.startswith("@"):
    print("Ищем ID канала по хэндлу...")
    channel_id = get_channel_id_by_handle(channel_handle_or_id)
    if not channel_id:
      print("Не удалось найти канал.")
      return
  else:
    channel_id = channel_handle_or_id

  # Получаем данные канала
  name, description, subscribers = get_channel_info(channel_id)
  if not name:
    print("Канал не найден или недоступен.")
    return

  print(f"Найден канал: {name} ({subscribers} подписчиков)")

  # Извлекаем контакты
  emails, telegram_links, other_links = extract_contacts(description)

  # Сохраняем в базу
  save_to_db(channel_id, channel_handle_or_id, name, description, subscribers, emails, telegram_links, other_links)

  print("Данные сохранены в БД!\n")


if __name__ == "__main__":
  youtube_channel = "@2DROTSLEAGUE"  # Можно передавать @handle или channel_id
  analyze_youtube(youtube_channel)
