from googleapiclient.discovery import build
from datetime import timedelta
import isodate  # pip install isodate

from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository

session = Connect()
videoRepository = VideoRepository(Connect.session)

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

    # Парсим информацию о видео
    video_info = {
        'comment_count': int(video_item['statistics']['commentCount']),
        #'tags': video_item['snippet']['tags'],
        'category': video_item['snippet']['categoryId'],

    }

    # Получаем комментарии

    return video_info


def print_video_info(video_data, id):
    """Выводит информацию о видео и комментарии"""
    video = videoRepository.get_by_id(id)
    print(f"Количество комментариев: {video_data['comment_count']}")
    #print(f"Тэги: {video_data['tags']}")
    print(f"Категории: {video_data['category']}")
    video.comment_count = video_data['comment_count']
    '''tags = video_data['tags']
    tags_encoded = []
    for tag in tags:
        tags_encoded.append(tag.encode("utf-8").decode("utf-8"))
    video.tags = tags_encoded'''
    video.category_id = video_data['category']
    print(id)
    videoRepository.save(video)




API_KEY = "AIzaSyBORP6ILds3WrN7bBDksTlh5iiEKJUgwyY"  # Замените на ваш ключ
VIDEO_ID = "Jbx9TCy0qZo"  # Пример ID видео

videos = videoRepository.get_by_id_above(0)

for video in videos:
    i = video.id
    video = videoRepository.get_by_id(i)
    try:
        video_data = get_video_info(video.youtube_id, API_KEY)
        if video_data:
            print_video_info(video_data, i)
        else:
            print("Видео не найдено.")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")