from googleapiclient.discovery import build

from db.connect.connect import Connect
from db.models.channel.channel import Channel
from db.models.playlist.playlist import Playlist
from db.repository.ChannelRepository import ChannelRepository
from db.repository.VideoRepository import VideoRepository

from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

session = Connect()
videoRepository = VideoRepository(Connect.session)
channelRepository = ChannelRepository(Connect.session)

def get_channel_stats(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    print(channel_id)
    request = youtube.channels().list(
        part='statistics',
        id=channel_id
    )
    response = request.execute()
    print(response)

    if not response.get('items'):
        return {
        'subscribers_count': None,
        'view_count': None,
        'video_count': None
    }


    print(response["items"][0]['statistics'])
    stats = response['items'][0]['statistics']
    print(int(stats.get('subscriberCount', 0)))
    return {
        'subscribers_count': int(stats.get('subscriberCount', 0)),
        'view_count': int(stats.get('viewCount', 0)),
        'video_count': int(stats.get('videoCount', 0))
    }

def get_video_info(video_id, api_key):
    """
    Получает информацию о видео и комментарии под ним
    """
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Получаем информацию о видео
    video_request = youtube.videos().list(
        part='snippet,contentDetails,statistics,status',
        id=video_id
    )
    video_response = video_request.execute()

    if not video_response.get('items'):
        return None

    video_item = video_response['items'][0]
    print(video_item['statistics'].get('subscriberCount'))

    # Парсим информацию о видео
    video_info = {
        'subscribers_count': int(video_item['statistics'].get('subscriberCount', 0))
        #'comment_count': int(video_item['statistics']['commentCount']),
        #'tags': video_item['snippet']['tags'],
        #'category': video_item['snippet']['categoryId'],

    }

    # Получаем комментарии

    return video_info

def print_channel_info(channel_data, channel):
    print(channel_data['view_count'])
    print(channel_data['video_count'])
    print(channel_data['view_count'])
    channel.view_count = channel_data['view_count']
    channel.video_count = channel_data['video_count']
    channel.subscriber_count = channel_data['subscribers_count']
    channelRepository.save(channel)
'''''
def print_video_info(video_data, id):
    """Выводит информацию о видео и комментарии"""
    video = videoRepository.get_by_id(id)
    #print(f"Количество комментариев: {video_data['comment_count']}")
    print(int(video_data.get('subscribers_count', 0)))
    #print(f"Категории: {video_data['category']}")
    #video.comment_count = video_data['comment_count']
    video.subscribers_count = video_data['subscribers_count']
    tags = video_data['tags']
    tags_encoded = []
    for tag in tags:
        tags_encoded.append(tag.encode("utf-8").decode("utf-8"))
    video.tags = tags_encoded
    #video.category_id = video_data['category']
    #print(id)
    videoRepository.save(video)'''




#videos = videoRepository.get_by_id_above(0)
#UCzxCeXT34Mk6cPVYlQ3TwOg

channels = channelRepository.get_by_id_above(0)
for channel in channels:
    if channel.video_count is None and channel.youtube_id is not None:
        channel_data = get_channel_stats(API_KEY, channel.youtube_id)
        print_channel_info(channel_data, channel)
''''
videos = videoRepository.get_unique_channel_titles()
for video in videos:
    if channelRepository.find_by_title(video.channel_title) is None:
        channel_data = get_channel_stats(API_KEY, video.channel_title)
        print_channel_info(channel_data)

for video in videos:
    i = video.id
    video = videoRepository.get_by_id(i)
    try:
        #video_data = get_video_info(video.youtube_id, API_KEY)
        channel_data = get_channel_stats(API_KEY, video.channel_title)
        print_video_info(channel_data, i)

    #if video_data:
     #   print_video_info(video_data, i)
    #else:
     #   print("Видео не найдено.")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")'''