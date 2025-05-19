import isodate
import time
from googleapiclient.discovery import build
from db.connect.connect import Connect
from db.models.comment.comment import Comment
from db.models.playlist.playlist import Playlist
from db.models.video.status import Status
from db.models.video.video import Video
from db.repository.ChannelRepository import ChannelRepository
from db.repository.CommentRepository import CommentRepository
from db.repository.PlaylistRepository import PlaylistRepository
from db.repository.VideoRepository import VideoRepository
from dotenv import load_dotenv
import os

load_dotenv()

session = Connect()
videoRepository = VideoRepository(Connect.session)
commentRepository = CommentRepository(Connect.session)
playlistRepository = PlaylistRepository(Connect.session)

API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=API_KEY)


def get_playlists_for_video(video_id, channel_id):
    """Получает все плейлисты канала, содержащие указанное видео"""
    playlists = []

    try:
        # 1. Получаем все плейлисты канала
        playlists_request = youtube.playlists().list(
            part="id",
            channelId=channel_id,
            maxResults=50
        )
        playlists_response = playlists_request.execute()

        # 2. Для каждого плейлиста проверяем наличие видео
        for playlist in playlists_response.get("items", []):
            playlist_id = playlist["id"]

            items_request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                videoId=video_id,
                maxResults=1
            )
            items_response = items_request.execute()

            if items_response.get("items"):
                # 3. Получаем полную информацию о плейлисте
                playlist_info = youtube.playlists().list(
                    part="snippet,contentDetails",
                    id=playlist_id
                ).execute()

                if playlist_info.get("items"):
                    playlists.append({
                        "id": playlist_id,
                        "published_at": playlist_info["items"][0]['snippet']['publishedAt'],
                        "title": playlist_info["items"][0]["snippet"]["title"],
                        "item_count": playlist_info["items"][0]["contentDetails"]["itemCount"]
                    })

    except Exception as e:
        print(f"Ошибка при поиске плейлистов: {str(e)}")

    return playlists

#print(get_playlists_for_video("_h-vAZRCHrc", "UC5gufuYHPSsJA-jul-iwyXA"))


def get_video_info(video_id, category, channel_id):
    """
    Получает полную информацию о видео, включая комментарии и плейлисты
    Возвращает словарь с данными или None, если видео не найдено
    """
    try:
        # Получаем основную информацию о видео
        video_request = youtube.videos().list(
            part='snippet,contentDetails,statistics,status',
            id=video_id
        )
        video_response = video_request.execute()

        if not video_response.get('items'):
            return None

        video_item = video_response['items'][0]

        # Обрабатываем теги видео
        tags = video_item['snippet'].get('tags', [])

        # Формируем основную информацию о видео
        video_info = {
            'video_id': video_item['id'],
            'title': video_item['snippet']['title'],
            'description': video_item['snippet']['description'],
            'published_at': video_item['snippet']['publishedAt'],
            'channel_title': video_item['snippet']['channelTitle'],
            'view_count': int(video_item['statistics']['viewCount']),
            'like_count': int(video_item['statistics'].get('likeCount', 0)),
            'duration': str(isodate.parse_duration(video_item['contentDetails']['duration'])),
            'comment_count': int(video_item['statistics']['commentCount']),
            'tags': tags,
            'category': video_item['snippet']['categoryId'],
            'manual_category': category,
            'comments': [],
            'playlists': []
        }

        # Получаем комментарии к видео
        try:
            comments_request = youtube.commentThreads().list(
                part='snippet,replies',
                videoId=video_id,
                maxResults=100,
                textFormat='plainText'
            )
            comments_response = comments_request.execute()
            c = 0
            while comments_response and c < 2000:
                for item in comments_response['items']:
                    comment = item['snippet']['topLevelComment']['snippet']
                    video_info['comments'].append({
                        'author': comment['authorDisplayName'],
                        'text': comment['textDisplay'],
                        'likes': comment['likeCount'],
                        'published_at': comment['publishedAt']
                    })
                    c += 1

                if 'nextPageToken' in comments_response:
                    comments_response = youtube.commentThreads().list(
                        part='snippet,replies',
                        videoId=video_id,
                        pageToken=comments_response['nextPageToken'],
                        maxResults=100,
                        textFormat='plainText'
                    ).execute()
                else:
                    break
        except Exception as e:
            print(f"Не удалось получить комментарии для видео {video_id}: {str(e)}")

        # Получаем информацию о плейлистах
        try:
            playlists = get_playlists_for_video(video_id, channel_id)
            print(playlists)
            video_info['playlists'] = playlists
        except Exception as e:
            print(f"Ошибка при получении плейлистов для видео {video_id}: {str(e)}")

        return video_info

    except Exception as e:
        print(f"Ошибка при получении информации о видео {video_id}: {str(e)}")
        return None


