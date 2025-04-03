import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import re
from collections import defaultdict

from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository


def plot_engagement_by_channel(df, channel_col='channel', views_col='views',
                               likes_col='likes', comments_col='comments',
                               palette='viridis', figsize=None):
    required_cols = [channel_col, views_col, likes_col, comments_col]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame должен содержать колонки: {required_cols}")

    # Рассчитываем рейтинг вовлеченности (в процентах)
    df['engagement_rate'] = (df[likes_col] + df[comments_col]) / df[views_col] * 100

    # Группируем по каналам
    engagement_df = df.groupby(channel_col)['engagement_rate'].mean().reset_index()
    engagement_df = engagement_df.sort_values('engagement_rate', ascending=False)

    # Автоподбор размера графика
    num_categories = len(engagement_df)
    if figsize is None:
        base_width = 10
        width_per_category = 0.8
        fig_width = max(base_width, num_categories * width_per_category)
        figsize = (fig_width, 6)

    plt.figure(figsize=figsize)
    sns.set_style("whitegrid")

    ax = sns.barplot(
        x=channel_col,
        y='engagement_rate',
        data=engagement_df,
        palette=palette,
        alpha=0.8
    )

    fontsize = 10 - min(2, num_categories // 10)  # Автоподбор размера шрифта

    for p in ax.patches:
        height = p.get_height()
        ax.annotate(
            f"{height:.1f}%",
            (p.get_x() + p.get_width() / 2., height),
            ha='center',
            va='center',
            xytext=(0, 5),
            textcoords='offset points',
            fontsize=fontsize
        )

    # Настройка оформления
    ax.set_title('Средний рейтинг вовлеченности по каналам', fontsize=14)
    ax.set_xlabel('Канал', fontsize=12)
    ax.set_ylabel('Рейтинг вовлеченности (%)', fontsize=12)

    # Настройка подписей категорий
    rotation = 45 if num_categories > 5 else 0
    plt.xticks(
        rotation=rotation,
        ha='right' if rotation != 0 else 'center',
        fontsize=10
    )

    plt.tight_layout()
    plt.show()


def plot_views_vs_video_length(df):
    """Функция для построения графика зависимости просмотров от длительности видео."""
    plt.figure(figsize=(12, 6))

    sns.lineplot(
        x='video_length',
        y='views',
        data=df,
        estimator='mean',
        color='green',
        linewidth=2
    )

    plt.xscale('log')
    plt.yscale('log')
    plt.title('Зависимость просмотров от длительности видео', fontsize=14)
    plt.xlabel('Длительность видео (секунды)', fontsize=12)
    plt.ylabel('Просмотры', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()


def plot_comment_count_vs_length(comment_stats):
    plt.figure(figsize=(12, 6))

    df = pd.DataFrame({
        'comment_length': list(comment_stats.keys()),
        'comment_count': list(comment_stats.values())
    }).sort_values('comment_length')

    # Оставляем подписи только для каждого 30-го значения
    xticks = df['comment_length'].iloc[::30]

    sns.barplot(
        x='comment_length',
        y='comment_count',
        data=df,
        color='blue',
        alpha=0.6
    )

    plt.title('Количество комментариев в зависимости от длины', fontsize=14)
    plt.xlabel('Длина комментария (символы)', fontsize=12)
    plt.ylabel('Количество комментариев', fontsize=12)
    plt.xticks(ticks=range(0, len(df), 30), labels=xticks, rotation=45)
    plt.tight_layout()
    plt.show()


session = Connect()
videoRepository = VideoRepository(Connect.session)

video_length = []
views = []
chanel = []
channel_views = []
comments = []
likes = []
all_comment_lengths = []
comment_stats = defaultdict(int)

for i in range(18, 889):
    video = videoRepository.get_by_id(i)
    if video is not None:
        views.append(video.view_count)
        time_str = str(video.duration)
        time_points = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        video_duration = list(map(float, re.findall(r"\d+\.?\d*", time_str)))[::-1]
        for j in range(len(video_duration)):
            time_points[6 - j - 1] = video_duration[j]

        years, mons, days, hours, mins, secs = time_points
        total_seconds = (
                years * 365 * 24 * 60 * 60 +
                mons * 30 * 24 * 60 * 60 +
                days * 24 * 60 * 60 +
                hours * 60 * 60 +
                mins * 60 +
                secs
        )
        video_length.append(total_seconds)
        len_comm = 0
        for (comment) in video.comments:
            len_comm = len(comment.text)
            all_comment_lengths.append(len_comm)
            comment_stats[len_comm] += 1
        if video.channel_title not in chanel:
            chanel.append(video.channel_title)
            channel_views.append(video.view_count)
            likes.append(video.like_count)
            comments.append(len(video.comments))
        else:
            ind = chanel.index(video.channel_title)
            channel_views[ind] += video.view_count
            likes[ind] += video.like_count
            comments[ind] += len(video.comments)

sorted_data = sorted(zip(chanel, channel_views, likes, comments),
                     key=lambda x: x[2],  # Сортировка по likes
                     reverse=True)

chanel_sorted, views_sorted, likes_sorted, comments_sorted = zip(*sorted_data)

test_data = {
    'channel': chanel_sorted[:15],
    'views': views_sorted[:15],
    'likes': likes_sorted[:15],
    'comments': comments_sorted[:15]
}
test_df = pd.DataFrame(test_data)
plot_engagement_by_channel(test_df)

df_videos = pd.DataFrame({
    'video_length': video_length,
    'views': views
}).sort_values('video_length')
plot_views_vs_video_length(df_videos)

if all_comment_lengths:
    plot_comment_count_vs_length(comment_stats)
