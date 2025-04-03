import re
import time
import random
import psycopg2
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import googleapiclient.discovery
from googleapiclient.errors import HttpError

class YouTubeScraper:
    def __init__(self, api_key: str, db_params: dict):
        self.api_key = api_key
        self.db_params = db_params
        self.youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        
        # Search topics with weights for better distribution
        self.search_topics = [
            ("gaming", 0.3),
            ("music", 0.2),
            ("tech", 0.2),
            ("science", 0.1),
            ("football", 0.1),
            ("movies", 0.05),
            ("fashion", 0.05)
        ]

    def get_weighted_random_topic(self) -> str:
        """Selects a search topic based on predefined weights"""
        topics, weights = zip(*self.search_topics)
        return random.choices(topics, weights=weights, k=1)[0]

    def fetch_channels(self, query: str, max_results: int = 10) -> List[str]:
        """Fetches channel IDs from YouTube search API"""
        try:
            request = self.youtube.search().list(
                part="snippet",
                type="channel",
                q=query,
                maxResults=max_results,
                order="viewCount"  # Get more popular channels first
            )
            response = request.execute()
            return [item["id"]["channelId"] for item in response.get("items", [])]
        except HttpError as e:
            print(f"YouTube API Error: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching channels: {e}")
            return []

    def get_channel_details(self, channel_id: str) -> Optional[Tuple]:
        """Retrieves detailed channel information"""
        try:
            request = self.youtube.channels().list(
                part="snippet,statistics",
                id=channel_id,
                fields="items(snippet(title,description),statistics(subscriberCount))"
            )
            response = request.execute()
            
            if not response.get("items"):
                return None
                
            item = response["items"][0]
            snippet = item["snippet"]
            stats = item["statistics"]
            
            return (
                channel_id,
                self.clean_text(snippet["title"]),
                self.clean_text(snippet.get("description", "")),
                int(stats.get("subscriberCount", 0))
            )
        except Exception as e:
            print(f"Error getting channel {channel_id} details: {e}")
            return None

    def extract_contacts(self, text: str) -> Tuple[List[str], List[str], List[str]]:
        """Extracts contact information from channel description"""
        text = text or ""
        emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        links = re.findall(r"https?://[^\s]+", text)
        
        telegram = [link for link in links if "t.me/" in link or "telegram.me/" in link]
        other_links = [link for link in links if link not in telegram]
        
        return emails, telegram, other_links

    @staticmethod
    def clean_text(text: str) -> str:
        """Sanitizes text for database storage"""
        if not text:
            return ""
        return text.encode("utf-8", errors="replace").decode("utf-8").strip()

    def save_channels(self, channels_data: List[Tuple]) -> bool:
        """Bulk saves channel data to PostgreSQL"""
        if not channels_data:
            return False

        try:
            with psycopg2.connect(**self.db_params) as conn:
                conn.set_client_encoding('UTF8')
                with conn.cursor() as cursor:
                    # Create table if not exists
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS youtube_channels (
                            channel_id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            description TEXT,
                            subscribers INTEGER,
                            emails TEXT[],
                            telegram_links TEXT[],
                            other_links TEXT[],
                            last_updated TIMESTAMP DEFAULT NOW()
                        )
                    """)
                    
                    # Prepare batch insert
                    query = """
                        INSERT INTO youtube_channels 
                        (channel_id, name, description, subscribers, emails, telegram_links, other_links)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (channel_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            subscribers = EXCLUDED.subscribers,
                            emails = EXCLUDED.emails,
                            telegram_links = EXCLUDED.telegram_links,
                            other_links = EXCLUDED.other_links,
                            last_updated = NOW()
                    """
                    
                    # Process and insert data
                    prepared_data = []
                    for channel_id, name, desc, subs in channels_data:
                        emails, telegram, other_links = self.extract_contacts(desc)
                        prepared_data.append((
                            channel_id,
                            name,
                            desc,
                            subs,
                            emails,
                            telegram,
                            other_links
                        ))
                    
                    cursor.executemany(query, prepared_data)
                    conn.commit()
                    return True
                    
        except Exception as e:
            print(f"Database error: {e}")
            return False

    def run(self, duration_hours: float = 4, min_subs: int = 1000000):
        """Main scraping loop with time limit"""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        
        print(f"Starting YouTube scraper for {duration_hours} hours...")
        
        while datetime.now() < end_time:
            try:
                # Get channels with weighted random topic
                topic = self.get_weighted_random_topic()
                print(f"\nSearching for '{topic}' channels...")
                
                channel_ids = self.fetch_channels(topic)
                if not channel_ids:
                    print("No channels found for this topic")
                    time.sleep(30)
                    continue
                
                # Process channels in batches
                valid_channels = []
                for channel_id in channel_ids:
                    details = self.get_channel_details(channel_id)
                    if not details:
                        continue
                        
                    _, _, _, subs = details
                    if subs >= min_subs:
                        valid_channels.append(details)
                        print(f"Found channel: {details[1]} ({subs:,} subs)")
                    else:
                        print(f"Skipping channel with {subs:,} subscribers")
                
                # Save batch to database
                if valid_channels:
                    success = self.save_channels(valid_channels)
                    print(f"Saved {len(valid_channels)} channels" if success else "Save failed")
                
                # Random delay between 30-90 seconds
                delay = random.randint(30, 60)
                print(f"Waiting {delay} seconds...")
                time.sleep(delay)
                
            except KeyboardInterrupt:
                print("\nStopping scraper...")
                break
            except Exception as e:
                print(f"Unexpected error in main loop: {e}")
                time.sleep(60)  # Longer delay on error
        
        print("\nScraping completed.")

if __name__ == "__main__":
    # Configuration
    CONFIG = {
        "api_key": "AIzaSyA4__CEwYmsgaFqjmQ0epUntSUgWtNUffM",
        "db_params": {
            "dbname": "postgres",
            "user": "postgres",
            "password": "penis",
            "host": "localhost",
            "port": "5432"
        }
    }
    
    # Initialize and run scraper
    scraper = YouTubeScraper(CONFIG["api_key"], CONFIG["db_params"])
    scraper.run(duration_hours=4, min_subs=1000000)