def print_video_info(video_data):
    """Выводит полную информацию о видео и сохраняет в базу данных"""
    video_in_table = videoRepository.get_by_youtube_id(video_data['video_id'])
    if video_in_table is None:

        # Выводим информацию о плейлистах
        if video_data['playlists']:
            print("\n=== Плейлисты ===")
            for i, playlist in enumerate(video_data['playlists'], 1):
                print(f"{i}. {playlist.get('title', playlist['title'])}")
                print(f"   ID: {playlist['id']}")
                print(f"   Видео в плейлисте: {playlist.get('item_count', 'N/A')}")
                print(f"   Создан: {playlist.get('published_at', 'N/A')}")
                print("   ---")
                if playlistRepository.get_by_youtube_id(playlist['id']) is None:
                    playlist1 = Playlist()
                    playlist1.title = playlist['title']
                    playlist1.youtube_id = playlist['id']
                    playlist1.published_at = playlist['published_at']
                    playlist1.video_count = playlist['item_count']
                    playlistRepository.save(playlist1)
        else:
            print("\nВидео не принадлежит ни к одному публичному плейлисту")

        print("\n=== Информация о видео ===")
        print(f"ID: {video_data['video_id']}")
        print(f"Название: {video_data['title']}")
        print(f"Канал: {video_data['channel_title']}")
        print(f"Дата публикации: {video_data['published_at']}")
        print(f"Длительность: {video_data['duration']}")
        print(f"Просмотры: {video_data['view_count']}")
        print(f"Лайки: {video_data['like_count']}")
        print(f"Количество комментариев: {video_data['comment_count']}")
        print(f"Категория YouTube: {video_data['category']}")
        print(f"Ручная категория: {video_data['manual_category']}")
        print(f"Тэги: {', '.join(video_data['tags']) if video_data['tags'] else 'Нет тэгов'}")

        # Сохраняем видео в базу данных
        if len(video_data['playlists'])>0:
            playlist_id = playlistRepository.get_by_youtube_id(video_data['playlists'][0]['id']).id
        else:
            playlist_id = None
        if videoRepository.get_by_youtube_id(video_data['video_id']) is None:
            video = Video()
            video.title = video_data['title']
            video.youtube_id = video_data['video_id']
            video.channel_title = video_data['channel_title']
            video.published_at = video_data['published_at']
            video.duration = video_data['duration']
            video.view_count = video_data['view_count']
            video.like_count = video_data['like_count']
            video.comment_count = video_data['comment_count']
            video.manual_category = video_data['manual_category']
            video.category_id = video_data['category']
            video.status = Status.created
            video.playlist_id = playlist_id

            # Обрабатываем теги
            if video_data['tags']:
                tags_encoded = [tag.encode("utf-8").decode("utf-8") for tag in video_data['tags']]
                video.tags = tags_encoded

            videoRepository.save(video)

            # Сохраняем комментарии
            if video_data['comments']:
                print("\n=== Комментарии ===")
                for i, comment in enumerate(video_data['comments'], 1):  # Выводим первые 5 комментариев
                    print(f"{i}. {comment['text']} (лайков: {comment['likes']})")

                    comment_db = Comment()
                    comment_db.text = comment['text']
                    comment_db.video_id = video.id
                    comment_db.like_count = comment['likes']
                    commentRepository.save(comment_db)
            else:
                print("\nКомментарии не найдены или отключены")
            # Обновляем статус видео
            video.status = Status.processed
            videoRepository.save(video)

    else:
        print(f"Видео {video_data['video_id']} уже существует в базе данных")

'''
video_data = get_video_info("_h-vAZRCHrc", '', "UC5gufuYHPSsJA-jul-iwyXA")
if video_data:
    print_video_info(video_data)
else:
    print(f"Видео не найдено.")

'''
def get_channel_videos(channel_id, max_results=210, next_page_token=None,category=None):
    """
    Получает все видео с указанного канала и их информацию
    Возвращает список ID видео
    """
    video_ids = []

    try:
        while len(video_ids) < max_results:
            request = youtube.search().list(
                channelId=channel_id,
                part="id",
                type="video",
                maxResults=min(10000, max_results - len(video_ids)),  # YouTube позволяет максимум 50 за запрос
                pageToken=next_page_token,
                order="date"
            )
            response = request.execute()

            for item in response.get("items", []):
                video_id = item["id"]["videoId"]
                if video_id not in video_ids:
                    video_ids.append(video_id)

                    # Получаем и обрабатываем информацию о видео
                    try:
                        video_data = get_video_info(video_id, category, channel_id)
                        if video_data:
                            print_video_info(video_data)
                        else:
                            print(f"Видео {video_id} не найдено.")
                    except Exception as e:
                        print(f"Ошибка при обработке видео {video_id}: {str(e)}")

            next_page_token = response.get("nextPageToken")
            print(next_page_token)
            if not next_page_token or len(video_ids) >= max_results:
                break

        print(f"\nВсего найдено видео: {len(video_ids)}")
        return video_ids

    except Exception as e:
        print(f"Ошибка при получении видео канала: {str(e)}")
        return []
#print(get_video_info('nu9wUEvy0JU', "Схожий контент с Andrey Sozykin", "UCrWWcscvUWaqdQJLQQGO6BA"))
#video_data = get_video_info('nu9wUEvy0JU', "Схожий контент с Andrey Sozykin", "UCrWWcscvUWaqdQJLQQGO6BA")
#if video_data:
 #   print_video_info(video_data)

# Пример использования

if __name__ == "__main__":
    start_time = time.time()
    channel_id = "UCu6mSoMNzHQiBIOCkHUa2Aw" # Пример ID канала
    video_ids = get_channel_videos(channel_id, max_results=210, category='канал похожий на Химия – Просто')
    end_time = time.time()  # Засекаем конечное время
    elapsed_time = end_time - start_time  # Вычисляем разницу
    print(f"Время выполнения: {elapsed_time:.4f} секунд")