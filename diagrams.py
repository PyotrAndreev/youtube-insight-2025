import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from collections import defaultdict

from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository
from functions.helper import convert_to_seconds


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

    fontsize = 10 - min(2, num_categories // 10)

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


def avg_comm_len_by_channel(df, channel_col='channel', comm_len_col='comm_len',
                            comm_amount_col='comm_amount',
                            palette='viridis', figsize=None):
    required_cols = [channel_col, comm_len_col, comm_amount_col]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame должен содержать колонки: {required_cols}")

    # Рассчитываем рейтинг вовлеченности (в процентах)
    df['avg_length'] = df[comm_len_col] // df[comm_amount_col]

    # Группируем по каналам
    engagement_df = df.groupby(channel_col)['avg_length'].mean().reset_index()
    engagement_df = engagement_df.sort_values('avg_length', ascending=False)

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
        y='avg_length',
        data=engagement_df,
        palette=palette,
        alpha=0.8
    )

    fontsize = 10 - min(2, num_categories // 10)

    for p in ax.patches:
        height = p.get_height()
        ax.annotate(
            height,
            (p.get_x() + p.get_width() / 2., height),
            ha='center',
            va='center',
            xytext=(0, 5),
            textcoords='offset points',
            fontsize=fontsize
        )

    # Настройка оформления
    ax.set_title('Средняя длина комментариев', fontsize=14)
    ax.set_xlabel('Канал', fontsize=12)
    ax.set_ylabel('Средняя длина комментариев', fontsize=12)

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


def plot_comment_count_vs_length(comment_stats, label):
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

    plt.title(f'Количество комментариев в зависимости от длины {label}', fontsize=14)
    plt.xlabel('Длина комментария (символы)', fontsize=12)
    plt.ylabel('Количество комментариев', fontsize=12)
    plt.xticks(ticks=range(0, len(df), 30), labels=xticks, rotation=45)
    plt.tight_layout()
    plt.show()


def plot_views_vs_video_length(df1, df2=None, label1='shorts', label2='обычные видео'):
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


def plot_engagement_by_category(df, category_col='category', views_col='views',
                                likes_col='likes', comments_col='comments',
                                palette='viridis', figsize=None):
    required_cols = [category_col, views_col, likes_col, comments_col]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame должен содержать колонки: {required_cols}")

    # Рассчитываем рейтинг вовлеченности (в процентах)
    df['engagement_rate'] = (df[likes_col] + df[comments_col]) / df[views_col] * 100

    # Группируем по категориям
    engagement_df = df.groupby(category_col)['engagement_rate'].mean().reset_index()
    engagement_df = engagement_df.sort_values('engagement_rate', ascending=False)

    # Автоподбор размера графика
    num_categories = len(engagement_df)
    if figsize is None:
        base_width = 10
        width_per_category = 0.8
        fig_width = max(base_width, num_categories * width_per_category)
        figsize = (fig_width, 6)

    # Создаем график
    plt.figure(figsize=figsize)
    sns.set_style("whitegrid")

    ax = sns.barplot(
        x=category_col,
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
    ax.set_title('Средний рейтинг вовлеченности по категориям', fontsize=14)
    ax.set_xlabel('Категория', fontsize=12)
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


session = Connect()
videoRepository = VideoRepository(Connect.session)

video_length = []
short_video_length = []
long_video_length = []
views = []
short_video_views = []
long_video_views = []
chanel = []
channel_views = []
comments = []
likes = []
chanel_id = []
all_comment_lengths = []
comment_stats_all = defaultdict(int)
comment_stats_shorts = defaultdict(int)
comment_stats_long_video = defaultdict(int)
channel_comments_length = []
channel_comments_amount = []
name_category = []
category_views = []
category_likes = []
category_comments = []
categories = ['None', 'Film & Animation', 'Autos & Vehicles', 'None', 'None', 'None', 'None', 'None', 'None', 'None',
              'Music', 'None', 'None', 'None', 'None', 'Pets & Animals', 'None', 'Sports', 'Short Movies',
              'Travel & Events', 'Gaming', 'Videoblogging', 'People & Blogs', 'Comedy', 'Entertainment',
              'News & Politics', 'Howto & Style', 'Education', 'Science & Technology', 'Nonprofits & Activism',
              'Movies', 'Anime/Animation', 'Action/Adventure', 'Classics', 'Comedy', 'Documentary', 'Drama', 'Family',
              'Foreign', 'Horror', 'Sci-Fi/Fantasy', 'Thriller', 'Shorts', 'Shows', 'Trailers']

videos = videoRepository.get_by_id_above(0)

for video in videos:
    i = video.id
    video = videoRepository.get_by_id(i)
    if video is not None:
        views.append(video.view_count)
        time_str = str(video.duration)
        total_seconds = convert_to_seconds(time_str)
        video_length.append(total_seconds)
        if total_seconds < 60:
            short_video_length.append(total_seconds)
            short_video_views.append(video.view_count)
        else:
            long_video_length.append(total_seconds)
            long_video_views.append(video.view_count)
        len_comm = 0
        len_comm_by_video = 0
        for (comment) in video.comments:
            len_comm = len(comment.text)
            all_comment_lengths.append(len_comm)
            comment_stats_all[len_comm] += 1
            len_comm_by_video += len_comm
            if total_seconds < 60:
                comment_stats_shorts[len_comm] += 1
            else:
                comment_stats_long_video[len_comm] += 1

        if video.category_id is not None:
            if categories[video.category_id] not in name_category:
                name_category.append(categories[video.category_id])
                category_views.append(video.view_count)
                category_likes.append(video.like_count)
                category_comments.append(len(video.comments))
            else:
                ind = name_category.index(categories[video.category_id])
                category_views[ind] += video.view_count
                category_likes[ind] += video.like_count
                category_comments[ind] += len(video.comments)

        if video.channel_title not in chanel:
            chanel.append(video.channel_title)
            channel_comments_length.append(len_comm_by_video)
            channel_comments_amount.append(len(video.comments))
            channel_views.append(video.view_count)
            likes.append(video.like_count)
            comments.append(len(video.comments))
        else:
            ind = chanel.index(video.channel_title)
            channel_comments_length[ind] += len_comm_by_video
            channel_comments_amount[ind] += len(video.comments)
            channel_views[ind] += video.view_count
            likes[ind] += video.like_count
            comments[ind] += len(video.comments)

sorted_data = sorted(zip(chanel, channel_views, likes, comments),
                     key=lambda x: x[2],  # Сортировка по likes
                     reverse=True)

sorted_data2 = sorted(zip(name_category, category_views, category_likes, category_comments),
                      key=lambda x: x[2],  # Сортировка по views
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

df_short_videos = pd.DataFrame({
    'video_length': short_video_length,
    'views': short_video_views
}).sort_values('video_length')

df_long_videos = pd.DataFrame({
    'video_length': long_video_length,
    'views': long_video_views
}).sort_values('video_length')

sorted_data = sorted(zip(chanel, channel_comments_length, channel_comments_amount),
                     key=lambda x: x[2],  # Сортировка по likes
                     reverse=True)

chanel_sorted, channel_comments_length_sorted, channel_comments_amount_sorted = zip(*sorted_data)

category_sorted, views_category_sorted, likes_category_sorted, comments_category_sorted = zip(*sorted_data2)

test_data = {
    'channel': chanel_sorted[:15],
    'comm_len': channel_comments_length_sorted[:15],
    'comm_amount': channel_comments_amount_sorted[:15]
}
test_data2 = {
    'category': category_sorted,
    'views': views_category_sorted,
    'likes': likes_category_sorted,
    'comments': comments_category_sorted
}
test_df2 = pd.DataFrame(test_data2)
plot_engagement_by_category(test_df2)

test_df = pd.DataFrame(test_data)
avg_comm_len_by_channel(test_df)

plot_views_vs_video_length(df_short_videos, df_long_videos)
plot_views_vs_video_length(df_videos)

plot_comment_count_vs_length(comment_stats_shorts, "Shorts")
plot_comment_count_vs_length(comment_stats_long_video, "Long videos")

if all_comment_lengths:
    plot_comment_count_vs_length(comment_stats_all, "All videos")
