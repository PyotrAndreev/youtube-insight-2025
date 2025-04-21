import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository
from functions.helper import convert_to_seconds


def plot_views_vs_video_length_points(df):
    """Функция для построения графика зависимости просмотров от длительности видео (точечный)."""
    plt.figure(figsize=(12, 6))
    df_agg = df.groupby('video_length')['views'].mean().reset_index()
    sns.scatterplot(
        x='video_length',
        y='views',
        data=df_agg,
        color='green',
        alpha=0.6,  # Прозрачность точек
        s=30  # Размер точек
    )

    plt.xscale('log')
    plt.yscale('log')
    plt.title('Зависимость просмотров от длительности видео', fontsize=14)
    plt.xlabel('Длительность видео (секунды)', fontsize=12)
    plt.ylabel('Просмотры', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()


def plot_views_vs_video_length(df1, df2=None, label1='shorts', label2='обычные видео'):
    """Строит линейный график зависимости просмотров от длительности видео для одного или двух наборов данных"""
    plt.figure(figsize=(12, 6))

    sns.lineplot(
        x='video_length',
        y='views',
        data=df1,
        estimator='mean',
        color='green',
        linewidth=2,
        label=label1
    )

    if df2 is not None:
        sns.lineplot(
            x='video_length',
            y='views',
            data=df2,
            estimator='mean',
            color='blue',
            linewidth=2,
            label=label2
        )

    plt.xscale('log')
    plt.yscale('log')
    plt.title('Зависимость просмотров от длительности видео', fontsize=14)
    plt.xlabel('Длительность видео (секунды)', fontsize=12)
    plt.ylabel('Просмотры', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.show()


session = Connect()
videoRepository = VideoRepository(Connect.session)

video_length = []
short_video_length = []
long_video_length = []
video_views = []
short_video_views = []
long_video_views = []
short_video_comments_number = []
long_video_comments_number = []

videos = videoRepository.get_by_id_above(0)

for video in videos:
    i = video.id
    video = videoRepository.get_by_id(i)
    if video is not None:
        video_views.append(video.view_count)
        time_str = str(video.duration)
        total_seconds = convert_to_seconds(time_str)
        video_length.append(total_seconds)
        if total_seconds < 60:
            short_video_length.append(total_seconds)
            short_video_comments_number.append(video.comment_count)
            short_video_views.append(video.view_count)
        else:
            if total_seconds < 10000:
                long_video_length.append(total_seconds)
                long_video_views.append(video.view_count)
                long_video_comments_number.append(video.comment_count)

df_videos = pd.DataFrame({
    'video_length': video_length,
    'views': video_views
}).sort_values('video_length')

df_short_videos = pd.DataFrame({
    'video_length': short_video_length,
    'views': short_video_views,
    'comments_number': short_video_comments_number,
}).sort_values('video_length')

df_long_videos = pd.DataFrame({
    'video_length': long_video_length,
    'views': long_video_views,
    'comments_number': long_video_comments_number,
}).sort_values('video_length')
plot_views_vs_video_length(df_short_videos, df_long_videos)
plot_views_vs_video_length_points(df_videos)
