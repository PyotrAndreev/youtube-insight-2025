from googleapiclient.discovery import build

API_KEY = "YOUR_API_KEY"

query = input("Введите тематику видео: ")

min_likes = int(input("Введите минимальное количество лайков под видео: "))

youtube = build('youtube', 'v3', developerKey=API_KEY)


def search_videos_by_topic(query, max_results=10):
    request = youtube.search().list(
        q=query,
        part='id',
        type='video',
        maxResults=max_results
    )
    response = request.execute()
    return [item['id']['videoId'] for item in response['items']]


def get_video_stats(video_id):
    request = youtube.videos().list(
        part='statistics',
        id=video_id
    )
    response = request.execute()
    return response['items'][0]['statistics']


def get_videos_with_likes_above_threshold(query, min_likes, max_results=10):
    video_ids = search_videos_by_topic(query, max_results)

    result = []
    for video_id in video_ids:
        try:
            stats = get_video_stats(video_id)
            like_count_str = stats.get('likeCount')
            if like_count_str is None:
                continue
            like_count = int(like_count_str)
            if like_count >= min_likes:
                result.append(video_id)
            like_count = int(stats.get('likeCount', 0))
            if like_count > min_likes:
                result.append(video_id)
        except Exception as e:
            print(f"Ошибка при обработке видео {video_id}: {e}")

    return result


video_ids = get_videos_with_likes_above_threshold(query, min_likes)

print(video_ids)
