import os
import time
import random
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import psycopg2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class YouTubeScraper:
    def __init__(self, api_keys: List[str], db_params: dict):
        self.api_keys = api_keys
        self.current_api_index = 0
        self.db_params = db_params
        self.youtube = self._build_youtube_client()  # Инициализация клиента при создании
        self.topics = [
            ("ai", 10),
            ("game", 8),
            ("crypto", 6),
            ("stocks", 5),
            ("startup", 5),
            ("investment", 4),
            ("tech", 7),
            ("fun", 2),
            ("news", 5),
            ("documentary", 5),
        ]

    def _build_youtube_client(self):
        """Создаёт новый клиент YouTube API с текущим ключом"""
        if not self.api_keys:
            raise ValueError("Не предоставлены API ключи YouTube")
        
        api_key = self.api_keys[self.current_api_index % len(self.api_keys)]
        return build("youtube", "v3", developerKey=api_key)

    def _rotate_api_key(self):
        """Переключается на следующий API ключ"""
        self.current_api_index += 1
        self.youtube = self._build_youtube_client()
        print(f"Переключились на API ключ #{self.current_api_index + 1}")

    def get_weighted_random_topic(self) -> str:
        topics, weights = zip(*self.topics)
        return random.choices(topics, weights=weights, k=1)[0]

    def fetch_channels(self, query: str, pages: int = 3, results_per_page: int = 10) -> List[str]:
        channel_ids = set()
        next_page_token = None
        
        for _ in range(pages):
            try:
                request = self.youtube.search().list(
                    part="snippet",
                    type="channel",
                    q=query,
                    maxResults=results_per_page,
                    order="viewCount",
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response.get("items", []):
                    if "id" in item and "channelId" in item["id"]:
                        channel_ids.add(item["id"]["channelId"])
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
                    
            except HttpError as e:
                print(f"YouTube API Error: {e}")
                if e.resp.status == 403:
                    self._rotate_api_key()
                else:
                    break
            except Exception as e:
                print(f"Unexpected error fetching channels: {e}")
                break
                
        return list(channel_ids)

    def filter_existing_channels(self, channel_ids: List[str]) -> List[str]:
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT channel_id FROM youtube_channels WHERE channel_id = ANY(%s)", (channel_ids,)
                    )
                    existing_ids = {row[0] for row in cursor.fetchall()}
                    return [cid for cid in channel_ids if cid not in existing_ids]
        except Exception as e:
            print(f"Ошибка при фильтрации каналов: {e}")
            return channel_ids

    def get_channel_details(self, channel_id: str) -> Optional[Tuple[str, str, str, int]]:
        try:
            request = self.youtube.channels().list(
                part="snippet,statistics",
                id=channel_id
            )
            response = request.execute()
            if response.get("items"):
                item = response["items"][0]
                title = item["snippet"]["title"]
                description = item["snippet"].get("description", "")
                subscribers = int(item["statistics"].get("subscriberCount", 0))
                return channel_id, title, description, subscribers
        except Exception as e:
            print(f"Ошибка при получении деталей канала {channel_id}: {e}")
        return None

    def save_channels(self, channel_data: List[Tuple[str, str, str, int]]) -> bool:
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cursor:
                    cursor.executemany(
                        """
                        INSERT INTO youtube_channels (channel_id, channel_name, description, subscribers)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (channel_id) DO NOTHING
                        """,
                        channel_data
                    )
            return True
        except Exception as e:
            print(f"Ошибка при сохранении каналов: {e}")
            return False

    def run(self, duration_hours: float = 4, min_subs: int = 1000000):
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        print(f" Стартуем на {duration_hours} ч. (до {end_time.strftime('%H:%M:%S')})")

        while datetime.now() < end_time:
            try:
                topic = self.get_weighted_random_topic()
                print(f"\n Ищем популярные каналы по теме: {topic}")

                channel_ids = self.fetch_channels(topic, pages=3)
                if not channel_ids:
                    print(" Нет результатов. Пауза 30 сек...")
                    time.sleep(30)
                    continue

                new_channel_ids = self.filter_existing_channels(channel_ids)
                print(f" Новые каналы: {len(new_channel_ids)} из {len(channel_ids)}")

                valid_channels = []
                for channel_id in new_channel_ids:
                    details = self.get_channel_details(channel_id)
                    if not details:
                        continue
                    _, name, _, subs = details
                    if subs >= min_subs:
                        valid_channels.append(details)
                        print(f" {name} — {subs:,} подписчиков")
                    else:
                        print(f" {name} — {subs:,} подписчиков (мало)")

                if valid_channels:
                    success = self.save_channels(valid_channels)
                    print(f" Сохранено: {len(valid_channels)} каналов" if success else "Ошибка при сохранении")

                delay = random.randint(15, 45)
                print(f" Пауза {delay} сек...")
                time.sleep(delay)

            except KeyboardInterrupt:
                print("\n Остановлено пользователем.")
                break
            except Exception as e:
                print(f" Ошибка в основном цикле: {e}")
                time.sleep(60)

        print("\n Скрапинг завершён.")