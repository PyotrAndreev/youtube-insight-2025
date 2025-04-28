import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

session = Connect()
videoRepository = VideoRepository(Connect.session)

video_data = []
videos = videoRepository.get_by_id_above(0)

for video in videos:
    i = video.id
    video = videoRepository.get_by_id(i)
    if video is not None:
        video_data.append({
            'id': video.youtube_id,
            'title': video.title,
            'likes': video.like_count,
            'comments': video.comment_count,
            'views': video.view_count
        })


def calculate_engagement(likes, comments, views):
    if views == 0:
        return 0
    return (likes + comments) / views


query_title = "география"
min_likes = 1000  # Минимальное количество лайков для похожих видео


def check_similar_videos(query_title, video_data, min_likes=0):
    filtered_videos = [v for v in video_data if v['likes'] >= min_likes]

    if not filtered_videos:
        print(f"Не найдено видео с количеством лайков больше {min_likes}")
        return

    video_titles = [item['title'] for item in filtered_videos]
    title_embeddings = model.encode(video_titles)

    query_embedding = model.encode([query_title])[0]

    # Вычисление схожести с другими названиями
    similarities = cosine_similarity(
        [query_embedding],
        title_embeddings
    )[0]

    most_similar_indices = np.argsort(similarities)[-3:][::-1]

    similar_engagements = []
    for idx in most_similar_indices:
        video = filtered_videos[idx]
        engagement = calculate_engagement(video['likes'], video['comments'], video['views'])
        similar_engagements.append(engagement)

    avg_engagement = np.mean(similar_engagements) if similar_engagements else 0

    print(f"Похожие видео на запрос: '{query_title}' (минимум {min_likes} лайков)\n")
    print(f"Средний рейтинг вовлеченности для похожих видео: {avg_engagement:.2%}\n")

    for idx in most_similar_indices:
        video = filtered_videos[idx]
        engagement = calculate_engagement(video['likes'], video['comments'], video['views'])

        print(f"Название: {video['title']}")
        print(f"Ссылка: https://www.youtube.com/watch?v={video['id']}")
        print(f"Схожесть: {similarities[idx]:.2f}")
        print(f"Лайки: {video['likes']}")
        print(f"Комментарии: {video['comments']}")
        print(f"Просмотры: {video['views']}")
        print(f"Рейтинг вовлеченности: {engagement:.2%}")
        print("-" * 50)


check_similar_videos(query_title, video_data, min_likes=min_likes)
